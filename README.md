# Sugo 🐱

Local, privacy-first audio transcription powered by Whisper

Record on your iPhone, AirDrop to your Mac, and transcribe instantly — no internet required. Sugo runs the AI model entirely on your machine and copies the transcript to your clipboard so you can paste it straight into ChatGPT or anywhere else.

---

## Quick Start

**Prerequisites:** macOS with Apple Silicon (M1/M2/M3/M4). No other setup needed.

### System Requirements by Model

| Model | RAM | Disk | Speed | Accuracy |
|-------|-----|------|-------|----------|
| **Medium** | 8 GB+ | ~1.5 GB | ~2-4x realtime | Good |
| **Large-v3** | 16 GB+ | ~3 GB | ~1-2x realtime | Best |

Sugo auto-selects the best model for your machine. Macs with 16 GB+ RAM get Large-v3 by default; 8 GB Macs get Medium. You can override this in Settings.

> **Speed note:** "2x realtime" means a 10-minute recording takes ~5 minutes to transcribe. Performance varies by Mac model.

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

## Upgrading an Existing Installation

If you already have Sugo installed, pull the latest changes:

```bash
cd transcriber
git pull
```

That's it. The next time you launch Sugo (double-click `start.command` or run `uv run python -m transcriber.app`), it will pick up all the new features automatically. No reinstallation needed — `uv` handles dependency updates on the fly.

If you run into issues after upgrading, reset your virtual environment:

```bash
rm -rf .venv
uv run python -m transcriber.app
```

---

## Setting Up a Command Shortcut

You can launch Sugo from anywhere in your terminal with a single command.

### Option A: Shell alias (recommended)

Add this to your `~/.zshrc` (or `~/.bashrc`):

```bash
alias sugo='cd ~/Desktop/dev/transcriber && uv run python -m transcriber.app'
```

Then reload your shell:

```bash
source ~/.zshrc
```

Now just type `sugo` in any terminal window.

### Option B: Dock shortcut

1. Right-click `start.command` in Finder
2. Select **Get Info**
3. Under **Open with**, choose **Terminal.app**
4. Drag `start.command` to the Dock for one-click access

### Option C: Spotlight / Launchpad

Rename `start.command` to `Sugo.command` and keep it in a convenient location. Spotlight indexes `.command` files, so you can press **Cmd+Space**, type "Sugo", and hit Enter.

---

## How It Works

```
Voice Memos -> AirDrop -> Sugo -> Copy -> ChatGPT
```

1. Record a voice memo on your iPhone
2. AirDrop the `.m4a` file to your Mac
3. Drop it into Sugo (or pick it from the file picker)
4. Click Copy and paste your transcript anywhere

---

## Features

- **Smart paragraphs** — automatically segments text based on speech pauses
- **Optional timestamps** — prepend `[MM:SS]` markers to each segment
- **Active model indicator** — always shows which Whisper model is loaded
- **Configurable settings** — paragraph gap, font size, auto-copy, timestamps
- Hungarian and English UI
- Transcription in 99+ languages
- Dark theme
- Drag-and-drop support
- One-click quit button (top-right, always visible)
- Supported formats: `.m4a`, `.mp3`, `.wav`, `.ogg`, `.flac`, `.webm`

### Settings

Open the gear icon to configure:

| Setting | Options | Default |
|---------|---------|---------|
| Model size | Auto, Medium (faster), Large-v3 (more accurate) | Auto |
| Paragraph pause | Off, 1s, 1.5s, 2s, 3s | 1.5s |
| Font size | Small, Medium, Large, Extra large | Medium |
| Auto-copy | On/Off | Off |
| Timestamps | On/Off | Off |

All settings are saved in your browser and persist between sessions.

---

## Privacy

All processing happens locally on your machine. No audio, no text, and no metadata ever leaves your Mac. There are no cloud APIs, no accounts, and no telemetry.

---

## Contributing

PRs are welcome. Open an issue first for larger changes.

---

## License

MIT — see [LICENSE](LICENSE)
