# Frontend Writing Style Configuration Guide

**Version:** 1.0  
**Date:** January 1, 2026  
**Backend API:** `https://blog-writer-api-dev-613248238610.europe-west9.run.app`

---

## Overview

This guide provides specifications for implementing the Writing Style Configuration feature in the Admin Dashboard. This feature allows administrators to control how blogs are written by managing prompt templates and organization-specific writing configurations.

### Purpose

- **Control Blog Writing Style**: Configure how the AI writes blogs (formal, casual, conversational)
- **Manage Prompt Templates**: Create and manage reusable writing style templates
- **Organization Overrides**: Allow organizations to customize their writing style
- **Natural Writing**: Eliminate AI-sounding transitions and produce more natural content

---

## Architecture

### Configuration Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    Admin Dashboard (Vercel)                  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Writing Style Configuration Page                     │   │
│  │  - List Templates                                     │   │
│  │  - Create/Edit Templates                              │   │
│  │  - Preview Generated Instructions                     │   │
│  │  - Save Organization Config                           │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                           │
                           │ REST API (HTTPS)
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                Google Cloud Run (Backend API)                │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Prompt Management API                                │   │
│  │  - GET /api/v1/prompts/templates                      │   │
│  │  - POST /api/v1/prompts/templates                     │   │
│  │  - PUT /api/v1/prompts/config/writing-style/{org_id}  │   │
│  │  - GET /api/v1/prompts/config/merged                  │   │
│  └──────────────────────────────────────────────────────┘   │
│                           │                                  │
│                           │                                  │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  PromptConfigService                                  │   │
│  │  - Load templates from Firestore                      │   │
│  │  - Merge configs (template + org + blog overrides)    │   │
│  │  - Generate instruction text                          │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                           │
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   Google Firestore                           │
│                                                              │
│  Collections:                                                │
│  - prompt_templates/                                         │
│  - organizations/{orgId}/writing_config/                     │
│  - blog_generations/{blogId}/config_override/                │
└─────────────────────────────────────────────────────────────┘
```

### Configuration Priority

When generating a blog, configurations are merged with the following priority (highest to lowest):

1. **Blog Override** (if specified) - Temporary per-blog customizations
2. **Organization Config** (if exists) - Organization-specific defaults
3. **Template Settings** (always) - Base template configuration

---

## API Endpoints

### Base URL
```
https://blog-writer-api-dev-613248238610.europe-west9.run.app
```

### 1. List Prompt Templates

**Endpoint:** `GET /api/v1/prompts/templates`

**Query Parameters:**
- `active_only` (boolean, optional): Only return active templates (default: true)
- `category` (string, optional): Filter by category (tone, structure, style)

**Response:**
```typescript
interface PromptTemplate {
  id: string;
  name: string;
  description: string;
  category: string;  // "tone", "structure", "style"
  settings: TemplateSettings;
  instruction_text: string;
  is_active: boolean;
  created_at: string;  // ISO 8601
  updated_at: string;  // ISO 8601
  created_by: string;
}

