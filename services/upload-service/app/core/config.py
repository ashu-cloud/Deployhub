from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Upload Service"
    DATABASE_URL: str = "postgresql+asyncpg://deployhub:password@localhost:5432/deployhub"
    KAFKA_BOOTSTRAP_SERVERS: str = "kafka:9092"
    # SASL/SSL settings — leave empty to use plain TCP (local dev)
    KAFKA_SECURITY_PROTOCOL: str = ""    # e.g. SASL_SSL
    KAFKA_SASL_MECHANISM: str = ""       # e.g. PLAIN
    KAFKA_SASL_USERNAME: str = ""
    KAFKA_SASL_PASSWORD: str = ""
    
    S3_ENDPOINT_URL: str = "http://localhost:9000"
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin123"
    S3_BUCKET_NAME: str = "deployhub-artifacts"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
