"""Query processing module for splitting and preference inference."""
import re
from typing import List, Optional

from .llm_client import get_llm


def split_query_to_questions(user_query: str) -> List[str]:
    """
    Split a possibly multi-question query into normalized questions.
    
    Uses LLM if available, falls back to regex splitting.
    
    Args:
        user_query: User's input query
        
    Returns:
        List of individual questions
    """
    model = get_llm()
    if model is not None:
        prompt = (
            "Extract all user questions from the input. "
            "Return ONLY a JSON array of strings. "
            "If there is just one question, return an array with one item.\n\n"
            f"INPUT:\n{user_query}"
        )
        try:
            response = model.invoke(prompt)
            from .utils import safe_json_list
            parsed = safe_json_list(response.content if hasattr(response, "content") else str(response))
            cleaned = [q.strip() for q in parsed if isinstance(q, str) and q.strip()]
            if cleaned:
                return cleaned
        except Exception as e:
            print(f"LLM question split failed, using fallback: {e}")
    
    # Fallback splitting
    parts = re.split(r"\?|\n| and |,", user_query)
    cleaned = [p.strip() for p in parts if p and p.strip()]
    if not cleaned:
        return [user_query.strip()]
    return cleaned


def infer_preferred_files(question: str, available_files: dict) -> Optional[List[str]]:
    """
    Infer likely source files from question using keyword matching.
    
    Args:
        question: User's question
        available_files: Dict of available files from metadata
        
    Returns:
        List of preferred files or None if no strong preference
    """
    q = question.lower()
    
    # Build distinct filenames
    filenames = set()
    for meta in available_files.values():
        if isinstance(meta, dict):
            file_name = meta.get("file")
            if file_name:
                filenames.add(file_name)
    
    print(f"infer_preferred_files() - Question: '{question}'")
    print(f"   Available files: {filenames}")
    
    preferred = []
    
    # Resume-related keywords
    if any(token in q for token in ["resume", "cv", "experience", "taran", "education", "skills", "background"]):
        resume_files = [f for f in filenames if "resume" in f.lower() or "taran" in f.lower()]
        if resume_files:
            preferred.extend(resume_files)
            print(f"   Resume keywords detected. Restricting to: {resume_files}")
    
    # Digital Twin / Tire related keywords
    if any(token in q for token in ["digital", "twin", "tire", "tyre", "sensor", "cad", "performance", "iot"]):
        twin_files = [f for f in filenames if any(kw in f.lower() for kw in ["digital", "twin", "tire", "tyre"])]
        if twin_files:
            preferred.extend(twin_files)
            print(f"   Digital Twin keywords detected. Restricting to: {twin_files}")
    
    # Return unique preferred files or None
    if preferred:
        seen = set()
        unique_preferred = []
        for f in preferred:
            if f not in seen:
                seen.add(f)
                unique_preferred.append(f)
        print(f"   Final preferred files: {unique_preferred}")
        return unique_preferred
    else:
        print(f"   No strong keywords detected. Searching all files.")
        return None