interface TemplateSettings {
  formality_level: number;  // 1-10 (1=casual, 10=formal)
  use_contractions: boolean;
  avoid_obvious_transitions: boolean;
  transition_blocklist: string[];
  preferred_transitions: string[];
  sentence_variety: boolean;
  conclusion_style: string;  // "natural_wrap_up", "summary", "call_to_action", "open_ended"
  engagement_style: string;  // "conversational", "professional", "authoritative", "analytical"
  use_first_person: boolean;
  personality: string;  // "friendly", "authoritative", "analytical", "conversational"
  heading_style: string;
  example_style: string;
  custom_instructions: string;
}
```

**Example Request:**
```bash
curl -X GET "https://blog-writer-api-dev-613248238610.europe-west9.run.app/api/v1/prompts/templates?active_only=true&category=tone"
```

**Example Response:**
```json
[
  {
    "id": "template_abc123",
    "name": "Natural Conversational (Default)",
    "description": "Default writing style that produces natural, human-sounding content",
    "category": "tone",
    "settings": {
      "formality_level": 6,
      "use_contractions": true,
      "avoid_obvious_transitions": true,
      "transition_blocklist": [
        "In conclusion",
        "Moreover",
        "Furthermore"
      ],
      "preferred_transitions": [
        "Here's the thing",
        "So",
        "Now"
      ],
      "sentence_variety": true,
      "conclusion_style": "natural_wrap_up",
      "engagement_style": "conversational",
      "use_first_person": false,
      "personality": "friendly",
      "heading_style": "statements",
      "example_style": "mixed",
      "custom_instructions": ""
    },
    "instruction_text": "Write in a balanced, professional yet friendly tone...",
    "is_active": true,
    "created_at": "2026-01-01T00:00:00Z",
    "updated_at": "2026-01-01T00:00:00Z",
    "created_by": "system"
  }
]
```

---

### 2. Get Organization Writing Config

**Endpoint:** `GET /api/v1/prompts/config/writing-style/{org_id}`

**Path Parameters:**
- `org_id` (string, required): Organization ID

**Response:**
```typescript
interface OrganizationWritingConfig {
  id?: string;
  org_id: string;
  template_id?: string;  // Reference to prompt template
  custom_overrides: TemplateSettings;  // Only fields that override template
  tone_style?: string;
  transition_words?: string[];
  formality_level?: number;
  example_style?: string;
  updated_at?: string;
  updated_by: string;
}
```

**Example Request:**
```bash
curl -X GET "https://blog-writer-api-dev-613248238610.europe-west9.run.app/api/v1/prompts/config/writing-style/org_123"
```

**Example Response:**
```json
{
  "id": "config_xyz789",
  "org_id": "org_123",
  "template_id": "template_abc123",
  "custom_overrides": {
    "formality_level": 7,
    "custom_instructions": "Always mention our brand values"
  },
  "tone_style": "professional",
  "updated_at": "2026-01-01T12:00:00Z",
  "updated_by": "admin@example.com"
}
```

---

### 3. Update Organization Writing Config

**Endpoint:** `PUT /api/v1/prompts/config/writing-style/{org_id}`

**Path Parameters:**
- `org_id` (string, required): Organization ID

**Request Body:**
```typescript
interface WritingStyleUpdateRequest {
  template_id?: string;
  custom_overrides?: Partial<TemplateSettings>;
  tone_style?: string;
  transition_words?: string[];
  formality_level?: number;  // 1-10
  example_style?: string;
}
```

**Example Request:**
```bash
curl -X PUT "https://blog-writer-api-dev-613248238610.europe-west9.run.app/api/v1/prompts/config/writing-style/org_123" \
  -H "Content-Type: application/json" \
  -d '{
    "template_id": "template_abc123",
    "custom_overrides": {
      "formality_level": 7,
      "use_contractions": false,
      "custom_instructions": "Always mention our brand values"
    },
    "tone_style": "professional"
  }'
