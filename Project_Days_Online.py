# Project_Days_Online v3.1
# Save as: Project_Days_Online.py
# Requires: pip install requests rich
import os, sys, time, random, json, uuid, requests
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()

# --- CONFIG ---
GAME_DIR = os.path.expanduser("~") + "/Project_Days"
DATA_DIR = os.path.join(GAME_DIR, "data")
FIREBASE_URL = "https://project-days-online-default-rtdb.asia-southeast1.firebasedatabase.app"  # <-- REPLACE with your Firebase Realtime Database URL (no trailing slash)
ADMIN_KEY_FILE = os.path.join(GAME_DIR, "admin_key.txt")
ADMIN_KEY = "VYOKER-GM-11022025"  # default master key (installer_admin will write to admin_key.txt)

# ensure data dir
os.makedirs(DATA_DIR, exist_ok=True)

# --- JSON loader (local fallback, remote from GitHub if needed) ---
def load_json_local(name, default):
    path = os.path.join(DATA_DIR, f"{name}.json")
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default
    else:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default, f, indent=2, ensure_ascii=False)
        return default

# minimal defaults if file missing
DEFAULT_ITEMS = {}
DEFAULT_WEAPONS = {}
DEFAULT_ARMORS = {}
DEFAULT_MONSTERS = {}
DEFAULT_DESCRIPTIONS = {}
DEFAULT_CRAFTING = {}
DEFAULT_CITIES = {}
DEFAULT_EVENTS = []
DEFAULT_SETTINGS = {"version":"3.1.0","data_pack":"full"}
DEFAULT_DIALOGS = {}
DEFAULT_QUESTS = {}

ITEMS = load_json_local("items", DEFAULT_ITEMS)
WEAPONS = load_json_local("weapons", DEFAULT_WEAPONS)
ARMORS = load_json_local("armors", DEFAULT_ARMORS)
MONSTERS = load_json_local("monsters", DEFAULT_MONSTERS)
DESCRIPTIONS = load_json_local("descriptions", DEFAULT_DESCRIPTIONS)
CRAFTING = load_json_local("crafting", DEFAULT_CRAFTING)
CITIES = load_json_local("cities", DEFAULT_CITIES)
EVENTS = load_json_local("events", DEFAULT_EVENTS)
SETTINGS = load_json_local("settings", DEFAULT_SETTINGS)
DIALOGS = load_json_local("dialogs", DEFAULT_DIALOGS)
QUESTS = load_json_local("quests", DEFAULT_QUESTS)

# --- FIREBASE HELPERS ---
def firebase_put(path, data):
    try:
        url = f"{FIREBASE_URL.rstrip('/')}/{path}.json"
        r = requests.put(url, json=data, timeout=6)
        return r.status_code in (200,201)
    except Exception as e:
        return False

def firebase_post(path, data):
    try:
        url = f"{FIREBASE_URL.rstrip('/')}/{path}.json"
        r = requests.post(url, json=data, timeout=6)
        return r.status_code in (200,201)
    except Exception:
        return False

def firebase_get(path):
    try:
        url = f"{FIREBASE_URL.rstrip('/')}/{path}.json"
        r = requests.get(url, timeout=6)
        if r.status_code==200:
            return r.json()
    except Exception:
        pass
    return None

# --- PLAYER SAVE/LOAD (simple file-based) ---
def gen_uuid():
    return str(uuid.uuid4())

def create_new_player():
    name = input("Masukkan nama karakter: ").strip() or "Player"
    pid = gen_uuid()
    player = {
        "UUID": pid,
        "NAME": name,
        "Level": 1,
        "EXP": 0,
        "HP": 100,
        "MaxHP": 100,
        "Energy": 100,
        "Hunger": 100,
        "ATK": 5,
        "DEF": 2,
        "DEX": 3,
        "Weapon": "Tangan Kosong",
        "Armor": "Pakaian Lusuh",
        "location": "Hutan Pinggiran",
        "created": time.strftime("%Y-%m-%d")
    }
    save_player_local(player)
    # send to firebase player tracker (best effort)
    try:
        firebase_put(f"players/{pid}", {
            "uuid": pid,
            "name": player["NAME"],
            "level": player["Level"],
            "location": player["location"],
            "last_online": int(time.time()),
            "created": player["created"]
        })
    except:
        pass
    return player

def save_player_local(player):
    os.makedirs(os.path.join(GAME_DIR,"saves"), exist_ok=True)
    path = os.path.join(GAME_DIR,"saves", f"{player['UUID']}.json")
    with open(path,"w",encoding="utf-8") as f:
        json.dump(player,f,indent=2,ensure_ascii=False)

