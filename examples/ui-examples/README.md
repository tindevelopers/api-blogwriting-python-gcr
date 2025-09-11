# 🎨 BlogWriter SDK UI Examples

This directory contains UI examples and templates for integrating with the BlogWriter SDK.

## 📁 Directory Structure

```
ui-examples/
├── react-dashboard/          # TailAdmin React Dashboard
├── nextjs-dashboard/         # TailAdmin Next.js Dashboard  
├── blog-writer-demo/         # Custom BlogWriter Demo App
└── README.md                 # This file
```

## 🚀 Available Templates

### 1. **React Dashboard** (`react-dashboard/`)
- **Source**: [TailAdmin React Dashboard](https://github.com/TailAdmin/free-react-tailwind-admin-dashboard)
- **Tech Stack**: React 19, TypeScript, Tailwind CSS
- **License**: MIT
- **Features**: 
  - Modern admin dashboard layout
  - Responsive design
  - Charts and analytics components
  - Form components perfect for blog generation
  - Table components for content management

### 2. **Next.js Dashboard** (`nextjs-dashboard/`)
- **Source**: [TailAdmin Next.js Dashboard](https://github.com/TailAdmin/free-nextjs-admin-dashboard)
- **Tech Stack**: Next.js 14, TypeScript, Tailwind CSS
- **License**: MIT
- **Features**:
  - Server-side rendering
  - App Router architecture
  - Optimized performance
  - SEO-friendly structure
  - Perfect for blog management interfaces

### 3. **BlogWriter Demo** (`blog-writer-demo/`)
- **Custom implementation** using TailAdmin components
- **Integrated with BlogWriter SDK**
- **Features**:
  - Blog generation interface
  - SEO optimization tools
  - Keyword analysis dashboard
  - Content management system
  - AI provider routing interface

## 🛠 Integration Guide

### Quick Start

1. **Choose your preferred template**:
   ```bash
   cd react-dashboard    # For React
   # OR
   cd nextjs-dashboard   # For Next.js
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Configure API endpoint**:
   ```javascript
   // In your config file
   const API_BASE_URL = 'http://localhost:8000/api/v1'
   ```

4. **Start development**:
   ```bash
   npm run dev
   ```

### BlogWriter SDK Integration

#### 1. **Blog Generation Interface**
```typescript
// Example component for blog generation
import { useState } from 'react'

const BlogGenerator = () => {
  const [blogData, setBlogData] = useState({
    topic: '',
    keywords: [],
    tone: 'professional',
    length: 'medium'
  })

  const generateBlog = async () => {
    const response = await fetch(`${API_BASE_URL}/blog/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(blogData)
    })
    
    const result = await response.json()
    // Handle result...
  }

  return (
    // Your UI components here
  )
}
```

#### 2. **SEO Analysis Dashboard**
```typescript
// Example SEO analysis component
const SEOAnalyzer = ({ content }: { content: string }) => {
  const [analysis, setAnalysis] = useState(null)

  const analyzeSEO = async () => {
    const response = await fetch(`${API_BASE_URL}/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content })
    })
    
    const result = await response.json()
    setAnalysis(result)
  }

  return (
    // SEO metrics display components
  )
}
```

#### 3. **Keyword Research Interface**
```typescript
// Example keyword research component
const KeywordResearch = () => {
  const [keywords, setKeywords] = useState([])

  const analyzeKeywords = async (keywordList: string[]) => {
    const response = await fetch(`${API_BASE_URL}/keywords/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ keywords: keywordList })
    })
    
    const result = await response.json()
    setKeywords(result.analyzed_keywords)
  }

  return (
    // Keyword analysis UI
  )
}
```

## 🎨 UI Components Available

### From TailAdmin Templates:

1. **Form Components**:
   - Input fields with validation
   - Select dropdowns
   - Textarea components
   - Toggle switches
   - Radio buttons

2. **Data Display**:
   - Tables with sorting/filtering
   - Cards and panels
   - Progress bars
   - Statistics widgets
   - Charts and graphs

3. **Navigation**:
   - Sidebar navigation
   - Breadcrumbs
   - Tabs
   - Pagination

4. **Feedback**:
   - Alerts and notifications
   - Loading spinners
   - Modal dialogs
   - Toast messages

## 🔧 Customization Guide

### 1. **Branding**
- Update colors in `tailwind.config.js`
- Replace logo files
- Modify typography settings

### 2. **Layout**
- Customize sidebar navigation
- Adjust responsive breakpoints
- Modify component spacing

### 3. **Components**
- Extend existing components
- Add new BlogWriter-specific components
- Integrate with your design system

## 📱 Responsive Design

All templates are fully responsive and work across:
- **Desktop**: Full dashboard experience
- **Tablet**: Optimized layout with collapsible sidebar
- **Mobile**: Mobile-first design with touch-friendly interface

## 🚀 Deployment

### Vercel (Recommended for Next.js)
```bash
npm install -g vercel
vercel --prod
```

### Netlify (Great for React)
```bash
npm run build
# Deploy dist/ folder to Netlify
```

### Docker
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

## 🔗 API Integration Examples

### Environment Configuration
```bash
# .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_API_KEY=your_api_key_here
```

### API Client Setup
```typescript
// lib/api.ts
class BlogWriterAPI {
  private baseURL: string
  
  constructor(baseURL: string) {
    this.baseURL = baseURL
  }

  async generateBlog(data: BlogRequest) {
    // Implementation
  }

  async analyzeSEO(content: string) {
    // Implementation  
  }

  async extractKeywords(content: string) {
    // Implementation
  }
}

export const api = new BlogWriterAPI(process.env.NEXT_PUBLIC_API_URL!)
```

## 📚 Additional Resources

- **TailAdmin Documentation**: [tailadmin.com](https://tailadmin.com)
- **Tailwind CSS**: [tailwindcss.com](https://tailwindcss.com)
- **BlogWriter SDK API**: See main README.md
- **Component Examples**: Check individual template directories

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch
3. Add your UI components or improvements
4. Submit a pull request

## 📄 License

- TailAdmin templates: MIT License
- Custom BlogWriter components: MIT License
- See individual template directories for specific license files
