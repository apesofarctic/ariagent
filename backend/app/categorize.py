"""Merchant → category. Rules table first, local LLM for the leftovers.

Deterministic when USE_LLM=false: unmatched merchants become "other".
Runs entirely on-device (Ollama); merchant strings are the only thing sent.
"""
import json
import re

from .llm import chat

CATEGORIES = [
    "salary", "rent", "subscription", "food", "groceries", "transport",
    "shopping", "utilities", "health", "entertainment", "emi", "insurance",
    "investment", "transfer", "cash", "education", "travel", "other",
]

# keyword (substring, lowercase) → category. Order matters: first hit wins.
RULES: list[tuple[str, str]] = [
    ("salary", "salary"), ("payroll", "salary"), ("sal cr", "salary"),
    ("rent", "rent"), ("landlord", "rent"), ("nobroker", "rent"),
    ("netflix", "subscription"), ("spotify", "subscription"), ("hotstar", "subscription"),
    ("prime video", "subscription"), ("primevideo", "subscription"), ("youtube", "subscription"),
    ("apple.com", "subscription"), ("google one", "subscription"), ("sonyliv", "subscription"),
    ("jiocinema", "subscription"), ("audible", "subscription"), ("gaana", "subscription"),
    ("swiggy", "food"), ("zomato", "food"), ("eatsure", "food"), ("dominos", "food"),
    ("mcdonald", "food"), ("kfc", "food"), ("restaurant", "food"), ("cafe", "food"),
    ("chai", "food"), ("starbucks", "food"), ("barista", "food"),
    ("bigbasket", "groceries"), ("blinkit", "groceries"), ("zepto", "groceries"),
    ("instamart", "groceries"), ("dmart", "groceries"), ("grofers", "groceries"),
    ("reliance fresh", "groceries"), ("more supermarket", "groceries"), ("kirana", "groceries"),
    ("uber", "transport"), ("ola", "transport"), ("rapido", "transport"),
    ("irctc", "transport"), ("redbus", "transport"), ("metro", "transport"),
    ("petrol", "transport"), ("fuel", "transport"), ("hpcl", "transport"),
    ("iocl", "transport"), ("bpcl", "transport"), ("fastag", "transport"),
    ("amazon", "shopping"), ("flipkart", "shopping"), ("myntra", "shopping"),
    ("ajio", "shopping"), ("nykaa", "shopping"), ("meesho", "shopping"),
    ("ikea", "shopping"), ("decathlon", "shopping"), ("croma", "shopping"),
    ("electricity", "utilities"), ("bescom", "utilities"), ("mseb", "utilities"),
    ("airtel", "utilities"), ("jio", "utilities"), ("vi ", "utilities"),
    ("vodafone", "utilities"), ("bsnl", "utilities"), ("broadband", "utilities"),
    ("act fibernet", "utilities"), ("tata power", "utilities"), ("gas", "utilities"),
    ("water bill", "utilities"), ("bwssb", "utilities"),
    ("pharmacy", "health"), ("apollo", "health"), ("medplus", "health"),
    ("1mg", "health"), ("pharmeasy", "health"), ("netmeds", "health"),
    ("clinic", "health"), ("hospital", "health"), ("diagnostic", "health"),
    ("lab ", "health"), ("practo", "health"),
    ("bookmyshow", "entertainment"), ("pvr", "entertainment"), ("inox", "entertainment"),
    ("steam", "entertainment"), ("playstation", "entertainment"),
    ("emi", "emi"), ("loan", "emi"), ("bajaj fin", "emi"), ("home credit", "emi"),
    ("lic ", "insurance"), ("policy", "insurance"), ("insurance", "insurance"),
    ("acko", "insurance"), ("digit", "insurance"), ("star health", "insurance"),
    ("sip", "investment"), ("zerodha", "investment"), ("groww", "investment"),
    ("mutual fund", "investment"), ("kuvera", "investment"), ("coin", "investment"),
    ("nps", "investment"), ("ppf", "investment"),
    ("atm", "cash"), ("cash wdl", "cash"), ("csh wdl", "cash"),
    ("school", "education"), ("college", "education"), ("udemy", "education"),
    ("coursera", "education"), ("byjus", "education"), ("tuition", "education"),
    ("makemytrip", "travel"), ("goibibo", "travel"), ("cleartrip", "travel"),
    ("indigo", "travel"), ("air india", "travel"), ("vistara", "travel"),
    ("oyo", "travel"), ("airbnb", "travel"), ("hotel", "travel"),
    ("upi", "transfer"), ("imps", "transfer"), ("neft", "transfer"), ("rtgs", "transfer"),
]

_LLM_SYSTEM = (
    "You classify bank-statement merchants into spending categories. "
    f"Allowed categories: {', '.join(CATEGORIES)}. "
    'Reply with ONLY a JSON object mapping each merchant to a category, e.g. {"ACME": "shopping"}.'
)


def categorize_by_rules(merchant: str) -> str | None:
    m = merchant.lower()
    for kw, cat in RULES:
        if kw in m:
            return cat
    return None


def _categorize_by_llm(merchants: list[str]) -> dict[str, str]:
    """Batch-classify unknown merchants with the local model. Empty dict on failure."""
    out: dict[str, str] = {}
    for i in range(0, len(merchants), 20):
        batch = merchants[i:i + 20]
        reply = chat(_LLM_SYSTEM, "Classify these merchants: " + json.dumps(batch), temperature=0.0)
        if not reply:
            continue
        match = re.search(r"\{.*\}", reply, re.DOTALL)
        if not match:
            continue
        try:
            parsed = json.loads(match.group(0))
        except json.JSONDecodeError:
            continue
        for k, v in parsed.items():
            if isinstance(v, str) and v.lower() in CATEGORIES:
                out[k] = v.lower()
    return out


def categorize(merchants: list[str]) -> tuple[dict[str, str], dict]:
    """Map each distinct merchant to a category.

    Returns (mapping, stats) where stats counts rules / llm / fallback assignments.
    Credits vs debits are not needed here — salary etc. is caught by keywords.
    """
    unique = list(dict.fromkeys(merchants))
    mapping: dict[str, str] = {}
    unknown: list[str] = []
    for m in unique:
        cat = categorize_by_rules(m)
        if cat:
            mapping[m] = cat
        else:
            unknown.append(m)

    llm_hits = _categorize_by_llm(unknown) if unknown else {}
    for m in unknown:
        mapping[m] = llm_hits.get(m, "other")

    stats = {
        "merchants": len(unique),
        "by_rules": len(unique) - len(unknown),
        "by_llm": len(llm_hits),
        "uncategorized": len(unknown) - len(llm_hits),
    }
    return mapping, stats
