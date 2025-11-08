"""
API routes for querying the SQLite database.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
from app.services.database_service import db

router = APIRouter()


# ========== Audio File Endpoints ==========

@router.get("/audio-files")
async def list_audio_files(
    limit: Optional[int] = Query(default=None, ge=1, le=100),
    offset: int = Query(default=0, ge=0)
) -> Dict[str, Any]:
    """
    List all audio files in the database.

    Query parameters:
    - limit: Maximum number of files to return (1-100)
    - offset: Number of files to skip

    Returns files sorted by creation date (newest first).
    """
    try:
        audio_files = db.list_audio_files(limit=limit, offset=offset)
        return {
            "audio_files": [file.to_dict() for file in audio_files],
            "count": len(audio_files),
            "offset": offset,
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing audio files: {str(e)}")


@router.get("/audio-files/{file_id}")
async def get_audio_file(file_id: str) -> Dict[str, Any]:
    """
    Get details of a specific audio file by ID.

    Returns:
    - Audio file metadata including file_id, filename, size, extension, path, and creation date
    """
    audio_file = db.get_audio_file(file_id)
    if not audio_file:
        raise HTTPException(status_code=404, detail=f"Audio file with ID {file_id} not found")

    return audio_file.to_dict()


@router.patch("/audio-files/{file_id}/rename")
async def rename_audio_file(file_id: str, new_filename: str = Query(...)) -> Dict[str, Any]:
    """
    Rename an audio file.

    Query parameters:
    - new_filename: The new filename

    Returns:
    - Updated audio file metadata
    """
    # Validate new filename
    if not new_filename or not new_filename.strip():
        raise HTTPException(status_code=400, detail="Filename cannot be empty")

    # Update the filename in the database
    with db.get_session() as session:
        from app.models.database import AudioFile
        audio_file_obj = session.query(AudioFile).filter(AudioFile.file_id == file_id).first()

        if not audio_file_obj:
            raise HTTPException(status_code=404, detail=f"Audio file with ID {file_id} not found")

        old_filename = audio_file_obj.filename
        audio_file_obj.filename = new_filename.strip()
        session.commit()
        session.refresh(audio_file_obj)

        return {
            "message": "Audio file renamed successfully",
            "file_id": file_id,
            "old_filename": old_filename,
            "new_filename": audio_file_obj.filename,
            "audio_file": audio_file_obj.to_dict()
        }


# ========== Transcription Endpoints ==========

@router.get("/transcriptions")
async def list_transcriptions(
    limit: Optional[int] = Query(default=None, ge=1, le=100),
    offset: int = Query(default=0, ge=0)
) -> Dict[str, Any]:
    """
    List all transcriptions in the database.

    Query parameters:
    - limit: Maximum number of transcriptions to return (1-100)
    - offset: Number of transcriptions to skip

    Returns transcriptions sorted by creation date (newest first).
    """
    try:
        transcriptions = db.list_transcriptions(limit=limit, offset=offset)
        return {
            "transcriptions": [t.to_dict() for t in transcriptions],
            "count": len(transcriptions),
            "offset": offset,
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing transcriptions: {str(e)}")


@router.get("/transcriptions/{transcription_id}")
async def get_transcription(transcription_id: str) -> Dict[str, Any]:
    """
    Get details of a specific transcription by ID.

    Returns:
    - Transcription data including transcription_id, file_id, text, metadata, and creation date
    """
    transcription = db.get_transcription(transcription_id)
    if not transcription:
        raise HTTPException(
            status_code=404,
            detail=f"Transcription with ID {transcription_id} not found"
        )

    return transcription.to_dict()


@router.get("/audio-files/{file_id}/transcriptions")
async def list_transcriptions_by_file(file_id: str) -> Dict[str, Any]:
    """
    Get all transcriptions for a specific audio file.

    Returns:
    - List of transcriptions for this file, sorted by creation date (newest first)
    """
    # Check if audio file exists
    audio_file = db.get_audio_file(file_id)
    if not audio_file:
        raise HTTPException(status_code=404, detail=f"Audio file with ID {file_id} not found")

    transcriptions = db.list_transcriptions_by_file(file_id)
    return {
        "file_id": file_id,
        "transcriptions": [t.to_dict() for t in transcriptions],
        "count": len(transcriptions)
    }


# ========== Extraction Endpoints ==========

@router.get("/extractions")
async def list_extractions(
    limit: Optional[int] = Query(default=None, ge=1, le=100),
    offset: int = Query(default=0, ge=0)
) -> Dict[str, Any]:
    """
    List all structured data extractions in the database.

    Query parameters:
    - limit: Maximum number of extractions to return (1-100)
    - offset: Number of extractions to skip

    Returns extractions sorted by creation date (newest first).
    """
    try:
        extractions = db.list_extractions(limit=limit, offset=offset)
        return {
            "extractions": [e.to_dict() for e in extractions],
            "count": len(extractions),
            "offset": offset,
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing extractions: {str(e)}")


@router.get("/extractions/{extraction_id}")
async def get_extraction(extraction_id: str) -> Dict[str, Any]:
    """
    Get details of a specific extraction by ID.

    Returns:
    - Extraction data including extraction_id, input text, structured data, schema, and metadata
    """
    extraction = db.get_extraction(extraction_id)
    if not extraction:
        raise HTTPException(
            status_code=404,
            detail=f"Extraction with ID {extraction_id} not found"
        )

    return extraction.to_dict()


@router.get("/transcriptions/{transcription_id}/extractions")
async def list_extractions_by_transcription(transcription_id: str) -> Dict[str, Any]:
    """
    Get all extractions for a specific transcription.

    Returns:
    - List of extractions for this transcription, sorted by creation date (newest first)
    """
    # Check if transcription exists
    transcription = db.get_transcription(transcription_id)
    if not transcription:
        raise HTTPException(
            status_code=404,
            detail=f"Transcription with ID {transcription_id} not found"
        )

    extractions = db.list_extractions_by_transcription(transcription_id)
    return {
        "transcription_id": transcription_id,
        "extractions": [e.to_dict() for e in extractions],
        "count": len(extractions)
    }


# ========== Utility Endpoints ==========

@router.get("/stats")
async def get_database_stats() -> Dict[str, Any]:
    """
    Get database statistics.

    Returns:
    - Count of audio files, transcriptions, and extractions in the database
    """
    return db.get_stats()


@router.delete("/clear")
async def clear_database() -> Dict[str, str]:
    """
    Clear all data from the SQLite database.

    WARNING: This will delete all stored data. Use with caution!
    This only clears the database, not the file-based logs.
    """
    db.clear_all()
    return {"message": "Database cleared successfully"}
