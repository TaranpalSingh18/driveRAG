"""Hybrid BM25 + FAISS semantic search module."""
from typing import List, Dict, Any, Optional

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

try:
    from rank_bm25 import BM25Okapi
    BM25_AVAILABLE = True
except ImportError:
    BM25_AVAILABLE = False

try:
    from ..app.config import BM25_WEIGHT, FAISS_WEIGHT
    from ..core.embeddings import get_embeddings
except ImportError:
    from app.config import BM25_WEIGHT, FAISS_WEIGHT
    from core.embeddings import get_embeddings


def hybrid_search(
    query: str,
    all_texts: List[str],
    metadata_store: Dict,
    vector_store: Optional[object],
    bm25_index: Optional[object],
    k: int = 5,
    preferred_files: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Hybrid search combining BM25 (lexical) and FAISS (semantic).
    
    Implements intelligent filtering based on preferred files and graceful
    fallbacks when dependencies are unavailable.
    
    Args:
        query: Search query string
        all_texts: All indexed text chunks
        metadata_store: Metadata for each chunk
        vector_store: FAISS index (optional)
        bm25_index: BM25 index (optional)
        k: Number of results to return
        preferred_files: List of preferred source files to restrict search
        
    Returns:
        List of search results with text, score, and source metadata
    """
    if not all_texts:
        return []
    
    # Apply file filter if specified
    if preferred_files:
        print(f"HARD FILTER: Restricting search to files: {preferred_files}")
        filtered_texts = []
        filtered_indices = {}
        
        for idx, text in enumerate(all_texts):
            source_meta = metadata_store.get(text, {})
            source_file = source_meta.get("file") if isinstance(source_meta, dict) else None
            if source_file in preferred_files:
                filtered_indices[len(filtered_texts)] = idx
                filtered_texts.append(text)
        
        print(f"   Filtered: {len(filtered_texts)} out of {len(all_texts)} total chunks")
        
        if not filtered_texts:
            print(f"   No chunks found for preferred files {preferred_files}")
            return []
    else:
        filtered_texts = all_texts
        filtered_indices = {i: i for i in range(len(all_texts))}
    
    results = []
    
    # BM25 Search (Lexical Matching)
    bm25_results = _bm25_search(
        query, all_texts, bm25_index, filtered_indices, k, preferred_files
    )
    
    # FAISS Search (Semantic Matching)
    faiss_results = _faiss_search(
        query, all_texts, vector_store, filtered_indices, k, preferred_files
    )
    
    # Combine results
    seen = set()
    for text, score in bm25_results + faiss_results:
        if text not in seen:
            source_meta = metadata_store.get(text, {})
            results.append({
                "text": text,
                "score": float(score),
                "source": source_meta
            })
            seen.add(text)
    
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:k]


def _bm25_search(
    query: str,
    all_texts: List[str],
    bm25_index: Optional[object],
    filtered_indices: Dict[int, int],
    k: int,
    preferred_files: Optional[List[str]]
) -> List[tuple]:
    """BM25 lexical search."""
    if not BM25_AVAILABLE or not bm25_index:
        return []
    
    query_tokens = query.lower().split()
    bm25_scores = bm25_index.get_scores(query_tokens)
    
    if preferred_files:
        # Filter to preferred files
        filtered_bm25_scores = [
            (filtered_indices[i], bm25_scores[filtered_indices[i]])
            for i in range(len(filtered_indices))
        ]
        sorted_pairs = sorted(filtered_bm25_scores, key=lambda x: x[1], reverse=True)[:k]
        bm25_top_indices = [orig_idx for orig_idx, score in sorted_pairs]
    else:
        if NUMPY_AVAILABLE:
            bm25_top_indices = np.argsort(bm25_scores)[::-1][:k]
        else:
            bm25_top_indices = sorted(
                range(len(bm25_scores)),
                key=lambda i: bm25_scores[i],
                reverse=True
            )[:k]
    
    max_bm25 = max(bm25_scores) if max(bm25_scores) > 0 else 1
    results = []
    for idx in bm25_top_indices:
        score = (bm25_scores[idx] / max_bm25) * BM25_WEIGHT
        results.append((all_texts[idx], score))
    
    return results


def _faiss_search(
    query: str,
    all_texts: List[str],
    vector_store: Optional[object],
    filtered_indices: Dict[int, int],
    k: int,
    preferred_files: Optional[List[str]]
) -> List[tuple]:
    """FAISS semantic search with fallback to text similarity."""
    
    # Vector search if FAISS available
    if FAISS_AVAILABLE and vector_store:
        try:
            query_embedding = get_embeddings([query])
            if NUMPY_AVAILABLE:
                query_embedding = np.array(query_embedding).astype("float32")
            
            search_k = k * 3 if preferred_files else k
            search_k = min(search_k, len(all_texts))
            
            distances, indices = vector_store.search(query_embedding, search_k)
            
            if preferred_files:
                filtered_pairs = []
                for pos, idx in enumerate(indices[0]):
                    if idx in filtered_indices.values():
                        dist = float(distances[0][pos])
                        filtered_pairs.append((all_texts[idx], dist))
                filtered_faiss = filtered_pairs[:k]
            else:
                filtered_faiss = [
                    (all_texts[int(idx)], float(distances[0][pos]))
                    for pos, idx in enumerate(indices[0][:k])
                ]
            
            if filtered_faiss:
                max_distance = max(d for _, d in filtered_faiss)
                if max_distance <= 0:
                    max_distance = 1
                return [
                    (text, (1 - dist / max_distance) * FAISS_WEIGHT)
                    for text, dist in filtered_faiss
                ]
        except Exception as e:
            print(f"Vector search failed: {e}")
    
    # Fallback: Simple text similarity
    query_lower = query.lower()
    scores = {}
    for text in all_texts:
        text_lower = text.lower()
        query_words = set(query_lower.split())
        text_words = set(text_lower.split())
        overlap = len(query_words & text_words)
        scores[text] = overlap
    
    top_texts = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:k]
    if top_texts:
        max_score = max(s for _, s in top_texts)
        if max_score <= 0:
            max_score = 1
        return [
            (text, (score / max_score) * FAISS_WEIGHT)
            for text, score in top_texts
        ]
    
    return []
