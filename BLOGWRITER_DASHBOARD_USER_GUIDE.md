# BlogWriter Dashboard User Guide

**Version:** 1.3.6  
**Last Updated:** 2025-01-27  
**Dashboard URL:** `https://blogwriter-python-gcr-dashboard.vercel.app`  
**Base API URL:** `https://blog-writer-api-dev-kq42l26tuq-od.a.run.app`  
**GitHub Repository:** [tindevelopers/blogwriter-python-gcr-dashboard](https://github.com/tindevelopers/blogwriter-python-gcr-dashboard)

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Getting Started](#getting-started)
3. [Dashboard Navigation](#dashboard-navigation)
4. [Testing Interface](#testing-interface)
5. [Analytics Dashboard](#analytics-dashboard)
6. [Configuration Panel](#configuration-panel)
7. [Monitoring & Logs](#monitoring--logs)
8. [Prompt Management](#prompt-management)
9. [Usage & Cost Monitoring](#usage--cost-monitoring)
10. [API Endpoints Reference](#api-endpoints-reference)
11. [Troubleshooting](#troubleshooting)

---

## Overview

The BlogWriter Dashboard is a **Next.js 16** application built with **Catalyst UI components** that serves as a **control panel** for managing your blog generation backend through Firebase. 

### Primary Purpose

The dashboard's **PRIMARY** functions are:

- ✅ **Control Backend Configuration** - Manage AI providers, prompts, and functions through Firebase Firestore
- ✅ **Monitor Usage and Costs** - Track API usage, costs, and performance metrics in real-time
- ✅ **System Health Monitoring** - View logs, errors, and system status

### Secondary Purpose

The dashboard's **SECONDARY** function is:

- ✅ **Test/Sample Content Generation** - Test blog, review, social post, and email generation endpoints for **testing and sampling purposes only** (not for production use)

### Key Distinction

**Dashboard = Control Panel for Backend**
- Controls backend configuration through Firebase
- Monitors backend API usage and costs
- Tests endpoints and samples content generation

**Production Content Generation = Direct API Calls**
- Production content generation happens through direct API calls to the backend
- Dashboard testing is for validation, sampling, and testing purposes only

### Technology Stack

- **Frontend:** Next.js 16 (App Router), React 18, TypeScript
- **UI Components:** Catalyst UI Kit (Tailwind CSS-based)
- **State Management:** TanStack Query (React Query)
- **Charts:** Recharts
- **Configuration Storage:** Firebase Firestore
- **Authentication:** NextAuth.js with Google OAuth
- **Deployment:** Vercel

---

## Getting Started

### Accessing the Dashboard

1. Navigate to `https://blogwriter-python-gcr-dashboard.vercel.app`
2. Click **"Sign In"** and authenticate with your Google account
3. You'll be redirected to the dashboard home page

### First-Time Setup

If you're an administrator setting up the dashboard:

1. **Configure Environment Variables:**
   - Backend API URL
   - Firebase credentials
   - Google OAuth credentials
   - Encryption keys

2. **Set Up Firebase Firestore:**
   - Create Firestore database
   - Configure security rules
   - Set up collections for configuration storage

3. **Configure AI Providers:**
   - Navigate to **Configuration → AI Providers**
   - Add API keys for OpenAI, Anthropic, and/or DeepSeek
   - Test connections

### Dashboard Layout

The dashboard uses a **sidebar navigation** layout with the following main sections:

1. **Dashboard Home** (`/`) - Overview and quick metrics
2. **Configuration** (`/configuration`) - **PRIMARY:** Control backend through Firebase (AI providers, prompts, functions)
3. **Analytics** (`/analytics`) - **PRIMARY:** Monitor usage metrics and cost tracking
4. **Testing** (`/testing`) - **SECONDARY:** Test/sample content generation and API endpoints
5. **Monitoring** (`/monitoring`) - **PRIMARY:** System health and logs

---

## Dashboard Navigation

### Sidebar Menu

The dashboard sidebar provides quick access to all features:

- **🏠 Dashboard** - System overview and quick metrics
- **⚙️ Configuration** - **PRIMARY:** Control backend through Firebase (AI providers, prompts, functions)
- **📊 Analytics** - **PRIMARY:** Usage and cost analytics
- **🧪 Testing** - **SECONDARY:** Test/sample content generation and API endpoints
- **📈 Monitoring** - **PRIMARY:** System health and logs

---

## Testing Interface

**Route:** `/testing`

**Purpose:** Test and sample content generation endpoints for **testing and validation purposes only**. This interface is NOT for production content generation.

The Testing Interface provides two main functions:

1. **Content Generation Testing/Sampling** - Test blog, review, social post, and email generation endpoints
2. **API Endpoint Testing** - Verify backend endpoints, configurations, and Firebase connections work correctly

### Content Generation Testing

**Purpose:** Sample content generation to test that endpoints work correctly and validate prompt configurations.

#### Blog Generation Testing

**Location:** Dashboard → Testing → Blog Generation

**Note:** This is for **testing/sampling purposes only**. Production blog generation should use direct API calls.

The form includes the following fields:

**Form Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| Topic | Text | ✅ Yes | Main topic of the blog (3-200 characters) |
| Keywords | Array | ✅ Yes | Target SEO keywords (minimum 1) |
| Blog Type | Dropdown | ❌ No | Choose from 28 types (default: custom) |
| Tone | Dropdown | ❌ No | professional, friendly, casual, technical (default: professional) |
| Length | Dropdown | ❌ No | short, medium, long (default: medium) |
| Word Count Target | Number | ❌ No | Target word count (100-10,000) |
| Target Audience | Text | ❌ No | Description of your target readers |
| Custom Instructions | Textarea | ❌ No | Additional guidance (max 5,000 chars) |
| Optimize for Traffic | Checkbox | ❌ No | Enable SEO optimization (default: ✅) |
| Analyze Backlinks | Checkbox | ❌ No | Extract keywords from backlinks |
| Backlink URL | Text | ⚠️ If backlinks enabled | URL to analyze for keywords |

**Blog Types Available:**

- **Core Types:** custom, brand, top_10, product_review, how_to, comparison, guide
- **Popular Types:** tutorial, listicle, case_study, news, opinion, interview, faq, checklist, tips, definition, benefits, problem_solution, trend_analysis, statistics, resource_list, timeline, myth_busting, best_practices, getting_started, advanced, troubleshooting

**Example:**

```
Topic: "Introduction to Python Programming"
Keywords: ["python", "programming", "coding"]
Blog Type: tutorial
Tone: friendly
Length: long
Word Count Target: 2000
Target Audience: Beginners learning to code
Custom Instructions: Include code examples and practical exercises
Optimize for Traffic: ✅
```

**Response Preview:**

After clicking **"Generate Blog"**, you'll see:

**Left Panel (Configuration):**
- Form fields remain visible for adjustments
- **Generate** button shows loading state

**Right Panel (Preview):**
- **Loading State:** Spinner with "Generating blog... This may take 10-60 seconds"
- **Results Display:**
  - Generated blog content (markdown format, rendered)
  - **Metadata Header:**
    - Quality score (0-100) with badge
    - Word count
    - Processing time (seconds)
    - Model used
  - **Action Buttons:**
    - **Copy** - Copy content to clipboard
    - **Download** - Download as markdown file
  - **Meta Tags Section** (if enabled):
    - Generated title
    - Generated description

#### Review Generation Testing

**Location:** Dashboard → Testing → Review Generation

**Note:** This is for **testing/sampling purposes only**. Production review generation should use direct API calls.

Test different review types:
- Product Reviews (`/api/v1/reviews/product`)
- Company Reviews (`/api/v1/reviews/company`)
- Local Business Reviews (`/api/v1/reviews/local-business`)
- Event Reviews (`/api/v1/reviews/event`)

#### Social Media Post Testing

**Location:** Dashboard → Testing → Social Media Posts

**Note:** This is for **testing/sampling purposes only**. Production social post generation should use direct API calls.

Test social post generation for multiple platforms (LinkedIn, Twitter/X, Instagram, Facebook).

#### Email Campaign Testing

**Location:** Dashboard → Testing → Email Campaigns

**Note:** This is for **testing/sampling purposes only**. Production email generation should use direct API calls.

Test email campaign generation (newsletter, promo, drip sequences).

### API Endpoint Testing

**Purpose:** Verify backend endpoints, configurations, and Firebase connections work correctly.

#### Health Check Testing

- Test `GET /health` endpoint
- Test `GET /api/v1/config` endpoint
- Verify backend is accessible and responding

#### Configuration Testing

- Test prompt management endpoints (`GET /api/v1/prompts/templates`)
- Verify Firebase writes/reads work correctly
- Test AI provider connections
- Validate prompt templates load correctly

#### Connection Testing

- Test AI provider API keys
- Test LiteLLM proxy connection
- Verify Firebase Firestore connectivity
- Test configuration sync between dashboard and backend

### Using the Testing Interface

**For Content Generation Testing:**

1. **Select content type** (Blog, Review, Social Post, Email)
2. **Fill in the form** with test parameters
3. **Click "Generate"** to test the endpoint
4. **Review results** to validate:
   - Endpoint responds correctly
   - Content quality meets expectations
   - Prompt configurations are applied correctly
   - Cost tracking works

**For API Endpoint Testing:**

1. **Select endpoint to test** (Health, Config, Prompts, etc.)
2. **Click "Test"** button
3. **Review response** to verify:
   - Endpoint is accessible
   - Response format is correct
   - Configuration is synced properly

### Important Notes

- **Testing Only:** Content generation in the dashboard is for testing/sampling purposes
- **Production Use:** Use direct API calls for production content generation
- **Cost Tracking:** All test generations are tracked in Analytics Dashboard
- **Configuration Validation:** Use testing to verify prompt templates and configurations work as expected

---

## Analytics Dashboard

**Route:** `/analytics`

The Analytics Dashboard provides comprehensive insights into your API usage, costs, and performance.

### Key Metrics Displayed

**Metric Cards (Top Row):**

1. **Total Requests**
   - Count of API calls
   - Trend indicator (+/- percentage)
   - Icon: Activity

2. **Total Cost**
   - Total cost in USD
   - Trend indicator
   - Icon: Dollar Sign

3. **Average Response Time**
   - Average latency in milliseconds
   - Trend indicator
   - Icon: Clock

4. **Cache Hit Rate**
   - Percentage of cached requests
   - Trend indicator
   - Icon: Zap

### Charts and Visualizations

**Tab 1: Overview**
- **Requests Over Time** - Line chart showing request volume
- **Cost Breakdown** - Pie chart by AI model

**Tab 2: Costs**
- Detailed cost analysis
- Cost trends over time
- Cost by operation type

**Tab 3: Performance**
- Response time trends
- Latency by model
- Error rates

**Tab 4: Models**
- Model usage statistics table
- Requests per model
- Tokens per model
- Cost per model

### Time Range Selection

Use the **Date Range Picker** to:
- Select last 7 days (default)
- Select last 30 days
- Select last 90 days
- Choose custom date range

### Data Source

**Endpoint:** `GET /api/v1/metrics`

This endpoint returns:
- Total requests
- Total cost
- Average latency
- Cache hit rate
- Cost breakdown by model
- Requests by model
- Time series data
- Model statistics

### Exporting Data

- **CSV Export** - Download usage data as CSV
- **JSON Export** - Download raw data as JSON
- **PDF Report** - Generate PDF report (coming soon)

---

## Configuration Panel

**Route:** `/configuration`

**PRIMARY FUNCTION:** Control backend configuration through Firebase Firestore.

The Configuration Panel is the **main control interface** for managing your backend. All configuration changes are stored in Firebase Firestore, which the backend reads to apply settings.

### How Configuration Works

```
Dashboard → Firebase Firestore → Backend (Cloud Run)
```

1. **You make changes** in the dashboard
2. **Dashboard writes** to Firebase Firestore
3. **Backend reads** from Firebase Firestore
4. **Backend applies** configuration changes

### Configuration Storage

All configurations are stored in **Firebase Firestore** with the following structure:

```
/organizations/{orgId}
  /config
    /ai_providers (document)
      - openai: { enabled, apiKey (encrypted), defaultModel, status }
      - anthropic: { enabled, apiKey (encrypted), defaultModel, status }
      - deepseek: { enabled, apiKey (encrypted), defaultModel, status }
    
    /litellm (document)
      - enabled: boolean
      - proxyUrl: string
      - apiKey: string (encrypted)
      - cacheEnabled: boolean
      - cacheTTL: number
    
    /prompts (collection)
      - {template_id}: { name, settings, instruction_text, ... }
    
    /writing_configs (document)
      - org_id: string
      - template_id: string
      - custom_overrides: object
```

The Configuration Panel allows you to manage AI providers, LiteLLM proxy settings, prompt templates, and system defaults.

### AI Providers Configuration

**Route:** `/configuration/ai-providers`

Configure individual AI providers:

#### OpenAI Configuration

**Fields:**
- **API Key** - Enter OpenAI API key (masked after saving)
- **Default Model** - Select default model (gpt-4o, gpt-4o-mini, gpt-4-turbo)
- **Enabled** - Toggle to enable/disable provider
- **Status** - Connection status badge (Connected/Disconnected)
- **Test Connection** - Button to verify API key

#### Anthropic (Claude) Configuration

**Fields:**
- **API Key** - Enter Anthropic API key
- **Default Model** - Select default model (claude-3-5-sonnet, claude-3-haiku)
- **Enabled** - Toggle to enable/disable
- **Status** - Connection status
- **Test Connection** - Verify API key

#### DeepSeek Configuration

**Fields:**
- **API Key** - Enter DeepSeek API key
- **Default Model** - Select default model
- **Enabled** - Toggle to enable/disable
- **Status** - Connection status
- **Test Connection** - Verify API key

**Security Notes:**
- API keys are encrypted before storage in Firebase Firestore
- Only last 4 characters are displayed after saving
- Changes are logged in audit trail
- Requires admin permissions
- Configuration is synced to backend automatically

**How It Works:**
1. Enter API key in dashboard
2. Dashboard encrypts and saves to Firebase Firestore
3. Backend reads from Firebase Firestore
4. Backend uses API key for AI provider calls

### LiteLLM Control Panel

**Route:** `/configuration/litellm`

Configure LiteLLM proxy for centralized AI routing:

**Features:**
- **Enable/Disable LiteLLM** - Toggle switch
- **Proxy URL** - LiteLLM proxy endpoint URL
- **Master API Key** - LiteLLM master key (encrypted)
- **Cache Settings:**
  - Enable caching toggle
  - Cache TTL (Time To Live) slider (60-86400 seconds)
- **Vercel AI Gateway Integration:**
  - Enable Vercel Gateway toggle
  - Vercel Gateway URL
  - Vercel Gateway Key
- **Connection Status** - Real-time status indicator
- **Test Connection** - Verify LiteLLM connection
- **Architecture Diagram** - Visual representation of current routing

**Architecture Modes:**

1. **Direct Mode** (LiteLLM disabled):
   ```
   Backend → AI Providers (Direct)
   ```

2. **LiteLLM Mode** (LiteLLM enabled, Vercel disabled):
   ```
   Backend → LiteLLM Proxy → AI Providers
   ```

3. **Vercel Gateway Mode** (Both enabled):
   ```
   Backend → LiteLLM Proxy → Vercel AI Gateway → AI Providers
   ```

### Prompt Template Management

**Route:** `/configuration/prompts`

**PRIMARY FUNCTION:** Manage prompt templates that control how the backend generates content.

Create, edit, and delete prompt templates that define writing styles:

- **Create Template** - Define new writing style templates
- **Edit Template** - Modify existing templates
- **Delete Template** - Remove unused templates
- **Preview Template** - See how template affects content generation

**Template Settings:**
- Formality level (1-5)
- Use contractions
- Avoid obvious transitions
- Transition blocklist/preferred transitions
- Sentence variety
- Conclusion style
- Engagement style
- Use first person
- Personality traits
- Heading style
- Example style
- Custom instructions

**How It Works:**
1. Create/edit template in dashboard
2. Dashboard saves to Firebase Firestore (`/prompts/{template_id}`)
3. Backend reads template from Firebase
4. Backend applies template during content generation

### Organization Writing Configuration

**Route:** `/configuration/writing-config`

Set default writing styles for your organization:

- **Default Template** - Select organization-wide template
- **Custom Overrides** - Override specific template settings
- **Tone Style** - Set default tone
- **Transition Words** - Customize preferred transitions
- **Formality Level** - Set organization-wide formality

**How It Works:**
1. Configure organization defaults in dashboard
2. Dashboard saves to Firebase Firestore (`/writing_configs/{org_id}`)
3. Backend reads organization config from Firebase
4. Backend applies config to all content generation for that organization

### General Settings

**Route:** `/configuration/general`

Configure system defaults (stored in Firebase):

- **Default Tone** - Default content tone (professional, friendly, casual)
- **Default Word Count** - Default target word count
- **Enable Polishing** - Auto-enable content polishing
- **Enable Quality Check** - Auto-enable quality checks
- **Default Model** - Default AI model to use

**How It Works:**
1. Set defaults in dashboard
2. Dashboard saves to Firebase Firestore (`/config/general`)
3. Backend reads defaults from Firebase
4. Backend applies defaults when not specified in API calls

---

## Monitoring & Logs

**Route:** `/monitoring`

Monitor system health, view logs, and track errors.

### System Health

**Health Indicators:**

1. **Backend API**
   - Status: Healthy/Unhealthy/Unknown
   - URL: Backend API endpoint
   - Response time
   - Last checked timestamp

2. **AI Gateway** (if enabled)
   - Status: Connected/Disconnected
   - Base URL
   - Response time

3. **Database**
   - Status: Connected/Disconnected
   - Connection pool status

### Recent Errors

**Error List:**
- Error messages
- Timestamp
- Endpoint that failed
- Error type
- Stack trace (expandable)

### Live Logs

**Log Viewer:**
- Real-time log streaming
- Filter by severity (Info, Warning, Error)
- Search functionality
- Auto-scroll toggle
- Export logs

### Performance Metrics

- **Request Rate** - Requests per minute
- **Error Rate** - Percentage of failed requests
- **Average Latency** - Response time trends
- **Cache Performance** - Cache hit/miss rates

---

## Prompt Management

**PRIMARY FUNCTION:** Manage prompts and functions that control backend content generation behavior.

### Overview

Prompt management allows you to create, customize, and manage writing styles and prompts that control how the backend generates content. All prompt configurations are stored in **Firebase Firestore** and read by the backend.

### How Prompt Management Works

```
Dashboard → Firebase Firestore → Backend (Cloud Run) → Content Generation
```

1. **Create/Edit Prompts** in dashboard
2. **Dashboard saves** to Firebase Firestore (`/prompts/{template_id}`)
3. **Backend reads** from Firebase Firestore
4. **Backend applies** prompts during content generation

### Prompt Template Management

**Location:** Dashboard → Configuration → Prompts

**Backend Endpoints (accessed through dashboard):**
- `GET /api/v1/prompts/templates` - List all prompt templates
- `GET /api/v1/prompts/templates/{template_id}` - Get specific template
- `POST /api/v1/prompts/templates` - Create new template
- `PUT /api/v1/prompts/templates/{template_id}` - Update template
- `DELETE /api/v1/prompts/templates/{template_id}` - Delete template

### Function Management

**Location:** Dashboard → Configuration → Functions

**PRIMARY FUNCTION:** Manage custom functions that extend backend capabilities.

Functions are custom code/logic that can be called during content generation. Functions are stored in Firebase Firestore and executed by the backend.

**Function Types:**
- Content processing functions
- Data enrichment functions
- Custom validation functions
- Integration functions

**How Functions Work:**
1. Create/define function in dashboard
2. Dashboard saves to Firebase Firestore (`/functions/{function_id}`)
3. Backend loads function from Firebase
4. Backend executes function during content generation when referenced

### Organization Writing Configuration

**Location:** Dashboard → Configuration → Writing Config

Set default writing styles for your organization:

**Configuration Options:**
- Default template selection
- Custom overrides
- Tone style
- Transition words
- Formality level

**How It Works:**
1. Configure organization defaults in dashboard
2. Dashboard saves to Firebase Firestore (`/writing_configs/{org_id}`)
3. Backend reads organization config from Firebase
4. Backend applies config to all content generation for that organization

**Backend Endpoints:**
- `GET /api/v1/prompts/config/writing-style/{org_id}` - Get organization config
- `PUT /api/v1/prompts/config/writing-style/{org_id}` - Update organization config

---

## Prompt Management

### Overview

The Prompt Management section allows you to create, customize, and manage writing styles and prompts without coding. These prompts control how the AI generates content.

**Location:** Dashboard → Prompt Management

### Creating a New Prompt Template

**Endpoint:** `POST /api/v1/prompts/templates`

**Steps:**

1. Click **"Create New Template"**
2. Fill in the template details:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| Name | Text | ✅ Yes | Template name (e.g., "Technical Blog Style") |
| Description | Text | ❌ No | What this template is used for |
| Category | Dropdown | ❌ No | tone, structure, style |
| Formality Level | Slider | ❌ No | 1-5 (1=casual, 5=formal) |
| Use Contractions | Checkbox | ❌ No | Allow contractions (don't, can't) |
| Avoid Obvious Transitions | Checkbox | ❌ No | Skip "in conclusion", "firstly" |
| Transition Blocklist | Textarea | ❌ No | Words/phrases to avoid (one per line) |
| Preferred Transitions | Textarea | ❌ No | Preferred transition words |
| Sentence Variety | Dropdown | ❌ No | low, medium, high |
| Conclusion Style | Dropdown | ❌ No | summary, call_to_action, question |
| Engagement Style | Dropdown | ❌ No | conversational, authoritative, friendly |
| Use First Person | Checkbox | ❌ No | Allow "I", "we", "our" |
| Personality | Textarea | ❌ No | Writing personality traits |
| Heading Style | Dropdown | ❌ No | question, statement, numbered |
| Example Style | Dropdown | ❌ No | brief, detailed, code_heavy |
| Custom Instructions | Textarea | ❌ No | Additional writing guidelines |

3. Click **"Save Template"**

**Example Template:**

```
Name: "Friendly Technical Blog"
Description: "For technical content that's approachable and engaging"
Category: style
Formality Level: 2
Use Contractions: ✅
Avoid Obvious Transitions: ✅
Sentence Variety: high
Conclusion Style: call_to_action
Engagement Style: conversational
Use First Person: ✅
Personality: "Enthusiastic but clear, uses analogies for complex concepts"
Heading Style: question
Custom Instructions: "Break down complex topics into digestible chunks. Use real-world examples."
```

### Managing Prompt Templates

#### List All Templates

**Endpoint:** `GET /api/v1/prompts/templates`

**Features:**
- View all templates in a table
- Filter by category
- Show only active templates
- Search by name

#### View Template Details

**Endpoint:** `GET /api/v1/prompts/templates/{template_id}`

**Shows:**
- Complete template configuration
- Generated instruction text
- Usage statistics
- Created/updated timestamps

#### Update Template

**Endpoint:** `PUT /api/v1/prompts/templates/{template_id}`

**Steps:**
1. Select template from list
2. Click **"Edit"**
3. Modify fields
4. Click **"Save Changes"**

**Note:** Updating settings automatically regenerates the instruction text.

#### Delete Template

**Endpoint:** `DELETE /api/v1/prompts/templates/{template_id}`

**Warning:** Deleting a template removes it permanently. Ensure no active content generation jobs are using it.

### Organization Writing Configuration

Set default writing styles for your entire organization.

**Location:** Dashboard → Prompt Management → Organization Settings

**Endpoint:** `PUT /api/v1/prompts/config/writing-style/{org_id}`

**Configuration Options:**

1. **Select Default Template**
   - Choose from your saved templates
   - Applies to all new content generation

2. **Custom Overrides**
   - Override specific template settings
   - Applies organization-wide

3. **Tone Style**
   - Set default tone for all content

4. **Transition Words**
   - Customize preferred transition words

5. **Formality Level**
   - Set organization-wide formality preference

**View Current Config:**

**Endpoint:** `GET /api/v1/prompts/config/writing-style/{org_id}`

### Per-Blog Overrides

Override organization defaults for specific blog generation jobs.

**Location:** Dashboard → Content Generation → Advanced Options

**Endpoint:** `POST /api/v1/prompts/config/blog-override/{blog_id}`

**Use Cases:**
- One-off content with different style
- Client-specific requirements
- A/B testing different styles

**Configuration:**
- Set during blog generation
- Expires after specified days (default: 7)
- Can be deleted manually

**Delete Override:**

**Endpoint:** `DELETE /api/v1/prompts/config/blog-override/{blog_id}`

### Merged Configuration Preview

Preview how configurations merge together before generating content.

**Endpoint:** `GET /api/v1/prompts/config/merged`

**Query Parameters:**
- `org_id` - Organization ID
- `blog_id` - Blog job ID (for overrides)
- `template_id` - Specific template to preview

**Response Shows:**
- Final merged configuration
- All active settings
- Instruction text that will be used

---

## Usage & Cost Monitoring

### Overview

Monitor all API usage, costs, and performance metrics in real-time through the Analytics Dashboard.

**Location:** Dashboard → Analytics

### System Metrics

**Endpoint:** `GET /api/v1/metrics`

This is the primary endpoint for monitoring usage and costs. It provides comprehensive metrics without requiring admin authentication.

**Metrics Provided:**

| Metric | Description | Display Location |
|--------|-------------|-------------------|
| Total Requests | Number of API calls | Analytics Dashboard - Metric Card |
| Total Cost | Total cost in USD | Analytics Dashboard - Metric Card |
| Average Latency | Average response time | Analytics Dashboard - Metric Card |
| Cache Hit Rate | Percentage of cached requests | Analytics Dashboard - Metric Card |
| Cost by Model | Breakdown by AI model | Analytics Dashboard - Pie Chart |
| Requests by Model | Count per model | Analytics Dashboard - Table |
| Time Series Data | Requests over time | Analytics Dashboard - Line Chart |

**Response Structure:**

```json
{
  "total_requests": 1250,
  "total_cost": 12.45,
  "avg_latency_ms": 1250,
  "cache_rate": 24.96,
  "cost_by_model": {
    "gpt-4o": 7.50,
    "gpt-4o-mini": 4.95
  },
  "requests_by_model": {
    "gpt-4o": 600,
    "gpt-4o-mini": 650
  },
  "time_series": [
    {
      "date": "2025-01-01",
      "requests": 45,
      "cost": 0.45
    }
  ],
  "model_stats": [
    {
      "model": "gpt-4o",
      "requests": 600,
      "tokens": 1500000,
      "cost": 7.50,
      "avg_latency": 1500
    }
  ]
}
```

### Cache Statistics

**Endpoint:** `GET /api/v1/cache/stats`

View cache performance metrics:

**Metrics:**
- Cache hit rate percentage
- Cache miss rate
- Total cache entries
- Cache size
- Eviction statistics

**Clear Cache:**

**Endpoint:** `DELETE /api/v1/cache/clear`

- Clear all cache entries
- Clear by pattern (optional)

### Real-Time Updates

**Polling Frequency:**
- Metrics refresh every **60 seconds** automatically
- Manual refresh button available
- Real-time updates when new requests are made

**Visualizations:**

1. **Line Chart** - Requests over time
2. **Pie Chart** - Cost breakdown by model
3. **Bar Chart** - Model usage comparison
4. **Table** - Detailed model statistics

### Exporting Data

**Available Formats:**
- **CSV Export** - Download usage data as CSV for Excel/Google Sheets
- **JSON Export** - Download raw data as JSON for programmatic analysis

**Export Options:**
- Export current view
- Export filtered data
- Export date range

---

## API Endpoints Reference

### Content Generation Endpoints (For Testing/Sampling)

**Note:** These endpoints are available for testing and sampling content generation through the dashboard. Production content generation should use direct API calls.

#### Blog Generation

**POST** `/api/v1/blog/generate-enhanced`

**Purpose:** Test/sample blog generation (for testing purposes only)

Generate high-quality blog content with SEO optimization.

**Request Body:**
```json
{
  "topic": "string (required)",
  "keywords": ["string (required)"],
  "blog_type": "string (optional)",
  "tone": "string (optional)",
  "length": "string (optional)",
  "word_count_target": 1500,
  "optimize_for_traffic": true,
  "analyze_backlinks": false,
  "backlink_url": "string (optional)",
  "use_dataforseo_content_generation": true,
  "target_audience": "string (optional)",
  "custom_instructions": "string (optional)",
  "writing_style_id": "string (optional)",
  "writing_style_overrides": {}
}
```

**Response:**
```json
{
  "title": "string",
  "content": "string (markdown)",
  "meta_title": "string",
  "meta_description": "string",
  "readability_score": 75.0,
  "seo_score": 85.0,
  "seo_metadata": {},
  "total_tokens": 0,
  "total_cost": 0.0,
  "generation_time": 2.5,
  "success": true,
  "warnings": []
}
```

#### Review Generation

**POST** `/api/v1/reviews/{review_type}`

**Purpose:** Test/sample review generation (for testing purposes only)

Generate product, company, local business, or event reviews.

**Review Types:** `product`, `company`, `local-business`, `event`

**Request Body:**
```json
{
  "entity_name": "string (required)",
  "entity_url": "string (optional)",
  "industry": "string (optional)",
  "category": "string (optional)",
  "location": "string (optional)",
  "target_audience": "string (optional)",
  "tone": "professional",
  "word_count": 1200,
  "include_citations": true,
  "pros_cons_required": true,
  "schema": true,
  "include_comparison_table": false,
  "keywords": ["string"]
}
```

#### Social Media Posts

**POST** `/api/v1/social/generate`

**Purpose:** Test/sample social media post generation (for testing purposes only)

Generate social media posts for multiple platforms.

**Request Body:**
```json
{
  "platforms": ["linkedin", "twitter", "instagram"],
  "campaign_goal": "traffic",
  "cta_url": "string (optional)",
  "brand_voice": "friendly",
  "variants": 5,
  "max_chars": 260,
  "include_hashtags": true,
  "topic": "string (required)",
  "target_audience": "string (optional)"
}
```

#### Email Campaigns

**POST** `/api/v1/email/generate-campaign`

**Purpose:** Test/sample email campaign generation (for testing purposes only)

Generate email campaign sequences.

**Request Body:**
```json
{
  "campaign_type": "drip",
  "emails_count": 4,
  "offer": "string (optional)",
  "audience_segment": "string (optional)",
  "personalization_tokens": ["{{first_name}}"],
  "tone": "friendly",
  "topic": "string (required)",
  "include_subject_variants": true
}
```

### Prompt Management Endpoints (Backend Control)

**PRIMARY FUNCTION:** Control backend prompt configurations through Firebase.

#### List Templates

**GET** `/api/v1/prompts/templates`

**Purpose:** List all prompt templates stored in Firebase Firestore

**Query Parameters:**
- `active_only` - Show only active templates (default: true)
- `category` - Filter by category (tone, structure, style)

#### Get Template

**GET** `/api/v1/prompts/templates/{template_id}`

**Purpose:** Retrieve a specific prompt template from Firebase Firestore

#### Create Template

**POST** `/api/v1/prompts/templates`

**Purpose:** Create a new prompt template and save to Firebase Firestore

**How It Works:**
1. Dashboard sends template data to backend
2. Backend saves to Firebase Firestore (`/prompts/{template_id}`)
3. Backend uses template for future content generation

**Request Body:**
```json
{
  "name": "string (required)",
  "description": "string (optional)",
  "category": "string (optional)",
  "settings": {
    "formality_level": 3,
    "use_contractions": true,
    "avoid_obvious_transitions": true,
    "transition_blocklist": [],
    "preferred_transitions": [],
    "sentence_variety": "medium",
    "conclusion_style": "summary",
    "engagement_style": "conversational",
    "use_first_person": false,
    "personality": "string",
    "heading_style": "statement",
    "example_style": "brief",
    "custom_instructions": "string"
  },
  "instruction_text": "string (optional, auto-generated)"
}
```

#### Update Template

**PUT** `/api/v1/prompts/templates/{template_id}`

**Purpose:** Update an existing prompt template in Firebase Firestore

**Request Body:** Same as create, with fields to update

**How It Works:**
1. Dashboard sends updated template data to backend
2. Backend updates Firebase Firestore (`/prompts/{template_id}`)
3. Backend uses updated template for future content generation

#### Get Organization Config

**GET** `/api/v1/prompts/config/writing-style/{org_id}`

**Purpose:** Retrieve organization writing configuration from Firebase Firestore

#### Update Organization Config

**PUT** `/api/v1/prompts/config/writing-style/{org_id}`

**Purpose:** Update organization writing configuration in Firebase Firestore

**How It Works:**
1. Dashboard sends config data to backend
2. Backend saves to Firebase Firestore (`/writing_configs/{org_id}`)
3. Backend applies config to all content generation for that organization

**Request Body:**
```json
{
  "template_id": "string (optional)",
  "custom_overrides": {},
  "tone_style": "string (optional)",
  "transition_words": [],
  "formality_level": 3,
  "example_style": "string (optional)"
}
```

#### Get Merged Config

**GET** `/api/v1/prompts/config/merged`

**Query Parameters:**
- `org_id` - Organization ID
- `blog_id` - Blog job ID (for overrides)
- `template_id` - Specific template to preview

#### Save Blog Override

**POST** `/api/v1/prompts/config/blog-override/{blog_id}`

**Request Body:**
```json
{
  "org_id": "string (required)",
  "config_overrides": {},
  "ttl_days": 7
}
```

### Usage & Cost Endpoints (Monitoring)

**PRIMARY FUNCTION:** Monitor backend API usage and costs.

#### Get Metrics

**GET** `/api/v1/metrics`

**Purpose:** Monitor backend API usage, costs, and performance metrics

Get comprehensive system metrics including usage, costs, and performance.

**Response:** Returns total requests, total cost, average latency, cache hit rate, cost breakdown by model, requests by model, time series data, and model statistics.

**No authentication required** - Public metrics endpoint

**Used By:** Analytics Dashboard for real-time monitoring

#### Get Cache Stats

**GET** `/api/v1/cache/stats`

Get cache performance statistics.

**Response:** Returns cache hit rate, miss rate, total entries, cache size, and eviction statistics.

#### Clear Cache

**DELETE** `/api/v1/cache/clear`

Clear cache entries.

**Query Parameters:**
- `pattern` - Optional pattern to match cache keys

**Response:** Returns number of cleared items

### Keyword Analysis Endpoints

#### Enhanced Keyword Analysis

**POST** `/api/v1/keywords/enhanced`

Analyze keywords with search volume, difficulty, intent, and more.

**Request Body:**
```json
{
  "keywords": ["string (required)"],
  "location": "United States (optional)",
  "language": "en (optional)",
  "include_serp": false,
  "serp_depth": 10
}
```

#### Streaming Keyword Analysis

**POST** `/api/v1/keywords/enhanced/stream`

Same as above, but returns streaming results.

#### AI Topic Suggestions

**POST** `/api/v1/keywords/ai-topic-suggestions`

Get AI-generated topic suggestions based on seed keywords.

**Request Body:**
```json
{
  "seed_keywords": ["string (required)"],
  "max_suggestions": 10,
  "industry": "string (optional)"
}
```

### Content Analysis Endpoints

#### Analyze Content

**POST** `/api/v1/analyze`

Analyze existing content for SEO, readability, and quality.

**Request Body:**
```json
{
  "content": "string (required)",
  "keywords": ["string (optional)"],
  "target_audience": "string (optional)"
}
```

#### Sentiment Analysis

**POST** `/api/v1/content/analyze-sentiment`

Analyze sentiment of content.

**Request Body:**
```json
{
  "content": "string (required)",
  "language": "en (optional)"
}
```

### Job Management Endpoints

#### Get Job Status

**GET** `/api/v1/blog/jobs/{job_id}`

Check status of async blog generation job.

**Response:**
```json
{
  "job_id": "string",
  "status": "pending|processing|completed|failed",
  "progress": 0.75,
  "result": {},
  "error": "string (if failed)",
  "created_at": "2025-01-27T10:00:00Z",
  "updated_at": "2025-01-27T10:05:00Z"
}
```

### Health & Status Endpoints

#### Health Check

**GET** `/health`

Check API health status.

#### Detailed Health

**GET** `/api/v1/health/detailed`

Get detailed health information for all services.

#### API Config

**GET** `/api/v1/config`

Get API configuration and available features.

#### Metrics

**GET** `/api/v1/metrics`

Get system metrics and performance data.

---

## Troubleshooting

### Common Issues

#### 1. Content Generation Testing Fails

**Symptoms:**
- Error message: "Failed to generate content"
- Timeout errors
- 503 Service Unavailable

**Solutions:**
- Check API health: `GET /health`
- Verify required fields are provided
- Check word count is within limits (100-10,000)
- Ensure topic is 3-200 characters
- Try reducing word count target
- Check DataForSEO credits if using content generation
- Verify backend is reading from Firebase correctly
- Check prompt templates are loaded from Firebase

#### 2. High Costs

**Symptoms:**
- Unexpectedly high usage costs
- Cost alerts triggered

**Solutions:**
- Review usage statistics in Analytics Dashboard
- Check cache hit rate (should be >20%)
- Use GPT-4o-mini for simpler tasks
- Enable caching in LiteLLM configuration
- Review daily breakdown for anomalies
- Check for duplicate requests
- Enable LiteLLM proxy for better caching

#### 3. Low Cache Hit Rate

**Symptoms:**
- Cache hit rate < 10%
- High costs despite similar requests

**Solutions:**
- Enable LiteLLM proxy with caching
- Review prompt templates for consistency
- Ensure similar requests use same parameters
- Check cache TTL settings in Configuration
- Consider increasing cache duration
- Review cache statistics: `GET /api/v1/cache/stats`

#### 4. DataForSEO Credits Depleted

**Symptoms:**
- Error: "DataForSEO credits insufficient"
- Content generation fails with DataForSEO errors

**Solutions:**
- Check credit balance in dashboard
- Disable `use_dataforseo_content_generation` temporarily
- Use standard blog generation endpoint
- Contact administrator to add credits
- Review credit usage by endpoint

#### 5. Prompt Template Not Applied

**Symptoms:**
- Generated content doesn't match template style
- Custom instructions ignored
- Configuration changes not taking effect

**Solutions:**
- Verify template is saved in Firebase Firestore
- Check backend is reading from Firebase correctly
- Verify template is active
- Check organization config isn't overriding
- Review merged config: `GET /api/v1/prompts/config/merged`
- Ensure `writing_style_id` is correct
- Check for blog-specific overrides
- Verify Firebase connection is working
- Check Firebase security rules allow backend to read

#### 9. Firebase Connection Issues

**Symptoms:**
- Configuration changes not saving
- Cannot read prompt templates
- "Firebase connection failed" errors

**Solutions:**
- Verify Firebase credentials are correct
- Check Firebase Firestore is accessible
- Review Firebase security rules
- Verify backend has read/write permissions
- Check Firebase project is active
- Verify network connectivity to Firebase
- Check Firebase quota limits

#### 10. Configuration Not Syncing

**Symptoms:**
- Changes made in dashboard not reflected in backend
- Backend using old configuration
- API calls not using updated settings

**Solutions:**
- Verify Firebase Firestore write succeeded
- Check backend is reading from correct Firebase collection
- Verify backend cache is cleared
- Check backend logs for Firebase read errors
- Ensure Firebase security rules allow backend reads
- Verify organization ID matches between dashboard and backend
- Check backend restart may be needed for some config changes

#### 6. Slow Response Times

**Symptoms:**
- Generation takes > 30 seconds
- Timeout errors

**Solutions:**
- Use async mode for long content
- Reduce word count target
- Disable optional features (backlink analysis, SERP optimization)
- Check system metrics: `GET /api/v1/metrics`
- Review latency in usage stats

#### 7. Authentication Errors

**Symptoms:**
- 401 Unauthorized errors
- Cannot access dashboard

**Solutions:**
- Verify you're logged in with Google account
- Check that your email is authorized
- Contact administrator for access
- Clear browser cookies and try again

#### 8. Dashboard Not Loading

**Symptoms:**
- Blank page
- Loading spinner never completes
- Error messages

**Solutions:**
- Check browser console for errors
- Verify backend API is accessible
- Check network connectivity
- Try refreshing the page
- Clear browser cache
- Check Vercel deployment status

### Getting Help

1. **Check API Documentation:**
   - Visit `/docs` for interactive Swagger UI
   - Visit `/redoc` for ReDoc documentation

2. **Review Logs:**
   - Check dashboard logs section
   - Review error messages in responses

3. **Contact Support:**
   - Use support email (provided by administrator)
   - Include:
     - Error message
     - Request details
     - Timestamp
     - Organization ID

---

## Best Practices

### Backend Configuration Management

1. **Use Firebase for Configuration:**
   - All configuration changes go through Firebase Firestore
   - Dashboard writes to Firebase, backend reads from Firebase
   - Verify changes are saved to Firebase before expecting backend to use them

2. **Test Configuration Changes:**
   - Use Testing Interface to verify prompt templates work
   - Test API endpoints after configuration changes
   - Verify backend is reading from Firebase correctly

3. **Monitor Configuration Impact:**
   - Check Analytics Dashboard after configuration changes
   - Monitor costs and usage patterns
   - Verify prompt templates are being applied correctly

### Content Generation Testing

1. **Use for Testing Only:**
   - Dashboard content generation is for testing/sampling purposes
   - Use direct API calls for production content generation
   - Test prompt templates and configurations before production use

2. **Start Simple:**
   - Begin with default settings
   - Add complexity gradually
   - Test with shorter content first

3. **Validate Prompts:**
   - Test that prompt templates are applied correctly
   - Verify custom instructions work as expected
   - Check that organization configs are respected

### Cost Management

1. **Use Caching:**
   - Enable LiteLLM proxy with caching
   - Reuse similar prompts
   - Monitor cache hit rates in Analytics
   - Adjust cache TTL in Configuration

2. **Choose Right Model:**
   - GPT-4o-mini for simple content (lower cost)
   - GPT-4o for complex content (higher quality)
   - Test model performance in Testing interface
   - Compare costs in Analytics Dashboard

3. **Monitor Usage:**
   - Check Analytics Dashboard daily
   - Review cost trends weekly
   - Set up alerts for high usage
   - Optimize based on data

### Prompt Management

1. **Organize Templates:**
   - Use clear naming conventions
   - Categorize by use case
   - Document template purposes
   - Store all templates in Firebase Firestore

2. **Version Control:**
   - Test templates in Testing Interface before deploying
   - Keep backups of working templates in Firebase
   - Document changes in template descriptions
   - Verify templates are saved to Firebase correctly

3. **Reuse Configurations:**
   - Set organization defaults in Firebase
   - Create reusable templates stored in Firebase
   - Share templates across teams via Firebase
   - Verify backend reads templates from Firebase correctly

---

## Appendix

### Blog Types Reference

| Type | Best For | Word Count |
|------|----------|------------|
| custom | General content | 800-2000 |
| tutorial | Step-by-step guides | 1500-3000 |
| how_to | How-to articles | 1000-2000 |
| listicle | Numbered lists | 1200-2500 |
| product_review | Product reviews | 1500-2500 |
| comparison | Product comparisons | 2000-3500 |
| case_study | Success stories | 2000-4000 |
| guide | Comprehensive guides | 2500-5000 |
| faq | Question-answer format | 1000-2000 |
| checklist | Actionable checklists | 800-1500 |

### Tone Options

- **professional** - Formal, business-focused
- **friendly** - Warm, approachable
- **casual** - Relaxed, conversational
- **technical** - Detailed, precise
- **authoritative** - Expert, confident
- **conversational** - Natural, engaging

### Length Options

- **short** - 500-800 words
- **medium** - 1000-2000 words (default)
- **long** - 2000-5000 words

### Cost Estimates

**AI Models (per 1K tokens):**
- GPT-4o-mini: ~$0.15
- GPT-4o: ~$2.50
- Claude-3.5-Sonnet: ~$3.00

**DataForSEO (per credit):**
- Varies by plan (check your plan)
- Content generation: ~1-2 credits per article
- Keyword analysis: ~5-10 credits per keyword set

**Typical Blog Generation:**
- 2000-word blog: $0.50-$2.00 (depending on model)
- With DataForSEO: +$0.10-$0.50 per article

---

---

## Additional Resources

### Dashboard Repository

- **GitHub:** [tindevelopers/blogwriter-python-gcr-dashboard](https://github.com/tindevelopers/blogwriter-python-gcr-dashboard)
- **Deployment:** Vercel
- **Architecture:** Turborepo monorepo with Next.js 16

### Backend API Documentation

- **API Docs:** `https://blog-writer-api-dev-kq42l26tuq-od.a.run.app/docs`
- **OpenAPI Schema:** `https://blog-writer-api-dev-kq42l26tuq-od.a.run.app/openapi.json`
- **Health Check:** `https://blog-writer-api-dev-kq42l26tuq-od.a.run.app/health`

### Technology Documentation

- **Next.js:** https://nextjs.org/docs
- **Catalyst UI:** Tailwind CSS-based component library
- **TanStack Query:** https://tanstack.com/query
- **Firebase:** https://firebase.google.com/docs/firestore

---

**Document Version:** 1.3.6  
**Last Updated:** 2025-01-27  
**Dashboard Version:** Next.js 16 with Catalyst UI  
**For Support:** Contact your administrator or refer to the GitHub repository

