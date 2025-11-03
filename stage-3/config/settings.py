"""Configuration management for Budget Tracker Agent"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Google OAuth
    google_client_id: str
    google_client_secret: str
    google_redirect_uri: str = "https://dffec538518c.ngrok-free.app/oauth/callback"
    
    # Firebase
    firebase_credentials_path: str = "config/firebase-credentials.json"
    
    # Gemini
    gemini_api_key: str
    
    # FastAPI
    host: str = "0.0.0.0"
    port: int = 8020
    debug: bool = True
    
    # Telex
    telex_api_url: str = "https://telex.im/ai-coworkers/spending-tracker-28337891be5e"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
