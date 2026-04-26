# API Documentation

## Overview

High Watch provides a RESTful API with the following endpoint groups:

- **Authentication** (`/auth`) - OAuth login/logout
- **Google Drive** (`/drive`) - File management
- **RAG Search** (`/rag`) - Semantic search and Q&A
- **Health** - Service status

All endpoints (except `/auth/login`, `/auth/callback`, `/health`, `/`) require authentication.

---

## Base URL

```
http://localhost:8000
```

Production documentation available at: `/docs` (Swagger UI)

---

## Authentication Endpoints

### 1. Initiate Login

```http
GET /auth/login
```

Redirects user to Google OAuth consent screen.

**Response:** HTTP 307 Redirect to Google OAuth URL

**Example:**
```bash
curl -i http://localhost:8000/auth/login
# Redirects to https://accounts.google.com/o/oauth2/v2/auth?...
```

---

### 2. OAuth Callback (Google Redirect)

```http
GET /auth/callback?code=AUTH_CODE&state=STATE
```

Handles OAuth callback from Google. Exchanges authorization code for access token.

**Parameters:**
- `code` (string, required) - Authorization code from Google
- `state` (string, required) - State parameter for CSRF protection

**Response:** HTTP 307 Redirect to frontend with `?auth=success`

**Status Codes:**
- 307 - Success, redirected to frontend
- 400 - Invalid state or token exchange failed

---

### 3. Check Auth Status

```http
GET /auth/status
```

Check if user is currently authenticated.

**Response:**
```json
{
  "authenticated": true
}
```

**Status Codes:**
- 200 - OK

---

### 4. Logout

```http
POST /auth/logout
```

Clear user session.

**Response:**
```json
{
  "status": "logged_out"
}
```

**Status Codes:**
- 200 - OK

---

## Google Drive Endpoints

### 1. List Files

```http
GET /drive/files
```

List all files from user's Google Drive.

**Headers:**
```
Authorization: Bearer {access_token}  (in session)
```

**Response:**
```json
{
  "files": [
    {
      "id": "file_id_123",
      "name": "resume.pdf",
      "mimeType": "application/pdf"
    }
  ]
}
```

**Status Codes:**
- 200 - Success
- 401 - Not authenticated

---

### 2. Download File

```http
GET /drive/download?file_id=FILE_ID
```

Download a file from Google Drive by ID.

**Parameters:**
- `file_id` (string, required) - Google Drive file ID

**Response:**
```json
{
  "content": "raw file content as string"
}
```

**Status Codes:**
- 200 - Success
- 401 - Not authenticated
- 404 - File not found

---

### 3. Index Drive Files

```http
POST /drive/index
```

Fetch all files from Google Drive, extract text, and add to vector store.

Supports: PDF and Google Docs.

**Headers:**
```
Content-Type: application/json
```

**Response:**
```json
{
  "status": "indexed",
  "files_processed": 5,
  "files_indexed": 3,
  "files_skipped": 2,
  "chunks_created": 150,
  "result": {
    "status": "added",
    "count": 150
  }
}
```

**Status Codes:**
- 200 - Success
- 400 - Error during indexing
- 401 - Not authenticated

**Example:**
```bash
curl -X POST http://localhost:8000/drive/index \
  -H "Cookie: session=..." \
  -H "Content-Type: application/json"
```

---

## RAG Search Endpoints

### 1. Hybrid Search

```http
POST /rag/search?query=QUERY&k=5
```

Search indexed documents using hybrid BM25 + FAISS search.

**Parameters:**
- `query` (string, required) - Search query
- `k` (integer, optional) - Number of results (default: 5)

**Response:**
```json
{
  "query": "What is digital twin?",
  "results": [
    {
      "text": "Digital twin is a virtual representation...",
      "score": 0.92,
      "source": {
        "file": "technical_spec.pdf",
        "type": "pdf"
      }
    }
  ],
  "count": 1
}
```

**Status Codes:**
- 200 - Success
- 400 - Vector DB empty
- 401 - Not authenticated

**Example:**
```bash
curl -X POST "http://localhost:8000/rag/search?query=digital%20twin&k=5" \
  -H "Cookie: session=..."
```

---

### 2. Question Answering (RAG Pipeline)

```http
POST /rag/ask?query=QUERY&k=5
```

Full RAG pipeline:
1. Splits query into sub-questions
2. Searches for context
3. Generates answers
4. Synthesizes final response

**Parameters:**
- `query` (string, required) - User question
- `k` (integer, optional) - Search results per question (default: 5)

