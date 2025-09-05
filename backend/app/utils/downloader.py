import yt_dlp
import os

def download_video(url: str, output_dir: str, ignore_playlist: bool = True) -> tuple[str | None, str | None]:
    """
    Downloads a video from the given URL using yt-dlp.
    Saves it as 'input.mp4' in the specified directory.
    
    Args:
        url: The URL of the video to download
        output_dir: The directory to save the video
        ignore_playlist: If True, download only the video even if the URL is part of a playlist
        
    Returns:
        A tuple of (video_path, video_title) or (None, None) if download failed
    """
    output_path = os.path.join(output_dir, "input.mp4")
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': output_path,
        'merge_output_format': 'mp4',
    }
    
    # If ignore_playlist is True, add the noplaylist option
    if ignore_playlist:
        ydl_opts['noplaylist'] = True
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            video_title = info_dict.get('title', 'Unknown_Title')
            return output_path, video_title
    except Exception as e:
        print(f"Error downloading video: {e}")
        return None, None

def extract_playlist_urls(playlist_url: str, max_videos: int = 50) -> list[str]:
    """
    Extracts individual video URLs from a playlist URL.
    Limits the number of videos to prevent excessively long jobs.
    """
    # For "Mix" playlists or other auto-generated playlists, 
    # we might want to limit the number of videos extracted
    ydl_opts = {
        'extract_flat': True,  # Don't download videos, just extract info
        'force_generic_extractor': False,
        'playlistend': max_videos,  # Limit the number of videos
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            playlist_info = ydl.extract_info(playlist_url, download=False)
            
            if 'entries' in playlist_info:
                # This is a playlist
                video_urls = []
                for entry in playlist_info['entries']:
                    if 'url' in entry:
                        # For YouTube, 'url' in flat extraction is usually the video ID
                        video_urls.append(f"https://www.youtube.com/watch?v={entry['url']}")
                    elif 'webpage_url' in entry:
                        # Fallback to webpage_url if available
                        video_urls.append(entry['webpage_url'])
                        
                    # Stop if we've reached the maximum number of videos
                    if len(video_urls) >= max_videos:
                        break
                        
                return video_urls
            else:
                # This is a single video
                return [playlist_url]
    except Exception as e:
        print(f"Error extracting playlist URLs: {e}")
        return []
