# Installation Guide

## Quick Start

### Prerequisites

- **Python 3.10+**
- **Node.js 16+** (for frontend)
- **pip** or **conda** (Python package manager)
- **npm** (Node package manager)

### Step-by-Step Installation

#### 1. Clone/Navigate to Project

```bash
cd high_watch
```

#### 2. Set Up Backend

##### Create Virtual Environment

```bash
# Windows
python -m venv backend\.venv
backend\.venv\Scripts\activate

# macOS/Linux
python -m venv backend/.venv
source backend/.venv/bin/activate
```

##### Install Dependencies

```bash
cd backend
pip install -r requirements.txt
cd ..
```

##### Configure Environment

```bash
# Copy template
cp .env.example .env

# Edit with your credentials
# Required: CLIENT_ID, CLIENT_SECRET, GROQ_API_KEY
```

#### 3. Set Up Frontend

```bash
cd frontend
npm install
cd ..
```

#### 4. Run Development Servers

##### Terminal 1: Backend

```bash
cd backend
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend available at: `http://localhost:8000`

##### Terminal 2: Frontend

```bash
cd frontend
npm run dev
```

Frontend available at: `http://localhost:5173`

---

## Google OAuth Setup

### 1. Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create new project (name: "High Watch")
3. Enable **Google Drive API** and **Google+ API**

### 2. Create OAuth Credentials

1. Go to **Credentials** → **Create Credentials** → **OAuth Client ID**
2. Select **Web Application**
3. Add authorized redirect URIs:
   - `http://localhost:8000/callback` (development)
   - `https://yourdomain.com/callback` (production)
4. Copy **Client ID** and **Client Secret**

### 3. Add to .env

```env
CLIENT_ID=your_client_id
CLIENT_SECRET=your_client_secret
SESSION_SECRET=generate-random-string
```

Generate SESSION_SECRET:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## Groq API Setup (Optional)

### 1. Get API Key

1. Go to [Groq Console](https://console.groq.com/)
2. Sign up / Log in
3. Create API key
4. Copy the key

### 2. Add to .env

```env
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.1-8b-instant
```

**Note:** The system works without Groq - it will return context chunks without LLM-generated answers.

---

## Optional Dependencies

### Install FAISS (Recommended)

```bash
# CPU version
pip install faiss-cpu

# GPU version (CUDA)
pip install faiss-gpu
```

Without FAISS, the system uses simple text similarity instead of vector search.

### Install Additional Tools

```bash
# For better performance
pip install numpy

# For improved search
pip install rank-bm25

# For better embeddings
pip install nomic-ai
```

---

## Docker Setup (Optional)

### Build Docker Image

```bash
docker build -t high-watch-backend ./backend
docker build -t high-watch-frontend ./frontend
```

### Run with Docker Compose

```bash
docker-compose up
```

Services:
- Backend: http://localhost:8000
- Frontend: http://localhost:5173
- PostgreSQL: localhost:5432 (if using db backend)

---

## Production Deployment

### Environment Variables for Production

```env
# Disable debug mode
DEBUG=false

# Use production database
DATABASE_URL=postgresql://user:password@host:5432/dbname

# Secure session
SESSION_SECRET=<strong-random-string>
HTTPS_ONLY=true

# Frontend
FRONTEND_URL=https://yourdomain.com

# CORS
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# OAuth
REDIRECT_URI=https://yourdomain.com/api/auth/callback
```

### Run with Gunicorn (Production)

```bash
pip install gunicorn

gunicorn \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  backend.app.main:app
```

### Nginx Configuration (Optional)

```nginx
upstream backend {
    server localhost:8000;
}

server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    # Frontend
    location / {
        proxy_pass http://localhost:5173;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Backend API
    location /api/ {
        proxy_pass http://backend/;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## Troubleshooting

### Module Import Errors

**Error:** `ModuleNotFoundError: No module named 'backend'`

**Solution:**
```bash
# From backend directory
python -m uvicorn app.main:app --reload
```

### CORS Issues

**Error:** `Access to XMLHttpRequest has been blocked by CORS policy`

**Solution:**
- Check `CORS_ORIGINS` in `.env`
- Ensure frontend URL matches exactly
- Restart backend server

### "Vector DB is empty"

**Error:** `Vector DB is empty. Please index files first.`

**Solution:**
1. Login with Google account
2. Navigate to Drive files
3. Click "Index Files"
4. Wait for indexing to complete
5. Try search again

### FAISS Not Available

**Error:** `FAISS not available - using fallback vector search`

**Solution:**
```bash
pip install faiss-cpu
# or
pip install faiss-gpu
```

### Groq Not Available

**Error:** `langchain-groq not available`

**Solution:**
```bash
pip install langchain-groq
```

Or ensure `GROQ_API_KEY` is set in `.env`.

### Port Already in Use

**Error:** `Address already in use`

**Solution:**
```bash
# Find process using port 8000
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Kill process
kill -9 <PID>  # macOS/Linux
taskkill /PID <PID> /F  # Windows

# Or use different port
uvicorn app.main:app --port 8001
```

---

## Verify Installation

### Backend Health Check

```bash
curl http://localhost:8000/health
# Should return: {"status":"healthy","service":"high-watch-backend"}
```

### Frontend Access

Open browser: `http://localhost:5173`

Should see login page.

### API Documentation

Open: `http://localhost:8000/docs`

Should see Swagger UI with all endpoints.

---

## Next Steps

1. **Login** with Google account
2. **Index** Google Drive files
3. **Search** your documents
4. **Ask** questions about your files

For detailed API documentation, see [API.md](API.md)

For architecture details, see [ARCHITECTURE.md](ARCHITECTURE.md)
