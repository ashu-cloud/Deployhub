from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Build Orchestrator"
    DATABASE_URL: str = "postgresql+asyncpg://deployhub:password@localhost:5432/deployhub"
    REDIS_URL: str = "redis://localhost:6379/0"
    KAFKA_BOOTSTRAP_SERVERS: str = "kafka:9092"
    # SASL/SSL settings — leave empty to use plain TCP (local dev)
    KAFKA_SECURITY_PROTOCOL: str = ""    # e.g. SASL_SSL
    KAFKA_SASL_MECHANISM: str = ""       # e.g. PLAIN
    KAFKA_SASL_USERNAME: str = ""
    KAFKA_SASL_PASSWORD: str = ""
    
    GITHUB_API_TOKEN: str = "" # Personal Access Token or GitHub App token for API calls
    GROQ_API_KEY: str = "" # Groq API Key for AI Diagnosis
    
    BUILD_TIMEOUT_SECONDS: int = 600
    BUILD_MEM_LIMIT: str = "512m"
    BUILD_CPU_QUOTA: int = 100000

    # Docker named volume that both this service and upload-service mount at
    # /tmp/builds. The sibling build container must bind the *volume name*
    # (Docker daemon sees host paths, not this container's filesystem).
    BUILD_VOLUME_NAME: str = ""
    ENV_VAR_ENCRYPTION_KEY: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
