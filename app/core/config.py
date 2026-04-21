from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr
from typing import Literal

class Settings(BaseSettings):
    SECRET_KEY: SecretStr                    
    ALGORITHM: Literal["HS256", "HS384", "HS512"] = "HS256"

    model_config = SettingsConfigDict(
        env_file=".env",          
        env_file_encoding="utf-8",
        case_sensitive=False,      
        extra="ignore"
    )

# Create a single instance
settings = Settings()