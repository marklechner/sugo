# Súgó — Design Spec

## Overview

Súgó is a local, privacy-first audio transcription tool for journalists and anyone who needs to convert speech to text. It runs entirely on the user's machine using Whisper (no cloud APIs, no data leaves the computer). The primary user is a non-technical Hungarian journalist using a MacBook Air M1 who records interviews on her iPhone via Voice Memos.

The name "Súgó" is Hungarian for "prompter/whisperer" — a nod to both the Whisper engine and the Hungarian theater tradition where a súgó whispers lines to actors.

## Problem

- Apple Intelligence doesn't support Hungarian transcription
- Commercial AI transcription tools are expensive and raise privacy concerns for journalists
- The user needs the simplest possible workflow: record → transfer → transcribe → copy text

## User Flow

1. Record interview on iPhone using Voice Memos
2. Tap Share → AirDrop → select MacBook (file lands in `~/Downloads/`)
3. Double-click **"Súgó"** launcher on Desktop
4. Browser opens to a clean, dark-themed page with a cat mascot
5. Drag audio file into the drop zone (or click to browse)
6. Click **"Átírás"** (Transcribe) button
7. Progress indicator shows work is happening
8. Full transcribed text appears
9. Click **"Másolás"** (Copy to Clipboard)
10. Paste into ChatGPT for refinement

## Architecture

```
┌─────────────────────────────────────────┐
│          Browser (localhost:8080)        │
│  Single HTML file (HTML + CSS + JS)     │
│  - Drag & drop / file picker            │
│  - Progress via SSE (streaming text)    │
│  - Text output + copy button            │
│  - HU/EN UI toggle                      │
│  - Whisper language selector             │
└──────────────┬──────────────────────────┘
               │ HTTP (localhost:8080)
┌──────────────▼──────────────────────────┐
│          Python Backend (FastAPI)        │
│  - File upload endpoint                  │
│  - Transcription via faster-whisper      │
│  - Model: medium (default) or large-v3   │
│  - Progress reporting via SSE            │
└──────────────────────────────────────────┘
```

### Tech Stack

| Component        | Choice                  | Rationale                                          |
|------------------|-------------------------|----------------------------------------------------|
| Language         | Python                  | Best Whisper ecosystem                             |
| Package manager  | uv                      | Fast, modern, user preference                      |
| Web framework    | FastAPI                 | Lightweight, async, handles file uploads well      |
| Whisper engine   | faster-whisper           | ~2x faster than openai-whisper on M1 CPU, lower memory |
| Whisper model    | medium (default) / large-v3 | medium for 8GB RAM, large-v3 for 16GB+         |
| Frontend         | Single HTML file         | No build tools, no npm, vanilla HTML/CSS/JS        |
| Launcher         | .command file            | macOS double-click launches Terminal script         |

FastAPI serves `index.html` at the root route and mounts the `static/` directory for any additional assets.

### Key Technical Decisions

