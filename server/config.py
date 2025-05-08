from dotenv import load_dotenv
from pathlib import Path
import os
from openai import OpenAI

load_dotenv(Path("secret.env").resolve())

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("Missing OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)