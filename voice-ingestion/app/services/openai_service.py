from typing import Any, Dict
from openai import OpenAI
from app.config import settings


class OpenAIService:
    """Service for interacting with OpenAI APIs (Whisper and GPT)."""

    def __init__(self):
        """Initialize OpenAI client."""
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)

    def transcribe_audio(
        self,
        audio_file_path: str,
        prompt: str | None = None
    ) -> Dict[str, Any]:
        """
        Transcribe audio using OpenAI Whisper.

        Args:
            audio_file_path: Path to the audio file
            prompt: Optional prompt to guide transcription

        Returns:
            Dictionary containing transcription and metadata
        """
        try:
            with open(audio_file_path, "rb") as audio_file:
                # Call Whisper API
                response = self.client.audio.transcriptions.create(
                    model=settings.WHISPER_MODEL,
                    file=audio_file,
                    prompt=prompt if prompt else None,
                    response_format="verbose_json"
                )

            # Extract response data
            result = {
                "transcription": response.text,
                "metadata": {
                    "language": getattr(response, "language", "unknown"),
                    "duration": getattr(response, "duration", None),
                    "model": settings.WHISPER_MODEL
                }
            }

            return result

        except Exception as e:
            raise Exception(f"Error transcribing audio: {str(e)}")

    def extract_structured_data(
        self,
        text: str,
        schema: Dict[str, Any],
        system_prompt: str | None = None
    ) -> Dict[str, Any]:
        """
        Extract structured data from text using GPT with function calling.

        Args:
            text: The text to extract data from
            schema: JSON schema defining the output structure
            system_prompt: Optional system prompt to guide extraction

        Returns:
            Dictionary containing structured data and metadata
        """
        try:
            # Default system prompt if none provided
            if not system_prompt:
                system_prompt = (
                    "Extract structured information from the provided text according to the given schema. "
                    "Be accurate and only include information explicitly stated in the text. "
                    "If a field's value is not found, use null."
                )

            # Create the function definition for structured output
            function = {
                "name": "extract_data",
                "description": "Extract structured data from text",
                "parameters": schema
            }

            # Call GPT API with function calling
            response = self.client.chat.completions.create(
                model=settings.GPT_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ],
                functions=[function],
                function_call={"name": "extract_data"}
            )

            # Extract the function call arguments (structured data)
            message = response.choices[0].message

            if message.function_call:
                import json
                structured_data = json.loads(message.function_call.arguments)
            else:
                structured_data = {}

            result = {
                "structured_data": structured_data,
                "metadata": {
                    "model": settings.GPT_MODEL,
                    "finish_reason": response.choices[0].finish_reason,
                    "usage": {
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens
                    }
                }
            }

            return result

        except Exception as e:
            raise Exception(f"Error extracting structured data: {str(e)}")


# Create a singleton instance
openai_service = OpenAIService()
