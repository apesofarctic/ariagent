"""Fetch the RBI customer-facing FAQ corpus.

The corpus AriAgent grounds against is not written by us: it is the Reserve Bank
of India's own FAQ set for the common person (rbi.org.in/commonperson), which is
the authority a retail-banking assistant has to agree with. Each FAQ page is one
document; each Q/A pair inside it becomes one retrievable passage, and the
question is a real customer question with a known correct answer -- which is what
makes an honest retrieval evaluation possible without inventing queries.
"""
from __future__ import annotations

import html
import json
import re
import time
from pathlib import Path

import requests

BASE = "https://www.rbi.org.in/commonperson/English/Scripts/"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; ariagent-research/1.0)"}
# Retail-relevant sections only: deposits/banking, payments, consumer protection,
# fintech, deposit insurance, NBFC, financial inclusion.
SECTIONS = [8, 23, 32, 35, 34, 28, 30]
OUT = Path(__file__).resolve().parent / "raw"


def get(url: str) -> str:
    for attempt in range(3):
        try:
            r = requests.get(url, headers=HEADERS, timeout=45)
            if r.status_code == 200:
                return r.text
        except requests.RequestException:
            pass
        time.sleep(2 * (attempt + 1))
    return ""


def faq_links(section_html: str) -> dict[str, str]:
    out: dict[str, str] = {}
    pat = r'<a[^>]*href=["\']?(FAQs\.aspx\?Id=\d+[^"\'>\s]*)["\']?[^>]*>(.*?)</a>'
    for m in re.finditer(pat, section_html, re.S | re.I):
        href, txt = m.group(1), re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", m.group(2))).strip()
        fid = re.search(r"Id=(\d+)", href, re.I)
        if fid and len(txt) > 5:
            out[fid.group(1)] = html.unescape(txt)
    return out


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    index: dict[str, dict] = {}
    for sid in SECTIONS:
        page = get(f"{BASE}FAQs.aspx?SID={sid}")
        found = faq_links(page)
        print(f"section {sid}: {len(found)} FAQ documents")
        for fid, title in found.items():
            if fid in index:
                continue
            body = get(f"{BASE}FAQs.aspx?Id={fid}")
            if not body or len(body) < 4000:
                continue
            (OUT / f"faq_{fid}.html").write_text(body, encoding="utf-8")
            index[fid] = {"id": fid, "title": title, "section": sid, "bytes": len(body)}
            time.sleep(0.4)
    (OUT / "index.json").write_text(json.dumps(index, indent=2), encoding="utf-8")
    print(f"total {len(index)} FAQ documents saved")


if __name__ == "__main__":
    main()
