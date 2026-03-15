# Súgó Transcriber

Local, privacy-first audio transcription tool powered by Whisper.

## Overview

Súgó is a privacy-focused transcription tool that runs entirely on your machine using OpenAI's Whisper model via faster-whisper.

## Features

- Local processing - no cloud uploads
- FastAPI-based web interface
- Real-time transcription status via Server-Sent Events
- Support for multiple audio formats

## Getting Started

### Installation

```bash
uv sync
```

### Running the Application

```bash
uv run uvicorn transcriber.app:app --reload
```

## Development

Install development dependencies:

```bash
uv sync --dev
```

Run tests:

```bash
uv run pytest
```

## License

MIT
