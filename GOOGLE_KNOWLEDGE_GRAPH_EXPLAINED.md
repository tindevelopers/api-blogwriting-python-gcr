# Google Knowledge Graph API - How It Works

## What is Google Knowledge Graph?

**Google Knowledge Graph** is Google's database of **entities** (people, places, things, concepts) and their relationships. It powers the knowledge panels you see in Google search results.

**Important:** Google Knowledge Graph API **does NOT require a website URL**. It's a **query API** that searches Google's knowledge database.

## How It Works

### 1. **Entity Search**
You query Google's Knowledge Graph with a term (like "Euras Technology" or "leak repair"), and it returns:
- Entity name and description
- Detailed information
- Entity types (Person, Organization, Thing, etc.)
- Related entities
- Images and URLs (if available)

### 2. **No Website Required**
- ✅ Works immediately - no website needed
- ✅ Queries Google's existing knowledge database
- ✅ Returns structured entity information
- ✅ Free tier: 100,000 queries/day

## How It's Used in Your Blog Writing Application

### 1. **Entity Recognition** (Phase 3 of Multi-Stage Pipeline)

When generating a blog about "Euras Technology leak repair":

```python
# The system queries Knowledge Graph for entities
entities = await knowledge_graph.search_entities("Euras Technology")
# Returns: Company info, description, related concepts

entities = await knowledge_graph.search_entities("leak repair")
# Returns: Service category, related services, industry info
```

**Result:** The system understands what "Euras Technology" is and what "leak repair" means in Google's knowledge base.

### 2. **Structured Data Generation** (Schema.org JSON-LD)

Automatically generates structured data for SEO:

```json
{
  "@context": "https://schema.org",
  "@type": "BlogPosting",
  "headline": "Using Euras Technology to Fix Leaks",
  "about": {
    "@type": "Thing",
    "name": "Euras Technology",
    "description": "Company description from Knowledge Graph"
  },
  "mentions": [
    {"@type": "Thing", "name": "Leak Detection"},
    {"@type": "Thing", "name": "Waterproofing"}
  ]
}
```

**Benefit:** Helps Google understand your content better, improving rich snippet potential.

### 3. **Entity Extraction from Content**

After generating blog content, the system:
- Scans the content for entity mentions
- Queries Knowledge Graph for each entity
- Extracts structured information
- Generates schema markup automatically

**Example:**
```
Content mentions: "Euras Technology", "basement leaks", "critical infrastructure"
→ Knowledge Graph identifies these as entities
→ Generates structured data with entity relationships
```

### 4. **Keyword Clustering** (Entity-Based Grouping)

Groups keywords by entities:
- Keywords about the same entity are clustered together
- Better content organization
- More semantic understanding

## Real-World Example

### Blog Topic: "Using Euras Technology to Fix Leaks"

**What Knowledge Graph Does:**

1. **Queries "Euras Technology":**
   - Returns: Company entity, description, type (Organization)
   - Provides: Official information, related concepts

2. **Queries "leak repair":**
   - Returns: Service category, related services
   - Provides: Industry context, related entities

3. **Generates Structured Data:**
   - Creates schema.org markup
   - Links entities to content
   - Improves SEO and rich snippet potential

4. **Enhances Content:**
   - Uses entity descriptions for better context
   - Links related concepts
   - Improves semantic understanding

## Benefits for Your Application

### ✅ **No Website Required**
- Works immediately
- No domain verification needed
- No site URL configuration

### ✅ **Automatic SEO Enhancement**
- Generates schema.org markup automatically
- Improves rich snippet potential
- Better entity recognition by Google

### ✅ **Better Content Quality**
- Uses Google's verified entity information
- Ensures accurate entity descriptions
- Links related concepts naturally

### ✅ **Free Tier**
- 100,000 queries/day free
- More than enough for blog generation
- No cost for typical usage

## Current Status

✅ **API Key:** Configured (`AIzaSyD4X2oqWolr4ehX...`)  
✅ **Secret:** Created in Secret Manager  
✅ **Code:** Already integrated in Multi-Stage Pipeline  
✅ **Ready to Use:** Will work immediately after deployment  

## How It's Used in Code

**File:** `src/blog_writer_sdk/integrations/google_knowledge_graph.py`

**Main Functions:**
1. `search_entities()` - Search for entities by name
2. `get_entity_details()` - Get detailed entity information
3. `extract_entities_from_content()` - Extract entities from blog content
4. `generate_structured_data()` - Generate schema.org JSON-LD markup
5. `generate_schema_markup()` - Create schema markup for entities

**Integration Points:**
- **Multi-Stage Pipeline** (Phase 3): Extracts entities and generates structured data
- **Keyword Clustering**: Uses entities to group related keywords
- **Content Enhancement**: Adds entity context to improve content quality

## Example Usage in Blog Generation

When you generate a blog with `use_knowledge_graph: true`:

1. **During Research Phase:**
   - Queries Knowledge Graph for main topic entities
   - Gets entity descriptions and related concepts
   - Uses this information to enhance research

2. **During Content Generation:**
   - Extracts entities mentioned in content
   - Queries Knowledge Graph for each entity
   - Uses entity information to improve content accuracy

3. **After Generation:**
   - Generates structured data (schema.org JSON-LD)
   - Includes entity relationships
   - Optimizes for rich snippets

## Summary

**Google Knowledge Graph API:**
- ✅ **No website URL needed** - It queries Google's database
- ✅ **Works immediately** - Just needs API key (already configured)
- ✅ **Enhances SEO** - Generates structured data automatically
- ✅ **Improves content** - Uses verified entity information
- ✅ **Free tier** - 100,000 queries/day

**It's already configured and ready to use!** After deployment, it will automatically enhance your blog content with entity recognition and structured data generation.

---

## Comparison: Knowledge Graph vs Search Console

| Feature | Google Knowledge Graph | Google Search Console |
|---------|----------------------|----------------------|
| **Requires Website?** | ❌ No | ✅ Yes (site URL needed) |
| **What It Does** | Queries Google's entity database | Accesses YOUR website's search data |
| **Use Case** | Entity recognition, structured data | Performance tracking, query data |
| **Setup** | Just API key | API key + site URL + service account |
| **Status** | ✅ Ready to use | ⏳ Needs site URL |

**Knowledge Graph is ready now!** Search Console can be configured later when you have a website.

