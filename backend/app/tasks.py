import asyncio
from app.ws import send_status_update
from app.utils.downloader import download_video, extract_playlist_urls
from app.utils.whisper import transcribe_video
from app.utils.translate import translate_srt
from app.utils.ffmpeg import burn_in_subtitles
from worker import celery_app
import os
import re
import shutil

def run_async(coro):
    """Helper to run an async function from a sync context."""
    return asyncio.run(coro)

def sanitize_filename(name):
    """
    Sanitize a string to be used as a filename.
    """
    # Replace invalid characters with underscores
    sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1F]', '_', name)
    # Limit length to 100 characters
    return sanitized[:100]

@celery_app.task(name="tasks.process_video")
def process_video_task(url: str, target_lang: str, job_id: str, hardcode: bool = True, source_lang: str = None, process_playlist: bool = False):
    """
    Celery task to process a video or a playlist.
    """
    job_dir = os.path.join("media", "jobs", job_id)
    os.makedirs(job_dir, exist_ok=True)
    
    # Base output directory for final results
    base_output_dir = os.path.join("media", "output")
    os.makedirs(base_output_dir, exist_ok=True)

    video_urls = []
    if process_playlist:
        run_async(send_status_update(job_id, "extracting_playlist"))
        video_urls = extract_playlist_urls(url, max_videos=50)  # Limit to 50 videos
        if not video_urls:
            run_async(send_status_update(job_id, "playlist_extraction_failed"))
            return
        print(f"Extracted {len(video_urls)} videos from playlist")
    else:
        # Single video
        video_urls = [url]
    
    # Process each video
    for i, video_url in enumerate(video_urls):
        # Create a subdirectory for each video if processing a playlist
        if process_playlist:
            video_job_dir = os.path.join(job_dir, f"video_{i+1}")
            os.makedirs(video_job_dir, exist_ok=True)
        else:
            video_job_dir = job_dir
            
        run_async(send_status_update(job_id, f"downloading_video_{i+1}"))
        # Pass ignore_playlist=False when processing a playlist, True otherwise
        video_path, video_title = download_video(video_url, video_job_dir, ignore_playlist=not process_playlist)
        if not video_path:
            run_async(send_status_update(job_id, f"download_failed_video_{i+1}"))
            continue  # Try the next video in the playlist

        run_async(send_status_update(job_id, f"transcribing_video_{i+1}"))
        transcription_result = transcribe_video(video_path, source_lang)
        if not transcription_result:
            run_async(send_status_update(job_id, f"transcription_failed_video_{i+1}"))
            continue
        source_srt_path, detected_lang = transcription_result
        
        # Use the provided source language if available, otherwise use the detected one
        source_lang = source_lang or detected_lang
        
        # Determine source language code for folder naming
        source_lang_code = source_lang or 'auto'
        # Take only the first part if it's a complex language code (e.g., 'en-US' -> 'en')
        source_lang_code = source_lang_code.split('-')[0]

        # If the source language is the same as the target, skip translation
        if source_lang and source_lang.startswith(target_lang):
            if hardcode:
                run_async(send_status_update(job_id, f"rendering_video_{i+1}"))
                output_video_path = burn_in_subtitles(video_path, source_srt_path)
                if not output_video_path:
                    run_async(send_status_update(job_id, f"render_failed_video_{i+1}"))
                    continue
                run_async(send_status_update(job_id, f"done_video_{i+1}"))
                
                # Create final output directory with video title and language info
                final_dir_name = f"{sanitize_filename(video_title)}_{source_lang_code}_to_{target_lang}"
                final_output_dir = os.path.join(base_output_dir, final_dir_name)
                os.makedirs(final_output_dir, exist_ok=True)
                
                # Move final video to the output directory
                final_video_path = os.path.join(final_output_dir, "output.mp4")
                shutil.move(output_video_path, final_video_path)
                
                # Copy the SRT file to the output directory
                final_srt_path = os.path.join(final_output_dir, f"subtitles_{source_lang_code}.srt")
                shutil.copy(source_srt_path, final_srt_path)
                
                print(f"Job {job_id} - Video {i+1} completed (subtitles already in target language). Output at {final_video_path}")
            else:
                run_async(send_status_update(job_id, f"done_video_{i+1}"))
                
                # Create final output directory with video title and language info
                final_dir_name = f"{sanitize_filename(video_title)}_{source_lang_code}_to_{target_lang}"
                final_output_dir = os.path.join(base_output_dir, final_dir_name)
                os.makedirs(final_output_dir, exist_ok=True)
                
                # Copy the video file to the output directory
                final_video_path = os.path.join(final_output_dir, "input.mp4")
                shutil.copy(video_path, final_video_path)
                
                # Copy the SRT file to the output directory
                final_srt_path = os.path.join(final_output_dir, f"subtitles_{source_lang_code}.srt")
                shutil.copy(source_srt_path, final_srt_path)
                
                print(f"Job {job_id} - Video {i+1} completed (subtitles already in target language). SRT available at {final_srt_path}")
            continue

        run_async(send_status_update(job_id, f"translating_video_{i+1}"))
        translated_srt_path = translate_srt(source_srt_path, target_lang, source_lang)
        if not translated_srt_path:
            run_async(send_status_update(job_id, f"translation_failed_video_{i+1}"))
            continue
        
        if hardcode:
            run_async(send_status_update(job_id, f"rendering_video_{i+1}"))
            output_video_path = burn_in_subtitles(video_path, translated_srt_path)
            if not output_video_path:
                run_async(send_status_update(job_id, f"render_failed_video_{i+1}"))
                continue
            run_async(send_status_update(job_id, f"done_video_{i+1}"))
            
            # Create final output directory with video title and language info
            final_dir_name = f"{sanitize_filename(video_title)}_{source_lang_code}_to_{target_lang}"
            final_output_dir = os.path.join(base_output_dir, final_dir_name)
            os.makedirs(final_output_dir, exist_ok=True)
            
            # Move final video to the output directory
            final_video_path = os.path.join(final_output_dir, "output.mp4")
            shutil.move(output_video_path, final_video_path)
            
            # Copy the original and translated SRT files to the output directory
            original_srt_path = os.path.join(final_output_dir, f"subtitles_{source_lang_code}.srt")
            shutil.copy(source_srt_path, original_srt_path)
            translated_srt_output_path = os.path.join(final_output_dir, f"subtitles_{target_lang}.srt")
            shutil.copy(translated_srt_path, translated_srt_output_path)
            
            print(f"Job {job_id} - Video {i+1} completed. Output at {final_video_path}")
        else:
            run_async(send_status_update(job_id, f"done_video_{i+1}"))
            
            # Create final output directory with video title and language info
            final_dir_name = f"{sanitize_filename(video_title)}_{source_lang_code}_to_{target_lang}"
            final_output_dir = os.path.join(base_output_dir, final_dir_name)
            os.makedirs(final_output_dir, exist_ok=True)
            
            # Copy the video file to the output directory
            final_video_path = os.path.join(final_output_dir, "input.mp4")
            shutil.copy(video_path, final_video_path)
            
            # Copy the original and translated SRT files to the output directory
            original_srt_path = os.path.join(final_output_dir, f"subtitles_{source_lang_code}.srt")
            shutil.copy(source_srt_path, original_srt_path)
            translated_srt_output_path = os.path.join(final_output_dir, f"subtitles_{target_lang}.srt")
            shutil.copy(translated_srt_path, translated_srt_output_path)
            
            print(f"Job {job_id} - Video {i+1} completed. SRT available at {translated_srt_output_path}")
            
    # If we got here, at least one video was processed successfully
    # For a single video, this is redundant but harmless
    # For a playlist, it indicates the overall job is done
    run_async(send_status_update(job_id, "done"))


