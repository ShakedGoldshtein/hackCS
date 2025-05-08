from pathlib import Path
from utils.openai_utils import pipe_unit


def check_files_exists(files):
    """
    Check if the files exist in the specified paths.
    """
    for file in files:
        if not Path(file).exists():
            raise FileNotFoundError(f"File not found: {file}")

def generate_pings(transcript, model="gpt-4.1-nano"):
    sysfs = [
        r'../prompts/clean_claims1.txt', 
        r'../prompts/create_debunks.txt']
    
    check_files_exists(sysfs)

    out = []
    for sysf in sysfs:
        res = pipe_unit(sysf, transcript, model=model)
        out.append(res)
    
    return out[-1]
