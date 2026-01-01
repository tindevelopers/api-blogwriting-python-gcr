# Firestore Schema for Blog Writer System

**Version:** 1.0  
**Date:** January 1, 2026  
**Purpose:** Store prompt templates, writing configurations, and system settings for the Blog Writer API

---

## Collections Overview

### 1. `prompt_templates` (Root Collection)

Global instruction templates that define how blogs should be written.

**Document Structure:**

```javascript
{
  "id": "auto-generated",
  "name": "Natural Conversational",
  "description": "Friendly, approachable writing style with natural transitions",
  "category": "tone", // Options: tone, structure, style
  "settings": {
    "formality_level": 6,
    "use_contractions": true,
    "avoid_obvious_transitions": true,
    "transition_blocklist": [
      "In conclusion",
      "Moreover",
      "Furthermore",
      "Additionally",
      "In summary"
    ],
    "preferred_transitions": [
      "Here's the thing",
      "So",
      "Now",
      "The bottom line",
      "What this means"
    ],
    "sentence_variety": true,
    "conclusion_style": "natural_wrap_up",
    "engagement_style": "conversational",
    "use_first_person": false,
    "personality": "friendly"
  },
  "instruction_text": "Compiled instruction text ready for prompt injection",
  "is_active": true,
  "created_at": "2026-01-01T00:00:00Z",
  "updated_at": "2026-01-01T00:00:00Z",
  "created_by": "admin@example.com"
}
```

**Indexes:**
- `is_active` (ascending)
- `category` (ascending)
- `created_at` (descending)

---

### 2. `organizations/{orgId}/writing_config` (Subcollection)

Organization-specific writing configuration that overrides global templates.

**Document ID:** `default` (or custom config names like `blog_style_v2`)

**Document Structure:**

```javascript
{
  "template_id": "template_doc_id", // Reference to prompt_templates
  "custom_overrides": {
    "formality_level": 7,
    "use_contractions": false,
    "transition_blocklist": ["In conclusion", "Moreover"],
    "custom_instructions": "Always mention our brand values"
  },
  "tone_style": "professional",
  "transition_words": ["Therefore", "However", "Additionally"],
  "formality_level": 7,
  "example_style": "specific_brands",
  "updated_at": "2026-01-01T00:00:00Z",
  "updated_by": "user@example.com"
}
```

**Path Pattern:** `organizations/{orgId}/writing_config/{configId}`

---

### 3. `blog_generations/{blogId}/config_override` (Subcollection)

Temporary per-blog configuration overrides that apply to a specific blog generation.

**Document ID:** Same as blog generation job ID

**Document Structure:**

```javascript
{
  "org_id": "org_123",
  "config_overrides": {
    "formality_level": 8,
    "conclusion_style": "call_to_action",
    "custom_instructions": "Include a section about pricing"
  },
  "created_at": "2026-01-01T00:00:00Z",
  "expires_at": "2026-01-08T00:00:00Z" // Auto-cleanup after 7 days
}
```

**Path Pattern:** `blog_generations/{blogId}/config_override`

**Cleanup:** Use Firestore TTL on `expires_at` field for automatic deletion.

---

## Configuration Merge Priority

When loading configuration for blog generation:

1. **Base Template** (from `prompt_templates`) - Lowest priority
2. **Organization Config** (from `organizations/{orgId}/writing_config/default`) - Medium priority
3. **Per-Blog Override** (from `blog_generations/{blogId}/config_override`) - Highest priority

The system merges these configurations, with higher priority overriding lower priority settings.

---

## Example Query Patterns

### Get Active Templates

```javascript
db.collection('prompt_templates')
  .where('is_active', '==', true)
  .orderBy('created_at', 'desc')
  .get()
```

### Get Organization Config

```javascript
db.collection('organizations')
  .doc(orgId)
  .collection('writing_config')
  .doc('default')
  .get()
```

### Get Blog Override

```javascript
db.collection('blog_generations')
  .doc(blogId)
  .collection('config_override')
  .doc(blogId)
  .get()
```

---

## Settings Reference

### Available Settings Keys

| Key | Type | Description | Default |
|-----|------|-------------|---------|
| `formality_level` | number (1-10) | Writing formality (1=casual, 10=formal) | 6 |
| `use_contractions` | boolean | Allow contractions (it's, don't) | true |
| `avoid_obvious_transitions` | boolean | Block AI-obvious transition words | true |
| `transition_blocklist` | array[string] | Phrases to avoid | See default template |
| `preferred_transitions` | array[string] | Recommended transitions | See default template |
| `sentence_variety` | boolean | Mix short and long sentences | true |
| `conclusion_style` | string | How to end blog | "natural_wrap_up" |
| `engagement_style` | string | Reader engagement approach | "conversational" |
| `use_first_person` | boolean | Use first-person voice | false |
| `personality` | string | Writing personality | "friendly" |
| `heading_style` | string | H2 heading format | "statements" |
| `example_style` | string | Example specificity | "mixed" |
| `custom_instructions` | string | Additional instructions | "" |

### Conclusion Style Options

- `natural_wrap_up` - End naturally without formulaic conclusion
- `summary` - Summarize key points
- `call_to_action` - End with CTA
- `open_ended` - Leave reader thinking

### Engagement Style Options

- `conversational` - Like talking to a friend
- `professional` - Business-like but friendly
- `authoritative` - Expert voice
- `analytical` - Data-driven approach

### Personality Options

- `friendly` - Warm and approachable
- `authoritative` - Expert and confident
- `analytical` - Logical and structured
- `conversational` - Casual and relatable

---

## Security Considerations

1. **Template Management** - Only admins can create/update `prompt_templates`
2. **Organization Configs** - Only org members can update their configs
3. **Read Access** - Backend service account has read-only access to all configs
4. **Consumer Frontend** - No direct Firestore access, must go through backend API

---

## Backup & Versioning

- **Automatic Backups** - Firestore automatic backups enabled daily
- **Version History** - Keep `updated_at` and `updated_by` for audit trail
- **Template History** - Consider creating `prompt_templates_history` collection for version control

---

## Migration Notes

If migrating from Supabase or existing system:

1. Export existing prompt configurations
2. Transform to Firestore document format
3. Use seed script to populate Firestore
4. Verify all templates are accessible
5. Test configuration merge logic
6. Update backend to read from Firestore

