import csv
import io
import json
import zipfile
from datetime import datetime, timezone

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from . import config, statements, store
from .categorize import categorize
from .data_generator import generate
from .forecast import forecast_balance
from .llm import llm_off
from .pipeline import run_pipeline

app = FastAPI(title="Ariagent")
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

# ---------------------------------------------------------------- demo state (in-memory)

DEMO_PROFILE = {
    "name": "Priya", "current_balance": 8000.0, "consent": True,
    "recurring": [
        {"type": "salary", "day_of_month": 1, "amount": 57500},
        {"type": "rent", "day_of_month": 28, "amount": 25000},
    ],
}
DEMO_TXNS = generate()          # replaced when the user uploads a test CSV
DEMO_SOURCE = "synthetic"

REAL_PROFILE_KEY = "real_profile"


def _active():
    """(txns, profile, is_real) for the current data mode."""
    if store.get_data_mode() == "real":
        txns = store.get_transactions()
        raw = store.get_setting(REAL_PROFILE_KEY)
        if txns and raw:
            return txns, json.loads(raw), True
        # real mode but nothing imported — fall back to demo rather than 500
    return DEMO_TXNS, DEMO_PROFILE, False


def _require_consent() -> dict:
    consent = store.get_consent()
    if not consent["granted"]:
        raise HTTPException(status_code=403, detail="Consent required before real data flows.")
    return consent


# ---------------------------------------------------------------- status / profile / txns

@app.get("/api/status")
def status():
    consent = store.get_consent()
    return {
        "data_mode": store.get_data_mode(),
        "consent": consent,
        "use_llm": config.USE_LLM,
        "llm_model": config.LLM_MODEL if config.USE_LLM else None,
        "real_data": store.real_data_meta(),
        "demo_source": DEMO_SOURCE,
    }


@app.get("/api/profile")
def profile():
    txns, prof, is_real = _active()
    return {"profile": prof, "balance": prof["current_balance"], "real": is_real}


@app.get("/api/transactions")
def transactions():
    txns, _, _ = _active()
    return [t.model_dump(mode="json") for t in txns]


@app.get("/api/forecast")
def forecast():
    txns, prof, _ = _active()
    return forecast_balance(txns, prof)


# ---------------------------------------------------------------- the agent stream

@app.get("/api/stream")
async def stream(mode: str = "live"):
    txns, prof, is_real = _active()
    consent = store.get_consent()
    consented = (set(k for k, v in consent["scopes"].items() if v)
                 if consent["granted"] else {"protect", "grow", "guide"})
    profile_for_run = {**prof, "consent": True}
    skip = store.deleted_inference_types()

    async def gen():
        if mode == "scripted":
            llm_off.set(True)   # deterministic text, same pipeline
        async for event in run_pipeline(
                txns, profile_for_run,
                consented_modes=consented,
                prepare_only=is_real,       # real data: analyse-only, never execute
                record=True, skip_types=skip):
            yield {"data": json.dumps(event, default=str)}
    return EventSourceResponse(gen())


# ---------------------------------------------------------------- consent

class ConsentBody(BaseModel):
    scopes: dict[str, bool]
    adult: bool


@app.get("/api/consent")
def get_consent():
    return store.get_consent()


@app.post("/api/consent")
def post_consent(body: ConsentBody):
    if not body.adult:
        raise HTTPException(status_code=400, detail="Ariagent is only for adult account holders.")
    scopes = {k: bool(body.scopes.get(k)) for k in ("protect", "grow", "guide")}
    if not any(scopes.values()):
        raise HTTPException(status_code=400, detail="Opt in to at least one mode.")
    rec = store.save_consent(scopes, body.adult)
    store.audit("user", "consent_granted",
                "Consent granted for: " + ", ".join(k for k, v in scopes.items() if v),
                "DPDP §6 — free, specific, informed opt-in", True, "system", "info")
    return rec


@app.delete("/api/consent")
def revoke_consent():
    store.revoke_consent()
    store.audit("user", "consent_revoked",
                "Consent withdrawn; processing stopped, mode reset to demo",
                "DPDP §6(4) — withdrawal as easy as giving", False, "system", "info")
    return store.get_consent()


# ---------------------------------------------------------------- data: upload / import / mode

@app.post("/api/data/upload")
async def upload(file: UploadFile = File(...), target: str = Form("demo")):
    if target == "real":
        _require_consent()
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (10 MB max).")
    try:
        columns, rows = statements.parse_file(file.filename or "upload.csv", content)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not rows:
        raise HTTPException(status_code=400, detail="No data rows found in the file.")
    mapping = statements.detect_mapping(columns, rows)
    token = statements.stash(file.filename or "upload", columns, rows)
    preview = [[("" if c is None else str(c)) for c in r] for r in rows[:15]]
    return {"token": token, "filename": file.filename, "columns": columns,
            "mapping": mapping, "preview": preview, "total_rows": len(rows)}


