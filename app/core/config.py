import os
from dotenv import load_dotenv
load_dotenv()
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Business AI Agent"
    VERSION: str = "1.0.0"
    ENV: str = "development"
    
    # LLM Keys
    # GOOGLE_API_KEY removed
    OPENAI_API_KEY: str

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""

    # Memory
    CHAT_HISTORY_WINDOW: int = 20
    CHAT_TTL_SECONDS: int = 3600  # 1 hour default

    # RAG
    VECTOR_DB_TYPE: str = "redis"

    class Config:
        env_file = ".env"

settings = Settings()
# Reload Trigger
