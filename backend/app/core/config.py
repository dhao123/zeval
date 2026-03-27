"""
Application configuration using Pydantic Settings.
"""
from functools import lru_cache
from typing import List, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    # Application
    app_name: str = "ZKH Benchmark Platform"
    app_version: str = "2.0.0"
    environment: str = "development"
    debug: bool = True
    log_level: str = "INFO"
    
    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/zkh_bench"
    database_url_sync: str = "postgresql://postgres:postgres@localhost:5432/zkh_bench"
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # RabbitMQ / Celery
    rabbitmq_url: str = "amqp://guest:guest@localhost:5672//"
    celery_result_backend: Optional[str] = None
    
    # MinIO
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket_name: str = "zkh-bench"
    minio_secure: bool = False
    
    # Security
    secret_key: str = "your-secret-key-change-this-in-production"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    algorithm: str = "HS256"
    
    # OpenAI
    openai_api_key: Optional[str] = None
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o"
    
    # ZKH
    zhk_api_key: Optional[str] = None
    zhk_base_url: str = "https://api.zkh.com/v1"
    
    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:5173"
    
    # SSO Configuration
    # SSO is required for AITest-compatible authentication
    sso_enabled: bool = True  # Enabled by default
    sso_service_url: str = "https://security-service-uat.zkh360.com"  # SSO service URL
    admin_role_id: int = 1885  # Admin role ID from security service
    
    # Local auth (always enabled for fallback)
    local_auth_enabled: bool = True
    
    # Aliyun OSS Configuration
    oss_access_key_id: str = ""
    oss_access_key_secret: str = ""
    oss_endpoint: str = "oss-cn-hangzhou.aliyuncs.com"
    oss_bucket_name: str = "zkh-qa"
    oss_internal_endpoint: Optional[str] = None  # 内网地址（可选）
    
    @property
    def cors_origin_list(self) -> List[str]:
        """Parse CORS origins string to list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    @property
    def celery_broker_url(self) -> str:
        """Get Celery broker URL."""
        return self.rabbitmq_url
    
    @property
    def celery_backend_url(self) -> str:
        """Get Celery result backend URL."""
        return self.celery_result_backend or self.redis_url


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
