import yt_dlp
import os

def download_video(url: str, output_dir: str) -> str | None:
    """
    Downloads a video from the given URL using yt-dlp.
    Saves it as 'input.mp4' in the specified directory.
    """
    output_path = os.path.join(output_dir, "input.mp4")
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': output_path,
        'merge_output_format': 'mp4',
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return output_path
    except Exception as e:
        print(f"Error downloading video: {e}")
        return None
