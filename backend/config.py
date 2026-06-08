from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv(Path(__file__).parent / ".env")


class Settings(BaseSettings):
    groq_api_key: str = ""
    anthropic_api_key: str = ""
    gemini_api_key: str = ""
    openrouter_api_key: str = ""
    tavily_api_key: str = ""
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "https://cloud.langfuse.com"
    environment: str = "development"
    frontend_url: str = "http://localhost:5173"
    default_model: str = "groq/llama-3.3-70b-versatile"
    supabase_url: str = ""
    supabase_key: str = ""

    class Config:
        env_file = str(Path(__file__).parent / ".env")


settings = Settings()
