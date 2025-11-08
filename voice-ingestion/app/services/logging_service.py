import json
import os
from datetime import datetime
from typing import Any, Dict
from uuid import uuid4
from app.config import settings


class LoggingService:
    """Service for logging requests, responses, and files."""

    @staticmethod
    def _get_timestamp() -> str:
        """Get current timestamp in ISO format."""
        return datetime.utcnow().isoformat()

    @staticmethod
    def _generate_id() -> str:
        """Generate a unique ID."""
        return str(uuid4())

    @staticmethod
    def log_audio_file(audio_bytes: bytes, filename: str, file_extension: str) -> str:
        """
        Log an uploaded audio file.

        Args:
            audio_bytes: The audio file content
            filename: Original filename
            file_extension: File extension (e.g., '.mp3')

        Returns:
            The file_id for the saved audio
        """
        file_id = LoggingService._generate_id()
        timestamp = LoggingService._get_timestamp()

        # Create filename with timestamp and ID
        log_filename = f"{timestamp.replace(':', '-')}_{file_id}{file_extension}"
        log_path = os.path.join(settings.AUDIO_LOG_DIR, log_filename)

        # Save audio file
        with open(log_path, "wb") as f:
            f.write(audio_bytes)

        # Save metadata
        metadata = {
            "file_id": file_id,
            "original_filename": filename,
            "timestamp": timestamp,
            "file_size_bytes": len(audio_bytes),
            "file_extension": file_extension,
            "log_path": log_path
        }

        metadata_path = os.path.join(
            settings.AUDIO_LOG_DIR,
            f"{timestamp.replace(':', '-')}_{file_id}_metadata.json"
        )

        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)

        return file_id

    @staticmethod
    def log_transcription(
        file_id: str,
        audio_filename: str,
        prompt: str,
        transcription: str,
        metadata: Dict[str, Any]
    ) -> str:
        """
        Log a transcription request and response.

        Args:
            file_id: The audio file ID
            audio_filename: Original audio filename
            prompt: The prompt used for transcription
            transcription: The transcription result
            metadata: Additional metadata from the API response

        Returns:
            The log_id for this transcription
        """
        log_id = LoggingService._generate_id()
        timestamp = LoggingService._get_timestamp()

        log_data = {
            "log_id": log_id,
            "file_id": file_id,
            "timestamp": timestamp,
            "request": {
                "audio_filename": audio_filename,
                "prompt": prompt,
                "model": settings.WHISPER_MODEL
            },
            "response": {
                "transcription": transcription,
                "metadata": metadata
            }
        }

        log_filename = f"{timestamp.replace(':', '-')}_{log_id}.json"
        log_path = os.path.join(settings.TRANSCRIPTION_LOG_DIR, log_filename)

        with open(log_path, "w") as f:
            json.dump(log_data, f, indent=2)

        return log_id

    @staticmethod
    def log_structured_output(
        text: str,
        schema: Dict[str, Any],
        system_prompt: str,
        structured_data: Dict[str, Any],
        metadata: Dict[str, Any]
    ) -> str:
        """
        Log a structured output extraction request and response.

        Args:
            text: The input text
            schema: The JSON schema used
            system_prompt: The system prompt used
            structured_data: The extracted structured data
            metadata: Additional metadata from the API response

        Returns:
            The log_id for this extraction
        """
        log_id = LoggingService._generate_id()
        timestamp = LoggingService._get_timestamp()

        log_data = {
            "log_id": log_id,
            "timestamp": timestamp,
            "request": {
                "text": text,
                "schema": schema,
                "system_prompt": system_prompt,
                "model": settings.GPT_MODEL
            },
            "response": {
                "structured_data": structured_data,
                "metadata": metadata
            }
        }

        log_filename = f"{timestamp.replace(':', '-')}_{log_id}.json"
        log_path = os.path.join(settings.STRUCTURED_OUTPUT_LOG_DIR, log_filename)

        with open(log_path, "w") as f:
            json.dump(log_data, f, indent=2)

        return log_id

    @staticmethod
    def get_audio_file_path(file_id: str) -> str | None:
        """
        Get the file path for an audio file by its ID.

        Args:
            file_id: The audio file ID

        Returns:
            The file path if found, None otherwise
        """
        # Search for files with this file_id in the audio log directory
        for filename in os.listdir(settings.AUDIO_LOG_DIR):
            if file_id in filename and not filename.endswith("_metadata.json"):
                return os.path.join(settings.AUDIO_LOG_DIR, filename)
        return None


# Create a singleton instance
logging_service = LoggingService()
