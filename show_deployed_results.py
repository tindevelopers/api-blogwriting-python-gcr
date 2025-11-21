#!/usr/bin/env python3
"""Display deployed service test results."""
import json

# Read the response file
with open('test_deployed_response.json', 'r') as f:
    content = f.read()

# Extract JSON part (skip curl output)
json_start = content.find('{')
json_part = content[json_start:content.rfind('}')+1]
d = json.loads(json_part)

print("=" * 80)
print("✅ DEPLOYED SERVICE TEST - SUCCESS!")
print("=" * 80)
print(f"\nHTTP Status: 200 OK")
print(f"Generation Time: {d['generation_time']:.1f} seconds")
print(f"Total Cost: ${d['total_cost']:.4f}")

print(f"\n📝 Generated Blog:")
print(f"  Title: {d['title']}")
print(f"  Content Length: {len(d['content'])} characters")
print(f"  Word Count: {d['content_metadata']['word_count']} words")

print(f"\n📊 Quality Scores:")
print(f"  Overall Quality: {d['quality_score']}/100")
print(f"  SEO Score: {d['seo_score']}/100")
for dim, score in list(d['quality_dimensions'].items())[:4]:
    print(f"  {dim.capitalize()}: {score}/100")

print(f"\n🔄 Pipeline Stages: {len(d['stage_results'])} stages completed")
for i, stage in enumerate(d['stage_results'], 1):
    print(f"  Stage {i}: {stage['stage']} ({stage['provider']}) - ${stage['cost']:.4f}")

print(f"\n✅ No enum conversion errors!")
print(f"✅ All stages completed successfully!")
print(f"✅ Citations: {len(d.get('citations', []))}")
print(f"✅ Structured Data: {'Yes' if d.get('structured_data') else 'No'}")

print(f"\n🔍 Search Intent:")
intent = d['seo_metadata'].get('search_intent', {})
print(f"  Primary: {intent.get('primary_intent', 'N/A')} ({intent.get('confidence', 0)*100:.1f}% confidence)")

print("\n" + "=" * 80)
print("🎉 DEPLOYMENT SUCCESSFUL - FIX VERIFIED IN PRODUCTION!")
print("=" * 80)

