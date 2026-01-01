# Per-Blog Writing Style Customization

**Version:** 1.0  
**Date:** January 1, 2026  
**Backend API:** `https://blog-writer-api-dev-613248238610.europe-west9.run.app`

---

## Overview

This guide provides specifications for implementing per-blog writing style customization in the Consumer Frontend. This feature allows end-users to optionally customize the writing style for individual blog generation requests without affecting organization-wide defaults.

### Purpose

- **Quick Style Adjustments**: Allow users to tweak writing style for specific blogs
- **Experimentation**: Enable A/B testing of different writing styles
- **Content Variety**: Generate blogs with varied tones for different audiences
- **Override Defaults**: Temporarily override organization defaults for special cases

---

## Architecture

### Configuration Priority Hierarchy

When generating a blog, configurations are merged in this order (highest to lowest priority):

1. **Per-Blog Override** (if specified) - Highest priority, applied only to this blog
2. **Organization Config** (if exists) - Organization defaults
3. **Template Settings** (always) - Base template configuration

### Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│               Consumer Frontend (Blog Testing Page)          │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Blog Generation Form                                 │   │
│  │  - Topic, Keywords, Length                            │   │
│  │  - [Optional] Writing Style Overrides ▼               │   │
│  │    • Formality slider                                 │   │
│  │    • Tone selection                                   │   │
│  │    • Custom instructions                              │   │
│  │  - Generate Blog Button                               │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                           │
                           │ POST /api/v1/blog/generate-enhanced
                           │ (includes writing_style_overrides)
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                Google Cloud Run (Backend API)                │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Blog Generation Pipeline                             │   │
│  │  1. Load org config from Firestore                    │   │
│  │  2. Apply per-blog overrides (if provided)            │   │
│  │  3. Generate blog with merged config                  │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## API Integration

### Blog Generation Request (Updated)

**Endpoint:** `POST /api/v1/blog/generate-enhanced`

**Request Body:**

```typescript
interface EnhancedBlogGenerationRequest {
  // ... existing fields ...
  primary_keyword: string;
  target_word_count?: number;
  tone?: string;
  
  // NEW: Per-blog writing style overrides
  writing_style_overrides?: WritingStyleOverrides;
}

interface WritingStyleOverrides {
  formality_level?: number;          // 1-10
  use_contractions?: boolean;
  conclusion_style?: string;          // "natural_wrap_up", "summary", "call_to_action", "open_ended"
  engagement_style?: string;          // "conversational", "professional", "authoritative", "analytical"
  personality?: string;               // "friendly", "authoritative", "analytical", "conversational"
  custom_instructions?: string;       // Max 2000 characters for per-blog overrides
}
```

**Example Request:**

```bash
curl -X POST "https://blog-writer-api-dev-613248238610.europe-west9.run.app/api/v1/blog/generate-enhanced" \
  -H "Content-Type: application/json" \
  -d '{
    "primary_keyword": "sustainable gardening tips",
    "target_word_count": 2000,
    "tone": "friendly",
    "writing_style_overrides": {
      "formality_level": 4,
      "use_contractions": true,
      "conclusion_style": "call_to_action",
      "engagement_style": "conversational",
      "personality": "friendly",
      "custom_instructions": "Focus on beginner-friendly advice. Include specific plant recommendations for small spaces."
    }
  }'
```

**Response:**

```typescript
interface BlogGenerationResponse {
  job_id: string;
  status: string;
  message: string;
}
```

---

## UI Component Specification

### WritingStyleOverridesPanel Component

**Location:** `components/WritingStyleOverridesPanel.tsx` (or similar)

**Purpose:** Optional panel/section for per-blog writing style customization.

**Props:**

```typescript
interface WritingStyleOverridesPanelProps {
  onChange: (overrides: WritingStyleOverrides | null) => void;
  defaultValues?: WritingStyleOverrides;
}
```

**Features:**

