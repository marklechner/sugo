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
