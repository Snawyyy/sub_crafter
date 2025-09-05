import asyncio
from app.ws import send_status_update
from app.utils.downloader import download_video
from app.utils.whisper import transcribe_video
from app.utils.translate import translate_srt
from app.utils.ffmpeg import burn_in_subtitles
from worker import celery_app
import os

def run_async(coro):
    """Helper to run an async function from a sync context."""
    return asyncio.run(coro)

@celery_app.task(name="tasks.process_video")
def process_video_task(url: str, target_lang: str, job_id: str, hardcode: bool = True, source_lang: str = None):
    """
    Celery task to process a video.
    """
    job_dir = os.path.join("media", "jobs", job_id)
    os.makedirs(job_dir, exist_ok=True)

    run_async(send_status_update(job_id, "downloading"))
    video_path = download_video(url, job_dir)
    if not video_path:
        run_async(send_status_update(job_id, "download_failed"))
        return

    run_async(send_status_update(job_id, "transcribing"))
    transcription_result = transcribe_video(video_path, source_lang)
    if not transcription_result:
        run_async(send_status_update(job_id, "transcription_failed"))
        return
    source_srt_path, detected_lang = transcription_result
    
    # Use the provided source language if available, otherwise use the detected one
    source_lang = source_lang or detected_lang

    # If the source language is the same as the target, skip translation
    if source_lang and source_lang.startswith(target_lang):
        if hardcode:
            run_async(send_status_update(job_id, "rendering"))
            output_video_path = burn_in_subtitles(video_path, source_srt_path)
            if not output_video_path:
                run_async(send_status_update(job_id, "render_failed"))
                return
            run_async(send_status_update(job_id, "done"))
            print(f"Job {job_id} completed (subtitles already in target language). Output at {output_video_path}")
        else:
            run_async(send_status_update(job_id, "done"))
            print(f"Job {job_id} completed (subtitles already in target language). SRT available at {source_srt_path}")
        return

    run_async(send_status_update(job_id, "translating"))
    translated_srt_path = translate_srt(source_srt_path, target_lang, source_lang)
    if not translated_srt_path:
        run_async(send_status_update(job_id, "translation_failed"))
        return
    
    if hardcode:
        run_async(send_status_update(job_id, "rendering"))
        output_video_path = burn_in_subtitles(video_path, translated_srt_path)
        if not output_video_path:
            run_async(send_status_update(job_id, "render_failed"))
            return
        run_async(send_status_update(job_id, "done"))
        print(f"Job {job_id} completed. Output at {output_video_path}")
    else:
        run_async(send_status_update(job_id, "done"))
        print(f"Job {job_id} completed. SRT available at {translated_srt_path}")


