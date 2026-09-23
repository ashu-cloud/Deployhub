from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Upload Service"
    DATABASE_URL: str  # Required — no default, must be supplied via environment
    KAFKA_BOOTSTRAP_SERVERS: str = "kafka:9092"
    # SASL/SSL settings — leave empty to use plain TCP (local dev)
    KAFKA_SECURITY_PROTOCOL: str = ""    # e.g. SASL_SSL
    KAFKA_SASL_MECHANISM: str = ""       # e.g. PLAIN
    KAFKA_SASL_USERNAME: str = ""
    KAFKA_SASL_PASSWORD: str = ""
    
    S3_ENDPOINT_URL: str = "http://localhost:9000"  # Safe non-credential default
    S3_ACCESS_KEY: str  # Required — must be supplied via environment
    S3_SECRET_KEY: str  # Required — must be supplied via environment
    S3_BUCKET_NAME: str = "deployhub-artifacts"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
