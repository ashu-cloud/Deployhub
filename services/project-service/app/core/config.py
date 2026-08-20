from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Project Service"
    DATABASE_URL: str = "postgresql+asyncpg://deployhub:password@localhost:5432/deployhub"
    REDIS_URL: str = "redis://localhost:6379/0"
    KAFKA_BOOTSTRAP_SERVERS: str = "kafka:9092"
    
    GITHUB_API_TOKEN: str = "" # Personal Access Token or GitHub App token for API calls
    WEBHOOK_SECRET: str = "supersecret_webhook_key_123"
    
    JWT_SECRET_KEY: str = "supersecretkey_change_in_production"
    JWT_ALGORITHM: str = "HS256"
    
    ENV_VAR_ENCRYPTION_KEY: str = "0123456789abcdef0123456789abcdef" # 32 bytes hex for AES-256

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
