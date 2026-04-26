"""Search and RAG API routes."""
from fastapi import APIRouter, Request

try:
    from ...core.auth import get_access_token, get_user_identity
    from ...rag.vector_store import vector_store
    from ...rag.hybrid_search import hybrid_search
    from ...rag.query_processing import split_query_to_questions, infer_preferred_files
    from ...rag.qa_pipeline import answer_question_from_chunks, synthesize_final_answer
except ImportError:
    from core.auth import get_access_token, get_user_identity
    from rag.vector_store import vector_store
    from rag.hybrid_search import hybrid_search
    from rag.query_processing import split_query_to_questions, infer_preferred_files
    from rag.qa_pipeline import answer_question_from_chunks, synthesize_final_answer

router = APIRouter(prefix="/rag", tags=["rag"])


@router.post("/search")
def search_files(request: Request, query: str, k: int = 5):
    """Search indexed files with hybrid BM25 + semantic search."""
    try:
        _ = get_access_token(request)
        user_id = get_user_identity(request)
        ctx = vector_store.get_user_context(user_id)
        
        if not ctx["all_texts"]:
            return {"error": "Vector DB is empty. Please index files first."}
        
        results = hybrid_search(
            query,
            ctx["all_texts"],
            ctx["metadata_store"],
            ctx["vector_store"],
            ctx["bm25_index"],
            k=k
        )
        
        return {
            "query": query,
            "results": results,
            "count": len(results)
        }
    
    except Exception as e:
        return {"error": str(e)}


@router.post("/ask")
def ask_files(request: Request, query: str, k: int = 5):
    """Full RAG pipeline: split query -> retrieve -> answer -> synthesize."""
    try:
        _ = get_access_token(request)
        user_id = get_user_identity(request)
        ctx = vector_store.get_user_context(user_id)
        
        if not ctx["all_texts"]:
            return {"error": "Vector DB is empty. Please index files first."}
        
        # Split query into sub-questions
        questions = split_query_to_questions(query)
        question_answers = []
        
        # Answer each question
        for q in questions:
            preferred_files = infer_preferred_files(q, ctx["metadata_store"])
            chunks = hybrid_search(
                q,
                ctx["all_texts"],
                ctx["metadata_store"],
                ctx["vector_store"],
                ctx["bm25_index"],
                k=k,
                preferred_files=preferred_files
            )
            qa = answer_question_from_chunks(q, chunks)
            question_answers.append(qa)
        
        # Synthesize final answer
        final_answer = synthesize_final_answer(query, question_answers)
        
        return {
            "query": query,
            "questions": questions,
            "question_answers": question_answers,
            "final_answer": final_answer,
        }
    
    except Exception as e:
        return {"error": str(e)}


@router.get("/stats")
def get_db_stats(request: Request):
    """Get vector database statistics."""
    _ = get_access_token(request)
    user_id = get_user_identity(request)
    return vector_store.get_stats(user_id)
