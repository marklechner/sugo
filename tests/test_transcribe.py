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


class TestReloadModel:
    """Test model reloading clears cache and loads new model."""

    @patch("transcriber.transcribe.WhisperModel")
    def test_reload_clears_cache_and_loads(self, mock_cls):
        mock_cls.return_value = MagicMock()
        load_model.cache_clear()

        # Load medium first
        load_model("medium")
        assert mock_cls.call_count == 1

        # Reload with large-v3
        from transcriber.transcribe import reload_model
        reload_model("large-v3")

        # cache_clear was called (medium gone), large-v3 loaded
        assert mock_cls.call_count >= 2
        mock_cls.assert_called_with("large-v3", device="cpu", compute_type="int8")

    @patch("transcriber.transcribe.WhisperModel")
    def test_reload_returns_model(self, mock_cls):
        mock_instance = MagicMock()
        mock_cls.return_value = mock_instance
        from transcriber.transcribe import reload_model
        result = reload_model("medium")
        assert result is mock_instance
