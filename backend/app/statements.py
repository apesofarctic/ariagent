"""Bank-statement import: parse CSV / Excel / PDF, detect a column mapping,
normalize confirmed rows into the Transaction schema. All on-device.

Flow: POST /api/data/upload → parse() + detect_mapping() → user confirms/edits
the mapping in the UI → POST /api/data/import → normalize() → categorize → store.
"""
import csv
import io
import re
import uuid
from datetime import date, datetime

from .schemas import Transaction

# in-memory stash of parsed uploads awaiting confirmation: token → payload
_PENDING: dict[str, dict] = {}

DATE_FORMATS = [
    "%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d/%m/%y", "%d-%m-%y",
    "%d %b %Y", "%d-%b-%Y", "%d %B %Y", "%b %d, %Y", "%m/%d/%Y", "%Y/%m/%d",
]

_DATE_HINTS = ["txn date", "transaction date", "value date", "date", "posted"]
_MERCHANT_HINTS = ["narration", "description", "particulars", "merchant",
                   "details", "remarks", "transaction details", "payee"]
_AMOUNT_HINTS = ["amount", "amt", "transaction amount"]
_DEBIT_HINTS = ["debit", "withdrawal", "withdrawal amt", "dr amount", "dr"]
_CREDIT_HINTS = ["credit", "deposit", "deposit amt", "cr amount", "cr"]
_CATEGORY_HINTS = ["category", "type of expense"]
_BALANCE_HINTS = ["closing balance", "balance", "running balance", "available balance"]


# ---------------------------------------------------------------- value parsing

def parse_date(value) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    s = str(value or "").strip().strip('"')
    if not s:
        return None
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def parse_amount(value) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value or "").strip().strip('"')
    if not s or s in ("-", "--"):
        return None
    neg = s.startswith("(") and s.endswith(")")
    sign = -1.0 if neg or re.search(r"\bDR\b", s, re.I) else 1.0
    s = re.sub(r"[^0-9.\-]", "", s.replace(",", ""))
    if not s or s == "-":
        return None
    try:
        val = float(s)
    except ValueError:
        return None
    return abs(val) * sign if (neg or sign < 0) else val


# ---------------------------------------------------------------- file parsing

def parse_file(filename: str, content: bytes) -> tuple[list[str], list[list]]:
    """Returns (columns, rows). Raises ValueError with a friendly message."""
    name = filename.lower()
    if name.endswith(".csv") or name.endswith(".txt"):
        return _parse_csv(content)
    if name.endswith(".xlsx") or name.endswith(".xls"):
        return _parse_excel(content)
    if name.endswith(".pdf"):
        return _parse_pdf(content)
    raise ValueError("Unsupported file type — upload a CSV, Excel (.xlsx) or PDF statement.")


def _parse_csv(content: bytes) -> tuple[list[str], list[list]]:
    text = content.decode("utf-8-sig", errors="replace")
    # some bank CSVs prepend preamble lines before the real header — find the
    # first line that looks like a header (≥3 delimited cells, one a date-ish word)
    lines = text.splitlines()
    reader = list(csv.reader(lines))
    start = 0
    for i, row in enumerate(reader[:20]):
        cells = [c.strip().lower() for c in row if c.strip()]
        if len(cells) >= 3 and any("date" in c for c in cells):
            start = i
            break
    rows = [r for r in reader[start:] if any(c.strip() for c in r)]
    if len(rows) < 2:
        raise ValueError("Couldn't find a table in this CSV.")
    header = [c.strip() for c in rows[0]]
    width = len(header)
    body = [(r + [""] * width)[:width] for r in rows[1:]]
    return header, body


