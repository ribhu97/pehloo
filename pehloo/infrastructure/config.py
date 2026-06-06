from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    openrouter_api_key: str
    pehloo_default_model: str = "anthropic/claude-sonnet-4-5"
    pehloo_max_steps_per_task: int = 15
    pehloo_output_dir: str = "./reports"
    pehloo_headless: bool = True
    pehloo_login_email: str | None = None
    pehloo_login_password: str | None = None


settings = Settings()  # type: ignore[call-arg]
