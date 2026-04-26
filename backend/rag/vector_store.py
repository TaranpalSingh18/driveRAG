"""Vector store initialization and management module."""
import json
import re
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    print("FAISS not available - using fallback vector search")

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    print("NumPy not available")

try:
    from rank_bm25 import BM25Okapi
    BM25_AVAILABLE = True
except ImportError:
    BM25_AVAILABLE = False
    print("BM25 not available")

try:
    from ..app.config import EMBEDDING_DIMENSION, VECTOR_DATA_ROOT
    from ..core.embeddings import get_embeddings
except ImportError:
    from app.config import EMBEDDING_DIMENSION, VECTOR_DATA_ROOT
    from core.embeddings import get_embeddings


class VectorStore:
    """Manages FAISS vector store and metadata."""
    
    def __init__(self):
        self.vector_store = None
        self.bm25_index = None
        self.metadata_store = {}
        self.all_texts = []
        self.embeddings_cache = {}
        self.current_user_id = None
        self.faiss_index_path = None
        self.metadata_path = None
        self.data_root = Path(VECTOR_DATA_ROOT)
        
    def initialize(self):
        """Initialize base data directory. User store loads lazily per request."""
        self.data_root.mkdir(parents=True, exist_ok=True)
        print(f"Vector data root ready at: {self.data_root}")

    def _sanitize_user_id(self, user_id: str) -> str:
        return re.sub(r"[^a-zA-Z0-9._-]", "_", str(user_id))

    def _set_active_user(self, user_id: str):
        safe_user = self._sanitize_user_id(user_id)
        if self.current_user_id == safe_user:
            return

        user_dir = self.data_root / safe_user
        user_dir.mkdir(parents=True, exist_ok=True)

        self.current_user_id = safe_user
        self.faiss_index_path = user_dir / "faiss_index.bin"
        self.metadata_path = user_dir / "metadata.json"

        if self.metadata_path.exists():
            self._load_from_disk()
        else:
            self._create_new()
    
    def _load_from_disk(self):
        """Load existing vector store from disk."""
        with open(self.metadata_path, "r") as f:
            self.metadata_store = json.load(f)
        self.all_texts = list(self.metadata_store.keys())
        
        if BM25_AVAILABLE:
            self.bm25_index = BM25Okapi([text.split() for text in self.all_texts])
        
        if FAISS_AVAILABLE and self.faiss_index_path.exists():
            try:
                self.vector_store = faiss.read_index(str(self.faiss_index_path))
                print("Loaded FAISS index")
            except Exception as e:
                print(f"Could not load FAISS index: {e}")
                self.vector_store = None
        
        print(f"Loaded {len(self.all_texts)} existing documents")
    
    def _create_new(self):
        """Create new empty vector store."""
        self.vector_store = None
        self.metadata_store = {}
        self.all_texts = []
        self.bm25_index = None
        self.embeddings_cache = {}
        print("Initialized new vector store")
    
    def add_documents(self, user_id: str, documents: List[str], doc_metadata: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        Add documents to vector store.
        
        Args:
            documents: List of text documents to add
            doc_metadata: List of metadata dicts for each document
            
        Returns:
            Status dict with operation results
        """
        self._set_active_user(user_id)

        if not documents:
            return {"status": "no documents"}
        
        # Generate embeddings
        embeddings = get_embeddings(documents)
        
        # Add to FAISS if available
        if FAISS_AVAILABLE:
            emb_dim = int(embeddings.shape[1]) if NUMPY_AVAILABLE else len(embeddings[0])
            if self.vector_store is None:
                self.vector_store = faiss.IndexFlatL2(emb_dim)
            elif self.vector_store.d != emb_dim:
                raise ValueError(
                    f"Embedding dimension mismatch: index={self.vector_store.d}, embeddings={emb_dim}. "
                    "Delete faiss_index.bin and metadata.json, then re-index."
                )
            
            if NUMPY_AVAILABLE:
                self.vector_store.add(np.array(embeddings).astype("float32"))
            else:
                self.vector_store.add(embeddings)
        
        # Store metadata and rebuild BM25
        for i, doc in enumerate(documents):
            self.all_texts.append(doc)
            self.metadata_store[doc] = doc_metadata[i] if doc_metadata else {"source": "unknown"}
            self.embeddings_cache[doc] = embeddings[i]
        
        if BM25_AVAILABLE:
            self.bm25_index = BM25Okapi([text.split() for text in self.all_texts])
        
        # Save to disk
        self._save_to_disk()
        
        return {"status": "added", "count": len(documents)}
    
    def _save_to_disk(self):
        """Save vector store and metadata to disk."""
        if self.metadata_path is None or self.faiss_index_path is None:
            raise ValueError("Active user store is not set.")

        self.metadata_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            if FAISS_AVAILABLE and self.vector_store:
                faiss.write_index(self.vector_store, str(self.faiss_index_path))
        except Exception as e:
            print(f"Could not save FAISS index: {e}")
        
        with open(self.metadata_path, "w") as f:
            json.dump(self.metadata_store, f)
    
    def get_user_context(self, user_id: str) -> Dict[str, Any]:
        self._set_active_user(user_id)
        return {
            "all_texts": self.all_texts,
            "metadata_store": self.metadata_store,
            "vector_store": self.vector_store,
            "bm25_index": self.bm25_index,
        }

    def get_stats(self, user_id: str) -> Dict[str, Any]:
        """Get vector store statistics."""
        self._set_active_user(user_id)
        return {
            "user_id": self.current_user_id,
            "total_documents": len(self.all_texts),
            "faiss_available": FAISS_AVAILABLE,
            "bm25_available": BM25_AVAILABLE,
            "numpy_available": NUMPY_AVAILABLE,
            "faiss_index_size": self.vector_store.ntotal if (FAISS_AVAILABLE and self.vector_store) else 0,
            "dimension": self.vector_store.d if (FAISS_AVAILABLE and self.vector_store) else EMBEDDING_DIMENSION,
            "status": "ready" if self.all_texts else "empty"
        }

    def clear_user_store(self, user_id: str) -> Dict[str, Any]:
        safe_user = self._sanitize_user_id(user_id)
        user_dir = self.data_root / safe_user

        if user_dir.exists():
            shutil.rmtree(user_dir)

        if self.current_user_id == safe_user:
            self.current_user_id = None
            self.faiss_index_path = None
            self.metadata_path = None
            self._create_new()

        return {"status": "cleared", "user_id": safe_user}

    def clear_all_stores(self) -> Dict[str, Any]:
        if self.data_root.exists():
            shutil.rmtree(self.data_root)
        self.data_root.mkdir(parents=True, exist_ok=True)

        self.current_user_id = None
        self.faiss_index_path = None
        self.metadata_path = None
        self._create_new()

        return {"status": "cleared_all"}


# Global instance
vector_store = VectorStore()