**Response:**
```json
{
  "query": "What roles have I held and what projects did I lead?",
  "questions": [
    "What roles have you held?",
    "What projects did you lead?"
  ],
  "question_answers": [
    {
      "question": "What roles have you held?",
      "answer": "Based on your resume, you have held the following roles...",
      "chunks": [
        {
          "text": "Senior Engineer at Company X...",
          "score": 0.95,
          "source": { "file": "resume.pdf" }
        }
      ]
    },
    {
      "question": "What projects did you lead?",
      "answer": "You led the following projects...",
      "chunks": [
        {
          "text": "Led development of real-time monitoring system...",
          "score": 0.88,
          "source": { "file": "resume.pdf" }
        }
      ]
    }
  ],
  "final_answer": "You have held multiple senior roles including Senior Engineer at Company X. Among your significant projects, you led the development of a real-time monitoring system..."
}
```

**Status Codes:**
- 200 - Success
- 400 - Vector DB empty
- 401 - Not authenticated

**Example:**
```bash
curl -X POST "http://localhost:8000/rag/ask?query=What%20is%20your%20experience&k=3" \
  -H "Cookie: session=..."
```

---

### 3. Database Statistics

```http
GET /rag/stats
```

Get vector database statistics.

**Response:**
```json
{
  "total_documents": 150,
  "faiss_available": true,
  "nomic_available": true,
  "bm25_available": true,
  "numpy_available": true,
  "faiss_index_size": 150,
  "dimension": 768,
  "status": "ready"
}
```

**Status Codes:**
- 200 - Success
- 401 - Not authenticated

---

## Health Endpoints

### 1. Health Check

```http
GET /health
```

Simple health check for monitoring/load balancing.

**Response:**
```json
{
  "status": "healthy",
  "service": "high-watch-backend"
}
```

**Status Codes:**
- 200 - Healthy
- 503 - Service unavailable

---

### 2. API Information

```http
GET /
```

Get API information and links.

**Response:**
```json
{
  "name": "High Watch API",
  "version": "1.0.0",
  "docs": "/docs",
  "health": "/health"
}
```

---

## Error Handling

### Error Response Format

All errors follow this format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Common Status Codes

| Code | Meaning | Solution |
|------|---------|----------|
| 200 | Success | Operation completed |
| 400 | Bad Request | Invalid parameters or empty vector DB |
| 401 | Unauthorized | User not authenticated, call `/auth/login` |
| 404 | Not Found | Resource not found |
| 500 | Server Error | Server-side error, check logs |

---

## Authentication Flow

```
1. Browser → GET /auth/login
   ↓
2. Backend → Redirect to Google OAuth
   ↓
3. User → Authenticates with Google
   ↓
4. Google → Redirect to /auth/callback?code=...
   ↓
5. Backend → Exchange code for token, store in session
   ↓
6. Backend → Redirect to frontend with ?auth=success
   ↓
7. Frontend → Subsequent requests include session cookie
```

---

## Usage Examples

### Complete Workflow

```bash
# 1. Login
curl -i http://localhost:8000/auth/login
# → Redirects to Google, user authenticates

# 2. Check authentication
curl http://localhost:8000/auth/status \
  -H "Cookie: session=<session_cookie>"

# 3. Index Drive files
curl -X POST http://localhost:8000/drive/index \
  -H "Cookie: session=<session_cookie>"

# 4. Search
curl -X POST "http://localhost:8000/rag/search?query=my%20projects" \
  -H "Cookie: session=<session_cookie>"

# 5. Ask question (full RAG)
curl -X POST "http://localhost:8000/rag/ask?query=what%20is%20my%20experience" \
  -H "Cookie: session=<session_cookie>"

# 6. Check stats
curl http://localhost:8000/rag/stats \
  -H "Cookie: session=<session_cookie>"

# 7. Logout
curl -X POST http://localhost:8000/auth/logout \
  -H "Cookie: session=<session_cookie>"
```

### Python Client Example

```python
import requests
from requests.cookies import RequestsCookieJar

# Create session
session = requests.Session()
jar = RequestsCookieJar()

BASE_URL = "http://localhost:8000"

# 1. Initialize login (in real app, redirect user to /auth/login)
# 2. After OAuth callback, session cookie is set

# 3. Search
response = session.post(
    f"{BASE_URL}/rag/ask",
    params={
        "query": "What is my experience?",
        "k": 5
    }
)
print(response.json())

# 4. Logout
response = session.post(f"{BASE_URL}/auth/logout")
print(response.json())
```

---

## Rate Limiting

Currently not implemented, but recommended for production:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/rag/ask")
@limiter.limit("10/minute")
def ask_files(request: Request, query: str):
    ...
```

---

## Caching Headers

For production, add caching headers:

```python
# Don't cache authenticated endpoints
cache_control_header = "no-cache, no-store, must-revalidate"

# Cache public data
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        # Include Cache-Control header
    }
```

---

## CORS Configuration

Currently allows localhost:5173 (development frontend).

For production, update `CORS_ORIGINS` in `.env`:

```env
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

---

## OpenAPI/Swagger

Full API documentation available at:

```
http://localhost:8000/docs
```

Interactive API testing available at:

```
http://localhost:8000/redoc
```
