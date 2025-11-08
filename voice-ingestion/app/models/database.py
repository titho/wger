"""
SQLAlchemy database models for storing audio files, transcriptions, and extractions.
"""
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import Column, String, Integer, Float, Text, DateTime, JSON, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class AudioFile(Base):
    """Represents an uploaded audio file."""
    __tablename__ = "audio_files"

    file_id = Column(String, primary_key=True)
    filename = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    file_extension = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    transcriptions = relationship("Transcription", back_populates="audio_file", cascade="all, delete-orphan")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "file_id": self.file_id,
            "filename": self.filename,
            "file_size": self.file_size,
            "file_extension": self.file_extension,
            "file_path": self.file_path,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class Transcription(Base):
    """Represents a transcription of an audio file."""
    __tablename__ = "transcriptions"

    transcription_id = Column(String, primary_key=True)
    file_id = Column(String, ForeignKey("audio_files.file_id"), nullable=False)
    transcription_text = Column(Text, nullable=False)
    prompt = Column(Text, nullable=True)
    language = Column(String, nullable=True)
    duration = Column(Float, nullable=True)
    model = Column(String, default="whisper-1", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    audio_file = relationship("AudioFile", back_populates="transcriptions")
    extractions = relationship("StructuredExtraction", back_populates="transcription", cascade="all, delete-orphan")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "transcription_id": self.transcription_id,
            "file_id": self.file_id,
            "transcription_text": self.transcription_text,
            "prompt": self.prompt,
            "language": self.language,
            "duration": self.duration,
            "model": self.model,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class StructuredExtraction(Base):
    """Represents structured data extracted from a transcription."""
    __tablename__ = "structured_extractions"

    extraction_id = Column(String, primary_key=True)
    transcription_id = Column(String, ForeignKey("transcriptions.transcription_id"), nullable=True)
    input_text = Column(Text, nullable=False)
    structured_data = Column(JSON, nullable=False)
    json_schema = Column(JSON, nullable=False)
    system_prompt = Column(Text, nullable=True)
    model = Column(String, default="gpt-4o-mini", nullable=False)
    prompt_tokens = Column(Integer, nullable=True)
    completion_tokens = Column(Integer, nullable=True)
    total_tokens = Column(Integer, nullable=True)
    finish_reason = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    transcription = relationship("Transcription", back_populates="extractions")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "extraction_id": self.extraction_id,
            "transcription_id": self.transcription_id,
            "input_text": self.input_text,
            "structured_data": self.structured_data,
            "json_schema": self.json_schema,
            "system_prompt": self.system_prompt,
            "model": self.model,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "finish_reason": self.finish_reason,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
