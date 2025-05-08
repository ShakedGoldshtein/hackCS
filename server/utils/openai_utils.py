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
