# Google Search Console Bulk Setup Guide - 25 Sites

## 🎯 Your Situation

- **25 sites** to configure
- **Service Account:** `blog-writer-dev@api-ai-blog-writer.iam.gserviceaccount.com`
- **Goal:** Add service account to all sites quickly

---

## ✅ Solution: Use Bulk Helper Script

I've created a helper script that makes this process faster and easier.

---

## 🚀 Quick Start

### Step 1: Create Sites List

Create a file `gsc-sites.txt` in the project root with all your site URLs:

```bash
# gsc-sites.txt
https://site1.com
https://site2.com
https://site3.com
sc-domain:example.com
# ... add all 25 sites
```

### Step 2: Run Helper Script

```bash
./scripts/bulk-add-gsc-service-account.sh
```

**What it does:**
- Lists all your sites
- Generates instructions for each site
- Creates a checklist file
- Provides copy-paste instructions

### Step 3: Add Service Account to Each Site

**For each site:**
1. Go to Google Search Console
2. Select the site
3. Settings → Users and permissions
4. Add user → Paste: `blog-writer-dev@api-ai-blog-writer.iam.gserviceaccount.com`
5. Permission: Full
6. Add

**Time:** ~30 seconds per site = ~12 minutes total for 25 sites

---

## 💡 Pro Tips for Faster Setup

### Tip 1: Use Multiple Browser Tabs

1. Open Google Search Console in multiple tabs (one per site)
2. Add service account to each tab
3. Faster than switching sites repeatedly

### Tip 2: Use Browser Extensions

**If you use Chrome:**
- Install a form-filler extension
- Pre-fill the email field
- Just select site and click "Add"

### Tip 3: Batch Process

**Do 5 sites at a time:**
- Open 5 tabs
- Add service account to all 5
- Take a break
- Repeat until all 25 are done

---

## 📋 Alternative: Using Your Existing Email

### Can You Use `analytics@tin.info`?

**Short Answer:** Not recommended, but possible with OAuth2

**Why Not Recommended:**
- ❌ More complex code changes
- ❌ OAuth tokens expire (need refresh logic)
- ❌ Still need to add email to each site manually
- ❌ Less secure than service account

**If You Really Want To:**
- Would need OAuth2 implementation
- Significant code changes
- Still requires manual steps
- Not worth the effort

**Recommendation:** ✅ Stick with service account

---

## 🔄 Can We Automate This?

### Google Search Console API Limitation

**❌ Google Search Console API does NOT support:**
- Adding users programmatically
- Removing users programmatically
- Managing permissions via API

**Why:** Security feature - user management must be done manually

### Possible Workarounds (Not Recommended)

1. **Browser Automation (Selenium):**
   - ❌ Fragile (UI changes break it)
   - ❌ Against Google's ToS potentially
   - ❌ Requires maintaining scripts

2. **Google Workspace Admin API:**
   - ✅ Only if sites are in Google Workspace
   - ✅ Only if you have admin access
   - ❌ Doesn't apply to most cases

**Recommendation:** ❌ Manual is the only reliable way

---

## ✅ Recommended Approach

### Use Service Account + Helper Script

**Why:**
- ✅ Service account already set up
- ✅ More secure
- ✅ Simpler
- ✅ Industry standard

**Process:**
1. Run helper script
2. Follow instructions for each site
3. ~12 minutes total for 25 sites
4. Done forever (one-time setup)

---

## 📝 Step-by-Step Instructions

### 1. Create Sites File

```bash
# Create gsc-sites.txt with all your sites
cat > gsc-sites.txt << EOF
https://site1.com
https://site2.com
https://site3.com
# ... add all 25 sites
EOF
```

### 2. Run Helper Script

```bash
./scripts/bulk-add-gsc-service-account.sh
```

### 3. Follow Instructions

The script will:
- Show you each site
- Provide copy-paste instructions
- Create a checklist
- Open Google Search Console (optional)

### 4. Add Service Account

**For each site:**
- Copy: `blog-writer-dev@api-ai-blog-writer.iam.gserviceaccount.com`
- Paste in "Add user" dialog
- Select "Full" permission
- Click "Add"

### 5. Verify

Check the checklist file to track progress.

---

## 🎯 Summary

**Can you use `analytics@tin.info`?**
- ❌ Not recommended (needs OAuth2, complex, still manual)

**Can you automate adding users?**
- ❌ No, Google doesn't allow it via API
- ✅ Helper script makes it faster

**Best Approach:**
- ✅ Use service account (already set up)
- ✅ Use helper script (makes it faster)
- ✅ ~12 minutes for 25 sites (one-time)

**The helper script is ready to use!** It will guide you through adding the service account to all 25 sites quickly.

