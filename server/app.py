from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from pathlib import Path
import os, uuid, re, json
from config import OPENAI_API_KEY
from openai import OpenAI
from tinydb import TinyDB, Query

from utils.analysis_utils import analyze_url
from utils.audio_utils import download_audio, cleanup_audio
from utils.whisper_utils import transcribe_audio
from utils.openai_utils import analyze_transcript_with_gpt




app = Flask(__name__)
CORS(app)

db = TinyDB("db.json")

@app.route("/analyze", methods=["OPTIONS"])
def analyze_options():
    return '', 200

@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        data = request.get_json(force=True)
        url  = data.get("url")
        if not url:
            return jsonify({"error": "No URL provided"}), 400

        audio_file = Path("audio") / f"audio_{uuid.uuid4()}.mp3"

        transcribe_json_file = analyze_url(url)
    except Exception as e:
        print(f"[ERROR] {e}")
        return jsonify({"error": str(e)}), 500

    finally:
        print(f"🗑️ Cleaning up audio file: {audio_file}")
        cleanup_audio(audio_file)
        
    return jsonify({"message": f"Analysis complete: {transcribe_json_file}"}), 200

if __name__ == "__main__":
    app.run(port=5100, debug=True)
