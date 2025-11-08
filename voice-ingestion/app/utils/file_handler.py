import os
from fastapi import UploadFile, HTTPException
from app.config import settings


class FileHandler:
    """Utility class for handling file operations."""

    @staticmethod
    def validate_audio_file(file: UploadFile) -> tuple[str, str]:
        """
        Validate an uploaded audio file.

        Args:
            file: The uploaded file

        Returns:
            Tuple of (filename, file_extension)

        Raises:
            HTTPException: If validation fails
        """
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")

        # Get file extension
        _, file_extension = os.path.splitext(file.filename)
        file_extension = file_extension.lower()

        # Validate file extension
        if file_extension not in settings.ALLOWED_AUDIO_FORMATS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file format. Allowed formats: {', '.join(settings.ALLOWED_AUDIO_FORMATS)}"
            )

        return file.filename, file_extension

    @staticmethod
    async def read_upload_file(file: UploadFile) -> bytes:
        """
        Read and validate the size of an uploaded file.

        Args:
            file: The uploaded file

        Returns:
            The file contents as bytes

        Raises:
            HTTPException: If file is too large
        """
        # Read file contents
        contents = await file.read()

        # Validate file size
        if len(contents) > settings.MAX_FILE_SIZE:
            max_size_mb = settings.MAX_FILE_SIZE / (1024 * 1024)
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {max_size_mb}MB"
            )

        if len(contents) == 0:
            raise HTTPException(status_code=400, detail="Empty file")

        return contents

    @staticmethod
    def get_file_size_mb(size_bytes: int) -> float:
        """
        Convert bytes to megabytes.

        Args:
            size_bytes: Size in bytes

        Returns:
            Size in megabytes (rounded to 2 decimals)
        """
        return round(size_bytes / (1024 * 1024), 2)


# Create a singleton instance
file_handler = FileHandler()
