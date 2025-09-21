"""
Configuration settings for FSN Appium Farm API
"""

from pydantic_settings import BaseSettings
from typing import Optional, List
from pydantic import field_validator
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # App Info
    app_name: str = "FSN Appium Farm API"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Database - Use existing license database with separate backend tables
    database_url: str = "postgresql+asyncpg://fsn_license_db_user:cokypdAxj9wxWMFCxZLsJJr1VlVStUUo@dpg-d32kllumcj7s739m1540-a.oregon-postgres.render.com/fsn_license_db"
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # Security
    secret_key: str = "your-secret-key-change-this"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # CORS
    allowed_origins: str = "http://localhost:3000,http://127.0.0.1:3000,https://fsn-appium.com,https://www.fsn-appium.com,https://fsndevelopment.com,https://www.fsndevelopment.com"
    
    def get_allowed_origins(self) -> List[str]:
        """Parse allowed origins from string to list"""
        if isinstance(self.allowed_origins, str):
            return [origin.strip() for origin in self.allowed_origins.split(',')]
        return self.allowed_origins
    
    # API Settings
    api_v1_prefix: str = "/api/v1"
    
    # Licensing System (Server Deployment Ready)
    license_server_url: str = "https://license.fsn-appium.com"  # Production license server
    license_client_id: str = ""  # Set via environment variable
    license_key: str = ""  # Set via environment variable
    license_check_interval: int = 86400  # 24 hours in seconds
    license_grace_period_days: int = 7
    license_dev_mode: bool = False  # Skip license checks in development
    
    # Deployment Environment
    deployment_env: str = "development"  # development, staging, production
    server_location: str = "local"  # local, vps, cloud
    
    class Config:
        env_file = ".env"


# Create settings instance
settings = Settings()
