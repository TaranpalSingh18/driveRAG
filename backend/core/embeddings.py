"""Embedding generation module with graceful fallbacks."""
import hashlib
from typing import List, Union

import numpy as np

try:
    from ..app.config import EMBEDDING_DIMENSION
except ImportError:
    from app.config import EMBEDDING_DIMENSION

# Optional imports with fallbacks
try:
    from nomic import embed
    NOMIC_AVAILABLE = True
except ImportError:
    NOMIC_AVAILABLE = False
    print("Nomic not available - using fallback embeddings")

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    print("NumPy not available")


def get_simple_embedding(text: str) -> List[float]:
    """Create a deterministic embedding from text hash (fallback method)."""
    h = hashlib.md5(text.encode()).digest()
    return list(h[:EMBEDDING_DIMENSION]) + [0] * max(0, EMBEDDING_DIMENSION - len(h))


def get_embeddings(texts: List[str]) -> Union[np.ndarray, List[List[float]]]:
    """
    Generate embeddings for a list of texts.
    
    Uses Nomic if available, falls back to hash-based embeddings.
    
    Args:
        texts: List of text strings to embed
        
    Returns:
        Array of embeddings (numpy array or list)
    """
    if NOMIC_AVAILABLE:
        try:
            result = embed.text(
                texts=texts,
                model="nomic-embed-text-v1.5",
                inference_mode="local"
            )
            return np.array(result["embeddings"]).astype("float32")
        except Exception as e:
            print(f"Nomic failed, using fallback: {e}")
    
    if NUMPY_AVAILABLE:
        return np.array([get_simple_embedding(t) for t in texts]).astype("float32")
    else:
        return [get_simple_embedding(t) for t in texts]
