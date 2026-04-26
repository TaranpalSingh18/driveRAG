"""Main FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

try:
    # Package mode: python -m uvicorn backend.main:app
    from .app.config import SESSION_SECRET, CORS_ORIGINS
    from .rag.vector_store import vector_store
    from .api.routes import auth, drive, search, health
except ImportError:
    # Module mode: cd backend && uvicorn main:app
    from app.config import SESSION_SECRET, CORS_ORIGINS
    from rag.vector_store import vector_store
    from api.routes import auth, drive, search, health


# Initialize FastAPI app
app = FastAPI(
    title="High Watch",
    description="RAG-powered document search with Google Drive integration",
    version="1.0.0"
)

# Add middleware
app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
    same_site="lax",
    https_only=False,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include route handlers
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(auth.legacy_router)
app.include_router(drive.router)
app.include_router(search.router)


# Startup event
@app.on_event("startup")
def startup_event():
    """Initialize vector store on app startup."""
    vector_store.initialize()
    print("Vector store initialized")


# Root endpoint
@app.get("/")
def read_root():
    """Root endpoint with API information."""
    return {
        "name": "High Watch API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
