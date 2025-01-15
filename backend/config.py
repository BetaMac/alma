from pydantic_settings import BaseSettings
from typing import List
from pydantic import validator, Field
import os
from urllib.parse import urlparse

class Settings(BaseSettings):
    # Server Configuration
    PORT: int = Field(8000, ge=1024, le=65535)
    HOST: str = Field("0.0.0.0", pattern=r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$|^localhost$")
    DEBUG: bool = Field(False)
    
    # Model Configuration
    MODEL_ID: str = Field(..., min_length=1)
    MODEL_FILE: str = Field(..., min_length=1)
    GPU_LAYERS: int = Field(50, ge=0)
    MAX_MEMORY_PERCENT: float = Field(0.9, ge=0.1, le=1.0)
    
    # Task Configuration
    DEFAULT_TIMEOUT: int = Field(600, ge=30)  # minimum 30 seconds
    MAX_RETRIES: int = Field(3, ge=0, le=10)
    
    # CORS Settings
    ALLOWED_ORIGINS: List[str] = Field(["http://localhost:3000"])
    
    # WebSocket Configuration
    WS_HEARTBEAT_INTERVAL: int = Field(30, ge=5, le=300)  # between 5 and 300 seconds
    
    @validator("ALLOWED_ORIGINS")
    def validate_allowed_origins(cls, v):
        for origin in v:
            try:
                result = urlparse(origin)
                if not all([result.scheme, result.netloc]):
                    raise ValueError(f"Invalid origin URL: {origin}")
            except Exception as e:
                raise ValueError(f"Invalid origin URL: {origin}, error: {str(e)}")
        return v
    
    @validator("MODEL_FILE")
    def validate_model_file(cls, v):
        if not v.endswith((".gguf", ".bin")):
            raise ValueError("Model file must be a .gguf or .bin file")
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = True

def load_config() -> Settings:
    """Load and validate configuration from environment variables."""
    try:
        config = Settings()
        # Validate the config can be serialized
        config_dict = config.model_dump()
        print("Configuration loaded successfully:")
        for key, value in config_dict.items():
            print(f"{key}: {value}")
        return config
    except Exception as e:
        print("Error loading configuration:")
        print(str(e))
        raise

# Global config instance
config = load_config() 