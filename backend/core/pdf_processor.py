"""PDF and text file processing module."""
from typing import List

try:
    import pymupdf as fitz
except ImportError:
    import fitz  # type: ignore


def extract_pdf_text(file_bytes: bytes) -> str:
    """
    Extract text from PDF bytes.
    
    Args:
        file_bytes: Raw PDF file content
        
    Returns:
        Extracted text from all pages
    """
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text


def chunk_text(text: str, size: int = 500) -> List[str]:
    """
    Split text into fixed-size chunks.
    
    Args:
        text: Text to chunk
        size: Chunk size in characters
        
    Returns:
        List of text chunks
    """
    return [text[i:i+size] for i in range(0, len(text), size)]
