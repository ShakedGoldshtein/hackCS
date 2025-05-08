import subprocess, os

def download_audio(url: str, filename: str) -> None:
    subprocess.run(["yt-dlp", "-x", "--audio-format", "mp3", url, "-o", filename], check=True)

def cleanup_audio(filename: str) -> None:
    if os.path.exists(filename):
        os.remove(filename)
