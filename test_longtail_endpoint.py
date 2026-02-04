#!/usr/bin/env python3
"""
Test the /api/v1/keywords/longtail endpoint and basic invariants.
"""

import json
import requests

BASE_URL = "https://blog-writer-api-dev-kq42l26tuq-od.a.run.app"


def test_longtail(keyword: str) -> None:
    url = f"{BASE_URL}/api/v1/keywords/longtail"
    payload = {
        "keyword": keyword,
        "location": "United States",
        "language": "en",
        "min_words": 3,
        "include_autocomplete": True,
        "include_paa": True,
        "include_related": True,
        "include_keyword_ideas": True,
        "include_evidence_urls": True,
        "limit": 100,
    }

    print(f"Testing longtail endpoint for: {keyword}")
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}\n")

    response = requests.post(url, json=payload, timeout=300)
    response.raise_for_status()
    data = response.json()

    items = data.get("items", [])
    min_words = payload["min_words"]

    # Invariants
    invalid = [i for i in items if len(i.get("phrase", "").split()) < min_words]
    print(f"Total items: {len(items)}")
    print(f"Invalid (<{min_words} words): {len(invalid)}")

    if invalid:
        print("Sample invalid items:")
        for item in invalid[:5]:
            print(f"- {item.get('phrase')}")

    print("\nBuckets summary:")
    for bucket, bucket_items in data.get("buckets", {}).items():
        print(f"- {bucket}: {len(bucket_items)}")

    print("\nSample items:")
    for item in items[:10]:
        print(f"- {item.get('phrase')} ({item.get('source')}, {item.get('intent')})")


if __name__ == "__main__":
    test_longtail("dog groomer")
