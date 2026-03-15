# Sugo Transcriber Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local, privacy-first audio transcription tool that runs in a browser, powered by faster-whisper, for Hungarian journalists.

**Architecture:** Python backend (FastAPI) serves a single-file HTML frontend. Audio files are uploaded via drag-and-drop, transcribed by faster-whisper using SSE for real-time progress, and the resulting text is displayed for copy-paste. A `.command` launcher enables double-click startup on macOS.

**Tech Stack:** Python 3.12+, uv, FastAPI, uvicorn, faster-whisper (CTranslate2), vanilla HTML/CSS/JS

---

## File Structure

```
transcriber/
├── pyproject.toml                  # uv project: dependencies, metadata, entry point
├── src/
│   └── transcriber/
│       ├── __init__.py             # Package init, version
│       ├── app.py                  # FastAPI app: routes, file upload, SSE endpoint, static serving
│       ├── transcribe.py           # Whisper model management: load model, transcribe audio, yield segments
│       └── static/
│           └── index.html          # Single-file frontend: all HTML, CSS, JS inlined
├── tests/
│   ├── __init__.py
│   ├── test_transcribe.py          # Unit tests for transcription logic
│   └── test_app.py                 # Integration tests for API endpoints
├── start.command                   # macOS double-click launcher
├── LICENSE                         # MIT
└── README.md                       # Setup + usage instructions
```

**Responsibilities:**

| File | Responsibility |
|------|---------------|
| `pyproject.toml` | Project metadata, dependencies, scripts |
| `transcribe.py` | Load/cache whisper model, transcribe a file path yielding segments, model selection by RAM |
| `app.py` | HTTP layer: upload endpoint, SSE streaming, serve static files, port selection |
| `index.html` | All UI: drag-drop, progress, text display, copy, i18n toggle, language selector |
| `start.command` | Bootstrap: install uv if needed, `uv run`, open browser |

---

## Chunk 1: Project Scaffold and Transcription Engine

### Task 1: Initialize uv project with dependencies

**Files:**
- Create: `pyproject.toml`
- Create: `src/transcriber/__init__.py`

- [ ] **Step 1: Create pyproject.toml**

```toml
[project]
name = "sugo-transcriber"
version = "0.1.0"
description = "Local, privacy-first audio transcription tool powered by Whisper"
readme = "README.md"
license = {text = "MIT"}
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.34.0",
    "faster-whisper>=1.1.0",
    "python-multipart>=0.0.20",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "httpx>=0.28.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/transcriber"]
```

- [ ] **Step 2: Create package init**

```python
# src/transcriber/__init__.py
__version__ = "0.1.0"
```

- [ ] **Step 3: Create test init**

```python
# tests/__init__.py
```

- [ ] **Step 4: Verify uv can resolve dependencies**

Run: `uv sync --dev`
Expected: Dependencies resolve and install successfully.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml src/transcriber/__init__.py tests/__init__.py uv.lock
git commit -m "feat: initialize uv project with dependencies"
```

---

### Task 2: Build transcription engine

**Files:**
- Create: `src/transcriber/transcribe.py`
- Create: `tests/test_transcribe.py`

- [ ] **Step 1: Write failing tests for transcription module**

```python
# tests/test_transcribe.py
import pytest
from unittest.mock import patch, MagicMock
from transcriber.transcribe import get_model_size, transcribe_audio, load_model


class TestGetModelSize:
    """Test model selection based on available RAM."""

    def test_returns_medium_for_8gb(self):
        with patch("transcriber.transcribe._get_system_ram_gb", return_value=8):
            assert get_model_size() == "medium"

    def test_returns_large_for_16gb(self):
        with patch("transcriber.transcribe._get_system_ram_gb", return_value=16):
            assert get_model_size() == "large-v3"

    def test_returns_medium_for_low_ram(self):
        with patch("transcriber.transcribe._get_system_ram_gb", return_value=4):
            assert get_model_size() == "medium"

    def test_explicit_model_overrides_auto(self):
        # When a model is explicitly requested, RAM detection is bypassed
        with patch("transcriber.transcribe._get_system_ram_gb", return_value=8):
            assert get_model_size(requested="large-v3") == "large-v3"


