from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from pathlib import Path
import os, uuid, re, json
from config import OPENAI_API_KEY
from openai import OpenAI

from utils.audio_utils import download_audio, cleanup_audio
from utils.whisper_utils import transcribe_audio
from utils.openai_utils import analyze_transcript_with_gpt


app = Flask(__name__)
CORS(app)

@app.route("/analyze", methods=["OPTIONS"])
def analyze_options():
    return '', 200

@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json(force=True)
    url  = data.get("url")
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    audio_dir = Path("audio")
    audio_dir.mkdir(exist_ok=True)
    audio_file = audio_dir / f"audio_{uuid.uuid4()}.mp3"
    absolute_path = audio_file.resolve()
    print(f"📁 Absolute path: {absolute_path}")
    try:
        download_audio(url, audio_file)
        transcript  = transcribe_audio(audio_file, language="he")
        slug = re.sub(r'https?://', '', url)
        slug = re.sub(r'[^\w-]', '_', slug)[:80]
        json_name = f"transcript_{slug}.json"
        json_path = Path("transcripts") / json_name

        transcript_absolute_path = json_path.resolve()
        print(f"📁 transcript_absolute_path: {transcript_absolute_path}")

        json_path.write_text(
            json.dumps(transcript["segments"], ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        return transcript
        # gpt_analysis = analyze_transcript_with_gpt(transcript["text"])

        # return jsonify({
        #     "message": "Transcript complete",
        #     "file": str(json_path),
        #     "gpt_analysis": gpt_analysis
        # })
    except Exception as e:
        print(f"[ERROR] {e}")
        return jsonify({"[Error] ": str(e)}), 500
    finally:
        cleanup_audio(audio_file)

if __name__ == "__main__":
    app.run(port=5100, debug=True)
