"""
SQLite database service using SQLAlchemy for storing and querying audio files, transcriptions, and extractions.
"""
from typing import List, Optional, Dict, Any
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from app.models.database import Base, AudioFile, Transcription, StructuredExtraction
from app.config import settings
import os


class Database:
    """
    SQLite database service using SQLAlchemy.

    This is a singleton service that manages the database connection and provides
    CRUD operations for audio files, transcriptions, and structured extractions.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        # Create database directory if it doesn't exist
        db_dir = os.path.join(os.path.dirname(settings.LOG_DIR), "database")
        os.makedirs(db_dir, exist_ok=True)

        # SQLite database file path
        db_path = os.path.join(db_dir, "voice_ingestion.db")
        self.database_url = f"sqlite:///{db_path}"

        # Create engine
        self.engine = create_engine(
            self.database_url,
            connect_args={"check_same_thread": False},  # Needed for SQLite
            echo=False  # Set to True for SQL query debugging
        )

        # Create session factory
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

        self._initialized = True

    def create_tables(self):
        """Create all database tables."""
        Base.metadata.create_all(bind=self.engine)

    @contextmanager
    def get_session(self):
        """
        Context manager for database sessions.

        Usage:
            with db.get_session() as session:
                # do database operations
                pass
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    # ========== Audio File Operations ==========

    def add_audio_file(self, audio_file: AudioFile) -> None:
        """Add an audio file to the database."""
        with self.get_session() as session:
            session.add(audio_file)

    def get_audio_file(self, file_id: str) -> Optional[AudioFile]:
        """Get an audio file by ID."""
        with self.get_session() as session:
            audio_file = session.query(AudioFile).filter(AudioFile.file_id == file_id).first()
            if audio_file:
                # Detach from session to avoid lazy loading issues
                session.expunge(audio_file)
            return audio_file

    def list_audio_files(self, limit: Optional[int] = None, offset: int = 0) -> List[AudioFile]:
        """
        List all audio files, sorted by creation date (newest first).

        Args:
            limit: Maximum number of files to return
            offset: Number of files to skip

        Returns:
            List of audio files
        """
        with self.get_session() as session:
            query = session.query(AudioFile).order_by(AudioFile.created_at.desc())

            if offset:
                query = query.offset(offset)
            if limit:
                query = query.limit(limit)

            files = query.all()
            # Detach from session
            for file in files:
                session.expunge(file)
            return files

    def delete_audio_file(self, file_id: str) -> bool:
        """
        Delete an audio file from the database.

        Returns:
            True if file was deleted, False if not found
        """
        with self.get_session() as session:
            audio_file = session.query(AudioFile).filter(AudioFile.file_id == file_id).first()
            if audio_file:
                session.delete(audio_file)
                return True
            return False

    # ========== Transcription Operations ==========

    def add_transcription(self, transcription: Transcription) -> None:
        """Add a transcription to the database."""
        with self.get_session() as session:
            session.add(transcription)

    def get_transcription(self, transcription_id: str) -> Optional[Transcription]:
        """Get a transcription by ID."""
        with self.get_session() as session:
            transcription = session.query(Transcription).filter(
                Transcription.transcription_id == transcription_id
            ).first()
            if transcription:
                session.expunge(transcription)
            return transcription

    def list_transcriptions(self, limit: Optional[int] = None, offset: int = 0) -> List[Transcription]:
        """
        List all transcriptions, sorted by creation date (newest first).

        Args:
            limit: Maximum number of transcriptions to return
            offset: Number of transcriptions to skip

        Returns:
            List of transcriptions
        """
        with self.get_session() as session:
            query = session.query(Transcription).order_by(Transcription.created_at.desc())

            if offset:
                query = query.offset(offset)
            if limit:
                query = query.limit(limit)

            transcriptions = query.all()
            # Detach from session
            for t in transcriptions:
                session.expunge(t)
            return transcriptions

    def list_transcriptions_by_file(self, file_id: str) -> List[Transcription]:
        """
        Get all transcriptions for a specific audio file.

        Args:
            file_id: The audio file ID

        Returns:
            List of transcriptions for this file, sorted by creation date (newest first)
        """
        with self.get_session() as session:
            transcriptions = session.query(Transcription).filter(
                Transcription.file_id == file_id
            ).order_by(Transcription.created_at.desc()).all()

            # Detach from session
            for t in transcriptions:
                session.expunge(t)
            return transcriptions

    def delete_transcription(self, transcription_id: str) -> bool:
        """
        Delete a transcription from the database.

        Returns:
            True if transcription was deleted, False if not found
        """
        with self.get_session() as session:
            transcription = session.query(Transcription).filter(
                Transcription.transcription_id == transcription_id
            ).first()
            if transcription:
                session.delete(transcription)
                return True
            return False

    # ========== Structured Extraction Operations ==========

    def add_extraction(self, extraction: StructuredExtraction) -> None:
        """Add a structured extraction to the database."""
        with self.get_session() as session:
            session.add(extraction)

    def get_extraction(self, extraction_id: str) -> Optional[StructuredExtraction]:
        """Get a structured extraction by ID."""
        with self.get_session() as session:
            extraction = session.query(StructuredExtraction).filter(
                StructuredExtraction.extraction_id == extraction_id
            ).first()
            if extraction:
                session.expunge(extraction)
            return extraction

    def list_extractions(self, limit: Optional[int] = None, offset: int = 0) -> List[StructuredExtraction]:
        """
        List all extractions, sorted by creation date (newest first).

        Args:
            limit: Maximum number of extractions to return
            offset: Number of extractions to skip

        Returns:
            List of extractions
        """
        with self.get_session() as session:
            query = session.query(StructuredExtraction).order_by(StructuredExtraction.created_at.desc())

            if offset:
                query = query.offset(offset)
            if limit:
                query = query.limit(limit)

            extractions = query.all()
            # Detach from session
            for e in extractions:
                session.expunge(e)
            return extractions

    def list_extractions_by_transcription(self, transcription_id: str) -> List[StructuredExtraction]:
        """
        Get all extractions for a specific transcription.

        Args:
            transcription_id: The transcription ID

        Returns:
            List of extractions for this transcription, sorted by creation date (newest first)
        """
        with self.get_session() as session:
            extractions = session.query(StructuredExtraction).filter(
                StructuredExtraction.transcription_id == transcription_id
            ).order_by(StructuredExtraction.created_at.desc()).all()

            # Detach from session
            for e in extractions:
                session.expunge(e)
            return extractions

    def delete_extraction(self, extraction_id: str) -> bool:
        """
        Delete an extraction from the database.

        Returns:
            True if extraction was deleted, False if not found
        """
        with self.get_session() as session:
            extraction = session.query(StructuredExtraction).filter(
                StructuredExtraction.extraction_id == extraction_id
            ).first()
            if extraction:
                session.delete(extraction)
                return True
            return False

    # ========== Utility Operations ==========

    def get_stats(self) -> Dict[str, int]:
        """Get database statistics."""
        with self.get_session() as session:
            audio_files_count = session.query(func.count(AudioFile.file_id)).scalar()
            transcriptions_count = session.query(func.count(Transcription.transcription_id)).scalar()
            extractions_count = session.query(func.count(StructuredExtraction.extraction_id)).scalar()

            return {
                "audio_files": audio_files_count or 0,
                "transcriptions": transcriptions_count or 0,
                "extractions": extractions_count or 0
            }

    def clear_all(self) -> None:
        """Clear all data from the database. Use with caution!"""
        with self.get_session() as session:
            session.query(StructuredExtraction).delete()
            session.query(Transcription).delete()
            session.query(AudioFile).delete()


# Singleton instance
db = Database()
