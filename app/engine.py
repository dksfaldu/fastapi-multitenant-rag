import os
import faiss
import logging
from typing import Dict
from llama_index.core import (
    VectorStoreIndex, 
    StorageContext, 
    load_index_from_storage, 
    Document
)
from llama_index.vector_stores.faiss import FaissVectorStore
from llama_index.core.memory import ChatMemoryBuffer

logger = logging.getLogger(__name__)

STORAGE_ROOT = "./Data"

# In-memory session tracking scoped per project definition
chat_memory_store: Dict[str, ChatMemoryBuffer] = {}

def get_chat_memory(project_id: str) -> ChatMemoryBuffer:
    """Provide a dedicated conversation memory buffer for each tenant."""
    if project_id not in chat_memory_store:
        chat_memory_store[project_id] = ChatMemoryBuffer.from_defaults(token_limit=4000)
    return chat_memory_store[project_id]

def get_project_index(project_id: str) -> VectorStoreIndex:
    """Load or initialize an isolated FAISS vector index per project_id."""
    persist_dir = os.path.join(STORAGE_ROOT, project_id)
    
    if os.path.exists(persist_dir) and os.path.exists(os.path.join(persist_dir, "default__vector_store.json")):
        logger.info(f"Loading existing index for project {project_id}")
        vector_store = FaissVectorStore.from_persist_dir(persist_dir)
        storage_context = StorageContext.from_defaults(
            vector_store=vector_store, persist_dir=persist_dir
        )
        return load_index_from_storage(storage_context=storage_context)
    else:
        logger.info(f"Creating new FAISS index for project {project_id}")
        os.makedirs(persist_dir, exist_ok=True)
        # text-embedding-3-small generates vectors of size 1536
        d = 1536
        faiss_index = faiss.IndexFlatL2(d)
        vector_store = FaissVectorStore(faiss_index=faiss_index)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        
        index = VectorStoreIndex.from_documents([], storage_context=storage_context)
        index.storage_context.persist(persist_dir=persist_dir)
        return index

def save_project_index(index: VectorStoreIndex, project_id: str):
    """Persist the project index modifications to disk."""
    persist_dir = os.path.join(STORAGE_ROOT, project_id)
    index.storage_context.persist(persist_dir=persist_dir)

def add_document_to_project(project_id: str, document_id: str, text_content: str):
    index = get_project_index(project_id)
    # The ref_doc_id is assigned inherently to permit discrete deletion mapping over vectors.
    doc = Document(text=text_content, id_=document_id, metadata={"document_id": document_id})
    index.insert(doc)
    save_project_index(index, project_id)

def delete_document_from_project(project_id: str, document_id: str) -> bool:
    index = get_project_index(project_id)
    try:
        # Removes mapping nodes corresponding to the respective tracking reference
        index.delete_ref_doc(document_id, delete_from_docstore=True)
        save_project_index(index, project_id)
        return True
    except Exception as e:
        logger.error(f"Error deleting doc {document_id} from project {project_id}: {e}")
        return False
