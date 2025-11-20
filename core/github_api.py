# core/github_api.py
import os, json, base64, time, requests
from core.constants import TOKEN_FILE, MAX_CHAT_SIZE_KB
from core.io_json import load_json, save_json

# -----------------------
# KONFIGURASI REPO
# -----------------------
GITHUB_REPO = "Vyoker/Project-Days-Online"
API_BASE = f"https://api.github.com/repos/{GITHUB_REPO}/contents"

CHAT_PATH = "chat.json"
MARKET_PATH = "market.json"
BANLIST_PATH = "banlist.json"
EVENTS_PATH = "events.json"

# Token
def load_token_file():
    if os.path.exists(TOKEN_FILE):
        try:
            return open(TOKEN_FILE, "r", encoding="utf-8").read().strip()
        except:
            return None
    return None

GITHUB_TOKEN = load_token_file()
ONLINE_MODE = True if GITHUB_TOKEN else False

# ---------------------
# REQUEST HELPERS
# ---------------------
def _headers():
    h = {"Accept": "application/vnd.github.v3+json"}
    if GITHUB_TOKEN:
        h["Authorization"] = f"token {GITHUB_TOKEN}"
    return h

def _get_file_and_sha(path, timeout=8):
    url = f"{API_BASE}/{path}"
    try:
        resp = requests.get(url, headers=_headers(), timeout=timeout)
        if resp.status_code == 200:
            js = resp.json()
            content = base64.b64decode(js["content"]).decode("utf-8")
            return json.loads(content), js["sha"], 200
        return None, None, resp.status_code
    except Exception as e:
        return None, None, f"error: {e}"

def _put_file(path, data, sha=None, commit_msg="update file"):
    url = f"{API_BASE}/{path}"
    payload = {
        "message": commit_msg,
        "content": base64.b64encode(json.dumps(data, indent=2).encode()).decode(),
    }
    if sha:
        payload["sha"] = sha
    try:
        resp = requests.put(url, headers=_headers(), json=payload, timeout=8)
        return resp, resp.status_code
    except Exception as e:
        return None, str(e)

def fetch_json_raw(path):
    url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/{path}"
    try:
        resp = requests.get(url, timeout=6)
        return resp.json(), resp.status_code
    except:
        return None, 0

# ---------------------
# CHAT SYSTEM (Online)
# ---------------------
def show_chat_preview(limit=20):
    data, status = fetch_json_raw(CHAT_PATH)
    if status != 200:
        return []
    return data[-limit:]

def send_chat_message(player, msg):
    if not ONLINE_MODE:
        return False, "Offline"

    # Ambil file dan sha
    chat_data, sha, status = _get_file_and_sha(CHAT_PATH)
    if status != 200:
        chat_data = []  # fallback

    entry = {
        "user": player.get("name","Unknown"),
        "uuid": player.get("uuid",""),
        "time": time.strftime("%H:%M"),
        "loc": player.get("location","?"),
        "msg": msg,
    }
    chat_data.append(entry)

    # trimming ukuran chat
    size_kb = len(json.dumps(chat_data).encode()) / 1024
    if size_kb > MAX_CHAT_SIZE_KB:
        chat_data = chat_data[-200:]  # simpan 200 pesan terakhir

    resp, status = _put_file(CHAT_PATH, chat_data, sha=sha, commit_msg="Chat update")
    if status not in (200,201):
        return False, f"Gagal update chat ({status})"
    return True, "ok"

# ---------------------
# EVENTS (Gift / Claim)
# ---------------------
def fetch_and_claim_events_for_player(player):
    events, sha, status = _get_file_and_sha(EVENTS_PATH)
    if status != 200:
        return []

    claimed = []
    remove_keys = []
    uuid = player.get("uuid")

    for key, ev in events.items():
        if ev.get("to") == uuid:
            # tambahkan hadiah
            items = ev.get("items", {})
            for it, qty in items.items():
                player["inventory"][it] = player["inventory"].get(it, 0) + qty

            claimed.append(ev)
            remove_keys.append(key)

    # hapus event yang sudah di-claim
    for k in remove_keys:
        events.pop(k, None)

    # push balik
    _put_file(EVENTS_PATH, events, sha=sha, commit_msg="Claim event")
    return claimed

def append_event(to_uuid, item, qty=1, sender="SYSTEM"):
    events, sha, status = _get_file_and_sha(EVENTS_PATH)
    if status != 200:
        events = {}
    eid = str(int(time.time() * 1000))
    events[eid] = {"to": to_uuid, "items": {item: qty}, "from": sender, "ts": int(time.time())}
    resp, st = _put_file(EVENTS_PATH, events, sha=sha, commit_msg="Gift event")
    return st in (200,201)

# ---------------------
# BAN SYSTEM
# ---------------------
def fetch_banlist():
    data, status = fetch_json_raw(BANLIST_PATH)
    return data if status == 200 else {}

def is_banned(uuid_str):
    bans = fetch_banlist()
    return uuid_str in bans

def append_ban(uuid_target, name, minutes=10):
    bans, sha, status = _get_file_and_sha(BANLIST_PATH)
    if status != 200:
        bans = {}
    bans[uuid_target] = {"name": name, "until": int(time.time()) + minutes * 60}
    resp, st = _put_file(BANLIST_PATH, bans, sha=sha, commit_msg="Add ban")
    return st in (200,201)

# ---------------------
# MARKETPLACE
# ---------------------
def market_refresh():
    remote, status = fetch_json_raw(MARKET_PATH)
    if status == 200 and isinstance(remote, list):
        save_json("market.json", remote)  # sync offline
        return remote
    return load_json("market.json", [])  # offline fallback

def push_market(market_list):
    data, sha, status = _get_file_and_sha(MARKET_PATH)
    resp, st = _put_file(MARKET_PATH, market_list, sha=sha, commit_msg="Market update")
    return st in (200,201)

# ---------------------
# QUESTS
# ---------------------
def fetch_quests():
    data, status = fetch_json_raw("quests.json")
    return data if status == 200 else {}

__all__ = [
    "ONLINE_MODE",
    "fetch_and_claim_events_for_player",
    "append_event",
    "show_chat_preview",
    "send_chat_message",
    "fetch_banlist",
    "append_ban",
    "is_banned",
    "market_refresh",
    "push_market",
    "fetch_quests",
]
