"""Question answering pipeline module."""
from typing import List, Dict, Any

from .llm_client import get_llm
from .utils import render_context


def answer_question_from_chunks(question: str, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate an answer to a question using retrieved chunks.
    
    Args:
        question: User's question
        chunks: Retrieved context chunks from search
        
    Returns:
        Dict with question, answer, and chunks
    """
    context = render_context(chunks)
    model = get_llm()
    
    if model is None:
        return {
            "question": question,
            "answer": "LLM unavailable. Returning context chunks only.",
            "chunks": chunks,
        }
    
    prompt = (
        "You are a precise RAG assistant. Answer the question strictly from the context. "
        "If the context does not contain the answer, explicitly say that. "
        "If the question asks about resume experience, extract roles, companies, and durations as bullet points.\n\n"
        f"QUESTION:\n{question}\n\n"
        f"CONTEXT:\n{context}\n\n"
        "Provide a concise factual answer."
    )
    
    try:
        response = model.invoke(prompt)
        answer_text = response.content if hasattr(response, "content") else str(response)
    except Exception as e:
        answer_text = f"Failed to generate answer: {e}"
    
    return {
        "question": question,
        "answer": answer_text.strip(),
        "chunks": chunks,
    }


def synthesize_final_answer(original_query: str, question_answers: List[Dict[str, Any]]) -> str:
    """
    Synthesize a final answer from multiple question-answer pairs.
    
    Args:
        original_query: Original user query
        question_answers: List of QA dicts from answer_question_from_chunks
        
    Returns:
        Synthesized final answer
    """
    model = get_llm()
    
    if model is None:
        joined = "\n\n".join(
            [f"Q: {item['question']}\nA: {item['answer']}" for item in question_answers]
        )
        return f"Combined answer (fallback):\n\n{joined}"
    
    qa_text = "\n\n".join(
        [f"Question: {item['question']}\nAnswer: {item['answer']}" for item in question_answers]
    )
    
    prompt = (
        "You are creating one final response from multiple answered sub-questions. "
        "Keep it clear and complete, avoid repetition, and include all key details.\n\n"
        f"ORIGINAL USER QUERY:\n{original_query}\n\n"
        f"SUB-QUESTION ANSWERS:\n{qa_text}"
    )
    
    try:
        response = model.invoke(prompt)
        return (response.content if hasattr(response, "content") else str(response)).strip()
    except Exception as e:
        return f"Failed to synthesize answer: {e}"
