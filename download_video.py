import os
import yt_dlp
import uuid

def download_video(url):
    """
    Downloads a video from a URL to a temporary file with a unique name.
    Returns the filename on success, None on failure.
    """
    # Generate a unique filename to prevent conflicts
    unique_id = uuid.uuid4()
    filename = f"temp_vid_{unique_id}.mp4"

    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': filename,
        'quiet': True,
        'overwrite': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return filename
    except Exception as e:
        print(f"Error downloading video: {e}")
        # Clean up the file if download fails
        if os.path.exists(filename):
            os.remove(filename)
        return None

def remove_video(filename):
    """
    Removes the specified video file.
    """
    if filename and os.path.exists(filename):
        try:
            os.remove(filename)
        except OSError as e:
            print(f"Error removing file {filename}: {e}")