from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess
import os
import uuid
import whisper
import openai
from dotenv import load_dotenv
from pathlib import Path
import re
import nltk
nltk.download('punkt', quiet=True)
from nltk.tokenize import sent_tokenize


load_dotenv(dotenv_path=Path("secret.env").resolve())
openai.api_key = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)
CORS(app, resources={r"/analyze": {"origins": "*"}}, methods=["GET", "POST", "OPTIONS"], allow_headers=["Content-Type"])
model = whisper.load_model("large")  # אפשר גם tiny או base אם אתה רוצה שזה יהיה מהיר

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

        # שלב ביניים: ניקוי ופישוט טקסט
        def gpt_clean_text(text):
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-4-turbo",
                    messages=[
                        {"role": "system", "content": "אתה מנקה טקסטים קלוקלים ומפשט ניסוחים כדי שיהיה ניתן להבין ולנתח אותם. הפלט שלך צריך להיות טקסט ברור, תמציתי וללא שגיאות לשוניות או תחביריות."},
                        {"role": "user", "content": f"פשט את הטקסט הבא כך שיהיה ברור וקריא יותר:\n{text}"}
                    ],
                    temperature=0.3
                )
                return response.choices[0].message.content.strip()
            except Exception as e:
                print("❌ שגיאה בפישוט הטקסט:", e)
                return text  # אם נכשל, נמשיך עם הטקסט המקורי

        def check_text_with_gpt(text):
            text = gpt_clean_text(text)
            split_response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",  # או gpt-4 אם יש לך גישה
                messages=[
                    {"role": "system", "content": "אתה עוזר NLP. חלק טקסט לטענות נפרדות. כל טענה בשורה חדשה בלבד."},
                    {"role": "user", "content": f"חלק את הטקסט הבא לטענות נפרדות. כל טענה צריכה להיות קצרה וממוקדת:\n{text}"}
                ],
                temperature=0.3
            )
            claims = [line.strip() for line in split_response.choices[0].message.content.strip().split('\n') if line.strip()]

            answers = []
            for claim in claims:
                try:
                    response = openai.ChatCompletion.create(
                        model="gpt-3.5-turbo",  # או gpt-4 אם יש לך גישה
                        messages=[
                            {"role": "system", "content": "אתה בודק עובדות מדויק. קבל טענה וענה האם היא נכונה או שגויה, ולמה."},
                            {"role": "user", "content": f"האם המשפט הבא נכון או שגוי? ענה רק 'נכון' או 'שגוי' ולאחר מכן הסבר מדוע:\n\"{claim}\""}
                        ],
                        temperature=0.2
                    )
                    answer_text = response.choices[0].message.content.strip()
                    verdict = "unknown"
                    if any(keyword in answer_text.lower() for keyword in ["נכון", "מדויק", "אמיתי", "תקף"]):
                        verdict = "true"
                    elif any(keyword in answer_text.lower() for keyword in ["שגוי", "לא נכון", "לא מדויק", "לא תקף"]):
                        verdict = "false"

                    answers.append({
                        "claim": claim,
                        "verdict": verdict,
                        "gpt_answer": answer_text
                    })
                except Exception as e:
                    answers.append({
                        "claim": claim,
                        "verdict": "unknown",
                        "gpt_answer": f"שגיאה בבדיקה: {str(e)}"
                    })

            return answers

        print("📝 תמלול שהתקבל:", text)

        # בדיקת GPT אחרי התמלול
        gpt_analysis = check_text_with_gpt(text)

        # החזר את התוצאה
        return jsonify({
            "verdict": "תמלול הושלם",
            "reason": text,
            "gpt_analysis": gpt_analysis  # עכשיו זו רשימת טענות עם ניתוחים
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