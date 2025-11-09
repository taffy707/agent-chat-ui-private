# Testing Document API Authentication

This guide will help you test the JWT authentication integration between your frontend (Agent Chat UI) and backend (Document API).

## Prerequisites

Before testing, ensure you have:

1. ✅ **Supabase Project Set Up**
   - Created a Supabase project at https://supabase.com
   - Configured authentication providers (email/password at minimum)
   - Noted your project URL and anon key

2. ✅ **Environment Variables Configured**

   **Frontend** (`.env` or `.env.local`):
   ```bash
   NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
   NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key-here
   NEXT_PUBLIC_DOCUMENT_API_URL=http://localhost:8000
   ```

   **Backend** (`document-api/.env`):
   ```bash
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_ANON_KEY=your-anon-key-here
   # ... other config
   ```

3. ✅ **Dependencies Installed**
   ```bash
   # Frontend
   pnpm install

   # Backend
   cd document-api
   pip install -r requirements.txt
   ```

---

## Step-by-Step Testing Guide

### Step 1: Start Both Servers

**Terminal 1 - Start Document API:**
```bash
cd document-api
python main.py
```

Expected output:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Starting Document Upload API...
INFO:     ✅ Database connection pool established
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Terminal 2 - Start Frontend:**
```bash
pnpm dev
```

Expected output:
```
  ▲ Next.js 15.x.x
  - Local:        http://localhost:3000
```

---

### Step 2: Verify Both Services Are Running

**Test Document API Health (No Auth Required):**
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "gcp_project": "your-project-id",
  "datastore_id": "your-datastore-id",
  "bucket": "your-bucket-name"
}
```

**Test Frontend:**
- Open browser: http://localhost:3000
- You should see the Agent Chat UI
- Should be redirected to `/signin` if not authenticated

---

### Step 3: Sign Up / Sign In via Frontend

1. **Navigate to Sign In page:**
   - Go to http://localhost:3000/signin
   - Or click sign-in from the navigation

2. **Create an account or sign in:**
   - Option A: Email/password
     - Enter email and password
     - If signing up, use `/signup` page
   - Option B: Google OAuth (if enabled)
     - Click "Sign in with Google"

3. **Verify successful authentication:**
   - After sign-in, you should be redirected to home page
   - Check sidebar (bottom) for your user profile
   - Open browser DevTools > Console
   - No authentication errors should appear

---

### Step 4: Get Your JWT Access Token

**Method 1: Browser DevTools (Easiest)**

Open browser DevTools (F12), go to Console, and run:

```javascript
// Get the current session
const session = JSON.parse(localStorage.getItem('supabase.auth.token'));
console.log('Access Token:', session?.currentSession?.access_token);

// Copy the token
copy(session?.currentSession?.access_token);
```

The token should look like:
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzA2...
```

**Method 2: Network Tab**

1. Open DevTools > Network tab
2. Make any API request from the frontend
3. Click on the request
4. Look at "Request Headers"
5. Find "Authorization: Bearer <token>"
6. Copy the token (everything after "Bearer ")

**Method 3: React Component (For Development)**

Add this temporary component to see your token:

```tsx
// Add to any page for debugging
import { useAuthContext } from "@/providers/Auth";

export function TokenDebug() {
  const { session } = useAuthContext();
  return (
    <pre className="text-xs">
      Token: {session?.access_token?.substring(0, 50)}...
    </pre>
  );
}
```

---

### Step 5: Test Authentication with curl

Now that you have your JWT token, test the Document API endpoints:

**Set token as environment variable:**
```bash
export TOKEN="your-actual-jwt-token-here"
```

**Test 1: Create a Collection (Authenticated)**
```bash
curl -X POST http://localhost:8000/collections \
  -H "Authorization: Bearer $TOKEN" \
  -F "name=Test Collection" \
  -F "description=Testing authentication"
```

Expected response (success):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "user-uuid-from-supabase",
  "name": "Test Collection",
  "description": "Testing authentication",
  "document_count": 0,
  "created_at": "2025-11-09T10:30:00.000Z",
  "updated_at": "2025-11-09T10:30:00.000Z"
}
```

**Test 2: List Collections (Authenticated)**
```bash
curl -X GET "http://localhost:8000/collections?limit=10&offset=0" \
  -H "Authorization: Bearer $TOKEN"
