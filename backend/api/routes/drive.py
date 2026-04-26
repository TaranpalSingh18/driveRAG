"""Google Drive API routes."""
import requests
from fastapi import APIRouter, Request

try:
    from ...core.auth import get_access_token, get_user_identity
    from ...core.pdf_processor import extract_pdf_text, chunk_text
    from ...rag.vector_store import vector_store
except ImportError:
    from core.auth import get_access_token, get_user_identity
    from core.pdf_processor import extract_pdf_text, chunk_text
    from rag.vector_store import vector_store

router = APIRouter(prefix="/drive", tags=["drive"])

GOOGLE_DOC_MIME = "application/vnd.google-apps.document"


@router.get("/files")
def get_files(request: Request):
    """List files from user's Google Drive."""
    token = get_access_token(request)
    headers = {"Authorization": f"Bearer {token}"}
    
    files_res = requests.get(
        "https://www.googleapis.com/drive/v3/files",
        headers=headers
    )
    
    return files_res.json()


@router.get("/download")
def download_file(request: Request, file_id: str):
    """Download a file from Google Drive."""
    token = get_access_token(request)
    headers = {"Authorization": f"Bearer {token}"}
    
    url = f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media"
    res = requests.get(url, headers=headers)
    
    return {
        "content": res.content.decode(errors="ignore")
    }


@router.post("/index")
def index_drive_files(request: Request):
    """Fetch files from Google Drive and index them into vector store."""
    try:
        token = get_access_token(request)
        user_id = get_user_identity(request)
        headers = {"Authorization": f"Bearer {token}"}
        
        # Fetch files metadata
        files_res = requests.get(
            "https://www.googleapis.com/drive/v3/files",
            headers=headers,
            params={"pageSize": 100, "fields": "files(id, name, mimeType)"}
        )
        files = files_res.json().get("files", [])
        
        documents = []
        metadata = []
        indexed_files = 0
        skipped_files = 0
        
        for file in files:
            file_id = file["id"]
            file_name = file["name"]
            mime_type = file.get("mimeType", "")
            
            # Only support PDF and Google Docs.
            if "pdf" in mime_type or file_name.endswith(".pdf"):
                try:
                    url = f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media"
                    res = requests.get(url, headers=headers)
                    text = extract_pdf_text(res.content)
                    chunks = chunk_text(text, size=500)
                    documents.extend(chunks)
                    metadata.extend([{"file": file_name, "type": "pdf"} for _ in chunks])
                    indexed_files += 1
                except Exception as e:
                    print(f"Error processing {file_name}: {e}")
                    skipped_files += 1
            
            elif mime_type == GOOGLE_DOC_MIME:
                try:
                    url = f"https://www.googleapis.com/drive/v3/files/{file_id}/export"
                    res = requests.get(url, headers=headers, params={"mimeType": "text/plain"})
                    text = res.text
                    chunks = chunk_text(text, size=500)
                    documents.extend(chunks)
                    metadata.extend([{"file": file_name, "type": "doc"} for _ in chunks])
                    indexed_files += 1
                except Exception as e:
                    print(f"Error processing {file_name}: {e}")
                    skipped_files += 1
            else:
                skipped_files += 1
        
        # Add to vector store
        result = vector_store.add_documents(user_id, documents, metadata)
        return {
            "status": "indexed",
            "user_id": user_id,
            "files_processed": len(files),
            "files_indexed": indexed_files,
            "files_skipped": skipped_files,
            "chunks_created": len(documents),
            "result": result
        }
    
    except Exception as e:
        return {"error": str(e)}


@router.post("/clear-index")
def clear_my_index(request: Request):
    """Clear only the authenticated user's vector index."""
    _ = get_access_token(request)
    user_id = get_user_identity(request)
    result = vector_store.clear_user_store(user_id)
    return result


@router.post("/clear-all-indexes")
def clear_all_indexes(request: Request):
    """Clear all users' vector indexes. Use for local/dev reset only."""
    _ = get_access_token(request)
    return vector_store.clear_all_stores()