def load_player_from_file(path):
    try:
        with open(path,"r",encoding="utf-8") as f:
            return json.load(f)
    except:
        return None

def list_local_saves():
    sdir = os.path.join(GAME_DIR,"saves")
    if not os.path.exists(sdir):
        return []
    files = [os.path.join(sdir,f) for f in os.listdir(sdir) if f.endswith(".json")]
    return files

# --- FIREBASE CHAT ---
def send_chat(player, msg):
    data = {"user": player["NAME"], "uuid": player["UUID"], "loc": player.get("location","-"), "msg": msg, "time": int(time.time())}
    return firebase_post("chat", data)

def fetch_chat(limit=20):
    data = firebase_get("chat") or {}
    msgs = list(data.values()) if isinstance(data, dict) else []
    msgs = sorted(msgs, key=lambda x: x.get("time",0))
    return msgs[-limit:]

# --- ADMIN HELPERS ---
def is_admin(player):
    # check local admin_key.txt presence and match
    try:
        if os.path.exists(ADMIN_KEY_FILE):
            with open(ADMIN_KEY_FILE,"r",encoding="utf-8") as f:
                k = f.read().strip()
            if k==ADMIN_KEY:
                return True
    except:
        pass
    # also check firebase admins list
    ad = firebase_get(f"admins/{player['UUID']}")
    return bool(ad)

def admin_login(player, key):
    if key!=ADMIN_KEY:
        return False, "Kunci admin salah."
    # write admin_key file locally (for admin installer only)
    try:
        with open(ADMIN_KEY_FILE,"w",encoding="utf-8") as f:
            f.write(key)
    except:
        pass
    # register admin uuid in firebase
    firebase_put(f"admins/{player['UUID']}", True)
    return True, "Mode Admin diaktifkan."

def admin_logout(player):
    # remove local key file if exists
    try:
        if os.path.exists(ADMIN_KEY_FILE):
            os.remove(ADMIN_KEY_FILE)
    except:
        pass
    firebase_put(f"admins/{player['UUID']}", False)
    return "Admin mode dimatikan."

def admin_gift(player, target_uuid, item, qty):
    entry = {"to": target_uuid, "item": item, "qty": int(qty), "from": player["UUID"], "time": int(time.time())}
    return firebase_post("gifts", entry)

def admin_ban(player, target_uuid, minutes):
    until = int(time.time()) + int(minutes)*60
    entry = {"uuid": target_uuid, "until": until, "by": player["UUID"], "time": int(time.time())}
    return firebase_post("banlist", entry)

def admin_unban(player, target_uuid):
    # remove all banlist entries for uuid (simple approach)
    bans = firebase_get("banlist") or {}
    modified = False
    if isinstance(bans, dict):
        for k,v in bans.items():
            if v.get("uuid")==target_uuid:
                firebase_put(f"banlist/{k}", None)
                modified = True
    return modified

def admin_broadcast(player, text):
    entry = {"from": player["UUID"], "msg": text, "time": int(time.time())}
    return firebase_post("broadcast", entry)

def admin_list_players():
    data = firebase_get("players") or {}
    out = []
    if isinstance(data, dict):
        for uuid,info in data.items():
            out.append({"uuid": uuid, "name": info.get("name","-"), "level": info.get("level",1), "location": info.get("location","-"), "last_online": info.get("last_online",0)})
    return out

def admin_show_player_detail(uuid):
    d = firebase_get(f"players/{uuid}") or {}
    return d

# --- UI / MENU (must preserve original layout, only add UUID) ---
def clear():
    os.system("clear")

def show_main_menu(player):
    clear()
    header = "[bold white on black]  PROJECT DAYS - APOCALYPSE  [/]\n"
    console.print(header)
    console.print(f"Nama   : {player['NAME']}")
    console.print(f"Level  : {player['Level']}    EXP: {player.get('EXP',0)}")
    console.print(f"HP     : {player['HP']} / {player['MaxHP']}    Energy: {player.get('Energy',100)}")
    console.print(f"ATK    : {player['ATK']}    DEF: {player['DEF']}    DEX: {player['DEX']}")
    console.print(f"Weapon : {player.get('Weapon','-')}    Armor: {player.get('Armor','-')}")
    # Mode line - change to Firebase
    console.print(f"\nMode   : Online (Firebase)")
    # ADD UUID line (only addition)
    console.print(f"UUID   : {player['UUID']}\n")
    console.print("1. Inventory")
    console.print("2. Explore")
    console.print("3. Travel")
    console.print("4. Toko")
    console.print("5. Chatting")
    console.print("6. Exit (Save & Quit)")
    choice = input("\nPilih menu: ").strip()
    return choice