- **faster-whisper over openai-whisper**: Uses CTranslate2 under the hood. ~2x faster than openai-whisper on Apple Silicon CPU with lower memory footprint, same accuracy. (The often-cited "4x" figure is from CUDA GPU benchmarks; on M1 CPU the speedup is more modest but still significant.)
- **Language forced to `hu` by default**: No auto-detection guessing. User can change via dropdown for other languages.
- **Single HTML file**: All CSS and JS inlined. No build step, no dependencies, trivial to maintain.
- **Model selection based on RAM**: On 8GB machines (like the target M1 Air), default to the `medium` model (~1.5GB RAM) for reliable performance. The `large-v3` model (~3GB RAM) is available as an option for 16GB+ machines. Both produce good Hungarian transcription; large-v3 is more accurate but risks memory pressure on 8GB devices.
- **Model downloads on first run**: The selected model downloads automatically on first launch and is cached locally for subsequent runs.
- **Progress via SSE (Server-Sent Events)**: The backend streams transcription progress to the frontend via SSE. As faster-whisper yields segments incrementally, completed text is streamed to the UI in real time, giving the user immediate visual feedback. An elapsed timer is shown alongside.
- **Temp file cleanup**: Uploaded audio is written to a temp file (required by faster-whisper's file-path API), then deleted immediately after transcription completes or on error. No audio data persists.
- **No artificial file size limit**: FastAPI's `UploadFile` streams to disk, so large files (e.g. 2-hour interviews, ~500MB) are handled without memory issues. No upload cap is enforced in v1.

## UI Design

### Visual Direction

Inspired by [exe.dev](https://exe.dev/):
- **Dark theme** — dark background, light text, high contrast
- **Minimal & spacious** — generous whitespace, single centered column
- **Modern sans-serif** typography (system font stack)
- **Cat mascot** — cute cat emoji/icon at the top as the app's identity
- **One accent color** for the primary action button against the dark background
- **Subtle interactions** — smooth transitions, gentle hover states

### Layout

The page is a single centered column with these states:

**State 1 — Ready:**
- Cat mascot + "Súgó" title
- Large drop zone: "Húzd ide a hangfájlt vagy kattints a tallózáshoz"
- HU/EN toggle (top corner, unobtrusive)
- Whisper language dropdown (small, defaults to Magyar/Hungarian)

**State 0 — First Run (model downloading):**
- Cat mascot + "Súgó" title
- Message: "A modell letöltése folyamatban... (ez csak egyszer szükséges)" / "Downloading model... (one-time only)"
- Indeterminate spinner (faster-whisper does not expose download progress callbacks)
- This state only appears on the very first launch

**State 2 — Processing:**
- Indeterminate spinner with elapsed time counter
- File name shown
- Transcribed text streams in progressively as segments complete (via SSE), giving immediate visual feedback

**State 3 — Complete:**
- Full transcribed text in a readable text area
- Large "Másolás" (Copy) button
- "Új átírás" (New Transcription) button to return to State 1

### UI Internationalization

- Two UI languages: Hungarian (default) and English
- Toggle via `HU | EN` switch in the corner
- All labels, buttons, status messages translated
- Implementation: JS object with string keys per language
- UI language is independent of Whisper transcription language

### Supported Audio Formats

- `.m4a` (Voice Memos native format)
- `.mp3`
- `.wav`
- `.ogg`, `.flac`, `.webm` (faster-whisper supports these natively)

## Project Structure

```
transcriber/
├── pyproject.toml              # uv project config, all dependencies
├── src/
│   └── transcriber/
│       ├── __init__.py
│       ├── app.py              # FastAPI server, routes, file upload
│       ├── transcribe.py       # Whisper model loading + transcription logic
│       └── static/
│           └── index.html      # Single-file frontend (HTML + CSS + JS)
├── start.command               # macOS double-click launcher
├── LICENSE                     # MIT
└── README.md
```

## Launcher (`start.command`)

A shell script with `.command` extension so macOS runs it on double-click:

1. `cd` to the project directory
2. Check if `uv` is installed; if not, install it via the official installer (prints a message explaining what's happening)
3. Run `uv run python -m transcriber.app` (auto-creates venv + installs deps on first run)
4. Open browser to `http://localhost:8080` (or next available port)
5. On first run, Whisper model downloads automatically (one-time)

**Note:** The `.command` file requires execute permission (`chmod +x`). Git preserves this, but GitHub ZIP downloads do not — the README should cover this.

## Language Extensibility

- Whisper large-v3 supports 99 languages out of the box
- Adding a new transcription language = adding an entry to the language dropdown
- No extra models or downloads needed
- Default is Hungarian; user can select any supported language

## Error Handling

All errors are surfaced in the browser UI with clear, translated messages (no terminal reading required):

- **Model download failure**: "A modell letöltése sikertelen. Ellenőrizd az internetkapcsolatot." / "Model download failed. Check your internet connection." Retry button shown.
- **Unsupported/corrupt file**: Client-side validation via `accept` attribute restricts to supported extensions. Server-side validation checks the file header before passing to faster-whisper. Clear message if invalid.
- **Port 8080 in use**: The launcher tries port 8080, then falls back to 8081-8085. If all are taken, prints a clear error and exits. The actual URL is printed in Terminal and opened in the browser automatically.
- **Transcription error**: "Hiba történt az átírás közben. Próbáld újra." / "An error occurred during transcription. Please try again." With a retry button.
- **Server shutdown**: When the user closes the Terminal window, the server stops. A note in the browser UI: if the page becomes unresponsive, relaunch Súgó. No auto-shutdown timer in v1 — the user simply closes Terminal when done.

## Privacy

- 100% local processing — no network calls during transcription, no cloud APIs, no telemetry
- The only network activity is the one-time model download on first launch
- Uploaded audio is written to a temp file for processing, then immediately deleted after transcription completes (or on error)
- The Whisper model runs entirely on-device

## Non-Goals (v1)

- Speaker diarization (who said what)
- Real-time / live transcription
- Automatic punctuation correction beyond what Whisper provides
- Built-in text editing or formatting tools (ChatGPT handles this)
- Mobile app or phone-side processing
- Native macOS `.app` bundle (future consideration)
- UI translations beyond HU and EN

## Open Source

- License: MIT
- Hosted on GitHub under the user's account
- README with clear setup instructions for contributors
- Designed for the community to add languages and contribute
