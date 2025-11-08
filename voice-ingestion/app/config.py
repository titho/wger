import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Settings:
    """Application settings loaded from environment variables."""

    # OpenAI API Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    # Backend Configuration
    BACKEND_PORT: int = int(os.getenv("BACKEND_PORT", "8000"))

    # CORS Configuration
    CORS_ORIGINS: list[str] = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000"
    ).split(",")

    # File Upload Configuration
    MAX_FILE_SIZE: int = 25 * 1024 * 1024  # 25MB in bytes
    ALLOWED_AUDIO_FORMATS: set[str] = {".mp3", ".wav", ".m4a", ".webm"}

    # Logging Configuration
    LOG_DIR: str = os.getenv("LOG_DIR", "../logs")
    AUDIO_LOG_DIR: str = os.path.join(LOG_DIR, "audio")
    TRANSCRIPTION_LOG_DIR: str = os.path.join(LOG_DIR, "transcriptions")
    STRUCTURED_OUTPUT_LOG_DIR: str = os.path.join(LOG_DIR, "structured_outputs")

    # OpenAI Model Configuration
    WHISPER_MODEL: str = "whisper-1"
    GPT_MODEL: str = "gpt-4o-mini"  # Using the latest model name

    def validate(self):
        """Validate that required settings are present."""
        if not self.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        return True


# Create a singleton settings instance
settings = Settings()
