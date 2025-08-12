import os
from typing import List
from pathlib import Path

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

class Settings:
    """Simplified application settings"""
    
    # Basic App Settings
    APP_NAME: str = os.getenv("APP_NAME", "Kenya Startup Navigator")
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    
    # API Configuration
    API_V1_PREFIX: str = "/api/v1"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    
    # Groq AI Configuration
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama3-70b-8192")
    GROQ_MAX_TOKENS: int = int(os.getenv("GROQ_MAX_TOKENS", "2048"))
    GROQ_TEMPERATURE: float = float(os.getenv("GROQ_TEMPERATURE", "0.7"))
    
    # CORS Settings - Simple parsing
    #ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:3001", "https://your-app.vercel.app"]
    #ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1", "your-api.railway.app"]
    #ALLOWED_HOSTS: List[str] = ["*"]

    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000", 
        "http://localhost:3001", 
        "https://your-app.vercel.app",
        "https://*.railway.app",
        "*"  # Allow all for Railway deployment
    ]
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
    
    # Logging Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # AI Response Configuration
    AI_RESPONSE_CACHE_TTL: int = int(os.getenv("AI_RESPONSE_CACHE_TTL", "3600"))
    MAX_QUERY_LENGTH: int = int(os.getenv("MAX_QUERY_LENGTH", "2000"))
    MIN_QUERY_LENGTH: int = int(os.getenv("MIN_QUERY_LENGTH", "5"))
    
    # Ecosystem Data Configuration
    ECOSYSTEM_DATA_REFRESH_INTERVAL: int = int(os.getenv("ECOSYSTEM_DATA_REFRESH_INTERVAL", "86400"))
    
    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"
    
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

# Create global settings instance
settings = Settings()

# Validate required settings
if not settings.GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY environment variable is required")

def get_settings() -> Settings:
    return settings

__all__ = ["settings", "get_settings", "Settings"]