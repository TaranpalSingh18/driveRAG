"""LLM client module for Groq integration."""
from typing import Optional

try:
    from langchain_groq import ChatGroq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    print("langchain-groq not available")

try:
    from ..app.config import GROQ_API_KEY, GROQ_MODEL
except ImportError:
    from app.config import GROQ_API_KEY, GROQ_MODEL


class LLMClient:
    """Singleton LLM client for Groq."""
    
    _instance = None
    _llm = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def get_llm(self) -> Optional[object]:
        """Get or initialize LLM client."""
        if self._llm is not None:
            return self._llm
        
        if not GROQ_AVAILABLE:
            return None
        
        if not GROQ_API_KEY:
            return None
        
        self._llm = ChatGroq(model=GROQ_MODEL, temperature=0)
        return self._llm


_client = LLMClient()


def get_llm() -> Optional[object]:
    """Get LLM client instance."""
    return _client.get_llm()