```

Expected response:
```json
{
  "user_id": "user-uuid-from-supabase",
  "total_count": 1,
  "limit": 10,
  "offset": 0,
  "returned_count": 1,
  "collections": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Test Collection",
      "document_count": 0,
      ...
    }
  ]
}
```

**Test 3: Upload a Document (Authenticated)**

First, create a test file:
```bash
echo "Hello, this is a test document!" > test.txt
```

Then upload:
```bash
curl -X POST http://localhost:8000/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "collection_id=550e8400-e29b-41d4-a716-446655440000" \
  -F "files=@test.txt"
```

Expected response (202 Accepted):
```json
{
  "status": "accepted",
  "message": "Successfully uploaded 1 document(s) to 'Test Collection' collection",
  "collection_id": "550e8400-e29b-41d4-a716-446655440000",
  "documents": [...],
  "vertex_ai_import": {
    "triggered": true,
    "successes": 1,
    ...
  }
}
```

**Test 4: Test Without Authentication (Should Fail)**
```bash
curl -X GET http://localhost:8000/collections
```

Expected response (401 Unauthorized):
```json
{
  "detail": "Not authenticated"
}
```

**Test 5: Test With Invalid Token (Should Fail)**
```bash
curl -X GET http://localhost:8000/collections \
  -H "Authorization: Bearer invalid-token-here"
