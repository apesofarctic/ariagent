import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
from .data_generator import generate
from .pipeline import run_pipeline

app = FastAPI(title="AriAgent")
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

PROFILE = {
    "name": "Apoorva", "current_balance": 8000.0, "consent": True,
    "recurring": [
        {"type": "salary", "day_of_month": 1, "amount": 50000},
        {"type": "rent", "day_of_month": 28, "amount": 25000},
    ],
}
TXNS = generate()


@app.get("/api/profile")
def profile():
    return {"profile": PROFILE, "balance": PROFILE["current_balance"]}


@app.get("/api/transactions")
def transactions():
    return [t.model_dump(mode="json") for t in TXNS]


@app.get("/api/stream")
async def stream():
    async def gen():
        async for event in run_pipeline(TXNS, PROFILE):
            yield {"data": json.dumps(event, default=str)}
    return EventSourceResponse(gen())
