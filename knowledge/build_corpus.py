"""Turn the fetched RBI FAQ pages into retrievable passages.

One passage = one Q/A pair. The indexed text is the ANSWER ONLY; the official
question is held out as an evaluation query. That split is deliberate: if the
question were indexed alongside its answer, lexical search would win every query
by copying the words back, and the retrieval numbers would measure nothing.

RBI publishes these pages in four different markups accumulated over twenty
years (numbered <p class="head">, bold <strong> headings, "Query:/Clarification:"
tables, "Query:/Response:" runs). The block walker below handles all four rather
than one, which is why the yield is 39 documents instead of 30.
"""
from __future__ import annotations

import html
import json
import re
from pathlib import Path

RAW = Path(__file__).resolve().parent / "raw"
OUT = Path(__file__).resolve().parent / "passages.jsonl"

TAG = re.compile(r"<[^>]+>")
WS = re.compile(r"\s+")
BLOCK_END = re.compile(r"</(p|tr|li|div|h[1-6])>|<br\s*/?>", re.I)
# "12.", "12)", "Q.12", "Query 12:", "12. Query:"
QNUM = re.compile(r"^\s*(?:Q\s*\.?\s*)?(\d+)\s*[\.\):]\s*(?:Query\s*[:.]?\s*)?(.*)$", re.S | re.I)
QWORD = re.compile(r"^\s*Query\s*\d*\s*[:.]\s*(.*)$", re.S | re.I)
ANSWER_MARK = re.compile(r"\b(?:Ans(?:wer)?|Clarification|Response|Reply)\s*[:.\-]\s*", re.I)
# supervisory / licensing / market-infrastructure documents: not what a retail
# customer assistant answers from, kept out of the index by document id.
NON_RETAIL_DOCS = {
    "1169", "1505", "1506", "956", "325", "3900", "3138", "3285", "3324",
    "2995", "3822", "3230", "3573",
}


def clean(fragment: str) -> str:
    fragment = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", fragment, flags=re.S | re.I)
    return WS.sub(" ", html.unescape(TAG.sub(" ", fragment))).strip()


def content_region(page: str) -> str:
    m = re.search(r"<td[^>]*class=['\"]textDetails['\"][^>]*>(.*)", page, re.S | re.I)
    body = m.group(1) if m else page
    end = re.search(r"<!--\s*Content end|id=['\"]pnlTop", body, re.I)
    return body[: end.start()] if end else body


def blocks(body: str) -> list[str]:
    out: list[str] = []
    for raw in BLOCK_END.split(body):
        if raw is None:
            continue
        t = clean(raw)
        if t and t not in {"&nbsp;", "Top"}:
            out.append(t)
    return out


def as_question(block: str) -> str | None:
    """Return the question text if this block opens a Q/A pair."""
    for pat in (QNUM, QWORD):
        m = pat.match(block)
        if not m:
            continue
        q = WS.sub(" ", m.group(m.lastindex)).strip()
        if "?" in q:
            q = q[: q.index("?") + 1]
        if 12 <= len(q) <= 400 and q.endswith("?"):
            return q
    return None


def parse(page: str) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    q: str | None = None
    buf: list[str] = []
    for block in blocks(content_region(page)):
        # a block that carries both halves, e.g. "Query 1: ... Clarification: ..."
        head = as_question(block)
        if head:
            if q and buf:
                pairs.append((q, " ".join(buf)))
            q, buf = head, []
            tail = ANSWER_MARK.split(block, maxsplit=1)
            if len(tail) > 1 and len(tail[-1]) > 60:
                buf.append(tail[-1].strip())
            continue
        if q is None:
            continue
        block = ANSWER_MARK.sub("", block, count=1).strip()
        if block:
            buf.append(block)
    if q and buf:
        pairs.append((q, " ".join(buf)))
    return [(q, a) for q, a in pairs if len(a) >= 120]


def main() -> None:
    index = json.loads((RAW / "index.json").read_text())
    rows: list[dict] = []
    per_doc: list[tuple[str, int, bool]] = []
    for fid, meta in index.items():
        page = (RAW / f"faq_{fid}.html").read_text(encoding="utf-8", errors="ignore")
        pairs = parse(page)
        retail = fid not in NON_RETAIL_DOCS
        per_doc.append((meta["title"][:58], len(pairs), retail))
        if not retail:
            continue
        title = re.sub(r"^\w{3} \d{2}, \d{4} - ", "", meta["title"]).strip()
        for j, (q, a) in enumerate(pairs):
            rows.append({
                "passage_id": f"rbi-{fid}-{j:03d}",
                "doc_id": fid,
                "doc_title": title,
                "section": meta["section"],
                "question": q,
                "text": WS.sub(" ", a).strip()[:2400],
                "n_words": len(a.split()),
            })
    with OUT.open("w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    for t, n, keep in sorted(per_doc, key=lambda x: -x[1]):
        print(f"{'  ' if keep else 'x '}{n:4d}  {t}")
    words = sum(r["n_words"] for r in rows)
    med = sorted(r["n_words"] for r in rows)[len(rows) // 2]
    docs = len({r["doc_id"] for r in rows})
    print(f"\nindexed {len(rows)} passages from {docs} retail documents, "
          f"{words:,} words, median {med} words/passage")


if __name__ == "__main__":
    main()
