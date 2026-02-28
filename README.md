# NexusRAG: Enterprise-Grade Multi-Tenant RAG Engine 🚀

**NexusRAG** is a production-ready, highly secure Retrieval-Augmented Generation (RAG) framework designed from the ground up for strict multi-tenancy. Built with **FastAPI**, **LlamaIndex**, **FAISS**, and **Azure OpenAI**, it provides absolute data partitioning between isolated project environments and features a stunning, built-in administrative dashboard for monitoring system activity and managing users.

---

## 🌟 Features

- **Strict Multi-Tenancy**: Every `project_id` gets entirely separate FAISS indices saved discretely on the file system, ensuring zero data leakage between tenants.
- **PDF Ingestion Engine**: A dedicated `/upload` endpoint securely accepts PDF files, automatically chunking and embedding the text using `pypdf` via LlamaIndex's native `SimpleDirectoryReader`.
- **Multi-LLM & Multi-Embedding Support**: Dynamically hot-swap active LLMs representing the backend (choices include **Azure OpenAI**, **Standard OpenAI**, and **Google Gemini**). Same modularity applies to Embeddings (`azure_openai`, `openai`, `gemini`).
- **Advanced Contextual Chat**: 
  - Employs a robust `condense_plus_context` chat engine.
  - Maintains isolated conversational memory buffers per project.
  - Returns answer source citations with relevancy scores natively.
- **Document Management**: Purges vectors and tracking components cleanly per document via the `/document` DELETE endpoint.
- **Admin Dashboard**: 
  - A modern, responsive UI served at `/admin`.
  - Protected via Basic Authentication.
  - Features real-time API logs specifically tracked per project, alongside instantaneous tenant and document metric aggregations.

---

## 🏗 Architecture

```text
multi_tenant_rag/
├── requirements.txt
├── .env.example
├── README.md
└── app/
    ├── __init__.py
    ├── config.py       # LlamaIndex Settings (Azure OpenAI + text-embedding-3-small)
    ├── model.py        # Pydantic Schemas
    ├── engine.py       # Core RAG engine managing isolated FAISS storage & memory
    ├── logger.py       # API activity timeline tracking and docstore stats parsing
    ├── admin.py        # Protected admin routing
    ├── admin_dashboard.html # Vanilla CSS styling for the monitoring UI
    └── main.py         # Main FastAPI routing application
```

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.9+
- An active [Azure OpenAI API Core Configuration](https://azure.microsoft.com/en-us/products/ai-services/openai-service) (for `gpt-4o`).
- A standard [OpenAI API Key](https://platform.openai.com/) (for embeddings via `text-embedding-3-small`).

### 2. Installation

Clone the repository and install dependencies:

```bash
git clone https://github.com/dksfaldu/fastapi-multitenant-rag.git
cd fastapi-multitenant-rag
pip install -r requirements.txt
```

### 3. Environment Configuration

Copy the example environment file and fill in your credentials:

```bash
cp .env.example .env
```

**`.env` Configuration Variables:**
```env
# Active Provider Choices
# LLM_PROVIDER options: 'azure_openai', 'openai', 'gemini'
LLM_PROVIDER="azure_openai"
# EMBEDDING_PROVIDER options: 'azure_openai', 'openai', 'gemini'
EMBEDDING_PROVIDER="openai"

# --- Azure OpenAI Configuration ---
AZURE_OPENAI_ENDPOINT="https://your-resource-name.openai.azure.com/"
AZURE_OPENAI_API_KEY="your-azure-api-key"
AZURE_OPENAI_API_VERSION="2024-02-15-preview"
AZURE_OPENAI_CHAT_DEPLOYMENT="gpt-4o"
AZURE_OPENAI_EMBEDDING_DEPLOYMENT="text-embedding-3-small"

# --- OpenAI Configuration ---
OPENAI_API_KEY="your-openai-api-key"
OPENAI_MODEL="gpt-4o"

# --- Google Gemini Configuration ---
GOOGLE_API_KEY="your-google-api-key"
GEMINI_MODEL="models/gemini-1.5-pro"
GEMINI_EMBEDDING_MODEL="models/text-embedding-004"

# --- Admin Dashboard ---
ADMIN_USERNAME="admin"
ADMIN_PASSWORD="secret"
```

### 4. Running the Application

Start the FastAPI application using Uvicorn:

```bash
uvicorn app.main:app --reload
```

---

## 🌐 API Interaction

Access the auto-generated interactive Swagger UI documentation at:
**`http://127.0.0.1:8000/docs`**

### Summary of REST Endpoints:
- `POST /upload`: Secure multi-part data aggregation targeting node-ids (`ref_doc_id`). Accepts `project_id`, `document_id`, and a `.pdf` file.
- `DELETE /document`: Purges isolated indices tracking segments tied to internal representations mapping a target `document_id`.
- `POST /chat`: Generates responses citing sources using isolated memory history tied correctly per querying `project_id`.

---

## 📊 Admin Dashboard

Access the built-in system administration dashboard directly by navigating to:
**`http://127.0.0.1:8000/admin`**

Log in using the `ADMIN_USERNAME` and `ADMIN_PASSWORD` defined in your `.env` to visually monitor system-wide activity, inspect document metrics across indices, and traverse timelines of user queries across unique project partitions.

---

## 🛡️ License

This project is licensed under the MIT License - see the LICENSE file for details.
