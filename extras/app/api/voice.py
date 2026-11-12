import logging
import json
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File, Form, status
from sqlalchemy.orm import Session

from extras.app.database.session import get_db
from extras.app.schemas.models import (
    VoiceAnalyzeRequest,
    VoiceAnalyzeResponse,
)
from extras.app.analyzers.voice_analyzer import VoiceAnalyzer
from extras.app.services.transcription import AudioTranscriptionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ext", tags=["Voice"])

voice_analyzer = VoiceAnalyzer()
transcription_service = AudioTranscriptionService()

@router.post("/analyze/voice", response_model=VoiceAnalyzeResponse)
async def analyze_voice_endpoint(
    request: Request,
    db: Session = Depends(get_db),
) -> VoiceAnalyzeResponse:
    """
    Analyzes phone call audio or transcript for spoken social engineering,
    digital arrest coercion, bank impersonation, and credential fraud.
    Supports both:
      1. Multipart/form-data audio file upload ('audio' file field).
      2. Application/json transcript payload ('transcript' string field).
    """
    content_type = request.headers.get("content-type", "")

    # Mode A: Multipart / Audio Upload
    if "multipart/form-data" in content_type:
        try:
            form = await request.form()
            audio_upload = form.get("audio")
            language = str(form.get("language", "auto"))

            if not audio_upload or not hasattr(audio_upload, "read"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Multipart request must include an 'audio' file upload field.",
                )

            filename = getattr(audio_upload, "filename", "recording.wav")
            audio_bytes = await audio_upload.read()

            logger.info(f"Received audio upload '{filename}' ({len(audio_bytes)} bytes)")

            # Transcribe audio using faster-whisper service
            transcription_result = await transcription_service.transcribe_audio(
                audio_bytes=audio_bytes,
                filename=filename,
                language=language,
            )

            transcript_text = transcription_result["transcript"]

            # Run voice scam analysis on transcribed text
            result = await voice_analyzer.analyze(
                transcript=transcript_text,
                transcription_meta=transcription_result,
                db=db,
            )
            return result

        except ValueError as ve:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
        except RuntimeError as re:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(re))
        except Exception as e:
            logger.exception("Error during audio transcription analysis: %s", e)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Audio analysis failed: {str(e)}")

    # Mode B: JSON Transcript Input
    else:
        try:
            body = await request.json()
            payload = VoiceAnalyzeRequest(**body)

            logger.info(f"Analyzing direct call transcript (len={len(payload.transcript)} chars)...")

            transcription_meta = {
                "language": payload.language,
                "duration_seconds": None,
                "confidence": 1.0,
                "source": "transcript",
            }

            result = await voice_analyzer.analyze(
                transcript=payload.transcript,
                transcription_meta=transcription_meta,
                db=db,
            )
            return result

        except Exception as e:
            logger.warning(f"Error parsing voice transcript JSON: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid transcript request: {str(e)}",
            )

