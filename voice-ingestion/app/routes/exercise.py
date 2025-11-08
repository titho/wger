"""Exercise resolution API endpoints."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

from app.services.exercise_resolver_service import exercise_resolver

router = APIRouter()


class ResolveExerciseRequest(BaseModel):
    """Request model for exercise resolution."""
    exercise_name: str = Field(..., description="User-provided exercise name to resolve")
    candidate_count: Optional[int] = Field(
        7,
        description="Number of candidates to present to LLM",
        ge=3,
        le=15
    )


class ResolveExerciseResponse(BaseModel):
    """Response model for exercise resolution."""
    success: bool
    exercise_id: Optional[str] = None
    exercise_name: Optional[str] = None
    exercise_details: Optional[Dict[str, Any]] = None
    resolution_method: str
    confidence_score: float
    candidates_count: int = 0
    user_input: str
    error: Optional[str] = None
    timestamp_iso: str


class EnrichedWorkoutLogRequest(BaseModel):
    """Request model for workout logging with exercise resolution."""
    action: str = Field(..., description="Action type (e.g., 'log_set')")
    exercise_name: str = Field(..., description="Exercise name from transcription")
    sets: List[Dict[str, Any]] = Field(..., description="List of sets with reps/weight")
    set_count: int
    pre_parsed_message: Optional[str] = None


class EnrichedWorkoutLogResponse(BaseModel):
    """Response model for enriched workout log with resolved exercise."""
    action: str
    exercise_id: Optional[str]
    exercise_name: Optional[str]
    exercise_details: Optional[Dict[str, Any]] = None
    sets: List[Dict[str, Any]]
    set_count: int
    pre_parsed_message: Optional[str]
    used_fallback: bool
    resolution_method: str
    confidence_score: float
    timestamp_iso: str
    error: Optional[str] = None


@router.post("/resolve-exercise", response_model=ResolveExerciseResponse)
async def resolve_exercise(request: ResolveExerciseRequest):
    """
    Resolve an exercise name to its ID using LLM with candidate selection.

    This endpoint:
    1. Uses fuzzy matching and alias lookup to find 5-10 candidate exercises
    2. Sends candidates to LLM to select the best match
    3. Returns the resolved exercise with details and confidence score
    """
    try:
        # Resolve the exercise
        result = exercise_resolver.resolve_exercise(
            exercise_name=request.exercise_name,
            candidate_count=request.candidate_count
        )

        # Add timestamp
        result["timestamp_iso"] = datetime.utcnow().isoformat() + "Z"
        result["user_input"] = request.exercise_name

        return result

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error resolving exercise: {str(e)}"
        )


@router.post("/enrich-workout-log", response_model=EnrichedWorkoutLogResponse)
async def enrich_workout_log(request: EnrichedWorkoutLogRequest):
    """
    Enrich a workout log entry with resolved exercise ID.

    This endpoint takes structured workout data (from Phase 2) and enriches it
    with the resolved exercise ID by calling the exercise resolver.
    """
    try:
        # Resolve the exercise
        resolution = exercise_resolver.resolve_exercise(
            exercise_name=request.exercise_name,
            candidate_count=7
        )

        # Build enriched response
        response = EnrichedWorkoutLogResponse(
            action=request.action,
            exercise_id=resolution.get("exercise_id"),
            exercise_name=resolution.get("exercise_name"),
            exercise_details=resolution.get("exercise_details"),
            sets=request.sets,
            set_count=request.set_count,
            pre_parsed_message=request.pre_parsed_message,
            used_fallback=(resolution.get("resolution_method") == "llm_match"),
            resolution_method=resolution.get("resolution_method", "unknown"),
            confidence_score=resolution.get("confidence_score", 0.0),
            timestamp_iso=datetime.utcnow().isoformat() + "Z",
            error=resolution.get("error") if not resolution.get("success") else None
        )

        return response

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error enriching workout log: {str(e)}"
        )


@router.get("/exercises/{exercise_id}")
async def get_exercise_details(exercise_id: str):
    """
    Get detailed information about a specific exercise by ID.
    """
    try:
        if exercise_id not in exercise_resolver.exercises_by_id:
            raise HTTPException(
                status_code=404,
                detail=f"Exercise with ID '{exercise_id}' not found"
            )

        exercise = exercise_resolver.exercises_by_id[exercise_id]
        return {
            "success": True,
            "exercise": exercise
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching exercise: {str(e)}"
        )


@router.get("/exercises/search/{query}")
async def search_exercises(query: str, limit: int = 10):
    """
    Search for exercises by name using fuzzy matching.

    Returns a list of matching exercises sorted by relevance.
    """
    try:
        from rapidfuzz import fuzz, process

        # Build search corpus
        search_corpus = {
            ex["name"].lower(): ex
            for ex in exercise_resolver.exercises
        }

        # Find matches
        matches = process.extract(
            query.lower(),
            search_corpus.keys(),
            scorer=fuzz.WRatio,
            limit=limit,
            score_cutoff=50
        )

        # Format results
        results = [
            {
                "exercise": search_corpus[match[0]],
                "similarity_score": match[1] / 100.0
            }
            for match in matches
        ]

        return {
            "success": True,
            "query": query,
            "results": results,
            "count": len(results)
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error searching exercises: {str(e)}"
        )

@router.post("/exercises/candidates")
async def get_candidate_exercises(request: ResolveExerciseRequest):
    """
    Get a list of candidate exercises for a given exercise name.
    """
    try:
        return {
            "success": True,
            "candidates": exercise_resolver._select_candidates(request.exercise_name, request.candidate_count)
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting candidate exercises: {str(e)}"
        )