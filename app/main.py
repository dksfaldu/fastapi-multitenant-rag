from fastapi import FastAPI, UploadFile, Form, HTTPException, File
from app.models import ChatRequest, DeleteRequest
from app.config import setup_settings
from app.engine import (
    add_document_to_project,
    delete_document_from_project,
    get_project_index,
    get_chat_memory
)
from app.logger import log_project_action
from app.admin import admin_router
from app.database import init_db
from app.ui import ui_router

from llama_index.core import QueryBundle
import logging
import os
import tempfile
import aiofiles
import shutil

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="TenaxRAG API", description="Production-ready FastAPI for multi-tenant LlamaIndex RAG")
app.include_router(admin_router)
app.include_router(ui_router)

@app.on_event("startup")
def startup_event():
    logger.info("Initializing application settings and AI models.")
    setup_settings()
    logger.info("Initializing SQLite Core...")
    init_db()

@app.post("/upload")
async def upload_document(
    project_id: str = Form(...),
    document_id: str = Form(...),
    file: UploadFile = File(...)
):
    """
    Accepts project_id, document_id, and a file.
    It provisions the file into a temporary block, processes data using LlamaIndex constructs targeting chunking, and persists it into the tenant's exact FAISS store structure.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
        
    if file.content_type != "application/pdf" and not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
    
    temp_dir = tempfile.mkdtemp()
    temp_path = os.path.join(temp_dir, file.filename)
    
    try:
        async with aiofiles.open(temp_path, 'wb') as out_file:
            content = await file.read()
            await out_file.write(content)
            
        from llama_index.core import SimpleDirectoryReader
        # Parses the incoming data streams into standardized objects mapped by SimpleDirectoryReader algorithms
        docs = SimpleDirectoryReader(input_dir=temp_dir).load_data()
        if not docs:
            raise ValueError("No valid text could be extracted from the provided document.")
            
        # Group fragments logically so references stay fully coherent during future deletions
        text_content = "\n\n".join([str(d.text) for d in docs])
        
        add_document_to_project(project_id, document_id, text_content)
        log_project_action(project_id, "UPLOAD", f"Processed document {document_id}: {file.filename}")
        
    except Exception as e:
        logger.error(f"Upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process document: {str(e)}")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
        
    return {"message": "Document uploaded and indexed successfully", "document_id": document_id, "project_id": project_id}

@app.delete("/document")
async def delete_document(req: DeleteRequest):
    """
    Purges vectors and text segments correlated to a particular Document ID efficiently from the FAISS framework scope.
    """
    try:
        success = delete_document_from_project(req.project_id, req.document_id)
        if success:
            log_project_action(req.project_id, "DELETE", f"Purged document {req.document_id}")
            return {"message": f"Document {req.document_id} was successfully deleted from project {req.project_id}"}
        else:
            raise HTTPException(status_code=404, detail="Document could not be found or removed.")
    except Exception as e:
        logger.error(f"Delete failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process deletion: {str(e)}")

@app.post("/chat")
async def chat(req: ChatRequest):
    """
    Implements a responsive context-based chat system integrating dynamically allocated conversation history specific strictly to the querying project_id.
    """
    try:
        index = get_project_index(req.project_id)
        memory = get_chat_memory(req.project_id)
        
        # Deploy explicit QueryBundle definition signaling advanced object extraction representation
        query_bundle = QueryBundle(query_str=req.message)
        
        chat_engine = index.as_chat_engine(
            chat_mode="condense_plus_context",
            memory=memory,
            context_prompt=(
                "You are an intelligent organizational assistant.\n"
                "Rely strictly on the provided context to address the user's query.\n"
                "Context:\n{context_str}\n"
                "Instruction: Provide an accurate and comprehensive response."
            ),
            verbose=True,
            similarity_top_k=3
        )
        
        response = chat_engine.chat(query_bundle.query_str)
        
        sources = []
        if response.source_nodes:
            for node in response.source_nodes:
                sources.append({
                    "score": float(node.score) if node.score is not None else 0.0,
                    "text": node.node.text[:200] + "..." if node.node.text else "",
                    "document_id": node.node.metadata.get("document_id", "unknown")
                })
                
        log_project_action(req.project_id, "CHAT", f"Query: '{req.message}' -> Response length: {len(response.response)}")
                
        return {
            "response": response.response,
            "sources": sources
        }
    except Exception as e:
        logger.error(f"Chat execution failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process chat: {str(e)}")