class TestLoadModel:
    """Test model loading and caching."""

    @patch("transcriber.transcribe.WhisperModel")
    def test_load_model_returns_whisper_model(self, mock_cls):
        mock_instance = MagicMock()
        mock_cls.return_value = mock_instance
        model = load_model("medium")
        mock_cls.assert_called_once_with("medium", device="cpu", compute_type="int8")
        assert model is mock_instance

    @patch("transcriber.transcribe.WhisperModel")
    def test_load_model_caches_by_size(self, mock_cls):
        mock_cls.return_value = MagicMock()
        # Clear any cached state
        load_model.cache_clear()
        m1 = load_model("medium")
        m2 = load_model("medium")
        assert m1 is m2
        assert mock_cls.call_count == 1


class TestTranscribeAudio:
    """Test transcription yielding segments."""

    @patch("transcriber.transcribe.load_model")
    def test_yields_segments_with_text(self, mock_load):
        mock_model = MagicMock()
        mock_segment_1 = MagicMock()
        mock_segment_1.text = "Helló világ"
        mock_segment_1.start = 0.0
        mock_segment_1.end = 2.5
        mock_segment_2 = MagicMock()
        mock_segment_2.text = " ez egy teszt"
        mock_segment_2.start = 2.5
        mock_segment_2.end = 5.0
        mock_info = MagicMock()
        mock_info.duration = 5.0
        mock_model.transcribe.return_value = (
            iter([mock_segment_1, mock_segment_2]),
            mock_info,
        )
        mock_load.return_value = mock_model

        segments = list(transcribe_audio("/fake/path.m4a", language="hu"))

        assert len(segments) == 2
        assert segments[0]["text"] == "Helló világ"
        assert segments[0]["start"] == 0.0
        assert segments[0]["end"] == 2.5
        assert segments[1]["text"] == " ez egy teszt"
        mock_model.transcribe.assert_called_once_with(
            "/fake/path.m4a", language="hu", beam_size=5
        )

    @patch("transcriber.transcribe.load_model")
    def test_includes_duration_in_first_segment(self, mock_load):
        mock_model = MagicMock()
        mock_segment = MagicMock()
        mock_segment.text = "Teszt"
        mock_segment.start = 0.0
        mock_segment.end = 1.0
        mock_info = MagicMock()
        mock_info.duration = 60.0
        mock_model.transcribe.return_value = (iter([mock_segment]), mock_info)
        mock_load.return_value = mock_model

        segments = list(transcribe_audio("/fake/path.m4a", language="hu"))

        assert segments[0]["duration"] == 60.0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_transcribe.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'transcriber.transcribe'`

- [ ] **Step 3: Implement transcription module**

```python
# src/transcriber/transcribe.py
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_transcribe.py -v`
Expected: All 6 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/transcriber/transcribe.py tests/test_transcribe.py
git commit -m "feat: add transcription engine with model auto-selection"
```

---

## Chunk 2: FastAPI Backend

### Task 3: Build FastAPI app with upload and SSE endpoints

**Files:**
- Create: `src/transcriber/app.py`
- Create: `tests/test_app.py`

- [ ] **Step 1: Write failing tests for API endpoints**

