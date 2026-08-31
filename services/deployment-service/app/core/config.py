from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Deployment Service"
    DATABASE_URL: str = "postgresql+asyncpg://deployhub:password@localhost:5432/deployhub"
    REDIS_URL: str = "redis://localhost:6379/0"
    KAFKA_BOOTSTRAP_SERVERS: str = "kafka:9092"
    # SASL/SSL settings — leave empty to use plain TCP (local dev)
    KAFKA_SECURITY_PROTOCOL: str = ""    # e.g. SASL_SSL
    KAFKA_SASL_MECHANISM: str = ""       # e.g. PLAIN
    KAFKA_SASL_USERNAME: str = ""
    KAFKA_SASL_PASSWORD: str = ""

    # Caddy's admin API is not published on any network interface. It is
    # reachable only over a filesystem-shared Unix socket between the caddy
    # and deployment-service containers.
    CADDY_ADMIN_URL: str = "unix:///srv/caddy-admin/admin.sock"
    BASE_DOMAIN: str = "localhost"
    MINIO_DIAL: str = "minio:9000"
    S3_BUCKET_NAME: str = "deployhub-artifacts"
    CORS_ORIGINS: str = "http://localhost:3000"

    # RS256: only the public key is needed to verify tokens minted by auth-service.
    JWT_ALGORITHM: str = "RS256"
    JWT_PUBLIC_KEY_PATH: str = "/secrets/jwt/public.pem"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
