# Integrations: Backlink & Interlink Recommendations (Target‑Agnostic)

API Version: 1.1.0  
Status: Stable (dev/staging/prod)  
Last Updated: 2025-11-10

## Overview
This endpoint computes recommended backlinks and interlinks for your content based on the keywords you provide. It is target‑agnostic: the backend does not branch on provider specifics. The frontend can pass any provider label and connection payload.

## Endpoint
`POST /api/v1/integrations/connect-and-recommend`

## Request Body
```json
{
  "provider": "custom",
  "tenant_id": "example-tenant",
  "connection": { "any": "opaque-config" },
  "keywords": ["example keyword", "another term"]
}
```

- `provider`: one of `webflow`, `wordpress`, `shopify`, `medium`, `custom` (string)
- `tenant_id`: optional tenant/account identifier
- `connection`: opaque JSON for tokens/ids; stored as-is in Supabase
- `keywords`: array of 1–50 strings

## Response
```json
{
  "provider": "custom",
  "tenant_id": "example-tenant",
  "saved_integration": true,
  "recommended_backlinks": 4,
  "recommended_interlinks": 6,
  "per_keyword": [
    { "keyword": "example keyword", "difficulty": 0.50, "suggested_backlinks": 3, "suggested_interlinks": 5 }
  ],
  "notes": null
}
```

## Persistence (Supabase)
Best‑effort inserts:
- `integrations_{ENV}`: basic integration metadata (`tenant_id`, `provider`, `connection`)
- `recommendations_{ENV}`: computed aggregate and per‑keyword recommendations

See `supabase_schema.sql` to create the env‑suffixed tables (`dev`, `staging`, `prod`) and optional RLS.

## Examples
```bash
curl -X POST "$BASE_URL/api/v1/integrations/connect-and-recommend" \
  -H "Content-Type: application/json" \
  -d '{
    "provider":"custom",
    "tenant_id":"example-tenant",
    "connection":{"token_ref":"abc123"},
    "keywords":["cloud run","content automation","seo"]
  }'
```

## Notes
- WordPress endpoints are guarded and return 501 if the WP backend module is not installed; this integrations endpoint remains fully functional.
- Analyzer uses DataForSEO (if configured) and falls back to heuristics otherwise.


