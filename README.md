# YouTube Captionizer – Project Blueprint

> **Goal:** Automatically download any YouTube video shared from Firefox, transcribe it with Whisper, translate captions with Gemini, burn or export captions, and play the result in **mpv** (or deliver an .srt / .vtt file)… all from one streamlined workflow.

---

## 1. High‑Level Architecture

```text
Firefox Extension  ──▶  FastAPI Backend  ──▶  Processing Pipeline  ──▶  Assets  ──▶  mpv / download
      (link grab)          (REST)               (Celery task)         (video+subs)
```

| Layer       | Tech                                             | Key Responsibilities                                                                                          |
| ----------- | ------------------------------------------------ | ------------------------------------------------------------------------------------------------------------- |
| **Browser** | Web‑extension (Manifest v3) + vanilla JS (or TS) | Detect active tab, extract canonical YouTube URL, POST `/enqueue`                                             |
| **API**     | Python 3.11 + FastAPI                            | Accept job, return job‑id / status, serve files, WebSocket progress push                                      |
| **Worker**  | Celery + Redis                                   | Heavy tasks: youtube‑dl / yt‑dlp, Whisper transcription, Gemini translate, subtitle muxing / burning (ffmpeg) |
| **Storage** | local `media/` tree or S3 compatible             | Raw video, `.srt` (Whisper), translated `.srt`, final `.mp4`                                                  |
| **Player**  | mpv (JSON IPC)                                   | Auto‑load generated subtitles or rendered video                                                               |

---

## 2. Data Flow – Step by Step

1. **Capture URL** – The add‑on calls `POST /enqueue` with `{url, target_lang}`.
2. **Job Ticket** – Backend creates UUID job folder in `media/jobs/<id>/` & pushes Celery task.
3. **Download** – Worker runs `yt-dlp --write-auto-subs --format best ...` → `input.mp4`.
4. **Whisper** – `whisper input.mp4 --model medium --language auto --output_format srt` → `source.srt`.
5. **Translate** – Stream `source.srt` chunks to Gemini 1.5 Flash `translate()` prompt → `translated.srt`.
6. **Mux/Burn** –
   - **Soft‑subs:** `ffmpeg -i input.mp4 -i translated.srt -c copy -c:s mov_text output.mp4`
   - **Hard‑subs:** `ffmpeg -i input.mp4 -vf subtitles=translated.srt output_burned.mp4`
7. **Serve / Play** – Backend exposes `/download/<id>` & `/stream/<id>.mp4`. Extension or local helper launches `mpv --sub-file=translated.srt input.mp4` or opens burned video.

---

## 3. Repository Structure

```text
youtube-captionizer/
├─ extension/
│  ├─ manifest.json
│  ├─ background.js
│  ├─ options.html / options.js
│  └─ icons/
├─ backend/
│  ├─ app/
│  │  ├─ main.py          # FastAPI routes / WebSockets
│  │  ├─ tasks.py         # Celery tasks
│  │  ├─ utils/
│  │  │  ├─ downloader.py # yt‑dl wrapper
│  │  │  ├─ whisper.py    # OpenAI/whisper‑cpp wrapper
│  │  │  ├─ translate.py  # Gemini client
│  │  │  └─ ffmpeg.py     # Subtitle mux helpers
│  ├─ worker.py           # Celery entrypoint
│  ├─ requirements.txt
│  └─ .env.example
├─ docker-compose.yml
└─ README.md (this file)
```

---

## 4. Key Implementation Notes

### 4.1 Firefox Extension

- **Manifest v3**, permissions: `tabs`, `<all_urls>`, storage.
- `background.js`:
  ```js
  browser.action.onClicked.addListener(async (tab) => {
    const url = tab.url;
    const targetLang = await browser.storage.local.get("lang");
    await fetch("http://localhost:8000/enqueue", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({ url, target_lang: targetLang || "he" })
    });
    browser.notifications.create({
      "type": "basic",
      "title": "Captionizer",
      "message": "Video sent for processing!"
    });
  });
  ```

### 4.2 Backend FastAPI

```python
@app.post("/enqueue", response_model=JobOut)
async def enqueue(req: JobIn):
    job_id = uuid4().hex
    celery_app.send_task("tasks.process_video", args=[req.url, req.target_lang, job_id])
    return {"job_id": job_id, "status": "queued"}
```

- Use Pydantic models.
- WebSocket `/ws/{job_id}` streams state updates: download → transcribe → translate → mux.

### 4.3 Celery Task (pseudo)

```python
@celery.task
def process_video(url, lang, job_id):
    paths = download(url, job_id)
    src_srt = whisper_transcribe(paths.video)
    tgt_srt = translate_srt(src_srt, lang)
    final_mp4 = mux_subs(paths.video, tgt_srt)
    notify(job_id, "done", final_mp4)
```

### 4.4 Whisper Choices

- **openai‑whisper** (CPU/GPU) or **whisper‑cpp** for pure C++.
- Pass `--language` if known to skip autodetect.

### 4.5 Gemini Translation

- Use Gemini Pro or Flash; keep prompts small (<8k tokens).
- Chunk SRT by time‑codes to avoid context overflow. Example prompt:
  ```text
  Translate the following SRT subtitles into Hebrew, retain timecodes:
  1
  00:00:00,000 --> 00:00:03,000
  Hello world!
  ```

### 4.6 Deployment

- **Docker Compose** spins up FastAPI (uvicorn), Redis, Celery worker.
- GPU? Add `--gpus all` + base image `nvidia/cuda:12.4.1-runtime`.

### 4.7 mpv Integration

- Simple option: open default video player; advanced: control mpv JSON IPC on socket `~/.mpv/socket` for overlay progress.

---

## 5. Environment Variables (`.env`)

```
GEMINI_API_KEY=...
WHISPER_MODEL=medium
```

---

## 6. Quick‑Start (Dev)

```bash
# clone repo
pip install -r backend/requirements.txt
uvicorn app.main:app --reload
celery -A app.worker worker --loglevel=info
# build extension → about:debugging → Load Temporary Add‑on
```

---

## 7. Stretch Goals

- GUI progress overlay in extension popup.
- Batch playlist support.
- LLM style transfer (formal / casual captions).

---

## 8. License

MIT – do whatever, just keep attribution.

---

Happy hacking! 🎬
