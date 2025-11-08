"""Service for resolving exercise names to IDs using LLM with candidate selection."""

import json
from typing import Dict, List, Any, Optional
from pathlib import Path
from rapidfuzz import fuzz, process
from openai import OpenAI
from app.config import settings


class ExerciseResolverService:
    """
    Resolves user-provided exercise names to exercise IDs.

    Strategy:
    1. Use fuzzy matching + alias lookups to find 5-10 best candidates
    2. Send candidates to LLM to pick the best match
    3. Return structured result with exercise details
    """

    def __init__(self):
        """Initialize the resolver with database and OpenAI client."""
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.alias_index: Dict[str, List[str]] = {}
        self.exercises: List[Dict[str, Any]] = []
        self.exercises_by_id: Dict[str, Dict[str, Any]] = {}
        self._load_databases()

    def _load_databases(self):
        """Load alias index and exercises database from JSON files."""
        try:
            # Get database paths relative to backend directory
            db_path = Path(__file__).parent.parent.parent.parent / "database"

            # Load alias index
            alias_path = db_path / "alias_index.json"
            with open(alias_path, "r", encoding="utf-8") as f:
                self.alias_index = json.load(f)

            # Load exercises
            exercises_path = db_path / "exercises.json"
            with open(exercises_path, "r", encoding="utf-8") as f:
                self.exercises = json.load(f)

            # Create ID lookup dictionary
            self.exercises_by_id = {
                ex["exerciseId"]: ex for ex in self.exercises
            }

            print(f"✅ Loaded {len(self.alias_index)} aliases and {len(self.exercises)} exercises")

        except Exception as e:
            print(f"❌ Error loading exercise databases: {str(e)}")
            raise

    def _normalize_name(self, name: str) -> str:
        """Normalize exercise name for matching."""
        return name.lower().strip()

    def _get_candidates_from_aliases(self, exercise_name: str) -> List[str]:
        """Get exercise IDs from alias index."""
        normalized = self._normalize_name(exercise_name)
        return self.alias_index.get(normalized, [])

    def _get_candidates_from_fuzzy(
        self,
        exercise_name: str,
        limit: int = 10,
        score_threshold: int = 60
    ) -> List[tuple[str, float]]:
        """
        Get top candidates using fuzzy matching against all exercise names.

        Returns list of (exercise_id, score) tuples.
        """
        normalized = self._normalize_name(exercise_name)

        # Build search corpus: map exercise names to IDs
        search_corpus = {ex["name"].lower(): ex["exerciseId"] for ex in self.exercises}

        # Use rapidfuzz to find best matches
        matches = process.extract(
            normalized,
            search_corpus.keys(),
            scorer=fuzz.WRatio,
            limit=limit,
            score_cutoff=score_threshold
        )

        # Convert to (exercise_id, score) format
        candidates = [
            (search_corpus[match[0]], match[1] / 100.0)  # Normalize score to 0-1
            for match in matches
        ]

        return candidates

    
    def _select_candidates(
        self,
        exercise_name: str,
        target_count: int = 7
    ) -> List[Dict[str, Any]]:
        """
        Select top candidates using both aliases and fuzzy matching.

        Returns list of exercise detail dictionaries.
        """
        candidate_ids = set()

        # First, check aliases for exact/close matches
        alias_ids = self._get_candidates_from_aliases(exercise_name)
        candidate_ids.update(alias_ids)

        # Then add fuzzy matches until we have enough candidates
        fuzzy_matches = self._get_candidates_from_fuzzy(
            exercise_name,
            limit=target_count * 2,  # Get more than needed, then filter
            score_threshold=50  # Lower threshold to get more candidates
        )

        for ex_id, score in fuzzy_matches:
            candidate_ids.add(ex_id)
            if len(candidate_ids) >= target_count:
                break

        # Get full exercise details for each candidate
        candidates = []
        for ex_id in list(candidate_ids)[:target_count]:
            if ex_id in self.exercises_by_id:
                exercise = self.exercises_by_id[ex_id]
                candidates.append({
                    "exercise_id": exercise["exerciseId"],
                    "name": exercise["name"],
                    "equipment": ", ".join(exercise.get("equipments", [])),
                    "target_muscles": ", ".join(exercise.get("targetMuscles", [])),
                    "body_parts": ", ".join(exercise.get("bodyParts", []))
                })

        return candidates

    def _build_llm_prompt(
        self,
        user_input: str,
        candidates: List[Dict[str, Any]]
    ) -> str:
        """Build the prompt for LLM to select best exercise match."""
        candidates_text = "\n".join([
            f"{i+1}. ID: {c['exercise_id']}, Name: \"{c['name']}\", "
            f"Equipment: {c['equipment']}, Target: {c['target_muscles']}, "
            f"Body Parts: {c['body_parts']}"
            for i, c in enumerate(candidates)
        ])

        prompt = f"""You are an exercise matching expert. Given a user's exercise description and a list of possible matches, select the BEST matching exercise.

User input: "{user_input}"

Candidate exercises:
{candidates_text}

Instructions:
- Consider exercise name similarity carefully
- Consider equipment mentioned (if any) in the user input
- Consider movement pattern and muscle groups
- If the user input is ambiguous, choose the most common variation
- If no good match exists among the candidates, return null

Return ONLY the exercise_id of the best match (e.g., "641mIfk"), or null if no match is appropriate.
Do not include any explanation or additional text."""

        return prompt

    def resolve_exercise(
        self,
        exercise_name: str,
        candidate_count: int = 7
    ) -> Dict[str, Any]:
        """
        Resolve exercise name to ID using LLM with candidate selection.

        Args:
            exercise_name: User-provided exercise name
            candidate_count: Number of candidates to present to LLM

        Returns:
            Dictionary with resolution result including exercise_id, confidence, etc.
        """
        try:
            # Step 1: Get candidates
            candidates = self._select_candidates(exercise_name, candidate_count)

            if not candidates:
                return {
                    "success": False,
                    "error": "No matching exercises found in database",
                    "exercise_id": None,
                    "exercise_name": None,
                    "resolution_method": "none",
                    "confidence_score": 0.0,
                    "candidates_count": 0
                }

            # Step 2: Build prompt and call LLM
            prompt = self._build_llm_prompt(exercise_name, candidates)

            response = self.client.chat.completions.create(
                model=settings.GPT_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an exercise database expert. Return only the exercise_id or null."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,  # Low temperature for consistent results
                max_tokens=50
            )

            # Extract the exercise_id from response
            llm_response = response.choices[0].message.content.strip()

            # Handle null/none responses
            if llm_response.lower() in ["null", "none", ""]:
                return {
                    "success": False,
                    "error": "LLM could not find a suitable match",
                    "exercise_id": None,
                    "exercise_name": None,
                    "resolution_method": "llm_no_match",
                    "confidence_score": 0.0,
                    "candidates_count": len(candidates),
                    "llm_response": llm_response
                }

            # Clean up the response (remove quotes, etc.)
            exercise_id = llm_response.strip('"').strip("'").strip()

            # Validate the exercise_id exists
            if exercise_id not in self.exercises_by_id:
                return {
                    "success": False,
                    "error": f"LLM returned invalid exercise_id: {exercise_id}",
                    "exercise_id": None,
                    "exercise_name": None,
                    "resolution_method": "llm_invalid",
                    "confidence_score": 0.0,
                    "candidates_count": len(candidates),
                    "llm_response": llm_response
                }

            # Get full exercise details
            exercise = self.exercises_by_id[exercise_id]

            return {
                "success": True,
                "exercise_id": exercise_id,
                "exercise_name": exercise["name"],
                "exercise_details": {
                    "target_muscles": exercise.get("targetMuscles", []),
                    "body_parts": exercise.get("bodyParts", []),
                    "equipment": exercise.get("equipments", []),
                    "gif_url": exercise.get("gifUrl", "")
                },
                "resolution_method": "llm_match",
                "confidence_score": 0.85,  # Could be adjusted based on LLM confidence
                "candidates_count": len(candidates),
                "user_input": exercise_name
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Error resolving exercise: {str(e)}",
                "exercise_id": None,
                "exercise_name": None,
                "resolution_method": "error",
                "confidence_score": 0.0,
                "user_input": exercise_name
            }


# Create singleton instance
exercise_resolver = ExerciseResolverService()
