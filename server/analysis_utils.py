import uuid
import re
import json
from pathlib import Path
from utils.audio_utils import download_audio
from utils.whisper_utils import transcribe_audio

def analyze_url(url):
    """
    Analyze the given URL by downloading the audio, transcribing it,
    and saving the transcript segments as a JSON file.

    Returns:
        dict: The full transcript dictionary.
    """
    try:
        # Create required directories
        audio_dir = Path("audio")
        transcript_dir = Path("transcripts")
        audio_dir.mkdir(exist_ok=True)
        transcript_dir.mkdir(exist_ok=True)

        # Generate a unique audio filename
        audio_file = audio_dir / f"audio_{uuid.uuid4()}.mp3"
        # absolute_path = audio_file.resolve()
        # print(f"📁 Audio file path: {absolute_path}")

        # Download and transcribe
        download_audio(url, audio_file)
        transcript = transcribe_audio(audio_file, language="he")

        # Create a safe slug for filename
        slug = re.sub(r'https?://', '', url)
        slug = re.sub(r'[^\w-]', '_', slug)[:80]
        json_name = f"transcript_{slug}.json"
        json_path = transcript_dir / json_name
        transcript_absolute_path = json_path.resolve()
        print(f"📁 Transcript path: {transcript_absolute_path}")

        # Save only segments to JSON
        json_path.write_text(
            json.dumps(transcript, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

        return transcript

    except Exception as e:
        print(f"❌ [Error] when analyzing URL {url}: {e}")
        return {"error": str(e)}
