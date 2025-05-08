
import openai
import json
import time
from config import client

def fact_check_claims(transcript_segments):
    system_prompt = (
        "You are a fact-checking assistant. You are given a transcript of a video (e.g., from Whisper). "
        "Your job is to extract factual **claims** and assess them.\n\n"
        "Instructions:\n"
        "- Only return factual **claims** (ignore greetings, jokes, vague or emotional talk).\n"
        "- For each claim, return:\n"
        "  - start (float): start time in seconds\n"
        "  - end (float): end time in seconds\n"
        "  - sentence (string): the full claim\n"
        "  - verdict (string): 'True', 'False', or 'Not Verifiable'\n"
        "  - If verdict is 'False', add an 'explanation' field: a short reason + reliable source\n\n"
        "Respond in a valid JSON array format like this:\n"
        "[\n"
        "  {\n"
        "    \"start\": 5.44,\n"
        "    \"end\": 8.74,\n"
        "    \"sentence\": \"We know for certain that there are 21 alive—there’s no debate about that.\",\n"
        "    \"verdict\": \"False\",\n"
        "    \"explanation\": \"According to UN data, only 15 hostages are confirmed alive. See: https://example.org/un-hostage-report\"\n"
        "  }\n"
        "]\n"
        "Return only claims. Skip everything else."
    )

  
    user_message = json.dumps(transcript_segments, ensure_ascii=False)

    response = client.chat.completions.create(
        model="gpt-4",  # Use a supported model name
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        temperature=0
    )

    output = response['choices'][0]['message']['content']

    print("📡 Raw GPT output:")
    print(output)

    try:
        parsed = json.loads(output)
        return parsed
    except json.JSONDecodeError as e:
        print("❌ Could not parse GPT output:", e)
        return []

# ========== Run it ==========
if __name__ == "__main__":
    input_file = "hostage_segments_no_ids.json"  # Your Whisper-style input file
    output_file = "fact_checked_claims.json"

    with open(input_file, "r", encoding="utf-8") as f:
        segments = json.load(f)

    # Run claim detection + verdict check
    claims = fact_check_claims(segments)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(claims, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Finished. {len(claims)} factual claims evaluated.")
    print(f"📁 Output saved to: {output_file}")
