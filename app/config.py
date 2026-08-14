from pydantic_settings import BaseSettings, SettingsConfigDict


# DeepSeek v4: added SECRET_KEY and ALGORITHM here so secrets
# live in .env instead of being hardcoded in router/auth.py
class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()