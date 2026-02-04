import re
from typing import Any, Dict, Iterable, List, Optional


_LOCAL_HINTS = {
    "near me",
    "nearby",
    "open now",
    "closest",
    "local",
    "mobile",
    "in ",
    "near ",
}

_COMMERCIAL_HINTS = {
    "price",
    "cost",
    "pricing",
    "quote",
    "booking",
    "book",
    "appointment",
    "deal",
    "coupon",
    "cheap",
    "best",
    "top",
    "reviews",
}

_INFORMATIONAL_HINTS = {
    "how to",
    "what is",
    "why",
    "guide",
    "tips",
    "benefits",
    "pros and cons",
    "mistakes",
    "schedule",
    "frequency",
    "checklist",
}


def _normalize_phrase(phrase: str) -> str:
    return " ".join(phrase.strip().split())


def classify_intent(phrase: str) -> str:
    """Classify intent into local_service, informational, commercial, or other."""
    normalized = phrase.lower().strip()

    if any(hint in normalized for hint in _LOCAL_HINTS):
        return "local_service"
    if any(hint in normalized for hint in _COMMERCIAL_HINTS):
        return "commercial"
    if any(hint in normalized for hint in _INFORMATIONAL_HINTS):
        return "informational"

    if re.match(r"^(how|what|why|when|where)\b", normalized):
        return "informational"

    return "other"


def _candidate_phrase(candidate: Dict[str, Any]) -> Optional[str]:
    for key in ("keyword", "phrase", "text", "query"):
        value = candidate.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return None


def extract_longtail_candidates(
    seed_keyword: str,
    candidates: Iterable[Dict[str, Any]],
    min_words: int = 3,
    max_items: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Extract, normalize, and dedupe longtail candidates."""
    unique: Dict[str, Dict[str, Any]] = {}
    seed_norm = _normalize_phrase(seed_keyword).lower()

    for candidate in candidates:
        phrase = _candidate_phrase(candidate)
        if not phrase:
            continue
        phrase_norm = _normalize_phrase(phrase)
        phrase_key = phrase_norm.lower()

        if phrase_key == seed_norm:
            continue
        if len(phrase_norm.split()) < min_words:
            continue

        if phrase_key not in unique:
            unique[phrase_key] = {
                "phrase": phrase_norm,
                "source": candidate.get("source") or candidate.get("type") or "unknown",
                "type": candidate.get("type") or "unknown",
                "search_volume": candidate.get("search_volume", 0) or 0,
                "cpc": candidate.get("cpc", 0.0) or 0.0,
                "competition": candidate.get("competition", 0.0) or 0.0,
                "keyword_difficulty": candidate.get("keyword_difficulty", 50.0) or 50.0,
                "evidence_urls": candidate.get("evidence_urls", []) or [],
            }

    items: List[Dict[str, Any]] = []
    for item in unique.values():
        item["intent"] = classify_intent(item["phrase"])
        items.append(item)

    if max_items is not None:
        items = items[:max_items]

    return items


def bucket_longtail_candidates(items: Iterable[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    buckets = {
        "local_service": [],
        "informational": [],
        "commercial": [],
        "other": [],
    }

    for item in items:
        intent = item.get("intent") or "other"
        if intent not in buckets:
            intent = "other"
        buckets[intent].append(item)

    return buckets
