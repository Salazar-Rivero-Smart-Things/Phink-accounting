import os

class Settings:
    PROJECT_NAME: str = "Phinx Accounting"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api"
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./phinx_accounting.db")
    
    # Llama 3.1 AI Service settings
    # Default: connects to local Ollama instance (http://localhost:11434)
    # or any OpenAI-compatible / local inference server
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    LLAMA_MODEL_NAME: str = os.getenv("LLAMA_MODEL_NAME", "llama3.1:8b")
    
    # Hugging Face token if using HF inference API
    HF_TOKEN: str = os.getenv("HF_TOKEN", "")

settings = Settings()
