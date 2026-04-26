"""Utility functions for RAG pipeline."""
import json
import re
from typing import List, Dict, Any


def safe_json_list(raw_text: str) -> List:
    """
    Safely extract and parse JSON array from text.
    
    Args:
        raw_text: Raw text potentially containing JSON
        
    Returns:
        Parsed list or empty list
    """
    try:
        return json.loads(raw_text)
    except Exception:
        pass
    
    match = re.search(r"\[[\s\S]*\]", raw_text)
    if not match:
        return []
    try:
        return json.loads(match.group(0))
    except Exception:
        return []


def render_context(chunks: List[Dict[str, Any]]) -> str:
    """
    Render search results as formatted context for LLM.
    
    Args:
        chunks: List of chunk dicts from search results
        
    Returns:
        Formatted context string
    """
    lines = []
    for idx, chunk in enumerate(chunks, start=1):
        source = chunk.get("source", {})
        source_name = source.get("file", "unknown")
        lines.append(
            f"[Chunk {idx}] score={chunk.get('score', 0):.4f} source={source_name}\n{chunk.get('text', '')}"
        )
    return "\n\n".join(lines)
