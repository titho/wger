from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings

# Initialize FastAPI app
app = FastAPI(
    title="Voice Ingestion Service",
    description="Transform voice recordings into structured data through a three-phase pipeline",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    # Validate settings
    settings.validate()

    # Create log directories
    import os
    os.makedirs(settings.AUDIO_LOG_DIR, exist_ok=True)
    os.makedirs(settings.TRANSCRIPTION_LOG_DIR, exist_ok=True)
    os.makedirs(settings.STRUCTURED_OUTPUT_LOG_DIR, exist_ok=True)

    # Initialize database
    from app.services.database_service import db
    db.create_tables()

    print(f"✅ Voice Ingestion Service started")
    print(f"📁 Log directories created")
    print(f"🗄️  SQLite database initialized")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "voice-ingestion-service",
        "version": "1.0.0"
    }


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Voice Ingestion Service API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "upload_audio": "/api/upload-audio",
            "transcribe": "/api/transcribe",
            "extract_data": "/api/extract-data",
            "exercise": {
                "resolve_exercise": "/api/resolve-exercise",
                "enrich_workout_log": "/api/enrich-workout-log",
                "get_exercise": "/api/exercises/{exercise_id}",
                "search_exercises": "/api/exercises/search/{query}"
            },
            "database": {
                "audio_files": "/api/db/audio-files",
                "transcriptions": "/api/db/transcriptions",
                "extractions": "/api/db/extractions",
                "stats": "/api/db/stats"
            }
        }
    }


# Import and include routers
from app.routes import audio, transcription, database, exercise
app.include_router(audio.router, prefix="/api", tags=["audio"])
app.include_router(transcription.router, prefix="/api", tags=["transcription"])
app.include_router(database.router, prefix="/api/db", tags=["database"])
app.include_router(exercise.router, prefix="/api", tags=["exercise"])
