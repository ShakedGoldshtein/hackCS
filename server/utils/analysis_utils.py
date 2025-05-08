import uuid
import re
import json
from pathlib import Path
from utils.debunk_utils import generate_pings
from utils.audio_utils import cleanup_audio, download_audio
from utils.openai_utils import transcribe_audio
from utils.openai_utils import analyze_transcript_with_gpt

def analyze_url(url):
    """
    Analyze the given URL by downloading the audio, transcribing it,
    and saving the transcript segments as a JSON file.

    Returns:
        transcribe path
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
        transcript = str(transcribe_audio(audio_file, language="en"))


        # Create a safe slug for filename
        slug = re.sub(r'https?://', '', url)
        slug = re.sub(r'[^\w-]', '_', slug)[:80]
        json_name = f"transcript_{slug}.json"
        json_path = transcript_dir / json_name
        transcript_absolute_path = json_path.resolve()
        print(f"📁 Transcript path: {transcript_absolute_path}")
        # print(f"[DEBUG]: transcipt1 type: {type(transcript)}")
        # Save only segments to JSON
        json_path.write_text(
            json.dumps(transcript, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        response_pings = generate_pings(transcript, model="gpt-4.1-nano")
        return response_pings

    except Exception as e:
        print(f"❌ [Error] when analyzing URL {url}: {e}")
        return {"error": str(e)}
    
    finally:
        print(f"🗑️ Cleaning up audio file: {audio_file}")
        cleanup_audio(audio_file)
