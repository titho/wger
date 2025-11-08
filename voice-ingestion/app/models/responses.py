from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class AudioUploadResponse(BaseModel):
    """Response model for audio upload."""

    file_id: str = Field(..., description="Unique identifier for the uploaded file")
    filename: str = Field(..., description="Original filename")
    file_size: int = Field(..., description="File size in bytes")
    file_extension: str = Field(..., description="File extension")
    message: str = Field(..., description="Success message")


class TranscriptionResponse(BaseModel):
    """Response model for audio transcription."""

    transcription: str = Field(..., description="The transcribed text")
    file_id: str = Field(..., description="The audio file ID")
    log_id: str = Field(..., description="The transcription log ID")
    metadata: Dict[str, Any] = Field(..., description="Additional metadata from transcription")


class StructuredDataResponse(BaseModel):
    """Response model for structured data extraction."""

    structured_data: Dict[str, Any] = Field(..., description="The extracted structured data")
    log_id: str = Field(..., description="The extraction log ID")
    metadata: Dict[str, Any] = Field(..., description="Additional metadata from extraction")


class ErrorResponse(BaseModel):
    """Response model for errors."""

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Additional error details")
