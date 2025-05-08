import openai, os
from pathlib import Path
from config import client

PROMPT_PATH = Path("prompts/analysis_prompt.txt")

def analyze_transcript_with_gpt(filename: str) -> str:
    text = Path(filename).read_text(encoding="utf-8")
    prompt = PROMPT_PATH.read_text(encoding="utf-8").format(text=text)
    response = client.chat.completions.create(
        model="gpt-4.1-nano", 
        messages=[
            {"role": "system", "content": prompt}
        ],
        temperature=0.2
    )
    return response.choices[0].message.content.strip()


def transcribe_audio(filename: str, language: str = "en") -> dict:
    filename = str(filename)
    if not os.path.exists(filename):
        raise FileNotFoundError(f"⚠️ Audio file not found: {filename}")

    print(f"🧠 audio file for transcription: {filename}")

    try:
        with open(filename, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                # model="tiny",
                file=audio_file,
                language=language,
                response_format="verbose_json"  # get segments too
            )
    except Exception as e:
        raise RuntimeError(f"❌ Whisper API transcription failed: {e}")

    print("✅ Transcription complete")
    return {"text": transcript.text,
        "segments": [
            {
                "id": i,
                "start": s.start,
                "end": s.end,
                "text": s.text
            }
            for i, s in enumerate(transcript.segments)
        ] if hasattr(transcript, "segments") else []
    }