from fastapi import APIRouter, HTTPException
from app.models.requests import StructuredDataRequest
from app.models.responses import StructuredDataResponse, ErrorResponse
from app.models.database import StructuredExtraction
from app.services.logging_service import logging_service
from app.services.openai_service import openai_service
from app.services.database_service import db

router = APIRouter()


@router.post(
    "/extract-data",
    response_model=StructuredDataResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}}
)
async def extract_structured_data(request: StructuredDataRequest):
    """
    Extract structured data from text using GPT-4o-mini with function calling.

    Requires:
    - text: The text to extract data from
    - schema: JSON schema defining the output structure
    - system_prompt: Optional system prompt to guide extraction

    Returns structured JSON data matching the provided schema.
    """
    try:
        # Validate schema
        if not request.json_schema:
            raise HTTPException(status_code=400, detail="Schema is required")

        if "type" not in request.json_schema:
            raise HTTPException(
                status_code=400,
                detail="Schema must include a 'type' field"
            )

        # Extract structured data
        result = openai_service.extract_structured_data(
            text=request.text,
            schema=request.json_schema,
            system_prompt=request.system_prompt
        )

        # Log the extraction
        log_id = logging_service.log_structured_output(
            text=request.text,
            schema=request.json_schema,
            system_prompt=request.system_prompt or "",
            structured_data=result["structured_data"],
            metadata=result["metadata"]
        )

        # Store in database
        extraction = StructuredExtraction(
            extraction_id=log_id,
            transcription_id=None,  # Not linked to a specific transcription in this flow
            input_text=request.text,
            structured_data=result["structured_data"],
            json_schema=request.json_schema,
            system_prompt=request.system_prompt,
            model=result["metadata"].get("model", "gpt-4o-mini"),
            prompt_tokens=result["metadata"].get("usage", {}).get("prompt_tokens"),
            completion_tokens=result["metadata"].get("usage", {}).get("completion_tokens"),
            total_tokens=result["metadata"].get("usage", {}).get("total_tokens"),
            finish_reason=result["metadata"].get("finish_reason")
        )
        db.add_extraction(extraction)

        return StructuredDataResponse(
            structured_data=result["structured_data"],
            log_id=log_id,
            metadata=result["metadata"]
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error extracting structured data: {str(e)}"
        )
