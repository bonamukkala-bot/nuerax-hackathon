import os
import uuid
from typing import List, Dict, Any, Tuple
import pandas as pd
from langchain_text_splitters import RecursiveCharacterTextSplitter
from tools.file_reader_tool import read_file, register_file

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


def save_uploaded_file(file_bytes: bytes, original_filename: str) -> Tuple[str, str]:
    file_id = str(uuid.uuid4())[:8]
    ext = os.path.splitext(original_filename)[1].lower()
    safe_name = f"{file_id}{ext}"
    file_path = os.path.join(UPLOAD_DIR, safe_name)
    with open(file_path, "wb") as f:
        f.write(file_bytes)
    register_file(file_id, file_path, original_filename)
    return file_id, file_path


def load_and_chunk(
    file_path: str,
    original_filename: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 100
) -> List[Dict[str, Any]]:
    raw_text = read_file(file_path, original_filename)
    if not raw_text or raw_text.startswith("Error"):
        return []

    ext = os.path.splitext(original_filename)[1].lower()

    if ext in [".csv", ".xlsx", ".xls"]:
        return [{
            "content": raw_text,
            "metadata": {
                "source": original_filename,
                "type": "structured_data",
                "chunk_index": 0
            }
        }]

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    chunks = splitter.split_text(raw_text)
    return [
        {
            "content": chunk,
            "metadata": {
                "source": original_filename,
                "type": "text",
                "chunk_index": i,
                "total_chunks": len(chunks)
            }
        }
        for i, chunk in enumerate(chunks) if chunk.strip()
    ]


def process_uploaded_file(
    file_bytes: bytes,
    original_filename: str
) -> Dict[str, Any]:
    try:
        # Step 1: Save file
        file_id, file_path = save_uploaded_file(file_bytes, original_filename)

        # Step 2: Load and chunk
        chunks = load_and_chunk(file_path, original_filename)

        if not chunks:
            return {
                "success": False,
                "file_id": file_id,
                "filename": original_filename,
                "error": "Could not extract content from file",
                "chunks": 0
            }

        # Step 3: Store in long-term memory
        # Only embed small files to avoid slow uploads
        try:
            if len(chunks) <= 20:
                from memory.long_term import get_long_term_memory
                ltm = get_long_term_memory()
                texts = [c["content"] for c in chunks]
                metadatas = [c["metadata"] for c in chunks]
                ltm.add_documents(texts, metadatas)
        except Exception:
            pass  # Don't fail upload if embedding fails

        ext = os.path.splitext(original_filename)[1].lower()
        preview = chunks[0]["content"][:300] if chunks else ""

        return {
            "success": True,
            "file_id": file_id,
            "filename": original_filename,
            "file_path": file_path,
            "extension": ext,
            "chunks": len(chunks),
            "preview": preview,
            "message": f"Successfully processed '{original_filename}'"
        }

    except Exception as e:
        return {
            "success": False,
            "filename": original_filename,
            "error": str(e),
            "chunks": 0
        }


def get_upload_dir() -> str:
    return UPLOAD_DIR