```

**Example Response:**
```json
{
  "message": "Writing config updated successfully"
}
```

---

### 4. Get Merged Writing Config

**Endpoint:** `GET /api/v1/prompts/config/merged`

**Query Parameters:**
- `org_id` (string, optional): Organization ID
- `blog_id` (string, optional): Blog generation job ID
- `template_id` (string, optional): Specific template ID to use

**Description:** Returns the final merged configuration after applying all overrides.

**Response:**
```typescript
interface MergedWritingConfig {
  formality_level: number;
  use_contractions: boolean;
  avoid_obvious_transitions: boolean;
  transition_blocklist: string[];
  preferred_transitions: string[];
  sentence_variety: boolean;
  conclusion_style: string;
  engagement_style: string;
  use_first_person: boolean;
  personality: string;
  heading_style: string;
  example_style: string;
  custom_instructions: string;
}
```

**Example Request:**
```bash
curl -X GET "https://blog-writer-api-dev-613248238610.europe-west9.run.app/api/v1/prompts/config/merged?org_id=org_123"
```

---

### 5. Get Instruction Text

**Endpoint:** `GET /api/v1/prompts/config/instruction-text`

**Query Parameters:**
- `org_id` (string, optional): Organization ID
- `blog_id` (string, optional): Blog generation job ID
- `template_id` (string, optional): Specific template ID to use

**Description:** Returns formatted instruction text ready for prompt injection.

**Response:**
```typescript
interface InstructionTextResponse {
  instruction_text: string;
}
```

**Example Request:**
```bash
curl -X GET "https://blog-writer-api-dev-613248238610.europe-west9.run.app/api/v1/prompts/config/instruction-text?org_id=org_123"
```

**Example Response:**
```json
{
  "instruction_text": "Write in a formal, authoritative tone.\nAvoid contractions. Use full forms (it is, do not, we will).\nAVOID these obvious AI transition words: In conclusion, Moreover, Furthermore\nInstead, use natural transitions: Therefore, However, Additionally\nVary sentence length - mix short punchy sentences with longer explanatory ones.\nEnd with a summary of key points.\nMaintain a professional yet friendly tone throughout.\nAvoid first-person voice. Use second-person (you) or third-person.\nDemonstrate expertise and authority.\n\nADDITIONAL INSTRUCTIONS:\nAlways mention our brand values"
}
```

---

## Component Specifications

### WritingStyleForm Component

**Location:** `components/WritingStyleForm.tsx` (or similar)

**Purpose:** Form component for configuring writing style settings.

**Props:**
```typescript
interface WritingStyleFormProps {
  initialValues?: OrganizationWritingConfig;
  availableTemplates: PromptTemplate[];
  orgId: string;
  onSave: (config: WritingStyleUpdateRequest) => Promise<void>;
  onCancel?: () => void;
}
```

**Features:**
1. **Template Selection**
   - Dropdown to select base template
   - Preview template settings
   - Show template description

2. **Formality Level Slider**
   - Range: 1 (Very Casual) to 10 (Very Formal)
   - Visual indicators for each level
   - Update in real-time

3. **Contractions Toggle**
   - Enable/disable use of contractions (it's, don't, etc.)

4. **Transitions Configuration**
   - Toggle to avoid obvious AI transitions
   - Add/remove blocked transition phrases
   - Add/remove preferred transition phrases

5. **Conclusion Style Dropdown**
   - Options: "Natural Wrap-up", "Summary", "Call-to-Action", "Open-ended"

6. **Engagement Style Dropdown**
   - Options: "Conversational", "Professional", "Authoritative", "Analytical"

7. **First Person Toggle**
   - Enable/disable first-person voice (I, we)

8. **Personality Dropdown**
   - Options: "Friendly", "Authoritative", "Analytical", "Conversational"

9. **Custom Instructions Textarea**
   - Free-form text field
   - Character counter
   - Max length: 5000 characters

10. **Preview Button**
    - Generate and display instruction text preview
    - Show merged configuration

11. **Save/Cancel Buttons**
    - Save configuration
    - Cancel changes

**Example UI Layout:**

```
┌─────────────────────────────────────────────────────────────┐
│  Writing Style Configuration                                 │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Base Template                                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ Natural Conversational (Default)             ▼        │  │
│  └───────────────────────────────────────────────────────┘  │
│  Default writing style that produces natural content         │
│                                                              │
│  Formality Level                                             │
│  Casual ●──────────○────────────────────── Formal            │
│         1  2  3  4  5  6  7  8  9  10                       │
│                                                              │
│  Writing Options                                             │
│  ☑ Use contractions (it's, don't, can't)                    │
│  ☑ Avoid obvious AI transitions                             │
│  ☐ Use first-person voice (I, we)                           │
│                                                              │
│  Blocked Transitions                                         │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ ✕ In conclusion                                        │  │
│  │ ✕ Moreover                                             │  │
│  │ ✕ Furthermore                                          │  │
│  │ + Add transition phrase                                │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                              │
│  Preferred Transitions                                       │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ ✕ Here's the thing                                     │  │
│  │ ✕ So                                                   │  │
│  │ ✕ Now                                                  │  │
│  │ + Add transition phrase                                │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                              │
│  Conclusion Style                                            │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ Natural Wrap-up                                  ▼     │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                              │
│  Engagement Style                                            │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ Conversational                                   ▼     │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                              │
│  Personality                                                 │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ Friendly                                         ▼     │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                              │
│  Custom Instructions (Optional)                              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                                                        │  │
│  │ Add any additional writing guidelines here...         │  │
│  │                                                        │  │
│  │                                                        │  │
│  └───────────────────────────────────────────────────────┘  │
│  0 / 5000 characters                                         │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │   Preview    │  │    Cancel    │  │  Save Changes    │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Implementation Example (React + TypeScript)

```typescript
import { useState, useEffect } from 'react';
import { Button, Input, Select, Slider, Switch, Textarea } from '@catalyst-ui/react';

interface WritingStyleFormProps {
  initialValues?: OrganizationWritingConfig;
  availableTemplates: PromptTemplate[];
  orgId: string;
  onSave: (config: WritingStyleUpdateRequest) => Promise<void>;
  onCancel?: () => void;
}

export function WritingStyleForm({
  initialValues,
  availableTemplates,
  orgId,
  onSave,
  onCancel
}: WritingStyleFormProps) {
  const [selectedTemplate, setSelectedTemplate] = useState<string>(
    initialValues?.template_id || availableTemplates[0]?.id
  );
  const [formalityLevel, setFormalityLevel] = useState<number>(
    initialValues?.formality_level || 6
  );
  const [useContractions, setUseContractions] = useState<boolean>(
    initialValues?.custom_overrides?.use_contractions ?? true
  );
  const [avoidTransitions, setAvoidTransitions] = useState<boolean>(
    initialValues?.custom_overrides?.avoid_obvious_transitions ?? true
  );
  const [blockedTransitions, setBlockedTransitions] = useState<string[]>(
    initialValues?.custom_overrides?.transition_blocklist || []
  );
  const [preferredTransitions, setPreferredTransitions] = useState<string[]>(
    initialValues?.custom_overrides?.preferred_transitions || []
  );
  const [conclusionStyle, setConclusionStyle] = useState<string>(
    initialValues?.custom_overrides?.conclusion_style || 'natural_wrap_up'
  );
  const [engagementStyle, setEngagementStyle] = useState<string>(
    initialValues?.custom_overrides?.engagement_style || 'conversational'
  );
  const [useFirstPerson, setUseFirstPerson] = useState<boolean>(
    initialValues?.custom_overrides?.use_first_person ?? false
  );
  const [personality, setPersonality] = useState<string>(
    initialValues?.custom_overrides?.personality || 'friendly'
  );
  const [customInstructions, setCustomInstructions] = useState<string>(
    initialValues?.custom_overrides?.custom_instructions || ''
  );
  const [isLoading, setIsLoading] = useState(false);
  const [previewText, setPreviewText] = useState<string>('');

  const handlePreview = async () => {
    setIsLoading(true);
    try {
      // Build merged config and get instruction text
      const response = await fetch(
        `/api/v1/prompts/config/instruction-text?org_id=${orgId}&template_id=${selectedTemplate}`,
        {
          method: 'GET',
          headers: { 'Content-Type': 'application/json' }
        }
      );
      const data = await response.json();
      setPreviewText(data.instruction_text);
    } catch (error) {
      console.error('Failed to generate preview:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSave = async () => {
    setIsLoading(true);
    try {
      const config: WritingStyleUpdateRequest = {
        template_id: selectedTemplate,
        formality_level: formalityLevel,
        custom_overrides: {
          formality_level: formalityLevel,
          use_contractions: useContractions,
          avoid_obvious_transitions: avoidTransitions,
          transition_blocklist: blockedTransitions,
          preferred_transitions: preferredTransitions,
          conclusion_style: conclusionStyle,
          engagement_style: engagementStyle,
          use_first_person: useFirstPerson,
          personality: personality,
          custom_instructions: customInstructions
        }
      };
      await onSave(config);
    } catch (error) {
      console.error('Failed to save configuration:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Template Selection */}
      <div>
        <label className="block text-sm font-medium mb-2">Base Template</label>
        <Select
          value={selectedTemplate}
          onChange={(e) => setSelectedTemplate(e.target.value)}
        >
          {availableTemplates.map((template) => (
            <option key={template.id} value={template.id}>
              {template.name}
            </option>
          ))}
        </Select>
        {selectedTemplate && (
          <p className="text-sm text-gray-500 mt-1">
            {availableTemplates.find(t => t.id === selectedTemplate)?.description}
          </p>
        )}
      </div>

      {/* Formality Level */}
      <div>
        <label className="block text-sm font-medium mb-2">
          Formality Level: {formalityLevel}
        </label>
        <Slider
          min={1}
          max={10}
          value={formalityLevel}
          onChange={(value) => setFormalityLevel(value)}
        />
        <div className="flex justify-between text-xs text-gray-500 mt-1">
          <span>Casual</span>
          <span>Formal</span>
        </div>
      </div>

      {/* Writing Options */}
      <div className="space-y-3">
        <div className="flex items-center">
          <Switch
            checked={useContractions}
            onChange={setUseContractions}
          />
          <label className="ml-3 text-sm">
            Use contractions (it's, don't, can't)
          </label>
        </div>
        <div className="flex items-center">
          <Switch
            checked={avoidTransitions}
            onChange={setAvoidTransitions}
          />
          <label className="ml-3 text-sm">
            Avoid obvious AI transitions
          </label>
        </div>
        <div className="flex items-center">
          <Switch
            checked={useFirstPerson}
            onChange={setUseFirstPerson}
          />
          <label className="ml-3 text-sm">
            Use first-person voice (I, we)
          </label>
        </div>
      </div>

      {/* Conclusion Style */}
      <div>
        <label className="block text-sm font-medium mb-2">Conclusion Style</label>
        <Select
          value={conclusionStyle}
          onChange={(e) => setConclusionStyle(e.target.value)}
        >
          <option value="natural_wrap_up">Natural Wrap-up</option>
          <option value="summary">Summary</option>
          <option value="call_to_action">Call-to-Action</option>
          <option value="open_ended">Open-ended</option>
        </Select>
      </div>

      {/* Engagement Style */}
      <div>
        <label className="block text-sm font-medium mb-2">Engagement Style</label>
        <Select
          value={engagementStyle}
          onChange={(e) => setEngagementStyle(e.target.value)}
        >
          <option value="conversational">Conversational</option>
          <option value="professional">Professional</option>
          <option value="authoritative">Authoritative</option>
          <option value="analytical">Analytical</option>
        </Select>
      </div>

      {/* Personality */}
      <div>
        <label className="block text-sm font-medium mb-2">Personality</label>
        <Select
          value={personality}
          onChange={(e) => setPersonality(e.target.value)}
        >
          <option value="friendly">Friendly</option>
          <option value="authoritative">Authoritative</option>
          <option value="analytical">Analytical</option>
          <option value="conversational">Conversational</option>
        </Select>
      </div>

      {/* Custom Instructions */}
      <div>
        <label className="block text-sm font-medium mb-2">
          Custom Instructions (Optional)
        </label>
        <Textarea
          value={customInstructions}
          onChange={(e) => setCustomInstructions(e.target.value)}
          maxLength={5000}
          rows={5}
          placeholder="Add any additional writing guidelines here..."
        />
        <div className="text-xs text-gray-500 mt-1">
          {customInstructions.length} / 5000 characters
        </div>
      </div>

      {/* Preview */}
      {previewText && (
        <div className="border rounded p-4 bg-gray-50">
          <h3 className="font-medium mb-2">Preview Instruction Text:</h3>
          <pre className="text-xs whitespace-pre-wrap">{previewText}</pre>
        </div>
      )}

      {/* Actions */}
      <div className="flex justify-end space-x-3">
        <Button variant="outline" onClick={handlePreview} disabled={isLoading}>
          Preview
        </Button>
        {onCancel && (
          <Button variant="secondary" onClick={onCancel} disabled={isLoading}>
            Cancel
          </Button>
        )}
        <Button onClick={handleSave} disabled={isLoading}>
          {isLoading ? 'Saving...' : 'Save Changes'}
        </Button>
      </div>
    </div>
  );
}
```

---

## Dashboard Page

### Page Route

**Path:** `/settings/writing-style` or `/configuration/writing-style`

### Page Layout

```
┌─────────────────────────────────────────────────────────────┐
│  [Dashboard Header]                                          │
├─────────────────────────────────────────────────────────────┤
│  [Sidebar Navigation]  │  Writing Style Configuration        │
│                        │                                     │
│  • Dashboard           │  Configure how the AI writes blogs  │
│  • Blog Generation     │  for your organization.             │
│  • Analytics           │                                     │
│  • Configuration       │  ┌─────────────────────────────┐   │
│    - AI Providers      │  │  Your Current Style          │   │
│    - Writing Style  ◀──│  │  Template: Natural Conv...   │   │
│    - API Keys          │  │  Formality: 6/10             │   │
│  • Monitoring          │  │  Contractions: Enabled       │   │
│  • Users               │  └─────────────────────────────┘   │
│                        │                                     │
│                        │  [WritingStyleForm Component]       │
│                        │                                     │
│                        │                                     │
│                        │                                     │
└────────────────────────┴─────────────────────────────────────┘
```

### Page Implementation

```typescript
// app/settings/writing-style/page.tsx
import { useState, useEffect } from 'react';
import { WritingStyleForm } from '@/components/WritingStyleForm';
import { useAuth } from '@/hooks/useAuth';
import { toast } from '@/components/ui/toast';

export default function WritingStyleConfigPage() {
  const { user, orgId } = useAuth();
  const [templates, setTemplates] = useState<PromptTemplate[]>([]);
  const [currentConfig, setCurrentConfig] = useState<OrganizationWritingConfig | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, [orgId]);

  const loadData = async () => {
    setIsLoading(true);
    try {
      // Load available templates
      const templatesResponse = await fetch(
        'https://blog-writer-api-dev-613248238610.europe-west9.run.app/api/v1/prompts/templates?active_only=true'
      );
      const templatesData = await templatesResponse.json();
      setTemplates(templatesData);

      // Load current organization config
      const configResponse = await fetch(
        `https://blog-writer-api-dev-613248238610.europe-west9.run.app/api/v1/prompts/config/writing-style/${orgId}`
      );
      const configData = await configResponse.json();
      setCurrentConfig(configData);
    } catch (error) {
      console.error('Failed to load data:', error);
      toast.error('Failed to load writing style configuration');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSave = async (config: WritingStyleUpdateRequest) => {
    try {
      const response = await fetch(
        `https://blog-writer-api-dev-613248238610.europe-west9.run.app/api/v1/prompts/config/writing-style/${orgId}`,
        {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(config)
        }
      );

      if (!response.ok) {
        throw new Error('Failed to update configuration');
      }

      toast.success('Writing style configuration updated successfully');
      loadData(); // Reload to show updated config
    } catch (error) {
      console.error('Failed to save configuration:', error);
      toast.error('Failed to save writing style configuration');
      throw error;
    }
  };

  if (isLoading) {
    return <div>Loading...</div>;
  }

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Writing Style Configuration</h1>
        <p className="text-gray-600">
          Configure how the AI writes blogs for your organization. These settings will be applied to all blog generation requests.
        </p>
      </div>

      {currentConfig && (
        <div className="mb-6 p-4 border rounded-lg bg-blue-50">
          <h2 className="font-semibold mb-2">Your Current Style</h2>
          <dl className="grid grid-cols-2 gap-2 text-sm">
            <dt className="text-gray-600">Template:</dt>
            <dd>{templates.find(t => t.id === currentConfig.template_id)?.name || 'Default'}</dd>
            <dt className="text-gray-600">Formality:</dt>
            <dd>{currentConfig.formality_level || 6}/10</dd>
            <dt className="text-gray-600">Contractions:</dt>
            <dd>{currentConfig.custom_overrides?.use_contractions ? 'Enabled' : 'Disabled'}</dd>
          </dl>
        </div>
      )}

      <WritingStyleForm
        initialValues={currentConfig}
        availableTemplates={templates}
        orgId={orgId}
        onSave={handleSave}
      />
    </div>
  );
}
```

---

## Testing Guide

### Manual Testing Checklist

1. **List Templates**
   - [ ] Can fetch and display all templates
   - [ ] Templates show correct name, description, category
   - [ ] Filtering by category works

2. **View Organization Config**
   - [ ] Can load current org configuration
   - [ ] Default values shown if no config exists
   - [ ] Template reference resolved correctly

3. **Update Configuration**
   - [ ] Can save new configuration
   - [ ] All fields persist correctly
   - [ ] Custom instructions saved properly
   - [ ] Success message displayed

4. **Preview Functionality**
   - [ ] Preview generates instruction text
   - [ ] Preview reflects current form values
   - [ ] Preview updates when template changes

5. **Form Validation**
   - [ ] Formality level constrained to 1-10
   - [ ] Custom instructions limited to 5000 chars
   - [ ] Required fields validated

6. **Integration**
   - [ ] Config applied to blog generation
   - [ ] Blog uses merged configuration
   - [ ] Transitions and style reflected in output

---

## Deployment

### Environment Variables

Add to Vercel environment variables:

```bash
NEXT_PUBLIC_API_BASE_URL=https://blog-writer-api-dev-613248238610.europe-west9.run.app
```

### Build & Deploy

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Deploy to Vercel
vercel --prod
```

---

## Support

For questions or issues:
- Backend API documentation: `https://blog-writer-api-dev-613248238610.europe-west9.run.app/docs`
- Backend repository: Contact admin
- Frontend repository: Your repo

---

## Changelog

### Version 1.0 (January 1, 2026)
- Initial writing style configuration feature
- WritingStyleForm component specification
- Dashboard page specification
- API endpoints documentation

