# Google Search Console Access Grant - Step-by-Step Guide

## 🎯 What This Means

**"Granting GSC access"** means adding the service account email as a **user** to each of your websites in Google Search Console.

**Why:** Google Search Console requires explicit permission for each service account to access each site's data.

**Where:** This is done in the **Google Search Console web UI** (not in code, not automated).

---

## ✅ What You Need to Do (Manual Step)

### Step 1: Get Your Service Account Email

**Service Account Email:**
```
blog-writer-dev@api-ai-blog-writer.iam.gserviceaccount.com
```

**Copy this email** - you'll need it for each site.

---

### Step 2: Go to Google Search Console

1. **Open your browser**
2. **Go to:** https://search.google.com/search-console
3. **Sign in** with your Google account (the one that owns/manages your websites)

---

### Step 3: Select Your First Site

1. **In the left sidebar**, you'll see a list of your website properties
2. **Click on the first site** you want to grant access to
   - Example: `https://example.com` or `sc-domain:example.com`

---

### Step 4: Add the Service Account as a User

1. **Click on "Settings"** (gear icon) in the left sidebar
2. **Click on "Users and permissions"**
3. **Click the "+" button** or **"Add user"** button (usually at the top)
4. **In the "Add user" dialog:**
   - **Email field:** Paste `blog-writer-dev@api-ai-blog-writer.iam.gserviceaccount.com`
   - **Permission level:** Select **"Full"** (this gives read access to all data)
5. **Click "Add"** or **"Done"**

---

### Step 5: Repeat for Each Site

**For each website you want to use with blog generation:**

1. Go back to the property selector (dropdown at top)
2. Select the next site
3. Repeat Steps 3-4 above
4. Continue until all sites are configured

---

## 📋 Visual Guide

### What You'll See:

```
Google Search Console
├── Property Selector (dropdown) ← Select your site here
├── Overview
├── Performance
├── ...
└── Settings ← Click here
    └── Users and permissions ← Click here
        └── [+ Add user] ← Click this button
            └── Email: blog-writer-dev@api-ai-blog-writer.iam.gserviceaccount.com
            └── Permission: Full
            └── [Add] ← Click to save
```

---

## 🎯 Why This Is Necessary

**Google Search Console Security:**
- Each site property has its own access control
- Service accounts need explicit permission per site
- This prevents unauthorized access to your site data
- Google requires manual approval (can't be automated)

**What Happens Without This:**
- ❌ Backend can't access GSC data
- ❌ API calls will fail with "permission denied"
- ❌ Blog generation won't get site-specific performance data
- ✅ Blog generation still works, just without GSC insights

---

## ✅ How to Verify It Worked

### Option 1: Check in Google Search Console UI

1. Go to: https://search.google.com/search-console
2. Select your site
3. Go to **Settings → Users and permissions**
4. **Look for:** `blog-writer-dev@api-ai-blog-writer.iam.gserviceaccount.com`
5. **Should show:** "Full" permission

### Option 2: Test via API (After Deployment)

After the next deployment, test with:

```bash
curl -X POST https://your-api-url/api/v1/blog/generate-enhanced \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Test topic",
    "keywords": ["test"],
    "gsc_site_url": "https://yoursite.com",
    "mode": "multi_phase"
  }'
```

**If GSC access is granted:**
- ✅ No warnings about GSC unavailable
- ✅ Response includes GSC data insights

**If GSC access is NOT granted:**
- ⚠️ Warning: "Search Console optimization unavailable"
- ⚠️ Blog generation continues without GSC data

---

## 🔄 Do You Need to Do This?

### ✅ YES - If You Want:
- Site-specific performance data
- Content opportunities from your site
- Content gap analysis
- Keyword performance insights

### ❌ NO - If You:
- Don't have Google Search Console set up
- Don't want site-specific data
- Just want basic blog generation

**Blog generation works WITHOUT GSC** - you just won't get site-specific insights.

---

## 📝 Quick Checklist

For each site you want to use:

- [ ] Go to https://search.google.com/search-console
- [ ] Select the site property
- [ ] Go to Settings → Users and permissions
- [ ] Click "Add user"
- [ ] Enter: `blog-writer-dev@api-ai-blog-writer.iam.gserviceaccount.com`
- [ ] Select "Full" permission
- [ ] Click "Add"
- [ ] Verify the email appears in the users list

**Repeat for each site.**

---

## 🎯 Summary

**What "Granting GSC Access" Means:**
- Adding the service account email as a user in Google Search Console
- Done manually in the Google Search Console web UI
- Required once per site
- Takes about 30 seconds per site

**What Happens:**
- Backend can now read your site's Search Console data
- Blog generation gets site-specific performance insights
- Content opportunities and gaps are identified
- Better keyword targeting based on your site's data

**If You Skip This:**
- Blog generation still works
- Just won't have site-specific GSC insights
- Will show warnings but continue normally

---

## 💡 Example Scenario

**You have 3 sites:**
1. `https://site1.com`
2. `https://site2.com`
3. `sc-domain:example.com`

**What to do:**
1. Go to Google Search Console
2. Select `https://site1.com` → Settings → Add user → `blog-writer-dev@...` → Full → Add
3. Select `https://site2.com` → Settings → Add user → `blog-writer-dev@...` → Full → Add
4. Select `sc-domain:example.com` → Settings → Add user → `blog-writer-dev@...` → Full → Add

**Done!** Now the backend can access GSC data for all 3 sites.

---

## ❓ Common Questions

**Q: Do I have to do this for every site?**
A: Yes, once per site. Each site property needs separate permission.

**Q: Can this be automated?**
A: No, Google doesn't allow programmatic user management in Search Console for security reasons.

**Q: What if I don't do this?**
A: Blog generation works, but without site-specific GSC insights. You'll see warnings.

**Q: How long does this take?**
A: About 30 seconds per site. If you have 10 sites, about 5 minutes total.

**Q: Do I need to do this every time?**
A: No, once per site. The permission persists until you remove it.

**Q: Can I use a different service account?**
A: Yes, but you'd need to update the backend configuration. The current setup uses `blog-writer-dev@...`.

---

## 🚀 Next Steps

1. **Do the UI steps above** (add service account to each site)
2. **Wait for next deployment** (automatic when you push to develop)
3. **Test** by passing `gsc_site_url` from frontend
4. **Verify** no GSC warnings in response

That's it! The UI step is the only manual thing you need to do.

