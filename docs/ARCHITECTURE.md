# Architecture Guide

## High-Level Design

```
┌─────────────────────────────────────────────────────────────┐
│                   Frontend (React + Vite)                    │
│         - User authentication                               │
│         - Search interface                                  │
│         - Results display                                   │
└──────────────────────────┬──────────────────────────────────┘
                           │ REST API
                           │ (FastAPI)
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
    ┌────────┐      ┌────────────┐      ┌──────────┐
    │  Auth  │      │   RAG      │      │  Drive   │
    │ Routes │      │  Routes    │      │  Routes  │
    └────────┘      └────────────┘      └──────────┘
        │                  │                   │
        └──────────────────┼───────────────────┘
                           ▼
        ┌──────────────────────────────────────┐
        │      Core Service Layer              │
        ├──────────────────────────────────────┤
        │  • Auth (OAuth token exchange)      │
        │  • Embeddings (Nomic/Fallback)      │
        │  • PDF Processing                   │
        │  • LLM Client (Groq)                │
        └──────────────────────────────────────┘
                           │
                           ▼
        ┌──────────────────────────────────────┐
        │    RAG Pipeline (Query → Answer)     │
        ├──────────────────────────────────────┤
        │  1. Split queries into sub-questions │
        │  2. Infer document preferences       │
        │  3. Perform hybrid search            │
        │  4. Generate answers per question    │
        │  5. Synthesize final response        │
        └──────────────────────────────────────┘
                           │
                           ▼
        ┌──────────────────────────────────────┐
        │   Vector Store & Search Engine       │
        ├──────────────────────────────────────┤
        │  • FAISS Index (Semantic)            │
        │  • BM25 Index (Lexical)              │
        │  • Metadata Store (JSON)             │
        │  • Embeddings Cache                  │
        └──────────────────────────────────────┘
```

## Module Dependencies

```
main.py
  ├─ app.config          (settings)
  ├─ app.middleware      (CORS, Sessions)
  │
  ├─ api.routes.auth     (OAuth, login, logout)
  │   └─ core.auth
  │
  ├─ api.routes.drive    (Google Drive ops)
  │   ├─ core.auth
  │   ├─ core.pdf_processor
  │   └─ rag.vector_store
  │
  ├─ api.routes.search   (Search & RAG)
  │   ├─ core.auth
  │   ├─ rag.vector_store
  │   ├─ rag.hybrid_search
  │   ├─ rag.query_processing
  │   └─ rag.qa_pipeline
  │
  └─ rag.vector_store    (FAISS mgmt)
      ├─ core.embeddings
      ├─ rag.hybrid_search
      └─ rag.utils
```

## Request Flow Examples

### User Login Flow
```
1. GET /auth/login
   ↓ [main.py]
   ├─ generate_auth_redirect_url() [core.auth]
   ├─ store state in session
   └─ return redirect to Google

2. User authenticates with Google
   ↓
   
3. GET /auth/callback?code=...&state=...
   ↓ [main.py]
   ├─ validate state
   ├─ exchange_code_for_token() [core.auth]
   ├─ store access_token in session
   └─ redirect to frontend
```

### Document Indexing Flow
```
1. POST /drive/index
   ↓ [api.routes.drive]
   ├─ get_access_token() [core.auth]
   ├─ fetch files from Google Drive API
   │
   ├─ For each PDF:
   │  ├─ extract_pdf_text() [core.pdf_processor]
   │  ├─ chunk_text() [core.pdf_processor]
   │  └─ add to documents list
   │
   ├─ For each TXT/MD:
   │  ├─ download file
   │  ├─ chunk_text() [core.pdf_processor]
   │  └─ add to documents list
   │
   └─ vector_store.add_documents(docs, metadata)
       ├─ get_embeddings(docs) [core.embeddings]
       │  ├─ Use Nomic if available
       │  └─ Fallback to MD5 hash
       │
       ├─ Create FAISS index
       ├─ Create BM25 index
       ├─ Save to disk
       └─ return status
```

