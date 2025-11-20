# core/data_store.py
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

# ========== DATA GAME ==========
ARMORS       = load_json("armors.json", {})
CITIES       = load_json("cities.json", {})
CRAFTING     = load_json("crafting.json", {})
DESCRIPTIONS = load_json("descriptions.json", {})
DIALOGS      = load_json("dialogs.json", {})
DROP         = load_json("drop.json", {})
EVENTS       = load_json("events.json", {})
ITEMS        = load_json("items.json", {})
MONSTERS     = load_json("monsters.json", {})
QUESTS       = load_json("quests.json", {})
SETTING      = load_json("settings.json", {})
SHOP         = load_json("shop.json", {})
WEAPONS      = load_json("weapons.json", {})
