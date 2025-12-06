# Testing Options for Frontend Team

**Question:** Where should I test the API?

**Answer:** You have multiple options! Choose what works best for you.

---

## Option 1: Test from Frontend Application (Recommended)

Run this code **in your frontend application** (React, Vue, Next.js, etc.):

```typescript
// In your frontend component/service
const response = await fetch('https://blog-writer-api-dev-kq42l26tuq-od.a.run.app/api/v1/blog/generate-enhanced', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    topic: "Dog Grooming Tips",
    keywords: ["dog grooming"],
    word_count_target: 100,
    blog_type: "guide"
  })
});

const data = await response.json();
console.log('Generated blog:', data);
```

**Where to put it:**
- React component: In a `useEffect` or button click handler
- Vue component: In a method or `mounted` hook
- Next.js API route: In your API route handler
- Service file: In your API service function

---

## Option 2: Test from Browser Console

Open your browser's developer console and paste:

```javascript
fetch('https://blog-writer-api-dev-kq42l26tuq-od.a.run.app/api/v1/blog/generate-enhanced', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    topic: "Dog Grooming Tips",
    keywords: ["dog grooming"],
    word_count_target: 100,
    blog_type: "guide"
  })
})
.then(res => res.json())
.then(data => console.log('Result:', data))
.catch(err => console.error('Error:', err));
```

**Steps:**
1. Open your browser (Chrome, Firefox, Safari)
2. Press F12 or right-click → Inspect
3. Go to "Console" tab
4. Paste the code above
5. Press Enter
6. See the result!

---

## Option 3: Test from Backend/CLI (Using curl)

If you want to test from the backend project or terminal:

```bash
curl -X POST https://blog-writer-api-dev-kq42l26tuq-od.a.run.app/api/v1/blog/generate-enhanced \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Dog Grooming Tips",
    "keywords": ["dog grooming"],
    "word_count_target": 100,
    "blog_type": "guide"
  }'
```

**Or use the test script we created:**

```bash
# From the backend project
./test_enhanced_endpoint_dog_grooming.sh
```

---

## Option 4: Test from Postman/Insomnia

1. **Method:** POST
2. **URL:** `https://blog-writer-api-dev-kq42l26tuq-od.a.run.app/api/v1/blog/generate-enhanced`
3. **Headers:**
   ```
   Content-Type: application/json
   ```
4. **Body (JSON):**
   ```json
   {
     "topic": "Dog Grooming Tips",
     "keywords": ["dog grooming"],
     "word_count_target": 100,
     "blog_type": "guide"
   }
   ```

---

## Option 5: Test from Frontend Test Suite

If you have frontend tests (Jest, Vitest, etc.):

```typescript
// In your test file
describe('Blog Generation API', () => {
  it('should generate a 100-word blog', async () => {
    const response = await fetch('https://blog-writer-api-dev-kq42l26tuq-od.a.run.app/api/v1/blog/generate-enhanced', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        topic: "Dog Grooming Tips",
        keywords: ["dog grooming"],
        word_count_target: 100,
        blog_type: "guide"
      })
    });

    const data = await response.json();
    
    expect(response.status).toBe(200);
    expect(data.title).toBeDefined();
    expect(data.content).toBeDefined();
    expect(data.content.split(' ').length).toBeGreaterThan(75);
    expect(data.content.split(' ').length).toBeLessThan(125);
  });
});
```

---

## 🎯 Recommended Approach

### For Quick Testing
**Use Browser Console (Option 2)** - Fastest way to test

### For Integration Testing
**Use Frontend Application (Option 1)** - Test in your actual app

### For Automated Testing
**Use Test Suite (Option 5)** - Add to your test suite

---

## 📋 What to Check

After running the test, verify:

1. ✅ **Status:** Response status is `200`
2. ✅ **Content:** `data.content` contains the blog text
3. ✅ **Word Count:** Should be ~75-125 words (target: 100)
4. ✅ **Subtopics:** `data.subtopics` array exists with 5-10 items
5. ✅ **Meta Tags:** `data.meta_title` and `data.meta_description` exist
6. ✅ **Cost:** `data.total_cost` is a reasonable number (~$0.007-0.009)

---

## 🔍 Example Response

```json
{
  "title": "Dog Grooming Tips for Pet Owners",
  "content": "Regular grooming is essential for maintaining your dog's health...",
  "meta_title": "Essential Dog Grooming Tips for Health and Well-Being",
  "meta_description": "Discover the importance of regular grooming...",
  "readability_score": 73.6,
  "seo_score": 45.0,
  "subtopics": [
    "Basic Brushing Techniques",
    "Bathing Best Practices",
    "Dental Hygiene"
  ],
  "total_tokens": 149,
  "total_cost": 0.00855,
  "generation_time": 8.0,
  "success": true
}
```

---

## 🚨 Common Issues

### CORS Error
If you get CORS errors from browser:
- The API should handle CORS, but if not, test from Postman/curl first
- Or test from your frontend app (which should have proper CORS setup)

### 500 Error
- Check that all required fields are present
- Verify `word_count_target` is between 100-10000
- Check backend logs for details

### Empty Response
- Check network tab for actual response
- Verify API endpoint URL is correct
- Check if API is deployed and running

---

## ✅ Quick Test Checklist

- [ ] Test from browser console (fastest)
- [ ] Test from your frontend app (most realistic)
- [ ] Verify response format matches expectations
- [ ] Check word count is within tolerance
- [ ] Verify subtopics are generated
- [ ] Confirm meta tags are present

---

**Bottom Line:** The code snippet is **JavaScript/TypeScript** meant for **frontend use**. Run it wherever you normally test your frontend code!

