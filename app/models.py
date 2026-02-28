from pydantic import BaseModel

class ChatRequest(BaseModel):
    project_id: str
    message: str

class DeleteRequest(BaseModel):
    project_id: str
    document_id: str