class ImportBody(BaseModel):
    token: str
    mapping: dict
    target: str = "demo"    # "demo" (test CSV) or "real" (Mode B)


@app.post("/api/data/import")
def import_data(body: ImportBody):
    global DEMO_TXNS, DEMO_SOURCE
    if body.target == "real":
        _require_consent()
    pending = statements.pop_pending(body.token)
    if not pending:
        raise HTTPException(status_code=400, detail="Upload expired — please upload the file again.")
    clean, errors = statements.normalize(pending["columns"], pending["rows"], body.mapping)
    if not clean:
        raise HTTPException(status_code=400,
                            detail="No usable rows after mapping. Check the column assignment. "
                                   + (errors[0] if errors else ""))

    need_category = [r["merchant"] for r in clean if not r["category"]]
    cat_map, stats = categorize(need_category)
    for r in clean:
        if not r["category"]:
            r["category"] = cat_map.get(r["merchant"], "other")
    txns = statements.to_transactions(clean, cat_map)

    if body.target == "real":
        n = store.save_transactions(txns, pending["filename"])
        prof = statements.derive_profile(clean, name="You")
        store.set_setting(REAL_PROFILE_KEY, json.dumps(prof))
        store.set_data_mode("real")
        store.audit("user", "data_imported",
                    f"Imported {n} transactions from {pending['filename']} (real data, on-device)",
                    "BYO statement — DPDP-consented, analyse-only", True, "system", "info")
    else:
        DEMO_TXNS = txns
        DEMO_SOURCE = f"csv:{pending['filename']}"
        DEMO_PROFILE.update(statements.derive_profile(clean, name=DEMO_PROFILE["name"]))
    statements.clear_pending(body.token)
    return {"imported": len(txns), "skipped": len(errors), "errors": errors[:10],
            "categorizer": stats, "target": body.target,
            "date_range": [str(txns[0].date), str(txns[-1].date)]}


class ModeBody(BaseModel):
    mode: str


@app.post("/api/data/mode")
def set_mode(body: ModeBody):
    if body.mode not in ("demo", "real"):
        raise HTTPException(status_code=400, detail="mode must be 'demo' or 'real'")
    if body.mode == "real":
        _require_consent()
        if store.real_data_meta()["count"] == 0:
            raise HTTPException(status_code=400, detail="No real data imported yet.")
    store.set_data_mode(body.mode)
    return {"data_mode": body.mode}


@app.post("/api/data/demo/reset")
def reset_demo():
    global DEMO_TXNS, DEMO_SOURCE
    DEMO_TXNS = generate()
    DEMO_SOURCE = "synthetic"
    DEMO_PROFILE.update({"name": "Priya", "current_balance": 8000.0, "recurring": [
        {"type": "salary", "day_of_month": 1, "amount": 57500},
        {"type": "rent", "day_of_month": 28, "amount": 25000},
    ]})
    return {"ok": True, "transactions": len(DEMO_TXNS)}


# ---------------------------------------------------------------- transparency / audit / rights

@app.get("/api/inferences")
def inferences():
    return store.get_inferences()


@app.delete("/api/inferences/{inference_id}")
def delete_inference(inference_id: int):
    type_ = store.delete_inference(inference_id)
    if not type_:
        raise HTTPException(status_code=404, detail="Inference not found.")
    store.audit("user", "inference_deleted",
                f"User marked inference '{type_}' as wrong — it will not be re-drawn",
                "DPDP §11–12 — right to correction", False, "system", "info")
    return {"deleted": type_}


@app.get("/api/audit")
def audit_log():
    return store.get_audit()


@app.get("/api/export")
def export(format: str = "json"):
    data = store.export_all()
    data["data_mode"] = store.get_data_mode()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M")
    if format == "json":
        return Response(
            content=json.dumps(data, indent=2, default=str),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=ariagent-export-{stamp}.json"})

    def to_csv(rows: list[dict]) -> str:
        if not rows:
            return ""
        buf = io.StringIO()
        w = csv.DictWriter(buf, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow({k: (json.dumps(v) if isinstance(v, (list, dict)) else v)
                        for k, v in r.items()})
        return buf.getvalue()

    zbuf = io.BytesIO()
    with zipfile.ZipFile(zbuf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("transactions.csv", to_csv(data["transactions"]))
        z.writestr("inferences.csv", to_csv(data["inferences"]))
        z.writestr("audit_log.csv", to_csv(data["audit_log"]))
        z.writestr("consent.json", json.dumps(data["consent"], indent=2, default=str))
    return Response(
        content=zbuf.getvalue(), media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=ariagent-export-{stamp}.zip"})


@app.delete("/api/data")
def delete_data():
    global DEMO_TXNS, DEMO_SOURCE
    store.delete_everything()
    DEMO_TXNS = generate()
    DEMO_SOURCE = "synthetic"
    return {"deleted": True}