### Question Answering Flow
```
1. POST /rag/ask?query="What is my experience?"
   ↓ [api.routes.search]
   ├─ get_access_token() [core.auth]
   │
   ├─ split_query_to_questions(query) [rag.query_processing]
   │  └─ Use LLM or regex to split
   │
   ├─ For each sub-question:
   │  │
   │  ├─ infer_preferred_files(q) [rag.query_processing]
   │  │  └─ Match keywords to files
   │  │
   │  ├─ hybrid_search(q, preferred_files) [rag.hybrid_search]
   │  │  ├─ BM25 search [bm25]
   │  │  ├─ FAISS search [faiss]
   │  │  └─ Combine & rank results
   │  │
   │  ├─ answer_question_from_chunks() [rag.qa_pipeline]
   │  │  ├─ render_context(chunks) [rag.utils]
   │  │  ├─ Call Groq LLM
   │  │  └─ return answer
   │  │
   │  └─ append (question, answer, chunks)
   │
   ├─ synthesize_final_answer(query, answers) [rag.qa_pipeline]
   │  ├─ Combine all answers
   │  ├─ Call Groq for synthesis
   │  └─ return final answer
   │
   └─ return full response
```

## Data Models

### Metadata Store (JSON)
```json
{
  "Resume section on experience...": {
    "file": "resume.pdf",
    "type": "pdf"
  },
  "Digital twin tire monitoring system...": {
    "file": "technical_spec.txt",
    "type": "text"
  }
}
```

### Search Result
```python
{
  "text": "actual chunk content",
  "score": 0.85,
  "source": {
    "file": "resume.pdf",
    "type": "pdf"
  }
}
```

### Q&A Response
```python
{
  "question": "What roles have you held?",
  "answer": "You held the following roles...",
  "chunks": [
    # source chunks used for answer
  ]
}
```

## Configuration Cascade

Priority (highest first):
1. Environment variables from `.env`
2. Default values in `app/config.py`
3. Module-level fallbacks
4. Hardcoded defaults in code

## Error Handling Strategy

### Graceful Degradation
- **No Nomic** → Use MD5 hash embeddings
- **No FAISS** → Use text similarity
- **No Groq** → Return context chunks only
- **No BM25** → Use string matching

### User-Facing Errors
- Invalid OAuth state → 400 Bad Request
- Not authenticated → 401 Unauthorized
- Empty vector DB → 400 + helpful message
- LLM failure → Include context anyway

## Testing Strategy

Unit tests should focus on:
- `core.embeddings` - Embedding generation with fallbacks
- `core.pdf_processor` - Text extraction
- `rag.query_processing` - Query splitting logic
- `rag.hybrid_search` - Search ranking
- `rag.qa_pipeline` - Answer formatting

Integration tests should cover:
- Full RAG pipeline (query → answer)
- Document indexing
- OAuth flow
- API endpoints

## Performance Considerations

### Caching
- Embeddings cache (in-memory)
- BM25 index (rebuilt on document add)
- Session tokens (server-side)

### Search Optimization
- FAISS uses IndexFlatL2 (not approximate, but fast enough)
- Can upgrade to IndexIVFFlat for larger datasets
- BM25 pre-filters candidates
- FAISS searches 3x candidates when filtering

### Scaling
- Consider sharding FAISS index for >1M documents
- Use PostgreSQL + pgvector for production
- Add Redis caching layer
- Implement async document processing

## Security Considerations

1. **OAuth**
   - Validate state parameter
   - Never log tokens
   - Use HTTPS in production

2. **File Access**
   - User can only access their own Google Drive
   - Access token stored securely in session

3. **LLM Inputs**
   - Sanitize user queries
   - Limit token usage
   - Rate limiting (implement via middleware)

4. **Environment**
   - Use strong SESSION_SECRET
   - Rotate secrets regularly
   - Use HTTPS in production
   - Set https_only=True for cookies
