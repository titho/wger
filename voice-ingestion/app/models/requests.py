from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class TranscriptionRequest(BaseModel):
    """Request model for audio transcription."""

    file_id: str = Field(..., description="The ID of the uploaded audio file")
    prompt: Optional[str] = Field(None, description="Optional prompt to guide transcription")


class StructuredDataRequest(BaseModel):
    """Request model for structured data extraction."""

    text: str = Field(..., description="The text to extract structured data from")
    json_schema: Dict[str, Any] = Field(..., description="JSON schema defining the output structure")
    system_prompt: Optional[str] = Field(
        None,
        description="Optional system prompt to guide extraction"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "text": "John Doe, email: john@example.com, phone: 555-1234",
                "schema": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "email": {"type": "string"},
                        "phone": {"type": "string"}
                    },
                    "required": ["name"]
                },
                "system_prompt": "Extract contact information from the text"
            }
        }
    }