def _parse_excel(content: bytes) -> tuple[list[str], list[list]]:
    import openpyxl
    wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    ws = wb.active
    raw = [[c for c in row] for row in ws.iter_rows(values_only=True)]
    wb.close()
    raw = [r for r in raw if any(c is not None and str(c).strip() for c in r)]
    # find header row: ≥3 non-empty string cells, one mentioning "date"
    start = 0
    for i, row in enumerate(raw[:20]):
        cells = [str(c).strip().lower() for c in row if c is not None and str(c).strip()]
        if len(cells) >= 3 and any("date" in c for c in cells):
            start = i
            break
    if len(raw) - start < 2:
        raise ValueError("Couldn't find a table in this spreadsheet.")
    header = [str(c).strip() if c is not None else f"col{j}" for j, c in enumerate(raw[start])]
    body = [list(r) for r in raw[start + 1:]]
    width = len(header)
    body = [(r + [None] * width)[:width] for r in body]
    return header, body


def _parse_pdf(content: bytes) -> tuple[list[str], list[list]]:
    import pdfplumber
    tables: list[list[list]] = []
    with pdfplumber.open(io.BytesIO(content)) as pdf:
        for page in pdf.pages:
            for tbl in page.extract_tables() or []:
                if tbl and len(tbl[0]) >= 3:
                    tables.append(tbl)
    if not tables:
        raise ValueError(
            "No table found in this PDF. If the statement is a scan, "
            "export CSV/Excel from your bank instead.")
    header = [str(c or "").strip().replace("\n", " ") for c in tables[0][0]]
    width = len(header)
    body: list[list] = []
    for tbl in tables:
        rows = tbl[1:] if [str(c or "").strip().replace("\n", " ") for c in tbl[0]] == header else tbl
        for r in rows:
            r = [str(c or "").replace("\n", " ").strip() for c in r]
            if any(r):
                body.append((r + [""] * width)[:width])
    return header, body


# ---------------------------------------------------------------- mapping

def _match(columns: list[str], hints: list[str], taken: set[str]) -> str | None:
    low = {c: c.lower().strip() for c in columns}
    for hint in hints:
        for col, lc in low.items():
            if col not in taken and hint == lc:
                return col
    for hint in hints:
        for col, lc in low.items():
            if col not in taken and hint in lc:
                return col
    return None


