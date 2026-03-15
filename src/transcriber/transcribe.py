"""Whisper model management and audio transcription."""

import os
import platform
import subprocess
from functools import lru_cache
from typing import Generator

from faster_whisper import WhisperModel


def _get_system_ram_gb() -> int:
    """Get total system RAM in GB."""
    if platform.system() == "Darwin":
        result = subprocess.check_output(
            ["sysctl", "-n", "hw.memsize"], text=True
        ).strip()
        return int(result) // (1024**3)
    # Fallback for Linux
    mem_bytes = os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES")
    return mem_bytes // (1024**3)


def get_model_size(requested: str | None = None) -> str:
    """Select model size based on available RAM.

    Args:
        requested: Explicit model size. If provided, bypasses auto-detection.

    Returns:
        Model size string for faster-whisper.
    """
    if requested:
        return requested
    ram_gb = _get_system_ram_gb()
    if ram_gb >= 16:
        return "large-v3"
    return "medium"


@lru_cache(maxsize=2)
def load_model(model_size: str) -> WhisperModel:
    """Load and cache a Whisper model.

    Args:
        model_size: Model size string (e.g. "medium", "large-v3").

    Returns:
        Loaded WhisperModel instance.
    """
    return WhisperModel(model_size, device="cpu", compute_type="int8")


def transcribe_audio(
    file_path: str,
    language: str = "hu",
    model_size: str | None = None,
) -> Generator[dict, None, None]:
    """Transcribe an audio file, yielding segments as they complete.

    Args:
        file_path: Path to the audio file.
        language: Language code for transcription.
        model_size: Explicit model size, or None for auto-detection.

    Yields:
        Dict with keys: text, start, end, and duration (first segment only).
    """
    size = get_model_size(model_size)
    model = load_model(size)
    segments, info = model.transcribe(file_path, language=language, beam_size=5)

    first = True
    for segment in segments:
        result = {
            "text": segment.text,
            "start": segment.start,
            "end": segment.end,
        }
        if first:
            result["duration"] = info.duration
            first = False
        yield result
