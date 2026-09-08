from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    supabase_db_url: str | None = None
    database_url: str | None = None
    sqlite_path: str = "./data/contactloop.db"
    supabase_url: str | None = None
    supabase_secret_key: str | None = None
    supabase_jwt_secret: str | None = None
    contact_brief_endpoint: str | None = None
    aws_region: str = "us-east-2"
    bedrock_model_id: str | None = None
    cors_origins: str = "*"
    app_env: str = "development"

    @property
    def sqlalchemy_url(self) -> str:
        if self.supabase_db_url:
            return self.supabase_db_url
        if self.database_url:
            return self.database_url
        return f"sqlite:///{self.sqlite_path}"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