def detect_mapping(columns: list[str], rows: list[list]) -> dict:
    """Best-guess mapping of source columns onto the Transaction schema."""
    taken: set[str] = set()
    mapping: dict[str, str | None] = {}

    mapping["date"] = _match(columns, _DATE_HINTS, taken)
    if mapping["date"]:
        taken.add(mapping["date"])
    mapping["merchant"] = _match(columns, _MERCHANT_HINTS, taken)
    if mapping["merchant"]:
        taken.add(mapping["merchant"])
    mapping["category"] = _match(columns, _CATEGORY_HINTS, taken)
    if mapping["category"]:
        taken.add(mapping["category"])
    mapping["balance"] = _match(columns, _BALANCE_HINTS, taken)
    if mapping["balance"]:
        taken.add(mapping["balance"])

    debit = _match(columns, _DEBIT_HINTS, taken)
    credit = _match(columns, _CREDIT_HINTS, taken | ({debit} if debit else set()))
    if debit and credit:
        mapping["debit"], mapping["credit"], mapping["amount"] = debit, credit, None
        taken |= {debit, credit}
    else:
        mapping["debit"] = mapping["credit"] = None
        mapping["amount"] = _match(columns, _AMOUNT_HINTS, taken)
        if mapping["amount"]:
            taken.add(mapping["amount"])

    # fallbacks by sniffing values in the first rows
    if not mapping["date"]:
        for j, col in enumerate(columns):
            if col in taken:
                continue
            hits = sum(1 for r in rows[:10] if j < len(r) and parse_date(r[j]))
            if hits >= max(2, len(rows[:10]) // 2):
                mapping["date"] = col
                taken.add(col)
                break
    if not mapping["amount"] and not (mapping["debit"] and mapping["credit"]):
        for j, col in enumerate(columns):
            if col in taken:
                continue
            hits = sum(1 for r in rows[:10] if j < len(r) and parse_amount(r[j]) is not None)
            if hits >= max(2, len(rows[:10]) // 2):
                mapping["amount"] = col
                taken.add(col)
                break
    if not mapping["merchant"]:
        for col in columns:
            if col not in taken:
                mapping["merchant"] = col
                break
    return mapping


# ---------------------------------------------------------------- normalize

def normalize(columns: list[str], rows: list[list], mapping: dict) -> tuple[list[dict], list[str]]:
    """Apply a confirmed mapping. Returns (clean rows, per-row error notes).

    Output rows are dicts {date, amount, merchant, category|None, balance|None};
    category is filled by the categorizer afterwards when absent.
    """
    idx = {c: i for i, c in enumerate(columns)}

    def cell(row, key):
        col = mapping.get(key)
        if not col or col not in idx or idx[col] >= len(row):
            return None
        return row[idx[col]]

    out: list[dict] = []
    errors: list[str] = []
    for n, row in enumerate(rows, start=1):
        d = parse_date(cell(row, "date"))
        if not d:
            errors.append(f"row {n}: unreadable date — skipped")
            continue
        if mapping.get("debit") and mapping.get("credit"):
            dr = parse_amount(cell(row, "debit")) or 0.0
            cr = parse_amount(cell(row, "credit")) or 0.0
            if dr == 0.0 and cr == 0.0:
                errors.append(f"row {n}: no amount — skipped")
                continue
            amount = cr - abs(dr)
        else:
            amount = parse_amount(cell(row, "amount"))
            if amount is None:
                errors.append(f"row {n}: unreadable amount — skipped")
                continue
        merchant = str(cell(row, "merchant") or "").strip() or "Unknown"
        merchant = re.sub(r"\s+", " ", merchant)[:80]
        category = str(cell(row, "category") or "").strip().lower() or None
        balance = parse_amount(cell(row, "balance"))
        out.append({"date": d, "amount": round(amount, 2), "merchant": merchant,
                    "category": category, "balance": balance})
    out.sort(key=lambda r: r["date"])
    return out, errors


def to_transactions(clean_rows: list[dict], categories: dict[str, str]) -> list[Transaction]:
    return [Transaction(date=r["date"], amount=r["amount"], merchant=r["merchant"],
                        category=r["category"] or categories.get(r["merchant"], "other"))
            for r in clean_rows]


def derive_profile(clean_rows: list[dict], name: str = "You") -> dict:
    """Build the profile the detectors need from an imported statement."""
    balance = None
    for r in reversed(clean_rows):
        if r.get("balance") is not None:
            balance = r["balance"]
            break
    if balance is None:
        balance = round(max(0.0, sum(r["amount"] for r in clean_rows)), 2)

    recurring = []
    salary = [r for r in clean_rows if r["amount"] > 0 and (r.get("category") == "salary")]
    if salary:
        recurring.append({"type": "salary",
                          "day_of_month": max(salary, key=lambda r: r["date"])["date"].day,
                          "amount": round(max(r["amount"] for r in salary), 2)})
    rent = [r for r in clean_rows if r["amount"] < 0 and (r.get("category") == "rent")]
    if rent:
        recurring.append({"type": "rent",
                          "day_of_month": max(rent, key=lambda r: r["date"])["date"].day,
                          "amount": round(max(abs(r["amount"]) for r in rent), 2)})
    return {"name": name, "current_balance": balance, "consent": True, "recurring": recurring}


# ---------------------------------------------------------------- pending stash

def stash(filename: str, columns: list[str], rows: list[list]) -> str:
    token = uuid.uuid4().hex
    _PENDING[token] = {"filename": filename, "columns": columns, "rows": rows}
    if len(_PENDING) > 8:                      # keep memory bounded
        _PENDING.pop(next(iter(_PENDING)))
    return token


def pop_pending(token: str) -> dict | None:
    return _PENDING.get(token)


def clear_pending(token: str) -> None:
    _PENDING.pop(token, None)
