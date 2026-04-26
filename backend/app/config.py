"""Application configuration and environment variables."""
import os
from dotenv import load_dotenv

load_dotenv()

# OAuth & API Configuration
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
SESSION_SECRET = os.getenv("SESSION_SECRET", "replace-this-in-production")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# URLs & Endpoints
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://127.0.0.1:5173")
DEFAULT_REDIRECT_URI = "http://localhost:8000/auth/callback"
REDIRECT_URI = os.getenv("REDIRECT_URI", DEFAULT_REDIRECT_URI)

# Google OAuth URLs
AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
SCOPE = "https://www.googleapis.com/auth/drive.readonly"

# LLM Configuration
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

# Vector DB Configuration
FAISS_INDEX_PATH = os.getenv("FAISS_INDEX_PATH", "data/faiss_index.bin")
METADATA_PATH = os.getenv("METADATA_PATH", "data/metadata.json")
VECTOR_DATA_ROOT = os.getenv("VECTOR_DATA_ROOT", "data/users")
EMBEDDING_DIMENSION = 768  # Nomic default embedding dimension

# Search Configuration
DEFAULT_SEARCH_K = 5
BM25_WEIGHT = 0.3
FAISS_WEIGHT = 0.7

# CORS Configuration
CORS_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173"
]

# Chunk Configuration
CHUNK_SIZE = 500
PDF_PAGE_SIZE = 2000
