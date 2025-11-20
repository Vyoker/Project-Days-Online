# core/io_json.py
import os
import json

DATA_PATH = "data"

def load_json(filename, default=None):
    path = os.path.join(DATA_PATH, filename)
    try:
        if not os.path.exists(path):
            return default if default is not None else {}
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return default if default is not None else {}

def save_json(filename, data):
    path = os.path.join(DATA_PATH, filename)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except:
        return False