1. **Collapsible/Expandable Section**
   - Initially collapsed to avoid clutter
   - "Customize Writing Style" toggle/button to expand
   - Show summary of active overrides when collapsed

2. **Formality Level Slider**
   - Range: 1 (Very Casual) to 10 (Very Formal)
   - Default: Use organization setting
   - Visual indicators

3. **Quick Tone Presets** (Optional)
   - Buttons for common combinations:
     - "Very Casual" (formality: 3, contractions: true)
     - "Balanced" (formality: 6, contractions: true)
     - "Professional" (formality: 8, contractions: false)
     - "Very Formal" (formality: 10, contractions: false)

4. **Contractions Toggle**
   - Quick switch for enabling/disabling contractions

5. **Conclusion Style Dropdown**
   - Options: "Natural Wrap-up", "Summary", "Call-to-Action", "Open-ended"

6. **Engagement Style Dropdown**
   - Options: "Conversational", "Professional", "Authoritative", "Analytical"

7. **Personality Dropdown**
   - Options: "Friendly", "Authoritative", "Analytical", "Conversational"

8. **Custom Instructions Textarea**
   - Brief, focused instructions for this specific blog
   - Character counter
   - Max length: 2000 characters (shorter than org-level)
   - Placeholder: "Add specific instructions for this blog only..."

9. **Clear/Reset Button**
   - Reset all overrides to use organization defaults

**Example UI Layout (Collapsed):**

