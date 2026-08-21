from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Build Orchestrator"
    DATABASE_URL: str = "postgresql+asyncpg://deployhub:password@localhost:5432/deployhub"
    REDIS_URL: str = "redis://localhost:6379/0"
    KAFKA_BOOTSTRAP_SERVERS: str = "kafka:9092"
    
    GITHUB_API_TOKEN: str = "" # Personal Access Token or GitHub App token for API calls
    
    BUILD_TIMEOUT_SECONDS: int = 600
    BUILD_MEM_LIMIT: str = "512m"
    BUILD_CPU_QUOTA: int = 100000

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
