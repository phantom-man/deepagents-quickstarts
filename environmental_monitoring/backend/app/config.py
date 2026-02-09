"""
Centralized Configuration for Environmental Monitoring System

Uses Pydantic Settings for type-safe configuration with environment variable support.
"""
from functools import lru_cache
from typing import List, Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # ==================== Application ====================
    app_name: str = "Environmental Monitoring System"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: str = "production"  # development, staging, production
    
    # ==================== Security ====================
    # API Key for protected endpoints (generate with: openssl rand -hex 32)
    api_key: str = ""
    
    # CORS - Comma-separated list of allowed origins
    cors_origins: str = "https://env-monitor-dashboard-758343025648.us-central1.run.app"
    
    # Rate limiting
    rate_limit_per_minute: int = 60
    rate_limit_burst: int = 10
    
    # ==================== Database ====================
    database_url: str = "sqlite+aiosqlite:///./environmental_monitoring.db"
    db_pool_size: int = 20
    db_max_overflow: int = 10
    
    # ==================== Cache ====================
    redis_url: Optional[str] = None  # Optional Redis URL for distributed caching
    cache_ttl_short: int = 300  # 5 minutes
    cache_ttl_medium: int = 3600  # 1 hour
    cache_ttl_long: int = 86400  # 24 hours
    
    # ==================== External API Keys ====================
    openweathermap_api_key: str = ""
    airnow_api_key: str = ""
    iqair_api_key: str = ""
    noaa_api_token: str = ""
    nasa_firms_api_key: str = ""
    nasa_earthdata_token: str = ""
    copernicus_api_key: str = ""
    purpleair_api_key: str = ""
    planetary_computer_key: str = ""
    
    # ==================== Moltbook Integration ====================
    moltbook_api_url: str = ""
    moltbook_api_key: str = ""
    moltbook_agent_id: str = ""
    
    # ==================== Logging ====================
    log_level: str = "INFO"
    log_format: str = "json"  # json or text
    
    # ==================== Sentry (Error Tracking) ====================
    sentry_dsn: Optional[str] = None
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        if not self.cors_origins:
            return []
        origins = [origin.strip() for origin in self.cors_origins.split(",")]
        # Always allow localhost in development
        if self.environment == "development":
            origins.extend([
                "http://localhost:8050",
                "http://localhost:8080",
                "http://127.0.0.1:8050",
                "http://127.0.0.1:8080",
            ])
        return list(set(origins))
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"
    
    @property
    def api_key_configured(self) -> bool:
        """Check if API key is configured."""
        return bool(self.api_key and len(self.api_key) >= 32)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Convenience access
settings = get_settings()
