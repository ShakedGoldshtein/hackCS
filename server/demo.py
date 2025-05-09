


transcript = r"""[
  {
    "id": 1,
    "start": <seconds>,
    "end": <seconds>,
    "claim_text": "Exact text of the claim",
    "debunking_information": "Brief explanation of why the claim is incorrect or logically flawed. Leave empty if unverified.",
    "severity": "low" | "high" | "unverified",
    "misinformation_type": "factual" | "logical"
  }
  // More debunked claims
]"""

from sentence_transformers import SentenceTransformer

from utils.debunk_utils import f
print(f(transcript))