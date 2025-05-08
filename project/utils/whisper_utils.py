from openai import OpenAI
import whisper
import os

model = whisper.load_model("tiny")

def transcribe_audio(filename: str, language: str = "he") -> dict:
    filename = str(filename)
    if not os.path.exists(filename):
        raise FileNotFoundError(f"⚠️ Audio file not found: {filename}")
    
    print(f"🧠 audio file for transcription: {filename}")
    
    try:
        result = model.transcribe(filename, language=language)
    except Exception as e:
        raise RuntimeError(f"❌ Whisper transcription failed: {e}")
    
    print("✅ Transcription complete")
    # print(result)
    return {
        "text": result["text"],
        "segments": [
            {
                "id": s["id"], 
                "start": s["start"], 
                "end": s["end"], 
                "text": s["text"]
            }
            for s in result["segments"]
        ]
    }
