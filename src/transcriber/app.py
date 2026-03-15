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