```

Expected response (401 Unauthorized):
```json
{
  "detail": "Authentication failed"
}
```

---

### Step 6: Test Via Frontend Code

Now test using the React hooks we created:

**Option A: Using Browser Console (Quick Test)**

1. Open http://localhost:3000 (make sure you're signed in)
2. Open DevTools > Console
3. Run this code:

```javascript
// Test creating a collection
async function testCreateCollection() {
  const response = await fetch('http://localhost:8000/collections', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${JSON.parse(localStorage.getItem('supabase.auth.token'))?.currentSession?.access_token}`
    },
    body: (() => {
      const formData = new FormData();
      formData.append('name', 'Test Collection from Browser');
      formData.append('description', 'Created via browser console');
      return formData;
    })()
  });

  const data = await response.json();
  console.log('Created collection:', data);
  return data;
}

testCreateCollection();
```

**Option B: Using the Example Component**

1. Copy the example component to your app:
```bash
cp DOCUMENT_API_USAGE_EXAMPLE.tsx src/app/test-documents/page.tsx
```

2. Navigate to: http://localhost:3000/test-documents

3. Try the following actions:
   - Click "Create Example Collection"
   - Click "Refresh Collections"
   - Select a collection
   - Upload a test file
   - View results in console

**Option C: Create a Simple Test Component**

Create `src/app/test-auth/page.tsx`:

```tsx
"use client";

import { useDocumentApi } from "@/hooks/useDocumentApi";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";

export default function TestAuthPage() {
  const { createCollection, listCollections, isAuthenticated } = useDocumentApi();

  const testAuth = async () => {
    try {
      // Create a collection
      const collection = await createCollection("Test Collection", "Testing auth");
      console.log("Created:", collection);
      toast.success(`Collection created: ${collection.name}`);

      // List collections
      const list = await listCollections();
      console.log("Collections:", list);
      toast.success(`Found ${list.collections.length} collections`);
    } catch (error) {
      console.error("Error:", error);
      toast.error(error instanceof Error ? error.message : "Test failed");
    }
  };

  if (!isAuthenticated) {
    return <div className="p-8">Please sign in to test authentication</div>;
  }

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-4">Authentication Test</h1>
      <Button onClick={testAuth}>Test Document API Auth</Button>
      <p className="mt-4 text-sm text-muted-foreground">
        Check browser console for detailed output
      </p>
    </div>
  );
}
```

---

### Step 7: Test User Isolation

Verify that users can only see their own data:

1. **Sign in as User A:**
   - Create a collection named "User A Collection"
   - Note the collection ID from response

2. **Sign out and sign in as User B:**
   - Try to list collections
   - You should NOT see "User A Collection"
   - Try to create your own collection

3. **Attempt to access User A's collection as User B:**
   ```bash
   # Get User B's token
   export TOKEN_B="user-b-jwt-token"

   # Try to access User A's collection ID
   curl -X GET http://localhost:8000/collections/user-a-collection-id \
     -H "Authorization: Bearer $TOKEN_B"
   ```

   Expected: 404 Not Found (collection doesn't exist for this user)

---

## Common Issues and Solutions

### Issue 1: "Authentication failed" Error

**Symptoms:**
```json
{
  "detail": "Authentication failed"
}
```

**Solutions:**
1. Verify Supabase credentials are correct in both frontend and backend
2. Check that you're signed in on the frontend
3. Ensure token hasn't expired (tokens expire after ~1 hour)
4. Try signing out and back in to get a fresh token

**Check Supabase connection:**
```bash
# In document-api directory
python -c "from config import settings; print(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY[:20])"
```

### Issue 2: "Not authenticated" Error

**Symptoms:**
```json
{
  "detail": "Not authenticated"
}
```

**Solutions:**
1. Ensure you're including the Authorization header
2. Check that the header format is exactly: `Authorization: Bearer <token>`
3. Verify no extra spaces or quotes around the token

**Test your token format:**
```bash
# Should be in format: Bearer eyJhbGciOiJIUzI1NiIs...
echo "Authorization: Bearer $TOKEN"
```

### Issue 3: CORS Errors

**Symptoms:**
```
Access to fetch at 'http://localhost:8000/collections' from origin 'http://localhost:3000' has been blocked by CORS policy
```

**Solutions:**
1. CORS is enabled by default in the Document API
2. If still seeing errors, check `main.py` lines 46-58
3. For production, update `allow_origins` list with your frontend domain

### Issue 4: Token Expired

**Symptoms:**
```json
{
  "detail": "Invalid token or user not found"
}
```

**Solutions:**
1. JWT tokens expire after ~1 hour (default Supabase setting)
2. Sign out and sign back in to get a new token
3. The frontend automatically refreshes tokens via Supabase SDK
4. For curl testing, get a fresh token from the browser

### Issue 5: Environment Variables Not Loading

**Symptoms:**
- "Supabase configuration missing" error
- API can't find SUPABASE_URL

**Solutions:**
1. Ensure `.env` file exists in `document-api/` directory
2. Restart the Python server after changing `.env`
3. Verify variable names match exactly (case-sensitive)
4. Check for typos in variable names

**Debug environment variables:**
```python
# In Python shell from document-api directory
from config import settings
print("URL:", settings.SUPABASE_URL)
print("Key:", settings.SUPABASE_ANON_KEY[:20], "...")
```

---

## Verification Checklist

Use this checklist to confirm everything is working:

- [ ] Frontend starts without errors at http://localhost:3000
- [ ] Document API starts without errors at http://localhost:8000
- [ ] Can sign in/sign up via frontend UI
- [ ] User profile appears in sidebar after sign-in
- [ ] Can extract JWT token from browser
- [ ] Health check endpoint works (`curl http://localhost:8000/health`)
- [ ] Create collection with token succeeds (201 Created)
- [ ] List collections with token succeeds (200 OK)
- [ ] Create collection without token fails (401 Unauthorized)
- [ ] Can upload documents to a collection
- [ ] Two different users see different collections (user isolation)
- [ ] Browser console shows no authentication errors
- [ ] `useDocumentApi()` hook works in React components

---

## Next Steps

Once authentication is working:

1. **Build Your UI:**
   - Use the example component as a starting point
   - Integrate document management into your application
   - Add file upload UI components

2. **Deploy to Production:**
   - Follow `document-api/DEPLOYMENT.md` for Google Cloud deployment
   - Update environment variables in production
   - Configure CORS for your production domain

3. **Add Features:**
   - Document search and filtering
   - Collection management UI
   - Document preview
   - Batch operations

4. **Monitor & Optimize:**
   - Check deletion queue stats
   - Monitor API logs
   - Optimize database queries
   - Set up alerts for auth failures

---

## Support

If you encounter issues not covered here:

1. Check `document-api/AUTHENTICATION.md` for detailed API docs
2. Review frontend auth docs: `docs/AUTHENTICATION.md`
3. Check FastAPI auto-docs: http://localhost:8000/docs
4. Review Supabase logs: https://supabase.com/dashboard/project/_/logs
5. Check browser console for JavaScript errors
6. Review Python logs for backend errors

---

## Quick Reference

**Get JWT Token (Browser Console):**
```javascript
copy(JSON.parse(localStorage.getItem('supabase.auth.token'))?.currentSession?.access_token)
```

**Test with curl:**
```bash
export TOKEN="your-token-here"
curl -X GET http://localhost:8000/collections -H "Authorization: Bearer $TOKEN"
```

**Use in React:**
```tsx
import { useDocumentApi } from "@/hooks/useDocumentApi";

function MyComponent() {
  const { createCollection } = useDocumentApi();

  const handleCreate = async () => {
    const collection = await createCollection("My Collection");
    console.log(collection);
  };

  return <button onClick={handleCreate}>Create</button>;
}
```

---

**Happy Testing! 🚀**
