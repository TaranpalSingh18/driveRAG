# High Watch

High Watch is a FastAPI and React app for indexing Google Drive files and answering questions over the indexed content with retrieval-augmented generation.

## What it does

- Connects to Google Drive with OAuth
- Extracts text from PDFs and Google Docs only
- Builds hybrid search with BM25 and FAISS when available
- Uses Groq for answer generation when configured
- Falls back to simpler search and response modes when optional dependencies are missing

## Project layout

- `backend/` contains the FastAPI app, authentication, retrieval pipeline, and vector store code
- `frontend/` contains the React UI
- `docs/` contains setup and API notes

## Backend structure

- `backend/app/config.py` holds environment and runtime settings
- `backend/core/` contains auth, embedding, and PDF helpers
- `backend/rag/` contains search, retrieval, and answer generation logic
- `backend/api/routes/` contains the HTTP route handlers

## Setup

1. Create a `.env` file from `.env.example` and fill in your Google and Groq values.
2. Install backend dependencies with `pip install -r requirements.txt`.
3. Start the backend from the `backend/` folder with `python -m uvicorn app.main:app --reload`.
4. Install frontend dependencies in `frontend/` with `npm install` and run `npm run dev`.

## API

The service exposes endpoints for:

- authentication
- listing and downloading Drive files
- indexing files into the vector store
- hybrid search
- question answering
- health checks

See `docs/API.md` for request and response details.

## Why the structure changed

The code was split into smaller modules to make it easier to read, test, and change. Configuration was centralized, retrieval logic was separated from route handlers, and the search pipeline was broken into focused pieces so individual parts can be improved without changing the whole app.

## Notes

- The system works without every optional dependency installed.
- Vector data is stored under `backend/data/`.
- Generated index files can be rebuilt by running the indexing flow again.
