import os
import logging
from dotenv import load_dotenv

from llama_index.llms.azure_openai import AzureOpenAI
from llama_index.llms.openai import OpenAI
from llama_index.llms.gemini import Gemini

from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.embeddings.azure_openai import AzureOpenAIEmbedding
from llama_index.embeddings.gemini import GeminiEmbedding

from llama_index.core import Settings

load_dotenv()
logger = logging.getLogger(__name__)

# Provider Configs
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "azure_openai").lower()
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "openai").lower()

# Azure Settings
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY", "")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
AZURE_OPENAI_CHAT_DEPLOYMENT = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT", "gpt-4o")
AZURE_OPENAI_EMBEDDING_DEPLOYMENT = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-3-small")

# Standard OpenAI Settings
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

# Gemini Settings
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "models/gemini-1.5-pro")
GEMINI_EMBEDDING_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL", "models/text-embedding-004")

# Admin
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "secret")

def setup_settings():
    """Confingures the global LlamaIndex Settings object directly with the chosen models."""
    
    # 1. Setup LLM
    if LLM_PROVIDER == "azure_openai":
        logger.info("Initializing Azure OpenAI for LLM.")
        Settings.llm = AzureOpenAI(
            model="gpt-4o",
            deployment_name=AZURE_OPENAI_CHAT_DEPLOYMENT,
            api_key=AZURE_OPENAI_API_KEY,
            azure_endpoint=AZURE_OPENAI_ENDPOINT,
            api_version=AZURE_OPENAI_API_VERSION,
        )
    elif LLM_PROVIDER == "openai":
        logger.info("Initializing standard OpenAI for LLM.")
        Settings.llm = OpenAI(
            model=OPENAI_MODEL, 
            api_key=OPENAI_API_KEY
        )
    elif LLM_PROVIDER == "gemini":
        logger.info("Initializing Google Gemini for LLM.")
        Settings.llm = Gemini(
            model=GEMINI_MODEL,
            api_key=GOOGLE_API_KEY
        )
    else:
        raise ValueError(f"Unknown LLM Provider specified: {LLM_PROVIDER}")
        
    # 2. Setup Embedding Model
    if EMBEDDING_PROVIDER == "azure_openai":
        logger.info("Initializing Azure OpenAI for Embeddings.")
        Settings.embed_model = AzureOpenAIEmbedding(
            model="text-embedding-3-small",
            deployment_name=AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
            api_key=AZURE_OPENAI_API_KEY,
            azure_endpoint=AZURE_OPENAI_ENDPOINT,
            api_version=AZURE_OPENAI_API_VERSION,
        )
    elif EMBEDDING_PROVIDER == "openai":
        logger.info("Initializing standard OpenAI for Embeddings.")
        Settings.embed_model = OpenAIEmbedding(
            model="text-embedding-3-small",
            api_key=OPENAI_API_KEY
        )
    elif EMBEDDING_PROVIDER == "gemini":
        logger.info("Initializing Google Gemini for Embeddings.")
        Settings.embed_model = GeminiEmbedding(
            model_name=GEMINI_EMBEDDING_MODEL,
            api_key=GOOGLE_API_KEY
        )
    else:
        raise ValueError(f"Unknown Embedding Provider specified: {EMBEDDING_PROVIDER}")

    # 3. Global parameters mapping
    Settings.chunk_size = 512
    Settings.chunk_overlap = 50
    
    logger.info("Application LLM settings mapping complete.")
