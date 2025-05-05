from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess
import os
import uuid
import whisper
import openai
from dotenv import load_dotenv
from pathlib import Path


load_dotenv(dotenv_path=Path("secret.env").resolve())
openai.api_key = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)
CORS(app, resources={r"/analyze": {"origins": "*"}}, methods=["GET", "POST", "OPTIONS"], allow_headers=["Content-Type"])
model = whisper.load_model("medium")  # אפשר גם tiny או base אם אתה רוצה שזה יהיה מהיר

@app.route("/analyze", methods=["OPTIONS"])
def analyze_options():
    return '', 200

@app.route("/analyze", methods=["POST"])
def analyze():

    data = request.get_json()
    url = data.get("url")

    if not url:
        return jsonify({"error": "Missing URL"}), 400

    print("📥 URL שהתקבל:", url)

    # שם זמני לקובץ
    filename = f"audio_{uuid.uuid4()}.mp3"

    try:
        print("⬇️ מוריד אודיו מהסרטון עם yt-dlp...")
        print("✅ yt-dlp path:", subprocess.run(["which", "yt-dlp"], capture_output=True, text=True).stdout.strip())
        # שלב 1: הורד אודיו מהסרטון
        command = [
            "yt-dlp",
            "-x", "--audio-format", "mp3",
            url,
            "-o", filename
        ]
        subprocess.run(command, check=True)

        print("✅ הורדת האודיו הסתיימה:", filename)

        print("🧠 מריץ תמלול עם whisper...")
        # שלב 2: תמלול עם whisper
        result = model.transcribe(filename, language="he")
        text = result["text"]

        def check_text_with_gpt(text):
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",  # או "gpt-4" אם יש לך
                messages=[
                    {"role": "system", "content": "אתה מומחה אמינות שתפקידו לזהות מידע שגוי או מסוכן בטקסטים."},
                    {"role": "user", "content": f"""הטקסט הבא הוא תמלול של וידאו מטיקטוק. תבחן אותו ותחזיר:
        1. האם הוא מכיל מידע שגוי? (כן/לא)
        2. מה רמת האמינות של הטקסט באחוזים?
        3. אילו טענות שגויות קיימות בו?
        4. מה ההסבר הנכון?

        טקסט:
        \"\"\"{text}\"\"\"
        """}
                ],
                temperature=0.2
            )
            return response.choices[0].message.content.strip()
        print("📝 תמלול שהתקבל:", text)

        # בדיקת GPT אחרי התמלול
        gpt_analysis = check_text_with_gpt(text)

        # החזר את התוצאה
        return jsonify({
            "verdict": "תמלול הושלם",
            "reason": text,
            "gpt_analysis": gpt_analysis
        })

    except Exception as e:
        print("❌ שגיאה:", e)
        return jsonify({"error": str(e)}), 500
    finally:
        # מחק את הקובץ
        if os.path.exists(filename):
            os.remove(filename)

if __name__ == "__main__":
    app.run(port=5100, debug=True)