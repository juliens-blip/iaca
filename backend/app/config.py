from pydantic_settings import BaseSettings
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent.parent


class Settings(BaseSettings):
    app_name: str = "IACA API"
    debug: bool = True
    database_url: str = f"sqlite:///{PROJECT_ROOT / 'data' / 'iaca.db'}"
    anthropic_api_key: str = ""
    google_api_key: str = ""
    ollama_host: str = "http://localhost:11434"
    whisper_model: str = "base"
    piper_voice: str = "/home/julien/.local/share/piper-voices/fr_FR-siwis-medium.onnx"
    docs_path: str = str(Path(__file__).parent.parent.parent / "docs")
    upload_path: str = str(Path(__file__).parent.parent.parent / "data" / "uploads")
    api_auth_token: str = ""
    rate_limit_enabled: bool = False
    rate_limit_requests: int = 60
    rate_limit_window_seconds: int = 60
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    class Config:
        env_file = str(PROJECT_ROOT / ".env")

    def get_cors_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_origins.split(",")
            if origin.strip()
        ]


settings = Settings()
