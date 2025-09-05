# YouTube Captionizer

Automatically download any YouTube video shared from Firefox, transcribe it with Whisper, translate captions with Qwen, burn or export captions, and play the result in **mpv** (or deliver an .srt / .vtt file)… all from one streamlined workflow.

---

## Features

- **Browser Integration:** A Firefox extension to capture the active YouTube tab URL.
- **Fast Processing:** Backend API (FastAPI) and worker (Celery) handle the workflow.
- **Transcription:** Uses Whisper for accurate speech-to-text.
- **Translation:** Leverages Qwen (via GEMINI_API_KEY) for translating captions.
- **Flexible Output:** Burn subtitles directly onto the video or export them as .srt/.vtt files.
- **Playback:** Seamlessly plays the final video in mpv or allows file download.

---

## Architecture

```text
Firefox Extension  ──▶  FastAPI Backend  ──▶  Processing Pipeline  ──▶  Assets  ──▶  mpv / download
      (link grab)          (REST)               (Celery task)         (video+subs)
```

| Layer       | Tech                                             | Key Responsibilities                                                                                          |
| ----------- | ------------------------------------------------ | ------------------------------------------------------------------------------------------------------------- |
| **Browser** | Web-extension (Manifest v3) + JavaScript         | Detect active tab, extract canonical YouTube URL, POST `/enqueue`                                             |
| **API**     | Python 3.11 + FastAPI                            | Accept job, return job-id / status, serve files, WebSocket progress push                                      |
| **Worker**  | Celery + Redis                                   | Heavy tasks: youtube-dl / yt-dlp, Whisper transcription, Qwen translation, subtitle muxing / burning (ffmpeg) |
| **Storage** | Local `media/` tree                              | Raw video, `.srt` (Whisper), translated `.srt`, final `.mp4`                                                  |
| **Player**  | mpv                                              | Auto-load generated subtitles or rendered video                                                               |

---

## Workflow

1. **Capture URL:** The Firefox add-on sends a POST request to `/enqueue` with the YouTube URL and target language.
2. **Job Creation:** The backend creates a unique job folder in `media/jobs/<id>/` and queues a Celery task.
3. **Download:** The worker downloads the video using `yt-dlp`.
4. **Transcription:** Whisper transcribes the audio to `source.srt`.
5. **Translation:** The `source.srt` file is translated using Qwen into the target language, producing `translated.srt`.
6. **Mux/Burn:**
   - **Soft-subtitles:** Mux the translated subtitles into the video container.
   - **Hard-subtitles:** Burn the subtitles directly onto the video frames using ffmpeg.
7. **Serve/Play:** The backend serves the final video file or subtitles. The extension or a local helper launches mpv to play the result.

---

## Project Structure

```text
youtube-captionizer/
├─ extension/
│  ├─ manifest.json
│  ├─ background.js
│  ├─ options.html / options.js
│  ├─ popup.html / popup.js
│  └─ icons/
├─ backend/
│  ├─ app/
│  │  ├─ main.py          # FastAPI routes / WebSockets
│  │  ├─ tasks.py         # Celery tasks
│  │  ├─ utils/
│  │  │  ├─ downloader.py # yt-dlp wrapper
│  │  │  ├─ whisper.py    # Whisper wrapper
│  │  │  ├─ translate.py  # Qwen client
│  │  │  └─ ffmpeg.py     # Subtitle mux helpers
│  ├─ media/              # Storage for job assets
│  ├─ worker.py           # Celery entrypoint
│  ├─ requirements.txt
│  └─ .env.example
├─ docker-compose.yml
└─ README.md (this file)
```

---

## Setup & Installation

### Prerequisites

- Python 3.11+
- Node.js & npm (for the extension)
- Redis server
- ffmpeg
- mpv
- yt-dlp

### Backend (Local)

1. Clone the repository.
2. Navigate to the `backend/` directory.
3. Create a virtual environment: `python -m venv .venv && source .venv/bin/activate` (Linux/macOS) or `python -m venv .venv && .venv\Scripts\activate` (Windows).
4. Install dependencies: `pip install -r requirements.txt`.
5. Create a `.env` file based on `.env.example` and add your `GEMINI_API_KEY`.

For a full local setup guide, see [LOCAL_SETUP.md](LOCAL_SETUP.md).

### Running the Backend (Local)

You can start all backend services (Redis, FastAPI, Celery) at once using the provided script:

```bash
./you_cap local
```

Alternatively, you can start them manually in separate terminals:

```bash
# Start the FastAPI server
uvicorn app.main:app --reload --port 8000

# In a new terminal, start the Celery worker
celery -A worker worker --loglevel=info
```
```

### Firefox Extension

1. Navigate to the `extension/` directory.
2. Load the extension in Firefox:
   - Open `about:debugging`.
   - Click "This Firefox".
   - Click "Load Temporary Add-on".
   - Select the `manifest.json` file from the `extension/` directory.

---

## Configuration

### Environment Variables (`.env`)

```env
GEMINI_API_KEY=your_gemini_api_key_here
WHISPER_MODEL=medium
```

---

## Development

- **API Documentation:** FastAPI provides interactive API docs at `http://localhost:8000/docs`.
- **WebSocket Updates:** Use WebSockets at `ws://localhost:8000/ws/{job_id}` for real-time job status updates.

---

## Deployment

This project includes a `docker-compose.yml` file for easy deployment. It defines services for the FastAPI backend, Celery worker, and Redis.

To deploy using Docker Compose:

1. Ensure Docker and Docker Compose are installed.
2. Build and start the services:
   ```bash
   docker-compose up --build
   ```

---

## License

MIT – do whatever, just keep attribution.