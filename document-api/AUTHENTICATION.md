# Document API Authentication

This document describes the authentication system for the Document Upload API. The API uses **Supabase JWT authentication** to secure all endpoints and ensure user-scoped access control.

## Table of Contents

- [Overview](#overview)
- [Setup](#setup)
- [How It Works](#how-it-works)
- [Making Authenticated Requests](#making-authenticated-requests)
- [Protected Endpoints](#protected-endpoints)
- [Error Handling](#error-handling)
- [Integration with Frontend](#integration-with-frontend)
- [Testing Authentication](#testing-authentication)
- [Troubleshooting](#troubleshooting)

---

## Overview

The Document API implements **JWT-based authentication** using Supabase. All collection and document management endpoints require a valid Bearer token in the Authorization header.

### Key Features

- ✅ **JWT Token Verification**: Validates tokens via Supabase
- ✅ **User-Scoped Access**: All data is scoped by authenticated user ID
- ✅ **Automatic Ownership Verification**: Users can only access their own collections and documents
- ✅ **Session Management**: Leverages Supabase's built-in session handling
- ✅ **Google Cloud Compatible**: Designed for deployment on Google Cloud Run

### Authentication Flow

```
1. User authenticates via frontend (Agent Chat UI)
   ↓
2. Frontend receives JWT token from Supabase
   ↓
3. Frontend includes token in API requests (Authorization: Bearer <token>)
   ↓
4. Document API validates token with Supabase
   ↓
5. API extracts user_id from validated token
   ↓
6. API scopes all operations to that user_id
```

---

## Setup

### 1. Configure Environment Variables

Add the following to your `.env` file (or set in your deployment environment):

```bash
# Supabase Authentication
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-supabase-anon-key-here
```

**Where to find these values:**

- Go to your Supabase project dashboard
- Navigate to **Settings > API**
- Copy the **Project URL** (SUPABASE_URL)
- Copy the **anon public** key (SUPABASE_ANON_KEY)

### 2. Install Dependencies

The authentication module requires the `supabase` Python package:

```bash
pip install -r requirements.txt
```

The requirements.txt already includes:

```
supabase>=2.8.0
```

### 3. Verify Configuration

Start the API and check that authentication is working:

```bash
python main.py
```

The API should start on port 8000. If Supabase credentials are missing, you'll see an error message.

---

## How It Works

### Authentication Module (`auth.py`)

The authentication system consists of three main components:

#### 1. `AuthenticatedUser` Class

Represents an authenticated user with the following properties:

```python
class AuthenticatedUser:
    user_id: str        # Supabase user ID (UUID)
    email: str          # User's email address
    display_name: str   # Display name (defaults to email if not set)
```

#### 2. `get_current_user()` Function

Validates a JWT token by calling Supabase's `auth.get_user()` method:

```python
def get_current_user(authorization: str) -> dict:
    """Validate JWT token and return Supabase User object"""
    supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
    response = supabase.auth.get_user(authorization)
    return response.user
```

#### 3. `resolve_user()` Dependency

FastAPI dependency that automatically authenticates requests:

```python
def resolve_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]
) -> AuthenticatedUser:
    """Extract and validate Bearer token, return authenticated user"""
    user = get_current_user(credentials.credentials)
    return AuthenticatedUser(
        user_id=user.id,
        email=user.email,
        display_name=user_metadata.get("name") or user.email
    )
```

### Protected Endpoints

All collection and document endpoints use the `resolve_user` dependency:

```python
@app.post("/collections")
async def create_collection(
    user: Annotated[AuthenticatedUser, Depends(resolve_user)],  # ← Authentication
    name: str = Form(...),
    description: Optional[str] = Form(None),
):
    # user.user_id is automatically available and verified
    collection_id = await db.create_collection(user.user_id, name, description)
    ...
```

### User-Scoped Data Access

The database layer automatically scopes all queries by user_id:

- **Collections**: `CREATE`, `READ`, `UPDATE`, `DELETE` all filtered by user_id
- **Documents**: All operations verify collection ownership via user_id
- **No cross-user access**: Users cannot see or modify other users' data

---

## Making Authenticated Requests

### Request Format

All protected endpoints require a Bearer token in the Authorization header:

```
Authorization: Bearer <jwt-token>
```

### Example: Create Collection

```bash
curl -X POST http://localhost:8000/collections \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -F "name=My Documents" \
  -F "description=Personal document collection"
```

### Example: Upload Document

```bash
curl -X POST http://localhost:8000/upload \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -F "collection_id=550e8400-e29b-41d4-a716-446655440000" \
  -F "files=@document.pdf"
```

### Example: List Collections

```bash
curl -X GET http://localhost:8000/collections \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### Example: Delete Document

```bash
curl -X DELETE http://localhost:8000/documents/123e4567-e89b-12d3-a456-426614174000 \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

---

## Protected Endpoints

The following endpoints require authentication:

### Collection Management

- `POST /collections` - Create a new collection
- `GET /collections` - List all collections for authenticated user
- `GET /collections/{collection_id}` - Get collection details
- `GET /collections/{collection_id}/documents` - List documents in collection
- `DELETE /collections/{collection_id}` - Delete collection and all its documents

### Document Management

- `POST /upload` - Upload documents to a collection
- `GET /documents` - List all documents for authenticated user
- `DELETE /documents/{doc_id}` - Delete a specific document

### Public Endpoints (No Authentication Required)

- `GET /` - API information
- `GET /health` - Health check
- `GET /debug/vertex-ai-documents` - Debug: List Vertex AI documents
- `GET /debug/verify-document/{vertex_ai_doc_id}` - Debug: Verify document exists
- `GET /deletion-queue/stats` - View deletion queue statistics
- `GET /operation/{operation_name}` - Check import operation status

---

## Error Handling

### 401 Unauthorized

Returned when authentication fails:

```json
{
  "detail": "Authentication failed"
}
```

**Common causes:**

- Missing Authorization header
- Invalid or expired JWT token
- Malformed Bearer token
- Supabase credentials misconfigured

### 403 Forbidden

Returned when user tries to access resources they don't own:

```json
{
  "detail": "You do not have permission to delete this document"
}
```

### 404 Not Found

Returned when resource doesn't exist or user doesn't have access:

```json
{
  "detail": "Collection 550e8400-e29b-41d4-a716-446655440000 not found or you don't have access"
}
```

### 500 Internal Server Error

Returned when Supabase configuration is missing:

```json
{
  "detail": "Supabase configuration missing. Please set SUPABASE_URL and SUPABASE_ANON_KEY."
}
```

---

## Integration with Frontend

The Document API is designed to work seamlessly with the Agent Chat UI frontend authentication.

### Frontend Flow

1. **User Signs In**: Frontend authenticates user via Supabase
2. **Get JWT Token**: Frontend retrieves session token from Supabase
3. **Make API Calls**: Frontend includes token in all Document API requests
4. **Token Refresh**: Frontend handles token refresh automatically (via Supabase SDK)

### Example Frontend Code (React/TypeScript)

```typescript
import { useAuthContext } from "@/providers/Auth";

function DocumentUpload() {
  const { session } = useAuthContext();

  const uploadDocument = async (file: File, collectionId: string) => {
    const formData = new FormData();
    formData.append("collection_id", collectionId);
    formData.append("files", file);

    const response = await fetch("http://localhost:8000/upload", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${session?.access_token}`, // ← JWT token
      },
      body: formData,
    });

    return response.json();
  };

  // ... rest of component
}
```

### Getting the JWT Token from Frontend

The JWT access token is available from the Supabase session:

```typescript
// Using the Auth context
const { session } = useAuthContext();
const token = session?.access_token;

// Or directly from Supabase client
import { getSupabaseClient } from "@/lib/auth/supabase-client";
const supabase = getSupabaseClient();
const {
  data: { session },
} = await supabase.auth.getSession();
const token = session?.access_token;
```

---

## Testing Authentication

### 1. Using the Frontend

The easiest way to test authentication is through the Agent Chat UI:

1. Start the frontend: `cd ../` then `pnpm dev`
2. Sign in via the UI
3. Use browser DevTools > Network tab to see API requests with Authorization headers

### 2. Using Postman or Insomnia

1. **Sign in via frontend** to get a valid JWT token
2. **Copy the token** from browser DevTools or localStorage
3. **Create a new request** in Postman/Insomnia
4. **Add Authorization header**: `Bearer <your-token>`
5. **Make requests** to any protected endpoint

### 3. Using curl with Real Token

```bash
# 1. Get token from frontend (browser console)
localStorage.getItem('supabase.auth.token')

# 2. Use token in curl
export TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

curl -X GET http://localhost:8000/collections \
  -H "Authorization: Bearer $TOKEN"
```

### 4. Testing Ownership Verification

Try to access another user's resources:

```bash
# Create collection as User A
curl -X POST http://localhost:8000/collections \
  -H "Authorization: Bearer $USER_A_TOKEN" \
  -F "name=User A Collection"

# Try to access as User B (should fail with 404)
curl -X GET http://localhost:8000/collections/{collection_id} \
  -H "Authorization: Bearer $USER_B_TOKEN"
```

---

## Troubleshooting

### Problem: "Authentication failed" Error

**Solution:**

1. Verify SUPABASE_URL and SUPABASE_ANON_KEY are set correctly
2. Check that the token is not expired (tokens typically expire after 1 hour)
3. Ensure token is being sent in Authorization header as `Bearer <token>`
4. Verify your Supabase project is active and accessible

### Problem: "Invalid authentication scheme" Error

**Solution:**

- Ensure the Authorization header uses the format: `Bearer <token>`
- Check for extra spaces or formatting issues
- Don't include quotes around the token

### Problem: CORS Errors from Frontend

**Solution:**
The API has CORS enabled for all origins by default. For production:

1. Edit `main.py` line 49:

```python
allow_origins=["https://your-frontend-domain.com"],
```

2. Ensure the frontend domain is in the allowed origins list

### Problem: "Supabase configuration missing" Error

**Solution:**

1. Ensure `.env` file exists in the `document-api` directory
2. Verify SUPABASE_URL and SUPABASE_ANON_KEY are set
3. Restart the API server after changing environment variables

### Problem: User Can See Other Users' Data

**Solution:**
This should never happen if authentication is working correctly. If it does:

1. Verify all database queries include user_id filtering
2. Check that `resolve_user` dependency is present on all protected endpoints
3. Review database.py to ensure user_id scoping is implemented

---

## Security Best Practices

### For Development

- ✅ Use `.env` file for local development
- ✅ Never commit `.env` files to version control
- ✅ Use test Supabase projects for development

### For Production

- ✅ Set environment variables via cloud provider (e.g., Google Cloud Secret Manager)
- ✅ Use HTTPS for all API requests
- ✅ Restrict CORS to specific frontend domains
- ✅ Enable Supabase Row Level Security (RLS) policies
- ✅ Monitor authentication failures and suspicious activity
- ✅ Regularly rotate Supabase API keys
- ✅ Use short-lived JWT tokens (1 hour default is good)

### Token Security

- **Never log JWT tokens** in application logs
- **Don't expose tokens** in client-side code or URLs
- **Use HTTPS** to prevent token interception
- **Implement token refresh** to minimize exposure time
- **Validate tokens** on every request (already implemented)

---

## Architecture

### Authentication Layer

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (Next.js)                      │
│  - Supabase Auth Provider                                    │
│  - Session Management                                        │
│  - JWT Token Storage                                         │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP Request + Bearer Token
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                  Document API (FastAPI)                      │
│  ┌──────────────────────────────────────────────────┐       │
│  │  Middleware: HTTPBearer (auth.py)                │       │
│  │  - Extract Authorization header                   │       │
│  │  - Validate JWT with Supabase                    │       │
│  │  - Create AuthenticatedUser object               │       │
│  └──────────────────┬───────────────────────────────┘       │
│                     ↓                                        │
│  ┌──────────────────────────────────────────────────┐       │
│  │  Endpoint Handlers (main.py)                     │       │
│  │  - Receive AuthenticatedUser via dependency      │       │
│  │  - Access user.user_id automatically             │       │
│  └──────────────────┬───────────────────────────────┘       │
│                     ↓                                        │
│  ┌──────────────────────────────────────────────────┐       │
│  │  Database Layer (database.py)                    │       │
│  │  - All queries scoped by user_id                 │       │
│  │  - Ownership verification built-in               │       │
│  └──────────────────┬───────────────────────────────┘       │
└────────────────────┼────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────────┐
│              PostgreSQL Database                             │
│  - collections table (with user_id column)                   │
│  - documents table (with user_id column)                     │
│  - User-scoped indexes for performance                       │
└─────────────────────────────────────────────────────────────┘
```

### Database Schema (User Scoping)

```sql
-- Collections table
CREATE TABLE collections (
    id UUID PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,  -- ← Supabase user ID
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(user_id, name)  -- ← Each user can have unique collection names
);

-- Documents table
CREATE TABLE documents (
    id UUID PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,  -- ← Supabase user ID
    collection_id UUID NOT NULL REFERENCES collections(id) ON DELETE CASCADE,
    original_filename VARCHAR(500) NOT NULL,
    gcs_blob_name VARCHAR(500) NOT NULL,
    gcs_uri TEXT NOT NULL,
    vertex_ai_doc_id VARCHAR(500) NOT NULL UNIQUE,
    file_type VARCHAR(100) NOT NULL,
    file_size_bytes BIGINT NOT NULL,
    content_type VARCHAR(100) NOT NULL,
    upload_date TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Indexes for user-scoped queries
CREATE INDEX idx_collections_user_id ON collections(user_id);
CREATE INDEX idx_documents_user_id ON documents(user_id);
CREATE INDEX idx_documents_user_collection ON documents(user_id, collection_id);
```

---

## Related Documentation

- **Frontend Authentication**: See `/docs/AUTHENTICATION.md` for frontend setup
- **API Reference**: See FastAPI auto-generated docs at `http://localhost:8000/docs`
- **Supabase Docs**: https://supabase.com/docs/guides/auth
- **Database Schema**: See `database.py` for complete schema definition

---

## Support

For issues or questions:

1. Check the [Troubleshooting](#troubleshooting) section above
2. Review [Supabase Auth documentation](https://supabase.com/docs/guides/auth/server-side/nextjs)
3. Check FastAPI logs for detailed error messages
4. Verify environment variables are set correctly
5. Test with a fresh Supabase token from the frontend

---

## License

This authentication implementation follows the same license as the main project.
