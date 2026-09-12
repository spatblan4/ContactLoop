from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    supabase_db_url: str | None = None
    database_url: str | None = None
    sqlite_path: str = "./data/contactloop.db"
    supabase_url: str | None = None
    supabase_secret_key: str | None = None
    contact_brief_endpoint: str | None = None
    contact_brief_timeout_seconds: int = 60
    supabase_function_timeout_seconds: int = 15
    aws_region: str | None = None
    bedrock_model_id: str | None = None
    bedrock_temperature: float = 0.2
    bedrock_guardrail_id: str | None = None
    bedrock_guardrail_version: str | None = None
    strands_console_tracing: bool = False
    strands_otlp_tracing: bool = False
    outreach_agent_timeout_seconds: float = 90.0
    bedrock_guardrail_redact_output: bool = False
    call_summary_quality_pipeline: bool = False
    mcp_server_url: str | None = None
    mcp_allowed_tools: str | None = None
    voice_notes_dir: str | None = None
    voice_max_upload_bytes: int = 26_214_400
    voice_transcribe_enabled: bool = False
    voice_transcribe_bucket: str | None = None
    voice_transcribe_language: str = "en-US"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
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
