#!/usr/bin/env python3
"""Display blog generation results."""
import json
import sys

# Read the response file
with open('test_local_full_response.json', 'r') as f:
    content = f.read()

# Extract JSON part (skip curl output)
json_start = content.find('{')
json_part = content[json_start:content.rfind('}')+1]
d = json.loads(json_part)

print("=" * 80)
print("QUALITY DIMENSIONS")
print("=" * 80)
for dim, score in d['quality_dimensions'].items():
    print(f"  {dim.capitalize()}: {score}/100")

print("\n" + "=" * 80)
print("PIPELINE STAGE RESULTS")
print("=" * 80)
for i, stage in enumerate(d['stage_results'], 1):
    print(f"\nStage {i}: {stage['stage']}")
    print(f"  Provider: {stage['provider']}")
    print(f"  Tokens: {stage['tokens']:,}")
    print(f"  Cost: ${stage['cost']:.4f}")

print("\n" + "=" * 80)
print("SEARCH INTENT ANALYSIS")
print("=" * 80)
intent = d['seo_metadata'].get('search_intent', {})
print(f"Primary Intent: {intent.get('primary_intent', 'N/A')}")
print(f"Confidence: {intent.get('confidence', 0)*100:.1f}%")
print("Probabilities:")
for intent_type, prob in intent.get('probabilities', {}).items():
    print(f"  {intent_type}: {prob*100:.1f}%")

print("\n" + "=" * 80)
print("CONTENT STRUCTURE")
print("=" * 80)
metadata = d.get('content_metadata', {})
print(f"Headings: {len(metadata.get('headings', []))}")
print(f"Images: {len(metadata.get('images', []))}")
print(f"Links: {len(metadata.get('links', []))}")
print(f"Lists: {'Yes' if metadata.get('has_lists') else 'No'}")
print(f"Tables: {'Yes' if metadata.get('has_tables') else 'No'}")

print("\n" + "=" * 80)
print("COST SUMMARY")
print("=" * 80)
print(f"Total Tokens: {d['total_tokens']:,}")
print(f"Total Cost: ${d['total_cost']:.4f}")
print(f"Generation Time: {d['generation_time']:.1f} seconds")
print(f"Cost per 1000 tokens: ${(d['total_cost'] / d['total_tokens'] * 1000):.4f}")

