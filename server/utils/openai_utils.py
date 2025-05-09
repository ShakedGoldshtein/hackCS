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



def pipe_unit(system_prompt_file: str, user_prompt: str, model="gpt-4.1-nano") -> dict:
    """
    Send a message to the OpenAI API and return the response.
    """
    with open(system_prompt_file, "r", encoding="utf-8") as f:
        system_prompt = f.read()

    response = client.responses.create(
        model=model,
        input=[
            {
                "role": "system",
                "content": [
                    {
                        "type": "input_text",
                        "text": system_prompt
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": user_prompt
                    }
                ]
            }
        ],
        text={
            "format": {
                "type": "text"
            }
        },
        reasoning={},
        tools=[
        {
            "type": "web_search_preview",
            "user_location": {
                "type": "approximate"
            },
            "search_context_size": "medium"
            }
        ],
        temperature=0.2,
        # max_output_tokens=4096,
        top_p=1,
        store=False
    )
    text = response.output[0].content[0].text
    return text.strip()



## TTS
def generate_audio_response(prompt):

    system_prompt_file = r"./prompts/tts_reactor.txt"
    with open(system_prompt_file, "r", encoding="utf-8") as f:
        system_prompt = f.read()
    response = client.audio.speech.create(
    model="gpt-4o-mini-tts",
    voice="shimmer",
    instructions=system_prompt,
    input=prompt,
    response_format="wav"
    )
<<<<<<< HEAD
    return response
=======
>>>>>>> 8028bbdf89bbb4c6a4f30b745219d67662c5f926

    # audio_bytes = audio_response.content
    # Audio(data=audio_bytes)