```
┌─────────────────────────────────────────────────────────────┐
│  Blog Generation                                             │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Topic                                                       │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ Best practices for sustainable gardening             │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                              │
│  Primary Keyword                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ sustainable gardening tips                            │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                              │
│  Target Word Count                                           │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ 2000                                                  │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                              │
│  ▶ Customize Writing Style (Optional)                       │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │                    Generate Blog                       │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

**Example UI Layout (Expanded):**

```
┌─────────────────────────────────────────────────────────────┐
│  Blog Generation                                             │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Topic                                                       │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ Best practices for sustainable gardening             │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                              │
│  Primary Keyword                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ sustainable gardening tips                            │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                              │
│  Target Word Count                                           │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ 2000                                                  │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                              │
│  ▼ Customize Writing Style (Optional)                       │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                                                      │   │
│  │  Quick Presets                                       │   │
│  │  ┌──────────┐ ┌──────────┐ ┌─────────────┐ ┌──────┐│   │
│  │  │  Casual  │ │ Balanced │ │Professional│ │Formal││   │
│  │  └──────────┘ └──────────┘ └─────────────┘ └──────┘│   │
│  │                                                      │   │
│  │  Formality Level: 4                                  │   │
│  │  Casual ●────────○──────────────────────── Formal    │   │
│  │         1  2  3  4  5  6  7  8  9  10               │   │
│  │                                                      │   │
│  │  ☑ Use contractions (it's, don't, can't)            │   │
│  │                                                      │   │
│  │  Conclusion Style                                    │   │
│  │  ┌───────────────────────────────────────────────┐  │   │
│  │  │ Call-to-Action                           ▼    │  │   │
│  │  └───────────────────────────────────────────────┘  │   │
│  │                                                      │   │
│  │  Engagement Style                                    │   │
│  │  ┌───────────────────────────────────────────────┐  │   │
│  │  │ Conversational                           ▼    │  │   │
│  │  └───────────────────────────────────────────────┘  │   │
│  │                                                      │   │
│  │  Personality                                         │   │
│  │  ┌───────────────────────────────────────────────┐  │   │
│  │  │ Friendly                                 ▼    │  │   │
│  │  └───────────────────────────────────────────────┘  │   │
│  │                                                      │   │
│  │  Custom Instructions for This Blog                  │   │
│  │  ┌───────────────────────────────────────────────┐  │   │
│  │  │ Focus on beginner-friendly advice. Include   │  │   │
│  │  │ specific plant recommendations for small      │  │   │
│  │  │ spaces.                                       │  │   │
│  │  └───────────────────────────────────────────────┘  │   │
│  │  67 / 2000 characters                                │   │
│  │                                                      │   │
│  │  ┌──────────────────┐                               │   │
│  │  │ Clear Overrides  │                               │   │
│  │  └──────────────────┘                               │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │                    Generate Blog                       │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## Implementation Example (React + TypeScript)

```typescript
import { useState } from 'react';
import { Button, Select, Slider, Switch, Textarea } from '@catalyst-ui/react';
import { ChevronDownIcon, ChevronRightIcon } from '@heroicons/react/24/outline';

interface WritingStyleOverrides {
  formality_level?: number;
  use_contractions?: boolean;
  conclusion_style?: string;
  engagement_style?: string;
  personality?: string;
  custom_instructions?: string;
}

interface WritingStyleOverridesPanelProps {
  onChange: (overrides: WritingStyleOverrides | null) => void;
  defaultValues?: WritingStyleOverrides;
}

export function WritingStyleOverridesPanel({
  onChange,
  defaultValues
}: WritingStyleOverridesPanelProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [formalityLevel, setFormalityLevel] = useState<number | undefined>(
    defaultValues?.formality_level
  );
  const [useContractions, setUseContractions] = useState<boolean | undefined>(
    defaultValues?.use_contractions
  );
  const [conclusionStyle, setConclusionStyle] = useState<string | undefined>(
    defaultValues?.conclusion_style
  );
  const [engagementStyle, setEngagementStyle] = useState<string | undefined>(
    defaultValues?.engagement_style
  );
  const [personality, setPersonality] = useState<string | undefined>(
    defaultValues?.personality
  );
  const [customInstructions, setCustomInstructions] = useState<string>(
    defaultValues?.custom_instructions || ''
  );

  // Check if any overrides are active
  const hasOverrides = () => {
    return (
      formalityLevel !== undefined ||
      useContractions !== undefined ||
      conclusionStyle !== undefined ||
      engagementStyle !== undefined ||
      personality !== undefined ||
      customInstructions.length > 0
    );
  };

  // Update parent component whenever values change
  const updateOverrides = () => {
    if (!hasOverrides()) {
      onChange(null);
      return;
    }

    const overrides: WritingStyleOverrides = {};
    if (formalityLevel !== undefined) overrides.formality_level = formalityLevel;
    if (useContractions !== undefined) overrides.use_contractions = useContractions;
    if (conclusionStyle) overrides.conclusion_style = conclusionStyle;
    if (engagementStyle) overrides.engagement_style = engagementStyle;
    if (personality) overrides.personality = personality;
    if (customInstructions) overrides.custom_instructions = customInstructions;

    onChange(overrides);
  };

  // Preset handlers
  const applyPreset = (preset: 'casual' | 'balanced' | 'professional' | 'formal') => {
    switch (preset) {
      case 'casual':
        setFormalityLevel(3);
        setUseContractions(true);
        setEngagementStyle('conversational');
        setPersonality('friendly');
        break;
      case 'balanced':
        setFormalityLevel(6);
        setUseContractions(true);
        setEngagementStyle('conversational');
        setPersonality('friendly');
        break;
      case 'professional':
        setFormalityLevel(8);
        setUseContractions(false);
        setEngagementStyle('professional');
        setPersonality('authoritative');
        break;
      case 'formal':
        setFormalityLevel(10);
        setUseContractions(false);
        setEngagementStyle('authoritative');
        setPersonality('authoritative');
        break;
    }
    updateOverrides();
  };

  const clearOverrides = () => {
    setFormalityLevel(undefined);
    setUseContractions(undefined);
    setConclusionStyle(undefined);
    setEngagementStyle(undefined);
    setPersonality(undefined);
    setCustomInstructions('');
    onChange(null);
  };

  // Trigger update when any value changes
  const handleFormalityChange = (value: number) => {
    setFormalityLevel(value);
    updateOverrides();
  };

  const handleContractionsChange = (value: boolean) => {
    setUseContractions(value);
    updateOverrides();
  };

  const handleConclusionStyleChange = (value: string) => {
    setConclusionStyle(value);
    updateOverrides();
  };

  const handleEngagementStyleChange = (value: string) => {
    setEngagementStyle(value);
    updateOverrides();
  };

  const handlePersonalityChange = (value: string) => {
    setPersonality(value);
    updateOverrides();
  };

  const handleCustomInstructionsChange = (value: string) => {
    setCustomInstructions(value);
    updateOverrides();
  };

  return (
    <div className="border rounded-lg p-4 bg-gray-50">
      {/* Header */}
      <button
        type="button"
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center justify-between w-full text-left"
      >
        <div className="flex items-center space-x-2">
          {isExpanded ? (
            <ChevronDownIcon className="w-5 h-5" />
          ) : (
            <ChevronRightIcon className="w-5 h-5" />
          )}
          <span className="font-medium">
            Customize Writing Style (Optional)
          </span>
          {hasOverrides() && (
            <span className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded">
              {Object.keys({
                formality_level: formalityLevel,
                use_contractions: useContractions,
                conclusion_style: conclusionStyle,
                engagement_style: engagementStyle,
                personality: personality,
                custom_instructions: customInstructions
              }).filter(k => 
                k === 'custom_instructions' 
                  ? customInstructions.length > 0 
                  : (k as any) !== undefined
              ).length} override{hasOverrides() && Object.keys({}).length !== 1 ? 's' : ''} active
            </span>
          )}
        </div>
      </button>

      {/* Expanded Content */}
      {isExpanded && (
        <div className="mt-4 space-y-4">
          {/* Quick Presets */}
          <div>
            <label className="block text-sm font-medium mb-2">Quick Presets</label>
            <div className="grid grid-cols-4 gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => applyPreset('casual')}
              >
                Casual
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => applyPreset('balanced')}
              >
                Balanced
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => applyPreset('professional')}
              >
                Professional
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => applyPreset('formal')}
              >
                Formal
              </Button>
            </div>
          </div>

          {/* Formality Level */}
          <div>
            <label className="block text-sm font-medium mb-2">
              Formality Level: {formalityLevel || 'Default'}
            </label>
            <Slider
              min={1}
              max={10}
              value={formalityLevel}
              onChange={handleFormalityChange}
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>Casual</span>
              <span>Formal</span>
            </div>
          </div>

          {/* Contractions Toggle */}
          <div className="flex items-center">
            <Switch
              checked={useContractions ?? false}
              onChange={handleContractionsChange}
            />
            <label className="ml-3 text-sm">
              Use contractions (it's, don't, can't)
            </label>
          </div>

          {/* Conclusion Style */}
          <div>
            <label className="block text-sm font-medium mb-2">Conclusion Style</label>
            <Select
              value={conclusionStyle || ''}
              onChange={(e) => handleConclusionStyleChange(e.target.value)}
            >
              <option value="">Use Default</option>
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
              value={engagementStyle || ''}
              onChange={(e) => handleEngagementStyleChange(e.target.value)}
            >
              <option value="">Use Default</option>
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
              value={personality || ''}
              onChange={(e) => handlePersonalityChange(e.target.value)}
            >
              <option value="">Use Default</option>
              <option value="friendly">Friendly</option>
              <option value="authoritative">Authoritative</option>
              <option value="analytical">Analytical</option>
              <option value="conversational">Conversational</option>
            </Select>
          </div>

          {/* Custom Instructions */}
          <div>
            <label className="block text-sm font-medium mb-2">
              Custom Instructions for This Blog
            </label>
            <Textarea
              value={customInstructions}
              onChange={(e) => handleCustomInstructionsChange(e.target.value)}
              maxLength={2000}
              rows={3}
              placeholder="Add specific instructions for this blog only..."
            />
            <div className="text-xs text-gray-500 mt-1">
              {customInstructions.length} / 2000 characters
            </div>
          </div>

          {/* Clear Button */}
          {hasOverrides() && (
            <div className="pt-2">
              <Button variant="secondary" size="sm" onClick={clearOverrides}>
                Clear All Overrides
              </Button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
```

---

## Integration into Blog Testing Page

### Updated Blog Generation Form

```typescript
// app/blog/test/page.tsx
import { useState } from 'react';
import { WritingStyleOverridesPanel } from '@/components/WritingStyleOverridesPanel';
import { toast } from '@/components/ui/toast';

export default function BlogTestingPage() {
  const [topic, setTopic] = useState('');
  const [primaryKeyword, setPrimaryKeyword] = useState('');
  const [wordCount, setWordCount] = useState(2000);
  const [tone, setTone] = useState('friendly');
  const [writingStyleOverrides, setWritingStyleOverrides] = useState<WritingStyleOverrides | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);

  const handleGenerate = async () => {
    setIsGenerating(true);
    try {
      const requestBody: EnhancedBlogGenerationRequest = {
        primary_keyword: primaryKeyword,
        target_word_count: wordCount,
        tone: tone,
        // Include overrides only if they exist
        ...(writingStyleOverrides && { writing_style_overrides: writingStyleOverrides })
      };

      const response = await fetch(
        'https://blog-writer-api-dev-613248238610.europe-west9.run.app/api/v1/blog/generate-enhanced',
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(requestBody)
        }
      );

      if (!response.ok) {
        throw new Error('Failed to generate blog');
      }

      const data = await response.json();
      toast.success(`Blog generation started! Job ID: ${data.job_id}`);
      
      // Navigate to results page or poll for status
      // ...
    } catch (error) {
      console.error('Failed to generate blog:', error);
      toast.error('Failed to generate blog');
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">Test Blog Generation</h1>

      <form onSubmit={(e) => { e.preventDefault(); handleGenerate(); }} className="space-y-6">
        {/* Topic */}
        <div>
          <label className="block text-sm font-medium mb-2">Topic</label>
          <input
            type="text"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder="E.g., Best practices for sustainable gardening"
            className="w-full px-3 py-2 border rounded"
            required
          />
        </div>

        {/* Primary Keyword */}
        <div>
          <label className="block text-sm font-medium mb-2">Primary Keyword</label>
          <input
            type="text"
            value={primaryKeyword}
            onChange={(e) => setPrimaryKeyword(e.target.value)}
            placeholder="E.g., sustainable gardening tips"
            className="w-full px-3 py-2 border rounded"
            required
          />
        </div>

        {/* Target Word Count */}
        <div>
          <label className="block text-sm font-medium mb-2">Target Word Count</label>
          <input
            type="number"
            value={wordCount}
            onChange={(e) => setWordCount(Number(e.target.value))}
            min={500}
            max={5000}
            className="w-full px-3 py-2 border rounded"
          />
        </div>

        {/* Tone */}
        <div>
          <label className="block text-sm font-medium mb-2">Tone</label>
          <select
            value={tone}
            onChange={(e) => setTone(e.target.value)}
            className="w-full px-3 py-2 border rounded"
          >
            <option value="friendly">Friendly</option>
            <option value="professional">Professional</option>
            <option value="casual">Casual</option>
            <option value="authoritative">Authoritative</option>
          </select>
        </div>

        {/* Writing Style Overrides */}
        <WritingStyleOverridesPanel
          onChange={setWritingStyleOverrides}
        />

        {/* Generate Button */}
        <Button
          type="submit"
          disabled={isGenerating}
          className="w-full"
        >
          {isGenerating ? 'Generating...' : 'Generate Blog'}
        </Button>
      </form>
    </div>
  );
}
```

---

## Use Cases

### Use Case 1: Casual Blog for Social Media

**Scenario:** User wants to generate a very casual, conversational blog for social media promotion.

**Override Configuration:**
- Formality Level: 3 (Casual)
- Use Contractions: Yes
- Engagement Style: Conversational
- Personality: Friendly
- Custom Instructions: "Use emojis sparingly. Keep it super casual and fun."

---

### Use Case 2: Professional White Paper

**Scenario:** User wants to generate a formal, authoritative piece for B2B audience.

**Override Configuration:**
- Formality Level: 9 (Very Formal)
- Use Contractions: No
- Engagement Style: Authoritative
- Personality: Authoritative
- Conclusion Style: Summary
- Custom Instructions: "Include industry statistics and cite sources."

---

### Use Case 3: Beginner-Friendly Tutorial

**Scenario:** User wants to write a beginner-friendly how-to guide.

**Override Configuration:**
- Formality Level: 5 (Balanced)
- Use Contractions: Yes
- Engagement Style: Conversational
- Personality: Friendly
- Custom Instructions: "Break down complex concepts. Include step-by-step instructions with examples."

---

## Testing Guide

### Manual Testing Checklist

1. **Basic Functionality**
   - [ ] Panel can expand and collapse
   - [ ] Form fields update correctly
   - [ ] Overrides passed to API correctly
   - [ ] Clear button resets all fields

2. **Quick Presets**
   - [ ] Casual preset applies correct values
   - [ ] Balanced preset applies correct values
   - [ ] Professional preset applies correct values
   - [ ] Formal preset applies correct values

3. **Individual Controls**
   - [ ] Formality slider updates value
   - [ ] Contractions toggle works
   - [ ] Dropdowns update correctly
   - [ ] Custom instructions accept input
   - [ ] Character counter updates

4. **Integration**
   - [ ] Overrides included in API request
   - [ ] Blog reflects override settings
   - [ ] Null sent when no overrides active
   - [ ] Organization defaults used when no overrides

5. **Edge Cases**
   - [ ] Max character limit enforced (2000)
   - [ ] Clearing overrides sends null
   - [ ] Partial overrides work correctly
   - [ ] Empty strings handled properly

---

## Best Practices

### For End Users

1. **Start with Presets**: Use quick presets as starting points
2. **Minimal Overrides**: Only override what's necessary
3. **Test Variations**: Try different styles for the same topic
4. **Use Custom Instructions**: Add context-specific guidelines
5. **Save Good Configs**: Note successful override combinations for reuse

### For Developers

1. **Validate Input**: Ensure formality level is 1-10
2. **Character Limits**: Enforce 2000 char limit for custom instructions
3. **Null Handling**: Send null when no overrides active
4. **UI Feedback**: Show active override count
5. **Debouncing**: Debounce custom instructions input
6. **Error Handling**: Gracefully handle API errors
7. **State Management**: Keep form state consistent

---

## Troubleshooting

### Issue: Overrides not applied to generated blog

**Solution:**
- Verify `writing_style_overrides` is included in request body
- Check that values are valid (formality: 1-10, valid enum strings)
- Ensure API endpoint is receiving the overrides correctly
- Check backend logs for config merging issues

### Issue: Character limit exceeded

**Solution:**
- Enforce 2000 character limit on frontend
- Show real-time character counter
- Display error message if limit exceeded
- Trim input before submission

### Issue: Presets not working

**Solution:**
- Verify preset values are correct
- Ensure `updateOverrides()` is called after preset applied
- Check state updates are triggering re-renders
- Verify onChange callback is working

---

## Support

For questions or issues:
- Backend API documentation: `https://blog-writer-api-dev-613248238610.europe-west9.run.app/docs`
- Configuration Guide: `FRONTEND_WRITING_STYLE_CONFIGURATION.md`

---

## Changelog

### Version 1.0 (January 1, 2026)
- Initial per-blog customization feature
- WritingStyleOverridesPanel component specification
- Integration guide for blog testing page
- Quick presets implementation

