import os
import tempfile
import logging
from typing import Dict, Any, Optional, Tuple

from extras.app.config import settings

logger = logging.getLogger(__name__)

# Cached Whisper model singleton
_WHISPER_MODEL = None
_WHISPER_INITIALIZATION_ATTEMPTED = False

def get_whisper_model():
    """Loads faster-whisper model lazily."""
    global _WHISPER_MODEL, _WHISPER_INITIALIZATION_ATTEMPTED
    if _WHISPER_INITIALIZATION_ATTEMPTED:
        return _WHISPER_MODEL

    _WHISPER_INITIALIZATION_ATTEMPTED = True
    try:
        from faster_whisper import WhisperModel
        logger.info(
            f"Loading faster-whisper model ({settings.WHISPER_MODEL_SIZE}) on device: {settings.WHISPER_DEVICE}..."
        )
        _WHISPER_MODEL = WhisperModel(
            settings.WHISPER_MODEL_SIZE,
            device=settings.WHISPER_DEVICE,
            compute_type=settings.WHISPER_COMPUTE_TYPE,
        )
        logger.info("faster-whisper model loaded successfully.")
    except Exception as e:
        logger.warning(f"Could not initialize faster-whisper model ({e}). Audio transcription will require mock or manual fallback.")
        _WHISPER_MODEL = None

    return _WHISPER_MODEL

class AudioTranscriptionService:
    """Handles audio file validation, conversion, transcription, and cleanup."""

    ALLOWED_EXTENSIONS = {".wav", ".mp3", ".m4a", ".webm"}

    def __init__(self, whisper_model=None):
        self._custom_model = whisper_model

    def validate_audio_file(self, filename: str, file_size: int) -> Tuple[bool, Optional[str]]:
        """Validates format and size of uploaded audio."""
        if not filename:
            return False, "Audio filename is required"

        ext = os.path.splitext(filename.lower())[1]
        if ext not in self.ALLOWED_EXTENSIONS:
            return False, f"Unsupported audio format '{ext}'. Supported formats: WAV, MP3, M4A, WEBM"

        if file_size <= 0:
            return False, "Uploaded audio file is empty (0 bytes)"

        if file_size > settings.MAX_AUDIO_SIZE_BYTES:
            max_mb = settings.MAX_AUDIO_SIZE_BYTES // (1024 * 1024)
            return False, f"Audio file exceeds maximum allowed limit of {max_mb} MB"

        return True, None

    async def transcribe_audio(
        self,
        audio_bytes: bytes,
        filename: str,
        language: str = "auto",
    ) -> Dict[str, Any]:
        """
        Transcribes audio bytes safely using temporary file, deleting it immediately afterwards.
        Returns dictionary with transcript, language, duration, and confidence.
        """
        is_valid, err_msg = self.validate_audio_file(filename, len(audio_bytes))
        if not is_valid:
            raise ValueError(err_msg)

        ext = os.path.splitext(filename.lower())[1]
        temp_path = None

        try:
            # Write to a secure temporary file
            with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
                tmp.write(audio_bytes)
                temp_path = tmp.name

            model = self._custom_model or get_whisper_model()
            if model is None:
                raise RuntimeError(
                    "Speech transcription model is currently unavailable on this host. Use JSON transcript mode."
                )

            # Transcribe
            lang_param = None if language in ("auto", "", None) else language
            segments, info = model.transcribe(
                temp_path,
                language=lang_param,
                beam_size=5,
                vad_filter=True,
            )

            transcript_segments = []
            segment_confidences = []
            for seg in segments:
                transcript_segments.append(seg.text.strip())
                # seg.avg_logprob can be used as proxy for confidence
                prob = max(0.1, min(1.0, 1.0 + (seg.avg_logprob / 5.0)))
                segment_confidences.append(prob)

            full_transcript = " ".join(transcript_segments).strip()
            if not full_transcript:
                full_transcript = "[No clear speech detected in recording]"

            avg_conf = (
                float(sum(segment_confidences) / len(segment_confidences))
                if segment_confidences
                else 0.85
            )

            return {
                "transcript": full_transcript,
                "language": info.language if hasattr(info, "language") else "en",
                "duration_seconds": round(float(info.duration), 2) if hasattr(info, "duration") else 0.0,
                "confidence": round(avg_conf, 2),
                "source": "audio",
            }

        finally:
            # Secure deletion of audio file immediately
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception as ex:
                    logger.warning(f"Failed to delete temp audio file {temp_path}: {ex}")