```python
# tests/test_app.py
import io
import json
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from transcriber.app import create_app


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


class TestHealthEndpoint:
    def test_health_returns_ok(self, client):
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


class TestIndexRoute:
    def test_root_serves_html(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]


class TestUploadAndTranscribe:
    @patch("transcriber.app.transcribe_audio")
    def test_upload_returns_sse_stream(self, mock_transcribe, client):
        mock_transcribe.return_value = iter([
            {"text": "Helló", "start": 0.0, "end": 1.0, "duration": 5.0},
            {"text": " világ", "start": 1.0, "end": 2.0},
        ])

        audio_content = b"fake audio content"
        response = client.post(
            "/api/transcribe",
            files={"file": ("test.m4a", io.BytesIO(audio_content), "audio/mp4")},
            data={"language": "hu"},
        )

        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]

        # Parse SSE events
        events = []
        for line in response.text.strip().split("\n"):
            if line.startswith("data: "):
                events.append(json.loads(line[6:]))

        assert len(events) >= 2
        assert events[0]["text"] == "Helló"
        assert events[0]["duration"] == 5.0
        assert events[1]["text"] == " világ"

    def test_upload_rejects_unsupported_format(self, client):
        response = client.post(
            "/api/transcribe",
            files={"file": ("test.exe", io.BytesIO(b"not audio"), "application/octet-stream")},
            data={"language": "hu"},
        )
        assert response.status_code == 400

    @patch("transcriber.app.transcribe_audio")
    def test_upload_cleans_up_temp_file(self, mock_transcribe, client):
        mock_transcribe.return_value = iter([
            {"text": "Test", "start": 0.0, "end": 1.0, "duration": 1.0},
        ])

        response = client.post(
            "/api/transcribe",
            files={"file": ("test.m4a", io.BytesIO(b"fake"), "audio/mp4")},
            data={"language": "hu"},
        )

        assert response.status_code == 200
        # Verify the temp file path passed to transcribe_audio no longer exists
        call_args = mock_transcribe.call_args
        temp_path = call_args[0][0]
        import os
        assert not os.path.exists(temp_path)


class TestModelStatusEndpoint:
    @patch("transcriber.app.get_model_size")
    def test_model_status_returns_info(self, mock_size, client):
        mock_size.return_value = "medium"
        response = client.get("/api/model-status")
        assert response.status_code == 200
        data = response.json()
        assert data["model_size"] == "medium"


class TestLoadModelEndpoint:
    @patch("transcriber.app.load_model")
    @patch("transcriber.app.get_model_size")
    def test_load_model_success(self, mock_size, mock_load, client):
        mock_size.return_value = "medium"
        mock_load.return_value = MagicMock()
        response = client.post("/api/load-model")
        assert response.status_code == 200
        assert response.json()["status"] == "ready"

    @patch("transcriber.app.load_model")
    @patch("transcriber.app.get_model_size")
    def test_load_model_failure(self, mock_size, mock_load, client):
        mock_size.return_value = "medium"
        mock_load.side_effect = RuntimeError("Download failed")
        response = client.post("/api/load-model")
        assert response.status_code == 500
        assert response.json()["status"] == "error"


class TestTranscribeErrorHandling:
    @patch("transcriber.app.transcribe_audio")
    def test_sse_emits_error_on_failure(self, mock_transcribe, client):
        mock_transcribe.side_effect = RuntimeError("Transcription failed")

        response = client.post(
            "/api/transcribe",
            files={"file": ("test.m4a", io.BytesIO(b"fake"), "audio/mp4")},
            data={"language": "hu"},
        )

        assert response.status_code == 200
        events = []
        for line in response.text.strip().split("\n"):
            if line.startswith("data: "):
                events.append(json.loads(line[6:]))
        assert any("error" in e for e in events)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_app.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'transcriber.app'`

- [ ] **Step 3: Implement FastAPI app**

```python
# src/transcriber/app.py
"""FastAPI application: routes, file upload, SSE streaming."""

import json
import os
import tempfile
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from transcriber.transcribe import transcribe_audio, get_model_size, load_model

ALLOWED_EXTENSIONS = {".m4a", ".mp3", ".wav", ".ogg", ".flac", ".webm"}
STATIC_DIR = Path(__file__).parent / "static"

# Track model readiness
_model_ready = False


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(title="Súgó Transcriber")

    @app.get("/", response_class=HTMLResponse)
    async def index():
        index_path = STATIC_DIR / "index.html"
        return HTMLResponse(content=index_path.read_text(encoding="utf-8"))

    @app.get("/api/health")
    async def health():
        return {"status": "ok"}

    @app.get("/api/model-status")
    async def model_status():
        global _model_ready
        size = get_model_size()
        return {"model_size": size, "ready": _model_ready}

    @app.post("/api/load-model")
    async def load_model_endpoint():
        """Trigger model download/loading. Called by frontend on first visit."""
        global _model_ready
        try:
            size = get_model_size()
            load_model(size)
            _model_ready = True
            return {"status": "ready", "model_size": size}
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={"status": "error", "detail": str(e)},
            )

    @app.post("/api/transcribe")
    async def transcribe(
        file: UploadFile = File(...),
        language: str = Form("hu"),
    ):
        # Validate file extension
        ext = Path(file.filename or "").suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file format: {ext}. Supported: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
            )

        # Write upload to temp file (chunked to avoid loading large files into memory)
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
        try:
            while chunk := await file.read(1024 * 1024):
                tmp.write(chunk)
            tmp.close()

            def generate():
                try:
                    for segment in transcribe_audio(tmp.name, language=language):
                        yield f"data: {json.dumps(segment, ensure_ascii=False)}\n\n"
                    yield f"data: {json.dumps({'done': True})}\n\n"
                except Exception as e:
                    yield f"data: {json.dumps({'error': str(e)})}\n\n"
                finally:
                    # Clean up temp file after streaming completes
                    if os.path.exists(tmp.name):
                        os.unlink(tmp.name)

            return StreamingResponse(
                generate(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "X-Accel-Buffering": "no",
                },
            )
        except Exception:
            # Clean up on error before streaming starts
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)
            raise

    return app


def find_available_port(start: int = 8080, end: int = 8085) -> int:
    """Find an available port in the given range."""
    import socket
    for port in range(start, end + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    raise RuntimeError(
        f"No available port found in range {start}-{end}. "
        "Close other applications using these ports and try again."
    )


def main():
    """Entry point for running the server."""
    import uvicorn
    import webbrowser

    port = find_available_port()
    url = f"http://localhost:{port}"
    print(f"\n  Súgó Transcriber running at: {url}\n")

    # Open browser after a short delay
    import threading
    threading.Timer(1.5, lambda: webbrowser.open(url)).start()

    app = create_app()
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Create a placeholder index.html so tests pass**

```html
<!-- src/transcriber/static/index.html -->
<!DOCTYPE html>
<html><head><title>Súgó</title></head><body><h1>Súgó</h1></body></html>
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest tests/test_app.py -v`
Expected: All 8 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add src/transcriber/app.py src/transcriber/static/index.html tests/test_app.py
git commit -m "feat: add FastAPI backend with upload, SSE, and temp file cleanup"
```

