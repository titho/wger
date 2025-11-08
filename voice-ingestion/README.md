# Voice Ingestion Backend

FastAPI backend for the voice ingestion service with OpenAI Whisper and GPT-4o-mini integration.

## Features

- **Audio Upload**: Upload audio files (mp3, wav, m4a, webm) up to 25MB
- **Whisper Transcription**: Convert voice to text using OpenAI Whisper
- **Structured Data Extraction**: Extract structured JSON from text using GPT-4o-mini with function calling
- **Comprehensive Logging**: All requests, responses, and files are logged to the `/logs` directory
- **CORS Support**: Configured for frontend integration

## Setup

### 1. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

Copy the example environment file and add your OpenAI API key:

```bash
cp .env.example .env
```

Edit `.env` and add your API key:
```
OPENAI_API_KEY=sk-your-actual-api-key-here
```

### 4. Run the Server

```bash
uvicorn app.main:app --reload --port 8000
```

Or from the project root:
```bash
cd backend
./venv/bin/uvicorn app.main:app --reload --port 8000
```

The server will start at `http://localhost:8000`

## API Endpoints

### Health Check
```
GET /health
```
Returns server health status.

### Root
```
GET /
```
Returns API information and available endpoints.

### Upload Audio
```
POST /api/upload-audio
Content-Type: multipart/form-data

Parameters:
- file: Audio file (mp3, wav, m4a, webm)

Returns:
- file_id: Unique identifier for the uploaded file
- filename: Original filename
- file_size: Size in bytes
- file_extension: File extension
```

### Transcribe Audio
```
POST /api/transcribe
Content-Type: application/x-www-form-urlencoded

Parameters:
- file_id: The ID of a previously uploaded audio file
- prompt: (Optional) Prompt to guide transcription

Returns:
- transcription: The transcribed text
- file_id: The audio file ID
- log_id: Log entry ID
- metadata: Transcription metadata (language, duration, model)
```

### Extract Structured Data
```
POST /api/extract-data
Content-Type: application/json

Body:
{
  "text": "John Doe, email: john@example.com, phone: 555-1234",
  "json_schema": {
    "type": "object",
    "properties": {
      "name": {"type": "string"},
      "email": {"type": "string"},
      "phone": {"type": "string"}
    },
    "required": ["name"]
  },
  "system_prompt": "Extract contact information" // Optional
}

Returns:
- structured_data: Extracted data matching the schema
- log_id: Log entry ID
- metadata: Extraction metadata (model, tokens used)
```

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app & routes
│   ├── config.py            # Configuration settings
│   ├── routes/
│   │   ├── audio.py         # Audio upload/transcription routes
│   │   └── transcription.py # Data extraction routes
│   ├── services/
│   │   ├── openai_service.py    # OpenAI API integration
│   │   └── logging_service.py   # Logging utilities
│   ├── models/
│   │   ├── requests.py      # Pydantic request models
│   │   └── responses.py     # Pydantic response models
│   └── utils/
│       └── file_handler.py  # File validation utilities
├── requirements.txt
├── .env.example
└── README.md
```

## Logging

All requests and responses are logged to `../logs/`:
- `logs/audio/` - Uploaded audio files and metadata
- `logs/transcriptions/` - Transcription requests/responses
- `logs/structured_outputs/` - Data extraction requests/responses

Each log file includes:
- Timestamp (ISO format)
- Unique ID
- Request parameters
- Response data
- Metadata (model used, tokens, etc.)

## Development

### Interactive API Docs

FastAPI provides automatic interactive documentation:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Testing with cURL

**Upload Audio:**
```bash
curl -X POST "http://localhost:8000/api/upload-audio" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/audio.mp3"
```

**Transcribe:**
```bash
curl -X POST "http://localhost:8000/api/transcribe" \
  -H "accept: application/json" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "file_id=<file-id-from-upload>&prompt=Transcribe accurately"
```

**Extract Data:**
```bash
curl -X POST "http://localhost:8000/api/extract-data" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "John Doe, email: john@example.com",
    "json_schema": {
      "type": "object",
      "properties": {
        "name": {"type": "string"},
        "email": {"type": "string"}
      }
    }
  }'
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | Required |
| `BACKEND_PORT` | Server port | 8000 |
| `CORS_ORIGINS` | Allowed CORS origins | `http://localhost:3000,http://127.0.0.1:3000` |

## Error Handling

The API returns standardized error responses:

```json
{
  "error": "error_type",
  "message": "Human-readable error message",
  "detail": "Additional details (optional)"
}
```

Common HTTP status codes:
- `200` - Success
- `400` - Bad Request (invalid input)
- `404` - Not Found (file_id not found)
- `500` - Internal Server Error

## Models Used

- **Whisper**: `whisper-1` (OpenAI Whisper for transcription)
- **GPT**: `gpt-4o-mini` (GPT-4o-mini for structured extraction)

## License

MIT
