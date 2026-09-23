from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Auth Service"
    DATABASE_URL: str  # Required — no default, must be supplied via environment
    REDIS_URL: str = "redis://localhost:6379/0"

    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""

    # RS256: this service holds the private key and signs tokens; every other
    # service only ever needs the public key to verify them. Keys are never
    # committed -- generate them with `python scripts/generate_secrets.py`.
    JWT_ALGORITHM: str = "RS256"
    JWT_PRIVATE_KEY_PATH: str = "/secrets/jwt/private.pem"
    JWT_PUBLIC_KEY_PATH: str = "/secrets/jwt/public.pem"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    CORS_ORIGINS: str = "http://localhost:3000"
    FRONTEND_URL: str = "http://localhost:3000"
    # Must match the callback URL registered on the GitHub OAuth app.
    GITHUB_REDIRECT_URI: str = "http://localhost:3000/api/v1/auth/callback"
    EXPOSE_API_DOCS: bool = False

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
