import json
import joblib
from sentence_transformers import SentenceTransformer
from utils.openai_utils import client

# Load model and embedder
logreg = joblib.load(r"../log_reg/logreg_model.joblib")
embedder = SentenceTransformer("all-MiniLM-L6-v2")

# Inline system prompt
system_prompt = """
You are a formal logician. Your job is to convert informal arguments into clear abstract logical structures using symbolic patterns.

DO NOT paraphrase or summarize the comment.
DO NOT use full natural language sentences.
DO NOT include emotional or semantic content.

Use generalized variables like A, B, X, Y to express the reasoning pattern.
Make sure the abstracted form still preserves the reasoning or fallacy.

Use the fallacy label to guide the abstraction when one exists. However, even when the fallacy label is "none", you MUST still abstract the reasoning into symbolic logic.

Examples:
- "All Chinese are thin, so all thin people are Chinese" → "All A are B, so all B are A"
- "Why worry about our corruption? Others are worse." → "X is bad, but Y is worse, so X is acceptable"
- "Experts say A, so A must be true" → "Authorities claim X, so X"
- "Lack of transparency is expected since power resists scrutiny" → "If A has property B, then A will do C"

Be terse. Use a single statement format like:
Logical structure: All A are B, so all B are A
"""

def embed_logical_structure(logical_structure: str):
    return embedder.encode(logical_structure)

def f(blocks: str) -> str:
    try:
        parsed_blocks = json.loads(blocks)

        for block in parsed_blocks:
            claim = block.get("claim_text", "")

            # Send prompt directly via raw client (no file)
            response = client.responses.create(
                model="gpt-4.1-nano",
                input=[
                    {
                        "role": "system",
                        "content": [
                            {"type": "input_text", "text": system_prompt}
                        ]
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "input_text", "text": claim}
                        ]
                    }
                ],
                text={"format": {"type": "text"}},
                reasoning={},
                tools=[{
                    "type": "web_search_preview",
                    "user_location": {"type": "approximate"},
                    "search_context_size": "medium"
                }],
                temperature=0.3
            )

            logic = response.output[0].content[0].text.strip()
            if "Logical structure:" in logic:
                logic = logic.split("Logical structure:")[-1].strip()
            else:
                logic = "[FAILED]"

            embedding = embed_logical_structure(logic)
            pred_label = logreg.predict([embedding])[0]

            block["logical_structure"] = logic
            block["logical_fallacy"] = pred_label


        return json.dumps(parsed_blocks, ensure_ascii=False, indent=2)

    except Exception as e:
        print(f"[ERROR in f(blocks)]: {e}")
        return json.dumps({"error": str(e)})



import json
from pathlib import Path
from utils.openai_utils import pipe_unit


import json

# def assign_ids(json_str):
#     """
#     Takes a JSON string of list of dicts, adds an 'id' field to each, and returns a JSON string.

#     Parameters:
#         json_str (str): JSON string representing a list of dictionaries.

#     Returns:
#         str: JSON string with 'id' fields added or overwritten.
#     """
#     entries = json.loads(str(json_str))  # parse string to list of dicts

#     for i, entry in enumerate(entries):
#         entry['id'] = i  # add/overwrite 'id'

#     return str(json.dumps(entries))  # return result as JSON string





def check_files_exists(files):
    """
    Check if the files exist in the specified paths.
    """
    for file in files:
        if not Path(file).exists():
            current_dir = Path.cwd()
            raise FileNotFoundError(f"File not found: {file}, current directory: {current_dir}")

def generate_pings(transcript, model="gpt-4.1-mini"):
    print("Generating pings...")
    sysfs = [
        r'./prompts/clean_claims1.txt', 
        r'./prompts/create_debunks.txt']
    try:
        check_files_exists(sysfs)
        res = str(transcript)
        out = []
        for sysf in sysfs:
            print(f"[DEBUG]: pipe started for {sysf}")
            res = str(pipe_unit(sysf, res, model=model))
            # print(f"[DEBUG]: res_pipe: \n{res}")
            # res = assign_ids(out)
            out.append(res)

        blocks = out[-1]
        updated_entries = f(blocks)    
        print(f"[DEBUG]: pipe finished!")
        # print(f"[DEBUG]: out[-1]: {out[-1]}")
        # return json.loads(out[-1])
        return json.loads(updated_entries)

    except Exception as e:
        print(f"❌ Error in generate_pings: {e}")
        return {"error": str(e)}