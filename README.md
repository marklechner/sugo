# Súgó 🐱

Local, privacy-first audio transcription powered by Whisper

Record on your iPhone, AirDrop to your Mac, and transcribe instantly — no internet required. Súgó runs the AI model entirely on your machine and copies the transcript to your clipboard so you can paste it straight into ChatGPT or anywhere else.

---

## Quick Start

**Prerequisites:** macOS with Apple Silicon (M1/M2/M3/M4). No other setup needed.

```bash
git clone https://github.com/yourusername/transcriber.git
cd transcriber
```

Then double-click `start.command`, or run:

```bash
uv run python -m transcriber.app
```

The first launch downloads the Whisper AI model (~1.5 GB, one-time only).

> **Downloaded as a ZIP from GitHub?** Run `chmod +x start.command` once before double-clicking.

---

## How It Works

```
Voice Memos → AirDrop → Súgó → Copy → ChatGPT
```

1. Record a voice memo on your iPhone
2. AirDrop the `.m4a` file to your Mac
3. Drop it into Súgó (or pick it from the file picker)
4. Click Copy and paste your transcript anywhere

---

## Features

- Hungarian and English UI
- Transcription in 99 languages
- Dark theme
- Drag-and-drop support
- Supported formats: `.m4a`, `.mp3`, `.wav`, `.ogg`, `.flac`, `.webm`

---

## Privacy

All processing happens locally on your machine. No audio, no text, and no metadata ever leaves your Mac. There are no cloud APIs, no accounts, and no telemetry.

---

## Contributing

PRs are welcome. Open an issue first for larger changes.

---

## License

MIT — see [LICENSE](LICENSE)
