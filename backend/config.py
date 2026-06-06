from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    groq_api_key: str = ""
    anthropic_api_key: str = ""
    gemini_api_key: str = ""
    tavily_api_key: str = ""
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "https://cloud.langfuse.com"
    environment: str = "development"
    frontend_url: str = "http://localhost:5173"
    default_model: str = "groq/llama-3.3-70b-versatile"

    class Config:
        env_file = ".env"


settings = Settings()
