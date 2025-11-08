from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from typing import Optional
from app.models.requests import TranscriptionRequest
from app.models.responses import AudioUploadResponse, TranscriptionResponse, ErrorResponse
from app.models.database import AudioFile, Transcription
from app.services.logging_service import logging_service
from app.services.openai_service import openai_service
from app.services.database_service import db
from app.utils.file_handler import file_handler

router = APIRouter()


@router.post(
    "/upload-audio",
    response_model=AudioUploadResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}}
)
async def upload_audio(file: UploadFile = File(...)):
    """
    Upload an audio file for processing.

    Accepts audio files in the following formats: mp3, wav, m4a, webm.
    Maximum file size: 25MB.

    Returns the file_id which can be used for transcription.
    """
    try:
        # Validate file
        filename, file_extension = file_handler.validate_audio_file(file)

        # Read file contents
        file_contents = await file_handler.read_upload_file(file)

        # Log the audio file
        file_id = logging_service.log_audio_file(
            audio_bytes=file_contents,
            filename=filename,
            file_extension=file_extension
        )

        # Store in database
        audio_file = AudioFile(
            file_id=file_id,
            filename=filename,
            file_size=len(file_contents),
            file_extension=file_extension,
            file_path=logging_service.get_audio_file_path(file_id)
        )
        db.add_audio_file(audio_file)

        return AudioUploadResponse(
            file_id=file_id,
            filename=filename,
            file_size=len(file_contents),
            file_extension=file_extension,
            message="Audio file uploaded successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")


@router.post(
    "/transcribe",
    response_model=TranscriptionResponse,
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}}
)
async def transcribe_audio(
    file_id: str = Form(...),
    prompt: Optional[str] = Form(None)
):
    """
    Transcribe an uploaded audio file to text using OpenAI Whisper.

    Requires:
    - file_id: The ID of a previously uploaded audio file
    - prompt: Optional prompt to guide transcription (improves accuracy)

    Returns the transcribed text and metadata.
    """
    try:
        # Get the audio file path
        audio_file_path = logging_service.get_audio_file_path(file_id)

        if not audio_file_path:
            raise HTTPException(
                status_code=404,
                detail=f"Audio file with ID {file_id} not found"
            )

        # Transcribe the audio
        result = openai_service.transcribe_audio(
            audio_file_path=audio_file_path,
            prompt=prompt
        )

        # Log the transcription
        log_id = logging_service.log_transcription(
            file_id=file_id,
            audio_filename=audio_file_path,
            prompt=prompt or "",
            transcription=result["transcription"],
            metadata=result["metadata"]
        )

        # Store in database
        transcription = Transcription(
            transcription_id=log_id,
            file_id=file_id,
            transcription_text=result["transcription"],
            prompt=prompt,
            language=result["metadata"].get("language"),
            duration=result["metadata"].get("duration"),
            model=result["metadata"].get("model", "whisper-1")
        )
        db.add_transcription(transcription)

        return TranscriptionResponse(
            transcription=result["transcription"],
            file_id=file_id,
            log_id=log_id,
            metadata=result["metadata"]
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error transcribing audio: {str(e)}"
        )
