from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Project Service"
    DATABASE_URL: str  # Required — no default, must be supplied via environment
    REDIS_URL: str = "redis://localhost:6379/0"
    KAFKA_BOOTSTRAP_SERVERS: str = "kafka:9092"
    # SASL/SSL settings — leave empty to use plain TCP (local dev)
    KAFKA_SECURITY_PROTOCOL: str = ""    # e.g. SASL_SSL
    KAFKA_SASL_MECHANISM: str = ""       # e.g. PLAIN
    KAFKA_SASL_USERNAME: str = ""
    KAFKA_SASL_PASSWORD: str = ""

    GITHUB_API_TOKEN: str = "" # Personal Access Token or GitHub App token for API calls

    # Public URL GitHub should POST webhooks to. Localhost is unreachable from
    # GitHub -- set this to an ngrok/cloudflare-tunnel URL when testing real pushes.
    WEBHOOK_BASE_URL: str = "http://localhost:3000/api/v1"

    # No hardcoded default: a shared webhook/HMAC secret must come from the
    # environment (see scripts/generate_secrets.py). An empty value fails
    # closed -- verify_github_signature() will reject every signature.
    WEBHOOK_SECRET: str = ""

    # RS256: this service only ever holds the *public* key, so it can verify
    # tokens minted by auth-service but can never mint its own.
    JWT_ALGORITHM: str = "RS256"
    JWT_PUBLIC_KEY_PATH: str = "/secrets/jwt/public.pem"

    # No hardcoded default -- must be a 64-char hex string (32 bytes / AES-256)
    # supplied via the environment. See scripts/generate_secrets.py.
    ENV_VAR_ENCRYPTION_KEY: str = ""

    CORS_ORIGINS: str = "http://localhost:3000"
    EXPOSE_API_DOCS: bool = False

    # Requests/window allowed per authenticated user for project creation.
    RATE_LIMIT_CREATE_PROJECT_MAX: int = 10
    RATE_LIMIT_CREATE_PROJECT_WINDOW_SECONDS: int = 10

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
