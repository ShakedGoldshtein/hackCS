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
        
        response = {}

        # ping responses
        response["pings"] = {} 
        data_entires = analyze_url(url) 
        max_end = max(entry["end"] for entry in data_entires)
        response["pings"]['entries'] = data_entires
        response["pings"]['max_end'] = max_end
        response["pings"]['url'] = url

        # audio_file = Path("audio") / f"audio_{uuid.uuid4()}.mp3"
        
        return jsonify(response), 200

    except Exception as e:
        print(f"[ERROR] {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(port=5100, debug=True)
