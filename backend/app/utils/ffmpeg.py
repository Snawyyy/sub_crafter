import subprocess
import os

def burn_in_subtitles(video_path: str, srt_path: str) -> str | None:
    """
    Burns subtitles into the video using ffmpeg.
    Creates 'output_burned.mp4'.
    """
    output_path = os.path.join(os.path.dirname(video_path), "output_burned.mp4")
    
    # Ensure Windows paths are correctly formatted for ffmpeg
    srt_path_escaped = srt_path.replace('\\', '\\\\').replace(':', '\\:')

    command = [
        "ffmpeg",
        "-i", video_path,
        "-vf", f"subtitles={srt_path_escaped}",
        "-y", # Overwrite output file if it exists
        output_path
    ]
    
    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
        return output_path
    except subprocess.CalledProcessError as e:
        print(f"Error burning subtitles with ffmpeg.")
        print(f"Command: {' '.join(command)}")
        print(f"Stderr: {e.stderr}")
        return None

def mux_subtitles(video_path: str, srt_path: str) -> str | None:
    """
    Muxes subtitles into the video container (soft subs).
    Creates 'output_muxed.mp4'.
    """
    output_path = os.path.join(os.path.dirname(video_path), "output_muxed.mp4")
    
    command = [
        "ffmpeg",
        "-i", video_path,
        "-i", srt_path,
        "-c", "copy",
        "-c:s", "mov_text",
        "-y",
        output_path
    ]

    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
        return output_path
    except subprocess.CalledProcessError as e:
        print(f"Error muxing subtitles with ffmpeg.")
        print(f"Command: {' '.join(command)}")
        print(f"Stderr: {e.stderr}")
        return None
