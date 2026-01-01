# Blog Writer Admin Dashboard - Starter Repository

**Stack:** Next.js 14 + TypeScript + Catalyst UI + Firebase + Vercel  
**Backend:** https://blog-writer-api-dev-613248238610.europe-west9.run.app

---

## Quick Start

```bash
# 1. Install dependencies
npm install

# 2. Copy Catalyst components
cp -r "/Users/gene/Library/CloudStorage/Dropbox/Cursor/Source Files - UX:UI/catalyst-ui-kit/typescript/"* ./components/catalyst/

# 3. Configure environment
cp .env.local.example .env.local
# Edit .env.local with your Firebase and API credentials

# 4. Generate API types
npm run generate:types

# 5. Initialize Firestore
npm run init:firestore

# 6. Run development
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

---

## Features

- ✅ **Testing Interface** - Test blog generation with live preview
- ✅ **Analytics Dashboard** - Usage tracking, cost monitoring, charts
- ✅ **LiteLLM Control** - Configure and monitor LiteLLM proxy
- ✅ **Configuration** - Secure AI provider key management (Firestore)
- ✅ **Monitoring** - System health, logs, error tracking
- ✅ **Type Safety** - 100% TypeScript via OpenAPI generation

---

## Architecture

```
Frontend (Vercel) → Backend API (Cloud Run) → AI Providers
                  ↓
            Firestore (Config Storage)
```

---

## Documentation

See **FRONTEND_CATALYST_IMPLEMENTATION_GUIDE.md** for complete implementation details.

---

## Deployment

```bash
# Deploy to Vercel
vercel --prod
```

Configure environment variables in Vercel Dashboard.

---

**Ready to build!** 🚀

