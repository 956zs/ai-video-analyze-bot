import os
import yt_dlp

def download_video(url):
    """
    Downloads a video from a URL to a temporary file 'temp_vid.mp4'.
    Returns the filename on success, None on failure.
    """
    ydl_opts = {
        'format': 'best[ext=mp4]/best',
        'outtmpl': 'temp_vid.mp4',
        'quiet': True,
        'overwrite': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return "temp_vid.mp4"
    except Exception as e:
        print(f"Error downloading video: {e}")
        return None

def remove_video(filename="temp_vid.mp4"):
    """
    Removes the specified video file.
    """
    if os.path.exists(filename):
        os.remove(filename)