---

## Chunk 3: Frontend UI

### Task 4: Build the single-file HTML frontend

**Files:**
- Modify: `src/transcriber/static/index.html`

This is a single HTML file containing all CSS and JS inline. No build tools. The design follows the exe.dev aesthetic: dark theme, minimal, spacious, with a cat mascot.

- [ ] **Step 1: Implement the full frontend**

The HTML file must include:

**CSS (inlined in `<style>`):**
- Dark background (`#0a0a0a` or similar), light text (`#e0e0e0`)
- System font stack: `-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif`
- Single centered column, max-width ~600px, generous padding
- Large drop zone with dashed border, hover/dragover highlight
- Accent color button (e.g. `#6366f1` indigo) for primary actions
- Smooth transitions on hover states and state changes
- Responsive text area for output with monospace font
- `HU | EN` toggle styled as small pill buttons in top-right corner
- Language dropdown styled to match dark theme

**JS (inlined in `<script>`):**
- **i18n system**: Object with `hu` and `en` keys mapping label IDs to translated strings. Function `setLang(lang)` updates all `[data-i18n]` elements. Persist choice in `localStorage`.
- **Drag and drop**: `dragover`, `dragleave`, `drop` events on drop zone. Also a hidden `<input type="file">` with `accept=".m4a,.mp3,.wav,.ogg,.flac,.webm"` triggered on click.
- **Upload + SSE**: On file select, POST to `/api/transcribe` as `multipart/form-data`. Read response as SSE using `EventSource` or manual `fetch` + `ReadableStream` (since POST isn't supported by `EventSource`, use fetch with streaming reader). Parse each `data:` line as JSON. Append `segment.text` to the output area progressively.
- **Elapsed timer**: Start a `setInterval` timer on upload, display `MM:SS` elapsed, stop on completion.
- **Copy button**: Use `navigator.clipboard.writeText()` with visual feedback ("Copied!" / "Másolva!").
- **State management**: Track `loading | ready | processing | complete | error` state. Show/hide relevant UI sections.
- **Model preloading (State 0)**: On page load, call `POST /api/load-model`. If model isn't ready, show State 0 (loading spinner + message). On success, transition to State 1. On failure, show error with retry button.
- **Error state**: Show translated error message with a "Retry" / "Próbáld újra" button. Used for both model download failures and transcription errors.
- **SSE error handling**: When a `data:` event contains an `error` key, transition to error state with the message.

**HTML structure:**
```
<header> — HU|EN toggle, small language dropdown
<main>
  <div class="hero"> — Cat emoji (🐱), "Súgó" title, subtitle
  <div class="loading"> — Spinner + "Model downloading..." message (State 0, first run only)
  <div class="dropzone"> — Drop zone (State 1)
  <div class="processing"> — Spinner, elapsed time, streaming text (State 2)
  <div class="result"> — Full text, Copy button, New button (State 3)
  <div class="error"> — Error message + Retry button (error state)
</main>
```

**Hungarian translations to include:**
| Key | HU | EN |
|-----|----|----|
| subtitle | Helyi hangátíró | Local audio transcriber |
| dropzone_text | Húzd ide a hangfájlt vagy kattints | Drop audio file here or click |
| transcribe_btn | Átírás | Transcribe |
| copy_btn | Másolás | Copy |
| copied | Másolva! | Copied! |
| new_btn | Új átírás | New transcription |
| processing | Átírás folyamatban... | Transcribing... |
| elapsed | Eltelt idő | Elapsed |
| error_format | Nem támogatott formátum | Unsupported format |
| error_generic | Hiba történt. Próbáld újra. | An error occurred. Try again. |
| error_model | A modell letöltése sikertelen. Ellenőrizd az internetkapcsolatot. | Model download failed. Check your internet connection. |
| model_loading | A modell letöltése folyamatban... (ez csak egyszer szükséges) | Downloading model... (one-time only) |
| retry_btn | Próbáld újra | Retry |
| whisper_lang | Beszéd nyelve | Speech language |

- [ ] **Step 2: Manual test — verify the UI renders**

Run: `uv run python -m transcriber.app`
Expected: Browser opens to `localhost:8080`, dark-themed page with cat mascot, drop zone visible, HU labels shown by default.

- [ ] **Step 3: Manual test — verify language toggle**

Click `EN` in the top corner.
Expected: All labels switch to English. Refresh page — English persists (localStorage).

- [ ] **Step 4: Commit**

```bash
git add src/transcriber/static/index.html
git commit -m "feat: add dark-themed frontend with i18n, drag-drop, and SSE streaming"
```

---

### Task 5: End-to-end manual test

No new files. This task validates the full flow works together.

- [ ] **Step 1: Start the server**

Run: `uv run python -m transcriber.app`

- [ ] **Step 2: Test with a real audio file**

Use any short audio file (`.m4a`, `.mp3`, or `.wav`). Drop it in the browser UI.
Expected:
- File accepted, transcription starts
- Text streams in progressively
- Elapsed timer counts up
- On completion, full text shown with Copy button
- Copy button copies text to clipboard
- "New transcription" resets to drop zone

- [ ] **Step 3: Test error handling**

Try dragging a `.txt` file.
Expected: Error message shown, no crash.

- [ ] **Step 4: Commit any fixes from manual testing**

```bash
git add -u
git commit -m "fix: address issues found during end-to-end testing"
```

---

## Chunk 4: Launcher and Distribution

### Task 6: Create macOS launcher

**Files:**
- Create: `start.command`

- [ ] **Step 1: Write the launcher script**

```bash
#!/bin/bash
# Súgó Transcriber — Double-click to launch
# This script installs dependencies on first run and starts the transcription server.

set -e

# Navigate to the script's directory (where the project lives)
cd "$(dirname "$0")"

echo ""
echo "  🐱 Súgó Transcriber"
echo "  ===================="
echo ""

# Check for uv, install if missing
if ! command -v uv &> /dev/null; then
    echo "  Installing uv (Python package manager)..."
    echo "  This is a one-time setup step."
    echo ""
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # Source the updated PATH
    export PATH="$HOME/.local/bin:$PATH"
    echo ""
    echo "  uv installed successfully."
    echo ""
fi

echo "  Starting Súgó..."
echo "  (On first run, the AI model will download — this may take a few minutes)"
echo ""

# Run the app via uv (auto-creates venv and installs deps on first run)
uv run python -m transcriber.app
```

- [ ] **Step 2: Make it executable**

Run: `chmod +x start.command`

- [ ] **Step 3: Test the launcher**

Run: `./start.command`
Expected: Server starts, browser opens. If uv is already installed, skips that step.

- [ ] **Step 4: Commit**

```bash
git add start.command
git commit -m "feat: add macOS double-click launcher"
```

---

### Task 7: Add LICENSE and README

**Files:**
- Create: `LICENSE`
- Create: `README.md`

- [ ] **Step 1: Create MIT license**

```
MIT License

Copyright (c) 2026 Mark

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

- [ ] **Step 2: Create README**

The README should include:
- Project name and description (with cat emoji)
- What it does (1-2 sentences)
- Screenshot placeholder
- Quick start: prerequisites (macOS, Apple Silicon), clone, double-click `start.command`
- Manual start: `uv run python -m transcriber.app`
- How it works: Voice Memos → AirDrop → Súgó → Copy → ChatGPT
- Supported languages (link to Whisper language list)
- Privacy note
- Note about `chmod +x start.command` if downloaded as ZIP from GitHub
- Contributing section
- License

- [ ] **Step 3: Commit**

```bash
git add LICENSE README.md
git commit -m "docs: add MIT license and README"
```

---

### Task 8: Run all tests and final verification

- [ ] **Step 1: Run full test suite**

Run: `uv run pytest tests/ -v`
Expected: All tests pass.

- [ ] **Step 2: Verify clean git state**

Run: `git status`
Expected: Clean working tree, nothing untracked.

- [ ] **Step 3: Final manual smoke test**

Run: `./start.command`
Verify: Full flow works end-to-end.