def load_game_menu():
    clear()
    console.print("[bold]LOAD GAME[/]\n")
    saves = list_local_saves()
    if not saves:
        console.print("Tidak ada save. Mulai game baru.\n")
        return None
    for i,p in enumerate(saves, start=1):
        data = load_player_from_file(p) or {}
        name = data.get("NAME","-")
        level = data.get("Level",1)
        uuidv = data.get("UUID","-")
        console.print(f"{i}. {name} (Lvl {level})")
        console.print(f"   UUID : {uuidv}\n")
    idx = input("Pilih slot number atau Enter untuk kembali: ").strip()
    if not idx:
        return None
    try:
        idx = int(idx)-1
        return load_player_from_file(saves[idx])
    except:
        return None

# --- CHAT MENU (uses firebase) ---
def chat_menu(player):
    clear()
    console.print("[bold]📻 RADIO SURVIVOR — Chat Global (Firebase)[/]\n")
    def display():
        msgs = fetch_chat(30)
        clear()
        console.print("[bold]📻 RADIO SURVIVOR — Chat Global (Firebase)[/]\n")
        for m in msgs:
            t = time.strftime("%H:%M:%S", time.localtime(m.get("time",0)))
            console.print(f"[{t}] [{m.get('loc','-')}] {m.get('user')}: {m.get('msg')}")
    display()
    while True:
        msg = input("\nPesan (/exit): ").strip()
        if msg.lower()=="/exit":
            return
        # admin command handling
        if msg.startswith("/admin"):
            parts = msg.split()
            if len(parts)>=3 and parts[1]=="login":
                ok,txt = admin_login(player, parts[2])
                console.print(txt)
                continue
            elif parts[1]=="logout":
                console.print(admin_logout(player))
                continue
        # other admin commands
        if msg.startswith("/player") or msg.startswith("/gift") or msg.startswith("/ban") or msg.startswith("/broadcast") or msg.startswith("/event") or msg.startswith("/unban"):
            if not is_admin(player):
                console.print("❌ Kamu bukan admin.")
                continue
            # process admin commands
            parts = msg.split()
            cmd = parts[0]
            if cmd=="/player":
                if len(parts)==1:
                    lst = admin_list_players()
                    for p in lst:
                        console.print(f"- {p['name']} (Lvl {p['level']}) UUID: {p['uuid']} Loc: {p['location']}")
                else:
                    info = admin_show_player_detail(parts[1]) or {}
                    console.print(json.dumps(info, indent=2, ensure_ascii=False))
                continue
            if cmd=="/gift":
                _, tgt, item, qty = parts[:4]
                admin_gift(player, tgt, item, qty)
                console.print("🎁 Gift dikirim.")
                continue
            if cmd=="/ban":
                _, tgt, minutes = parts[:3]
                admin_ban(player, tgt, minutes)
                console.print("⛔ Player dibanned.")
                continue
            if cmd=="/unban":
                _, tgt = parts[:2]
                admin_unban(player, tgt)
                console.print("✅ Player di-unban.")
                continue
            if cmd=="/broadcast":
                text = msg.replace("/broadcast ","",1)
                admin_broadcast(player, text)
                console.print("📢 Broadcast terkirim.")
                continue
            if cmd=="/event":
                _, date, reward = parts[:3]
                item,qty = reward.split(":")
                firebase_post("events_manual", {"date":date,"item":item,"qty":int(qty)})
                console.print("🔥 Event manual ditambahkan.")
                continue
        # normal chat send
        ok = send_chat(player, msg)
        if not ok:
            console.print("⚠️ Gagal mengirim pesan. Cek koneksi.")
        display()

# --- MAIN LOOP ---
def main():
    clear()
    console.print(Panel("Project Days Online v3.1", expand=False))
    console.print("1. New Game")
    console.print("2. Load Game")
    console.print("3. Quit")
    sel = input("Pilihan: ").strip()
    if sel=="1":
        player = create_new_player()
    elif sel=="2":
        player = load_game_menu()
        if not player:
            return
    else:
        return
    # main game menu loop
    while True:
        choice = show_main_menu(player)
        if choice=="1":
            console.print("Inventory (placeholder)")
            time.sleep(1)
        elif choice=="2":
            console.print("Explore (placeholder)")
            time.sleep(1)
        elif choice=="3":
            console.print("Travel (placeholder)")
            time.sleep(1)
        elif choice=="4":
            console.print("Toko (placeholder)")
            time.sleep(1)
        elif choice=="5":
            chat_menu(player)
        elif choice=="6":
            save_player_local(player)
            console.print("Save completed. Bye.")
            break
        else:
            console.print("Pilihan tidak dikenal.")
            time.sleep(0.5)

if __name__=="__main__":
    main()
