import os

class Settings:
    PROJECT_NAME: str = "Phink Accounting"
    VERSION: str = "0.2.0"
    API_V1_STR: str = "/api"
    
    # Database (SQLite locally or PostgreSQL on Railway via DATABASE_URL)
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./phink_accounting.db")
    
    # 1) Lokal Llama 3.1 8B Instruct (`llama serve` på din PC når den står på)
    LLAMA_SERVER_URL: str = os.getenv("LLAMA_SERVER_URL", "http://127.0.0.1:9931")
    LLAMA_MODEL_NAME: str = os.getenv(
        "LLAMA_MODEL_NAME",
        "lmstudio-community/Meta-Llama-3.1-8B-Instruct-GGUF:Q4_K_M"
    )
    LLAMA_API_KEY: str = os.getenv("LLAMA_API_KEY", "sk-phink-local")

    # 2) 24/7 Sky-Llama 3.1 8B Instruct (f.eks. Groq / Together / OpenRouter når PC-en din er avslått)
    CLOUD_LLM_BASE_URL: str = os.getenv("CLOUD_LLM_BASE_URL", "https://api.groq.com/openai/v1")
    CLOUD_LLM_API_KEY: str = os.getenv("CLOUD_LLM_API_KEY", "")
    CLOUD_LLM_MODEL: str = os.getenv("CLOUD_LLM_MODEL", "llama-3.1-8b-instant")

    # 3) Alternativ Ollama URL
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    
    # 4) Domenekonfigurasjon, Autentisering og Kundebehandler / Operator PIN
    PUBLIC_DOMAIN: str = os.getenv("PUBLIC_DOMAIN", "www.phink-acounting.no")
    OPERATOR_PIN: str = os.getenv("OPERATOR_PIN", "2026")
    AUTH_SECRET: str = os.getenv("AUTH_SECRET", "phink-accounting-local-secret-change-in-prod-2026")
    ACCESS_TOKEN_EXPIRE_HOURS: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_HOURS", "72"))

    # Hugging Face token
    HF_TOKEN: str = os.getenv("HF_TOKEN", "")

settings = Settings()
