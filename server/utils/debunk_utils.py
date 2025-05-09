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
    sysfs = [
        r'./prompts/clean_claims1.txt', 
        r'./prompts/create_debunks.txt']
    try:
        check_files_exists(sysfs)

        res = transcript
        out = []
        for sysf in sysfs:
            # print(f"[DEBUG]: res type: {type(res)}")
            res = pipe_unit(sysf, res, model=model)
            # res = assign_ids(out)
            out.append(res)
        
        return json.loads(out[-1])

    except Exception as e:
        print(f"❌ Error in generate_pings: {e}")
        return {"error": str(e)}