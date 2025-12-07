# Local Test Instructions - Status Code Fix

## Fix Applied ✅

The `generate_text` method in `src/blog_writer_sdk/integrations/dataforseo_integration.py` now checks the DataForSEO API status code before extracting the result.

**Before:** Code tried to extract result even when API returned error status code  
**After:** Code checks `task_status == 20000` first and raises clear error if not successful

## Quick Test (Without Full Server)

### Option 1: Test the Code Logic Directly

```bash
cd /Users/gene/Projects/api-blogwriting-python-gcr

# Activate virtual environment if available
source .venv/bin/activate  # or: python3 -m venv .venv && source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the test script
python3 test_dataforseo_status_code_fix.py
```

### Option 2: Test via Full API Server

```bash
cd /Users/gene/Projects/api-blogwriting-python-gcr

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set DataForSEO credentials (or they'll be loaded from Secret Manager)
export DATAFORSEO_API_KEY=your_key
export DATAFORSEO_API_SECRET=your_secret

# Start server
python3 main.py

# In another terminal, run the test
./test_local_quick_generate.sh
```

## What to Look For

### ✅ Fix Working Correctly

If the fix is working, you should see:

1. **Clear Error Message** with status code:
   ```
   ValueError: DataForSEO generate_text failed: status_code=40204, message=Access denied...
   ```

2. **Helpful Guidance**:
   - Status 40204: "Subscription required - check DataForSEO plan includes Content Generation API"
   - Status 40501: "Invalid field - API format may have changed"

3. **No "Empty Content" Error**:
   - Should NOT see: "Generated content is empty or too short"
   - Should see: Actual DataForSEO API error with status code

### ❌ If Still Getting "Empty Content" Error

If you still see "empty or too short" error, check:

1. **Code is deployed**: Make sure the fix is in the running code
2. **Check logs**: Look for DataForSEO API response in server logs
3. **Verify status code**: The logs should show `task_status_code` value

## Expected Behavior

### Before Fix:
```
Error: "Content generation failed: Generated content is empty or too short (0 chars)"
```

### After Fix:
```
Error: "DataForSEO generate_text failed: status_code=40204, message=Access denied. Visit Plans and Subscriptions to activate your subscription (Subscription required - check DataForSEO plan includes Content Generation API)"
```

## Test Scripts Created

1. **`test_dataforseo_status_code_fix.py`** - Direct test of DataForSEO integration
2. **`test_local_quick_generate.sh`** - Test via local API server
3. **`start_local_test.sh`** - Start server and run test automatically

## Manual Code Verification

You can verify the fix is in place by checking:

```python
# In src/blog_writer_sdk/integrations/dataforseo_integration.py
# Around line 1940-1950, you should see:

task_status = first_task.get("status_code")
task_message = first_task.get("status_message", "")

# Check task status code first - 20000 = success
if task_status != 20000:
    error_msg = f"DataForSEO generate_text failed: status_code={task_status}, message={task_message}"
    logger.error(error_msg)
    # ... error handling ...
    raise ValueError(error_msg)
```

## Next Steps

1. ✅ Code fix applied
2. ⏳ Test locally (using instructions above)
3. ⏳ Deploy to Cloud Run
4. ⏳ Test on production
5. ⏳ Verify error messages are helpful

