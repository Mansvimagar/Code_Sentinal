from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://codesentinel:codesentinel@localhost:5432/codesentinel"
    jwt_secret: str = "development-only-secret"
    webhook_secret: str = "development-webhook-secret"
    github_app_id: str | None = None
    github_private_key: str | None = None
    github_api_url: str = "https://api.github.com"
    require_dashboard_auth: bool = False
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
