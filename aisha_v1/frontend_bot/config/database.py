"""
Настройки базы данных (PostgreSQL и Redis).
"""

from typing import Optional, Dict, Any
from pydantic_settings import BaseSettings
from pydantic import Field, validator, PostgresDsn, RedisDsn

class DatabaseConfig(BaseSettings):
    """Настройки базы данных."""
    
    # PostgreSQL
    POSTGRES_HOST: str = Field(..., env="POSTGRES_HOST")
    POSTGRES_PORT: int = Field(5432, env="POSTGRES_PORT", ge=1, le=65535)
    POSTGRES_DB: str = Field(..., env="POSTGRES_DB")
    POSTGRES_USER: str = Field(..., env="POSTGRES_USER")
    POSTGRES_PASSWORD: str = Field(..., env="POSTGRES_PASSWORD")
    DATABASE_URL: Optional[PostgresDsn] = Field(None, env="DATABASE_URL")
    
    # Redis
    REDIS_HOST: str = Field(..., env="REDIS_HOST")
    REDIS_PORT: int = Field(6379, env="REDIS_PORT", ge=1, le=65535)
    REDIS_DB: int = Field(0, env="REDIS_DB", ge=0)
    REDIS_PASSWORD: Optional[str] = Field(None, env="REDIS_PASSWORD")
    REDIS_SSL: bool = Field(False, env="REDIS_SSL")
    REDIS_POOL_SIZE: int = Field(10, env="REDIS_POOL_SIZE", ge=1)
    REDIS_POOL_TIMEOUT: int = Field(5, env="REDIS_POOL_TIMEOUT", ge=1)
    REDIS_RETRY_ON_TIMEOUT: bool = Field(True, env="REDIS_RETRY_ON_TIMEOUT")
    REDIS_MAX_RETRIES: int = Field(3, env="REDIS_MAX_RETRIES", ge=1)
    REDIS_RETRY_INTERVAL: int = Field(1, env="REDIS_RETRY_INTERVAL", ge=1)
    REDIS_URL: Optional[RedisDsn] = Field(None, env="REDIS_URL")
    
    @validator("DATABASE_URL", pre=True)
    def assemble_db_url(cls, v: Optional[str], values: Dict[str, Any]) -> str:
        if isinstance(v, str):
            return v
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            user=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_HOST"),
            port=str(values.get("POSTGRES_PORT")),
            path=f"/{values.get('POSTGRES_DB')}"
        )
    
    @validator("REDIS_URL", pre=True)
    def assemble_redis_url(cls, v: Optional[str], values: Dict[str, Any]) -> str:
        if isinstance(v, str):
            return v
        return RedisDsn.build(
            scheme="redis",
            host=values.get("REDIS_HOST"),
            port=values.get("REDIS_PORT"),
            path=f"/{values.get('REDIS_DB')}"
        )
    
    class Config:
        env_file = ".env"
        case_sensitive = True 