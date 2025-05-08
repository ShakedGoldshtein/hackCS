from openai import OpenAI
from faster_whisper import WhisperModel
import os

model = WhisperModel("medium", compute_type="int8")


def transcribe_audio(file_path, language="he"):
    segments_generator, _ = model.transcribe(file_path, language=language, beam_size=2)

    transcript = []
    for i, segment in enumerate(segments_generator):
        transcript.append({
            "start": float(segment.start),
            "end": float(segment.end),
            "text": segment.text.strip()
        })

    return transcript
