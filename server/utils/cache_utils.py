from tinydb import TinyDB, Query
from datetime import datetime

def get_or_generate_entry(url, generator_func):
    db = TinyDB("db.json")
    responses_table = db.table("responses")
    Url = Query()
    
    existing = responses_table.search(Url.url == url)
    if existing:
        print("🎯 Cache hit! Retrieved cached response for url:", url)
        return existing[0]

    # If not found, run function to generate entries
    entries = generator_func(url)
    if not isinstance(entries, list):
        raise ValueError("Function must return a list of dicts")

    # Create new record
    created_at = datetime.utcnow().isoformat()
    new_doc = {
        "url": url,
        "created_at": created_at,
        "entries": entries
    }
    print("🌟 New entry created, url:", url)
    responses_table.insert(new_doc)
    return new_doc