# Project Days - Apocalypse
# Version 2.3

import os, sys, time, random, json, base64, threading, select, uuid
import requests

from rich.console import Console
from rich.panel import Panel
from rich.align import Align
from rich.text import Text
from rich import box
from rich.table import Table

console = Console()

# ====== Theme colors ======
HEADER_BG = "grey11 on rgb(85,52,36)"   # dark rust
ACCENT = "rgb(182,121,82)"             # rusty orange
HIGHLIGHT = "rgb(210,180,140)"         # tan
DANGER = "rgb(140,34,34)"              # dark red

# ====== UTILITIES ======
def slow(text, delay=0.01, style=None):
    """Print text with slow-typing effect."""
    s = str(text)
    for c in s:
        sys.stdout.write(c)
        sys.stdout.flush()
        time.sleep(delay)
    print()

def loading_animation(message="Loading", duration=1.8, speed=0.25):
    """Simple loading dots animation using rich."""
    end = time.time() + duration
    i = 0
    while time.time() < end:
        dots = "." * ((i % 3) + 1)
        console.print(Panel(f"[{HIGHLIGHT}]{message}[/]{dots}", style=ACCENT, box=box.ROUNDED), end="\r")
        time.sleep(speed)
        i += 1
    console.print("")

def clear():
    os.system("clear" if os.name != "nt" else "cls")
    header = Text(" ☣ PROJECT DAYS — APOCALYPSE ☣ ", style=f"bold {HIGHLIGHT} on {HEADER_BG}")
    console.print(Panel(header, box=box.DOUBLE, style=HEADER_BG))

# ====== GLOBALS & DATA ======
SAVE_FOLDER = "saves"
os.makedirs(SAVE_FOLDER, exist_ok=True)

# --- Weapons / Armor / Items ---
weapon_list = {
    "Tangan Kosong": {"type": "melee", "atk": 5},
    "Pisau": {"type": "melee", "atk": 8},
    "Palu": {"type": "melee", "atk": 12},
    "Tombak": {"type": "melee", "atk": 16},
    "Kampak": {"type": "melee", "atk": 20},
    "Pedang": {"type": "melee", "atk": 25},
    "Pistol": {"type": "gun", "ammo": "Ammo 9mm", "atk": 35, "scale": 0.05},
    "Shotgun": {"type": "gun", "ammo": "Ammo 12mm", "atk": 55, "scale": 0.05},
    "Sniper": {"type": "gun", "ammo": "Ammo 7.2mm", "atk": 95, "scale": 0.05},
    "Senapan Serbu": {"type": "gun", "ammo": "Ammo 7.2mm", "atk": 60, "scale": 0.05},
}

armor_list = {
    "Pakaian Lusuh": {"def": 5},
    "Kaos": {"def": 8},
    "Kaos Panjang": {"def": 10},
    "Sweater": {"def": 14},
    "Jaket": {"def": 20},
    "Rompi Lv1": {"def": 30},
    "Rompi Lv2": {"def": 40},
    "Rompi Lv3": {"def": 50},
}

zombie_types = {
    "Zombie": {"hp_mod": 1.0, "atk_mod": 1.0, "def_mod": 1.0, "dodge": 0},
    "Zombie Atlit": {"hp_mod": 0.7, "atk_mod": 0.8, "def_mod": 0.8, "dodge": 35},
    "Zombie Berotot": {"hp_mod": 1.35, "atk_mod": 1.3, "def_mod": 1.0, "dodge": 0},
    "Zombie Armored": {"hp_mod": 1.3, "atk_mod": 1.1, "def_mod": 1.4, "dodge": 0},
    "Zombie Mutant": {"hp_mod": 1.4, "atk_mod": 1.3, "def_mod": 1.25, "dodge": 15},
}

item_effects = {
    "Perban": {"type": "heal", "heal": 25},
    "Herbal": {"type": "heal", "heal": 15},
    "Painkiller": {"type": "heal", "heal": 35},
    "Medkit": {"type": "heal", "heal": 50},
    "Makanan": {"type": "heal_energy", "heal": 10, "energy": 30},
    "Minuman": {"type": "energy", "energy": 20},
}

# ====== GITHUB PASSIVE BACKEND CONFIG ======
GITHUB_REPO = "Vyoker/Project-Days-Online"
CHAT_PATH = "chat.json"
MARKET_PATH = "market.json"
BANLIST_PATH = "banlist.json"
EVENTS_PATH = "events.json"
TOKEN_FILE = "gh_token.txt"  # file di folder game berisi token (recommended)
ADMIN_FILE = "admin.txt"     # local file berisi admin UUID

def load_github_token():
    if os.path.exists(TOKEN_FILE):
        try:
            return open(TOKEN_FILE, "r").read().strip()
        except:
            return None
    return None

GITHUB_TOKEN = load_github_token()
API_BASE = f"https://api.github.com/repos/{GITHUB_REPO}/contents"

# ONLINE MODE flag (updated at startup)
ONLINE_MODE = False

# --- GitHub API helpers ---
def _get_file_and_sha(path, timeout=8):
    url = f"{API_BASE}/{path}"
    headers = {"Accept": "application/vnd.github.v3+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"
    try:
        resp = requests.get(url, headers=headers, timeout=timeout)
    except Exception as e:
        return None, None, getattr(e, 'errno', -1)
    if resp.status_code == 200:
        js = resp.json()
        content_b64 = js.get("content", "")
        try:
            raw = base64.b64decode(content_b64).decode("utf-8")
            parsed = json.loads(raw) if raw.strip() else []
        except Exception:
            parsed = []
        sha = js.get("sha")
        return parsed, sha, 200
    elif resp.status_code == 404:
        return [], None, 404
    else:
        return None, None, resp.status_code

def _put_file(path, data_list, sha=None, commit_msg="Update from Project Days", timeout=12):
    url = f"{API_BASE}/{path}"
    headers = {"Accept": "application/vnd.github.v3+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"
    content_str = json.dumps(data_list, indent=2, ensure_ascii=False)
    content_b64 = base64.b64encode(content_str.encode("utf-8")).decode("utf-8")
    payload = {"message": commit_msg, "content": content_b64}
    if sha:
        payload["sha"] = sha
    try:
        resp = requests.put(url, headers=headers, data=json.dumps(payload), timeout=timeout)
    except Exception as e:
        return None, str(e)
    return resp, resp.status_code

def safe_append_and_put(path, new_entry, max_retries=4, backoff_base=1.2):
    last_err = None
    for attempt in range(1, max_retries + 1):
        existing, sha, status = _get_file_and_sha(path)
        if existing is None:
            last_err = f"GET failed status {status}"
            time.sleep(backoff_base * attempt)
            continue
        if not isinstance(existing, list):
            existing = []
        existing.append(new_entry)
        time.sleep(random.uniform(0.2, 0.9))
        resp, code_or_err = _put_file(path, existing, sha=sha, commit_msg=f"Update {path} by ProjectDays")
        if resp is None:
            last_err = f"PUT exception: {code_or_err}"
            time.sleep(backoff_base * attempt)
            continue
        if resp.status_code in (200, 201):
            return True, "ok"
        elif resp.status_code == 409:
            last_err = f"409 conflict"
            time.sleep(backoff_base * attempt + random.uniform(0,0.8))
            continue
        else:
            last_err = f"PUT err {resp.status_code}: {resp.text}"
            break
    return False, last_err

def fetch_json_raw(path, timeout=8):
    raw_url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/{path}"
    try:
        r = requests.get(raw_url, timeout=timeout)
        if r.status_code == 200:
            try:
                return json.loads(r.text), 200
            except:
                return [], 200
    except:
        pass
    data, sha, status = _get_file_and_sha(path)
    if data is None:
        return [], status
    return data, 200

def check_github_token_valid():
    """
    Cek token minimal: bila GITHUB_TOKEN tidak ada, warn.
    Jika ada, coba GET repo root to ensure token valid (or public access OK).
    """
    global ONLINE_MODE
    if not GITHUB_TOKEN:
        ONLINE_MODE = False
        return False, "Token tidak ditemukan (gh_token.txt). Marketplace/chat memerlukan token untuk mengirim."
    # try list contents root
    url = f"https://api.github.com/repos/{GITHUB_REPO}"
    headers = {"Accept": "application/vnd.github.v3+json", "Authorization": f"token {GITHUB_TOKEN}"}
    try:
        r = requests.get(url, headers=headers, timeout=8)
        if r.status_code == 200:
            ONLINE_MODE = True
            return True, "Token valid"
        else:
            ONLINE_MODE = False
            return False, f"Token gagal/akses repo (status {r.status_code})"
    except Exception as e:
        ONLINE_MODE = False
        return False, f"Error koneksi: {e}"

# ===== Banlist & Events helpers =====
def fetch_banlist():
    data, status = fetch_json_raw(BANLIST_PATH)
    if status != 200:
        return []
    return data

def is_banned(uuid_str):
    bans = fetch_banlist()
    now = int(time.time())
    for b in bans:
        try:
            if b.get("uuid") == uuid_str and int(b.get("until", 0)) > now:
                return True, b
        except:
            continue
    return False, None

def append_ban(uuid_target, name, minutes=10):
    until = int(time.time()) + minutes * 60
    entry = {"uuid": uuid_target, "name": name, "until": until}
    return safe_append_and_put(BANLIST_PATH, entry)

def fetch_and_claim_events_for_player(player):
    """
    Fetch events.json, deliver events for player['UUID'], and remove them from remote.
    """
    # get file and sha (we need to overwrite with filtered list)
    existing, sha, status = _get_file_and_sha(EVENTS_PATH)
    if existing is None:
        return []
    if not isinstance(existing, list):
        existing = []
    deliver = []
    remaining = []
    for e in existing:
        if e.get("to") == player.get("UUID"):
            deliver.append(e)
        else:
            remaining.append(e)
    # overwrite remote with remaining
    try:
        resp, code = _put_file(EVENTS_PATH, remaining, sha=sha, commit_msg=f"Claim events for {player.get('UUID')}")
        # ignore failure for now (could retry)
    except:
        pass
    # actually apply items to player inventory
    for ev in deliver:
        item = ev.get("item")
        qty = int(ev.get("qty", 1))
        if item:
            player["inventory"][item] = player["inventory"].get(item, 0) + qty
    return deliver

def append_event(to_uuid, item, qty=1, sender="SYSTEM"):
    entry = {"to": to_uuid, "item": item, "qty": int(qty), "from": sender, "time": time.strftime("%H:%M:%S")}
    return safe_append_and_put(EVENTS_PATH, entry)

# ====== SEND CHAT (with auto-reset on file size) ======
MAX_CHAT_SIZE_KB = 500  # reset threshold

def send_chat_message(player, msg):
    """
    Send chat message with checks:
    - ban check
    - auto-reset chat file if too large
    - safe append to chat.json
    """
    # ban check
    banned, ban_entry = is_banned(player.get("UUID"))
    if banned:
        until_t = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ban_entry.get("until", 0)))
        return False, f"Kamu diblokir dari chat sampai {until_t} (UUID: {ban_entry.get('uuid')})"

    # fetch existing to check size
    existing, sha, status = _get_file_and_sha(CHAT_PATH)
    if existing is None:
        existing = []

    # current size in KB
    try:
        size_kb = len(json.dumps(existing)) / 1024.0
    except:
        size_kb = 0.0

    if size_kb > MAX_CHAT_SIZE_KB:
        # reset file with system message
        sys_msg = {
            "user": "SYSTEM",
            "msg": f"Chat direset otomatis — file lama terlalu besar ({int(size_kb)} KB).",
            "time": time.strftime("%H:%M:%S"),
            "loc": "Server"
        }
        # overwrite remote
        try:
            _put_file(CHAT_PATH, [sys_msg], sha=None, commit_msg="Auto-reset chat due to size")
        except:
            pass
        # small sleep
        time.sleep(1)
        existing = [sys_msg]

    new_entry = {
        "user": player.get("NAME", "Survivor"),
        "msg": str(msg),
        "time": time.strftime("%H:%M:%S"),
        "loc": player.get("location", ""),
        "uuid": player.get("UUID")
    }

    ok, info = safe_append_and_put(CHAT_PATH, new_entry)
    return ok, info

def show_chat_preview(limit=20):
    data, status = fetch_json_raw(CHAT_PATH)
    if status != 200:
        return []
    return data[-limit:]

# ====== MARKET (unchanged) ======
def post_market_item(player, item_name, qty=1):
    new_entry = {
        "seller": player.get("NAME", "Survivor"),
        "item": item_name,
        "qty": int(qty),
        "time": time.strftime("%H:%M:%S"),
        "loc": player.get("location", "")
    }
    ok, info = safe_append_and_put(MARKET_PATH, new_entry)
    return ok, info

def fetch_market(limit=20):
    data, status = fetch_json_raw(MARKET_PATH)
    if status != 200:
        return []
    return data[-limit:]

# ====== SAVE / LOAD ======
def save_game(player):
    try:
        loading_animation("💾 Menyimpan")
        filename = os.path.join(SAVE_FOLDER, f"{player['NAME']}.json")
        with open(filename, "w") as f:
            json.dump(player, f, indent=4)
        slow(f"💾 Game berhasil disimpan: {filename}", 0.01)
        time.sleep(0.6)
    except Exception as e:
        slow(f"Gagal menyimpan game: {e}", 0.01)

def load_game_interactive():
    files = [f for f in os.listdir(SAVE_FOLDER) if f.endswith('.json')]
    clear()
    if not files:
        slow("Tidak ada save yang ditemukan.", 0.02)
        time.sleep(1)
        return None
    table = Table(title="Saves", box=box.SIMPLE)
    table.add_column("No", style=HIGHLIGHT)
    table.add_column("Nama Save", style=HIGHLIGHT)
    for i, f in enumerate(files, start=1):
        table.add_row(str(i), f[:-5])
    console.print(table)
    try:
        num = int(input("Masukkan nomor: ").strip())
        if num < 1 or num > len(files): raise ValueError
        path = os.path.join(SAVE_FOLDER, files[num-1])
        with open(path, 'r') as f:
            data = json.load(f)
        # claim events if any
        try:
            claimed = fetch_and_claim_events_for_player(data)
            if claimed:
                slow(f"🎁 Kamu menerima {len(claimed)} hadiah event saat login!", 0.02)
                time.sleep(0.6)
        except:
            pass
        slow(f"Memuat data {data.get('NAME','Unknown')}...", 0.01)
        time.sleep(0.8)
        return data
    except Exception:
        slow("Input tidak valid.", 0.02)
        time.sleep(1)
        return None

# ====== PLAYER CREATION & STATUS ======
def create_new_game():
    # jika sudah ada save game, batasi pembuatan akun 1x (hapus save lama bila user setuju)
    if os.path.exists(SAVE_FOLDER) and any(f.endswith(".json") for f in os.listdir(SAVE_FOLDER)):
        clear()
        slow("Terlihat ada save game sebelumnya.\nJika kamu membuat New Game, semua save lama akan dihapus.", 0.02)
        confirm = input("Lanjutkan dan hapus semua save lama? (y/n): ").strip().lower()
        if confirm != "y":
            slow("Pembuatan akun dibatalkan.", 0.02)
            time.sleep(0.6)
            return None
        for f in os.listdir(SAVE_FOLDER):
            if f.endswith(".json"):
                try:
                    os.remove(os.path.join(SAVE_FOLDER, f))
                except:
                    pass
        slow("Semua save lama dihapus.", 0.02)
        time.sleep(0.8)

    clear()
    slow("Memasuki dunia Project Days...\n", 0.02)
    time.sleep(0.6)
    slow("Tahun 2089... Dunia runtuh setelah wabah biologi.", 0.02)
    slow("Kau harus bertahan, mencari makanan, dan menghindari zombie.\n", 0.02)
    time.sleep(0.6)
    name = input("Masukkan nama karaktermu: ").strip().title()
    if not name:
        name = "Survivor"
    # UUID unik untuk player
    player_uuid = str(uuid.uuid4())
    player = {
        "NAME": name,
        "UUID": player_uuid,
        "Level": 1,
        "EXP": 0,
        "EXP_TO_NEXT": 100,
        "HP": 100,
        "MAX_HP": 100,
        "ENERGY": 100,
        "MAX_ENERGY": 100,
        "ATK": 10,
        "DEF": 5,
        "DEX": 3,
        "Weapon": "Tangan Kosong",
        "Armor": "Pakaian Lusuh",
        "inventory": {
            "Perban": 2,
            "Minuman": 2,
            "Makanan": 1,
            "Ammo 9mm": 10,
            "Ammo 12mm": 2,
            "Ammo 7.2mm": 1,
            "Tombak": 1,
        },
        "location": "Hutan Pinggiran"
    }

    # jika nama admin (Vyoker) dan admin.txt belum ada, buat admin.txt berisi UUID
    if player["NAME"].lower() == "vyoker":
        if not os.path.exists(ADMIN_FILE):
            try:
                with open(ADMIN_FILE, "w") as af:
                    af.write(player_uuid)
                slow("Admin file dibuat dan UUID-mu didaftarkan sebagai admin.", 0.02)
                time.sleep(0.6)
            except:
                pass

    save_game(player)
    # claim any events (rare, in case)
    try:
        claimed = fetch_and_claim_events_for_player(player)
        if claimed:
            slow(f"🎁 Kamu menerima {len(claimed)} hadiah event saat membuat akun!", 0.02)
            time.sleep(0.6)
    except:
        pass

    slow(f"\nSelamat, {player['NAME']}! Karaktermu telah dibuat. UUID kamu: {player['UUID']}", 0.02)
    time.sleep(0.8)
    return player

def check_level_up(player):
    while player.get('EXP', 0) >= player.get('EXP_TO_NEXT', 100):
        player['EXP'] -= player['EXP_TO_NEXT']
        player['Level'] += 1
        player['EXP_TO_NEXT'] = player.get('EXP_TO_NEXT',100) + 50
        player['ATK'] += 2
        player['DEF'] += 1
        player['DEX'] += 1
        player['MAX_HP'] += 10
        player['MAX_ENERGY'] += 5
        player['HP'] = player['MAX_HP']
        player['ENERGY'] = player['MAX_ENERGY']
        slow(f"\n🎉 Naik level! Sekarang kamu level {player['Level']}", 0.02)
        time.sleep(0.8)

# ====== UI: Title & Menus ======
def show_title():
    clear()
    console.print(Panel(Text("PROJECT DAYS v2.3 ONLINE (FULL)", style=f"bold {HIGHLIGHT}"), box=box.DOUBLE, style=HEADER_BG))
    # show online status briefly
    status_text = "🌐 Online (Connected to GitHub)" if ONLINE_MODE else "📴 Read-Only (Token tidak ditemukan / Invalid)"
    console.print(Panel(Text(status_text, style=HIGHLIGHT), box=box.ROUNDED, style=HEADER_BG))
    console.print("\n1. New Game".ljust(30) + "2. Load Game")
    console.print("3. Exit\n")
    choice = input("Pilih: ").strip()
    if choice == "1":
        player = create_new_game()
        if player:
            main_menu(player)
        else:
            show_title()
    elif choice == "2":
        player = load_game_interactive()
        if player:
            main_menu(player)
        else:
            show_title()
    elif choice == "3":
        slow("Keluar...", 0.02)
        sys.exit()
    else:
        slow("Input tidak valid.", 0.02)
        time.sleep(0.6)
        show_title()

def tampil_status(player):
    clear()
    table = Table.grid(expand=True)
    table.add_column(ratio=2)
    table.add_column(ratio=3)
    stats = (f"🔰 Level: {player.get('Level',1)}  | EXP: {player.get('EXP',0)}/{player.get('EXP_TO_NEXT',100)}\n"
             f"❤️ HP: {player.get('HP',100)}/{player.get('MAX_HP',100)}  | ⚡ Energy: {player.get('ENERGY',100)}/{player.get('MAX_ENERGY',100)}\n"
             f"🗡️ ATK: {player.get('ATK',10)}  | 🛡️ DEF: {player.get('DEF',5)}  | 🎯 DEX: {player.get('DEX',3)}")
    table.add_row(Panel(Text(f"🧍  Nama: {player.get('NAME','Survivor')}", style=HIGHLIGHT), box=box.ROUNDED, style=HEADER_BG),
                  Panel(Text(stats, style=HIGHLIGHT), box=box.ROUNDED, style=HEADER_BG))
    console.print(table)
    console.print(Panel(Text(f"⚙️ Weapon: {player.get('Weapon','Tangan Kosong')}    🧥 Armor: {player.get('Armor','Pakaian Lusuh')}", style=HIGHLIGHT), box=box.ROUNDED, style=HEADER_BG))
    # show online mode indicator only in main menu (we rely on show_title and main_menu to include it)
    # nothing else here to avoid clutter

def main_menu(player):
    while True:
        tampil_status(player)
        # ONLINE indicator in main menu
        if ONLINE_MODE:
            console.print(Panel("🌐 Mode: [green]Online (Connected to GitHub)[/]", box=box.ROUNDED, style=HEADER_BG))
        else:
            console.print(Panel("📴 Mode: [red]Read-Only (Token tidak ditemukan / Invalid)[/]", box=box.ROUNDED, style=HEADER_BG))
        console.print("\n1. Inventory\n2. Explore\n3. Travel\n4. Toko\n5. Chatting\n6. Exit (Save & Quit)\n")
        choice = input("Pilih menu: ").strip()
        if choice == "1":
            slow("Membuka inventory...", 0.02)
            inventory_menu(player)
        elif choice == "2":
            slow("Bersiap untuk menjelajah...", 0.02)
            explore_menu(player)
        elif choice == "3":
            slow("Mempersiapkan perjalanan...", 0.02)
            travel_menu(player)
        elif choice == "4":
            slow("Menuju toko terdekat...", 0.02)
            shop_menu(player)
        elif choice == "5":
            # aktifkan chatting global
            okmsg, info = check_github_token_valid()
            if not okmsg:
                slow(f"⚠️ {info}\nChat/Marketplace memerlukan token GitHub yang valid di gh_token.txt", 0.02)
                input("Tekan Enter untuk kembali...")
            else:
                chat_menu(player)
        elif choice == "6":
            save_game(player)
            slow("Sampai jumpa, survivor.", 0.02)
            time.sleep(0.6)
            clear()
            sys.exit()
        else:
            slow("Pilihan tidak valid.", 0.02)
            time.sleep(0.6)

# ====== INVENTORY SYSTEM ======
def inventory_menu(player):
    while True:
        clear()
        console.print(Panel(Text(f"📦 INVENTORY — {player.get('NAME','Survivor')}", style=HIGHLIGHT), box=box.ROUNDED, style=HEADER_BG))
        if not player.get("inventory"):
            console.print("Inventory kosong.\n", style=HIGHLIGHT)
        else:
            table = Table(box=box.MINIMAL)
            table.add_column("No", style=HIGHLIGHT)
            table.add_column("Item", style=HIGHLIGHT)
            table.add_column("Qty", style=HIGHLIGHT)
            for i, (item, jumlah) in enumerate(player["inventory"].items(), start=1):
                table.add_row(str(i), item, str(jumlah))
            console.print(table)
        console.print("\n1. Lihat deskripsi item\n2. Gunakan item\n3. Buang item\n4. Crafting\n5. Kembali\n")
        choice = input("Pilih: ").strip()
        if choice == "1":
            lihat_deskripsi()
        elif choice == "2":
            gunakan_item(player)
        elif choice == "3":
            buang_item(player)
        elif choice == "4":
            crafting_menu(player)
        elif choice == "5":
            return
        else:
            slow("Pilihan tidak valid.", 0.02)
            time.sleep(0.6)

def lihat_deskripsi():
    clear()
    slow("Beberapa contoh item:\n", 0.01)
    slow("🩹 Perban  — Mengembalikan 25 HP.", 0.01)
    slow("🥤 Minuman — Mengembalikan 20 Energy.", 0.01)
    slow("🍖 Makanan — Mengembalikan 30 Energy & 10 HP.", 0.01)
    slow("🌿 Herbal — Bahan ramuan, mengembalikan 15 HP.", 0.01)
    slow("🪵 Kayu, Batu — Bahan untuk crafting.", 0.01)
    input("Tekan Enter untuk kembali...")

def gunakan_item(player):
    global weapon_list, armor_list
    valid_items = {k: v for k, v in player["inventory"].items() if v > 0}
    if not valid_items:
        slow("Inventory kosong.", 0.02)
        time.sleep(1)
        return
    clear()
    console.print(Panel(Text("Pilih item yang ingin digunakan:", style=HIGHLIGHT), box=box.ROUNDED, style=HEADER_BG))
    items = list(valid_items.items())
    for i, (nama, jumlah) in enumerate(items, start=1):
        console.print(f"{i}. {nama} ({jumlah})")
    console.print()
    try:
        choice = int(input("Nomor item: ").strip())
        if choice < 1 or choice > len(items):
            raise ValueError
        item, jumlah = items[choice - 1]
    except ValueError:
        slow("Pilihan tidak valid.", 0.02)
        return
    # consumable
    if item in item_effects:
        effect = item_effects[item]
        if effect["type"] == "heal":
            player["HP"] = min(player["HP"] + effect["heal"], player["MAX_HP"])
            slow(f"Kamu menggunakan {item}. HP +{effect['heal']}", 0.01)
        elif effect["type"] == "energy":
            player["ENERGY"] = min(player["ENERGY"] + effect["energy"], player["MAX_ENERGY"])
            slow(f"Kamu menggunakan {item}. Energy +{effect['energy']}", 0.01)
        elif effect["type"] == "heal_energy":
            player["HP"] = min(player["HP"] + effect["heal"], player["MAX_HP"])
            player["ENERGY"] = min(player["ENERGY"] + effect["energy"], player["MAX_ENERGY"])
            slow(f"Kamu menggunakan {item}. HP +{effect['heal']} dan Energy +{effect['energy']}", 0.01)
    elif item in weapon_list:
        wdata = weapon_list[item]
        if wdata.get("type") == "gun":
            ammo_t = wdata.get("ammo")
            if player["inventory"].get(ammo_t, 0) <= 0:
                slow(f"Kamu tidak punya peluru {ammo_t}! Tidak bisa equip {item}.", 0.01)
                return
        player["Weapon"] = item
        slow(f"Kamu kini menggunakan senjata: {item}!", 0.01)
    elif item in armor_list:
        player["Armor"] = item
        slow(f"Kamu kini memakai armor: {item}!", 0.01)
    else:
        slow("Item ini tidak bisa digunakan langsung.", 0.01)
        return
    if item in player["inventory"]:
        player["inventory"][item] -= 1
        if player["inventory"][item] <= 0:
            del player["inventory"][item]
    time.sleep(0.6)

def buang_item(player):
    valid_items = {k: v for k, v in player["inventory"].items() if v > 0}
    if not valid_items:
        slow("Tidak ada item untuk dibuang.", 0.02)
        time.sleep(1)
        return
    clear()
    console.print(Panel(Text("Pilih item yang ingin dibuang:", style=HIGHLIGHT), box=box.ROUNDED, style=HEADER_BG))
    items = list(valid_items.items())
    for i, (item, jumlah) in enumerate(items, start=1):
        console.print(f"{i}. {item} ({jumlah})")
    console.print()
    try:
        choice = int(input("Nomor item: ").strip())
        item, jumlah = items[choice - 1]
        del player["inventory"][item]
        slow(f"{item} dibuang.", 0.02)
    except Exception:
        slow("Pilihan tidak valid.", 0.02)
    time.sleep(0.6)

def crafting_menu(player):
    clear()
    console.print(Panel(Text("⚒️  MENU CRAFTING", style=HIGHLIGHT), box=box.ROUNDED, style=HEADER_BG))
    console.print("\n1. Perban (Butuh: 2x Kain)\n2. Kayu Tajam (Butuh: 2x Kayu + 1x Batu)\n3. Kembali\n")
    choice = input("Pilih resep: ").strip()
    if choice == "1":
        if player["inventory"].get("Kain", 0) >= 2:
            loading_animation("🩹 Meracik Perban")
            player["inventory"]["Kain"] -= 2
            player["inventory"]["Perban"] = player["inventory"].get("Perban", 0) + 1
            slow("Kamu berhasil membuat 1x Perban.", 0.01)
        else:
            slow("Bahan tidak cukup.", 0.01)
    elif choice == "2":
        if player["inventory"].get("Kayu", 0) >= 2 and player["inventory"].get("Batu", 0) >= 1:
            loading_animation("⚒️ Membuat Kayu Tajam")
            player["inventory"]["Kayu"] -= 2
            player["inventory"]["Batu"] -= 1
            player["inventory"]["Kayu Tajam"] = player["inventory"].get("Kayu Tajam", 0) + 1
            slow("Kamu membuat 1x Kayu Tajam.", 0.01)
        else:
            slow("Bahan tidak cukup.", 0.01)
    elif choice == "3":
        return
    else:
        slow("Pilihan tidak valid.", 0.02)
    time.sleep(0.6)

# ====== TRAVEL & SHOP ======
def travel_menu(player):
    clear()
    console.print(Panel(Text("🚗  TRAVEL MENU", style=HIGHLIGHT), box=box.ROUNDED, style=HEADER_BG))
    console.print(f"\n📍 Lokasi saat ini : {player['location']}\n⚡ Energi         : {player['ENERGY']}/{player['MAX_ENERGY']}\n")
    konfirmasi = input("Ingin melakukan perjalanan ke kota lain? (y/n): ").strip().lower()
    if konfirmasi != "y":
        slow("Perjalanan dibatalkan.", 0.02)
        time.sleep(0.6)
        return
    kota_indonesia = [
        "Jakarta", "Bandung", "Surabaya", "Yogyakarta", "Semarang", "Medan",
        "Palembang", "Makassar", "Denpasar", "Balikpapan", "Malang", "Pontianak",
        "Manado", "Padang", "Samarinda", "Banjarmasin", "Cirebon", "Tasikmalaya",
        "Solo", "Bogor", "Batam", "Pekanbaru", "Kupang", "Jayapura", "Mataram"
    ]
    tujuan = random.choice([k for k in kota_indonesia if k != player["location"]])
    biaya = random.randint(30, 60)
    if player["ENERGY"] < biaya:
        slow("Energi kamu tidak cukup untuk melakukan perjalanan jauh.", 0.02)
        time.sleep(0.6)
        return
    loading_animation(f"🌍 Menjelajah ke {tujuan}")
    player["ENERGY"] -= biaya
    player["location"] = tujuan
    slow(f"\nSetelah perjalanan panjang, kamu tiba di {tujuan}.", 0.02)
    time.sleep(0.6)

def shop_menu(player):
    clear()
    console.print(Panel(Text(f"🏪  TOKO - {player['location']}", style=HIGHLIGHT), box=box.ROUNDED, style=HEADER_BG))
    console.print("\n1. Kios (Barter)\n2. Marketplace (Global)\n3. Kembali\n")
    pilihan = input("Pilih menu: ").strip()
    if pilihan == "1":
        barter_shop(player)
    elif pilihan == "2":
        okmsg, info = check_github_token_valid()
        if not okmsg:
            slow(f"⚠️ {info}\nMarketplace memerlukan token GitHub yang valid di gh_token.txt", 0.02)
            input("Tekan Enter untuk kembali...")
        else:
            market_menu(player)
    elif pilihan == "3":
        return
    else:
        slow("Pilihan tidak valid.", 0.02)
        time.sleep(0.6)

def barter_shop(player):
    clear()
    slow(f"\nKamu memasuki kios barter di {player['location']}...\n", 0.02)
    time.sleep(0.6)
    kota_pesisir = ["Surabaya", "Makassar", "Denpasar", "Balikpapan", "Manado", "Batam", "Padang"]
    kota_gunung  = ["Bandung", "Malang", "Bogor", "Tasikmalaya", "Solo"]
    kota_besar   = ["Jakarta", "Yogyakarta", "Semarang", "Medan", "Palembang", "Samarinda"]
    if player["location"] in kota_pesisir:
        stok_pedagang = ["Ikan Kering", "Air Laut", "Obat Luka", "Kayu", "Pisau"]
    elif player["location"] in kota_gunung:
        stok_pedagang = ["Kayu", "Batu", "Daun Herbal", "Obat", "Tombak"]
    elif player["location"] in kota_besar:
        stok_pedagang = ["Ammo 9mm", "Makanan Kaleng", "Perban", "Minuman", "Kain"]
    else:
        stok_pedagang = ["Kain", "Obat", "Batu", "Kayu", "Minuman"]
    while True:
        clear()
        console.print(Panel(Text(f"🤝  KIOS BARTER — {player['location']}", style=HIGHLIGHT), box=box.ROUNDED, style=HEADER_BG))
        for i, item in enumerate(stok_pedagang, 1):
            console.print(f"{i}. {item}")
        console.print("6. Kembali")
        console.print(Panel(Text("Inventory kamu:", style=HIGHLIGHT), box=box.ROUNDED, style=HEADER_BG))
        if player["inventory"]:
            for k, v in player["inventory"].items():
                console.print(f"- {k} ({v})")
        else:
            console.print("❌ Kamu tidak punya item apapun.")
        pilih = input("Pilih item dari pedagang (1-5): ").strip()
        if pilih == "6":
            slow("Kamu meninggalkan kios.", 0.02)
            time.sleep(0.6)
            return
        if not pilih.isdigit() or int(pilih) not in range(1, 6):
            slow("Pilihan tidak valid.", 0.02)
            continue
        item_toko = stok_pedagang[int(pilih) - 1]
        if not player["inventory"]:
            slow("Kamu tidak punya barang untuk ditukar!", 0.02)
            time.sleep(0.6)
            continue
        console.print(Panel(Text("Barang kamu untuk barter:", style=HIGHLIGHT), box=box.ROUNDED, style=HEADER_BG))
        for i, (item, jumlah) in enumerate(player["inventory"].items(), 1):
            console.print(f"{i}. {item} ({jumlah})")
        pilih_barter = input("Pilih barangmu untuk ditukar: ").strip()
        if not pilih_barter.isdigit() or int(pilih_barter) < 1 or int(pilih_barter) > len(player["inventory"]):
            slow("Pilihan tidak valid.", 0.02)
            continue
        item_player = list(player["inventory"].keys())[int(pilih_barter) - 1]
        if random.randint(1, 100) <= 70:
            if player["inventory"][item_player] > 1:
                player["inventory"][item_player] -= 1
            else:
                player["inventory"].pop(item_player)
            player["inventory"][item_toko] = player["inventory"].get(item_toko, 0) + 1
            slow(f"Barter berhasil! Kamu menukar 1x {item_player} dengan 1x {item_toko}.", 0.02)
        else:
            slow(f"Pedagang menolak menukar {item_player}.", 0.02)
        time.sleep(0.6)

# ====== EXPLORE & LOOT ======
def explore_menu(player):
    while True:
        clear()
        console.print(Panel(Text("🌍  EXPLORE MENU", style=HIGHLIGHT), box=box.ROUNDED, style=HEADER_BG))
        console.print("\n1. Hutan\n2. Desa\n3. Kota\n4. Kembali\n")
        choice = input("Pilih lokasi: ").strip()
        if choice == "1":
            lokasi = "Hutan"
            energi = 15
            chance_zombie = 30
            chance_item = 80
            reward_exp = 10
        elif choice == "2":
            lokasi = "Desa"
            energi = 25
            chance_zombie = 70
            chance_item = 80
            reward_exp = 20
        elif choice == "3":
            lokasi = "Kota"
            energi = 50
            chance_zombie = 90
            chance_item = 80
            reward_exp = 40
        elif choice == "4":
            return
        else:
            slow("Pilihan tidak valid.", 0.02)
            continue
        if player["ENERGY"] < energi:
            slow("Energi tidak cukup untuk menjelajah ke sana.", 0.02)
            time.sleep(0.6)
            continue
        player["ENERGY"] -= energi
        loading_animation(f"🌍 Menjelajah ke {lokasi}")
        time.sleep(0.6)
        event_roll = random.randint(1, 100)
        if event_roll <= chance_item:
            dapat_item(player, lokasi)
        elif event_roll <= chance_item + chance_zombie:
            battle_zombie(player, lokasi, reward_exp)
        else:
            slow("Tidak terjadi apa-apa...", 0.02)
            time.sleep(0.6)

def dapat_item(player, lokasi):
    slow("Kamu menemukan sesuatu di sekitar...\n", 0.02)
    loot_table = {
        "Hutan": ["Kayu", "Batu", "Daun", "Makanan", "Minuman"],
        "Desa": ["Perban", "Kain", "Makanan", "Minuman", "Pisau"],
        "Kota": ["Perban", "Painkiller", "Makanan", "Minuman"]
    }
    if lokasi == "Kota":
        roll = random.randint(1, 100)
        if roll <= 20:
            item = random.choice(["Pistol", "Shotgun", "Sniper", "Senapan Serbu"])
        elif 21 <= roll <= 50:
            peluru_roll = random.randint(1, 100)
            if peluru_roll <= 50:
                item = "Ammo 9mm"
            elif peluru_roll <= 90:
                item = "Ammo 12mm"
            else:
                item = "Ammo 7.2mm"
        else:
            item = random.choice(loot_table[lokasi])
    else:
        item = random.choice(loot_table[lokasi])
    jumlah = random.randint(1, 3)
    player["inventory"][item] = player["inventory"].get(item, 0) + jumlah
    slow(f"Kamu mendapatkan {jumlah}x {item}!", 0.02)
    time.sleep(0.6)

# ====== BATTLE ZOMBIE ======
def battle_zombie(player, lokasi, reward_exp):
    global weapon_list, armor_list, zombie_types
    loading_animation(f"☣ Zombie mendekat di {lokasi}")
    zname = random.choice(list(zombie_types.keys()))
    ztype = zombie_types[zname]
    base_hp = random.randint(30, 70)
    base_atk = random.randint(5, 15)
    base_def = random.randint(0, 10)
    zombie = {
        "name": zname,
        "hp": int(base_hp * ztype["hp_mod"]),
        "atk": int(base_atk * ztype["atk_mod"]),
        "def": int(base_def * ztype["def_mod"]),
        "dodge": ztype["dodge"],
        "exp": reward_exp + random.randint(5, 15)
    }
    slow(f"Kamu bertemu dengan {zombie['name']}!\n", 0.02)
    slow(f"• HP: {zombie['hp']} | ATK: {zombie['atk']} | DEF: {zombie['def']} | DODGE: {zombie['dodge']}%\n", 0.01)
    time.sleep(0.6)
    while player["HP"] > 0 and zombie["hp"] > 0:
        console.print(Panel(Text(f"⚔️  {zombie['name']} — ❤️  {zombie['hp']}", style=HIGHLIGHT), box=box.SQUARE, style=HEADER_BG))
        console.print(Panel(Text(f"🧍  {player['NAME']} — ❤️  {player['HP']} / {player['MAX_HP']}", style=HIGHLIGHT), box=box.SQUARE, style=HEADER_BG))
        console.print("1. Serang\n2. Gunakan Item\n3. Kabur\n")
        action = input("Pilih aksi: ").strip()
        if action == "1":
            weapon_name = player.get("Weapon", "Tangan Kosong")
            weapon_data = weapon_list.get(weapon_name, {"type": "melee", "atk": 5})
            base_atk = weapon_data["atk"]
            atk_bonus = base_atk * (player["ATK"] * 0.02)
            total_damage = int(base_atk + atk_bonus)
            if weapon_data.get("type") == "gun":
                ammo_type = weapon_data.get("ammo")
                if player["inventory"].get(ammo_type, 0) <= 0:
                    slow(f"Tidak ada peluru {ammo_type}! Serangan gagal!", 0.02)
                    total_damage = 0
                else:
                    player["inventory"][ammo_type] -= 1
                    slow(f"🔫 {weapon_name} digunakan, peluru {ammo_type} tersisa {player['inventory'].get(ammo_type,0)}", 0.02)
            if random.randint(1,100) <= zombie.get("dodge",0):
                slow(f"{zombie['name']} berhasil menghindar!", 0.02)
            else:
                dmg_after_def = max(1, int(total_damage - zombie.get("def",0)))
                zombie["hp"] -= dmg_after_def
                slow(f"Kamu menyerang dan memberi {dmg_after_def} damage!", 0.02)
        elif action == "2":
            gunakan_item(player)
            continue
        elif action == "3":
            if random.random() < 0.5:
                slow("Kamu berhasil kabur!", 0.02)
                return
            else:
                slow("Gagal kabur!", 0.02)
        else:
            slow("Pilihan tidak valid.", 0.02)
            continue
        if zombie["hp"] > 0:
            if random.randint(1,100) <= player.get("DEX",0):
                slow("Kamu berhasil menghindar serangan!", 0.02)
            else:
                base_dmg_zombie = zombie["atk"]
                def_reduction = base_dmg_zombie * (player["DEF"] * 0.015)
                total_zombie_dmg = max(1, int(base_dmg_zombie - def_reduction))
                player["HP"] -= total_zombie_dmg
                slow(f"{zombie['name']} menyerangmu dan memberi {total_zombie_dmg} damage!", 0.02)
        if zombie["hp"] <= 0:
            slow(f"\n{zombie['name']} dikalahkan!", 0.03)
            gained_exp = zombie["exp"]
            player["EXP"] += gained_exp
            slow(f"Kamu mendapat {gained_exp} EXP!", 0.02)
            drop_item(player)
            # level up otomatis
            if player["EXP"] >= player["EXP_TO_NEXT"]:
                player["EXP"] -= player["EXP_TO_NEXT"]
                player["Level"] += 1
                player["ATK"] += 2
                player["DEF"] += 1
                player["DEX"] += 1
                player["HP"] = player["MAX_HP"]
                player["ENERGY"] = player["MAX_ENERGY"]
                slow(f"\nNaik Level! Sekarang kamu Level {player['Level']}!", 0.02)
                slow("Stat meningkat: +2 ATK, +1 DEF, +1 DEX\n", 0.02)
            check_level_up(player)
            time.sleep(0.6)
            return
        if player["HP"] <= 0:
            slow("\nKamu tumbang... Game Over!\n", 0.03)
            time.sleep(2)
            sys.exit()

# ====== DROP ITEM ======
def drop_item(player):
    if random.randint(1, 100) <= 50:
        item = random.choice(["Ammo 9mm", "Perban", "Minuman"])
        jumlah = random.randint(1, 2)
        player["inventory"][item] = player["inventory"].get(item, 0) + jumlah
        slow(f"Zombie menjatuhkan {jumlah}x {item}!", 0.02)
        time.sleep(0.6)

# ====== CHAT / MARKET UI (with admin commands) ======
def chat_menu(player):
    clear()
    slow("📻 RADIO SURVIVOR — Chat Global (Ketik /exit untuk keluar)\n", 0.01)
    slow("Perintah admin: /ban  /event  (hanya admin)\n", 0.01)

    # initial display
    def display_chats():
        chats = show_chat_preview(limit=20)
        clear()
        slow("📻 RADIO SURVIVOR — Chat Global\n", 0.01)
        for c in chats:
            user = c.get('user', '?')
            time_s = c.get('time', '')
            loc = c.get('loc','-')
            msg = c.get('msg','')
            slow(f"[{time_s}] [{loc}] {user}: {msg}", 0.005)
        slow("\nKetik pesan. /exit untuk keluar. Admin: /ban, /event", 0.005)

    display_chats()
    while True:
        msg = input("Pesan: ").strip()
        if msg == "":
            # empty -> ignore
            continue
        if msg.lower() == "/exit":
            clear()
            slow("📻 Kamu meninggalkan radio survivor...\n", 0.02)
            time.sleep(0.5)
            return

        # ADMIN COMMANDS
        admin_uuid_local = None
        if os.path.exists(ADMIN_FILE):
            try:
                admin_uuid_local = open(ADMIN_FILE, "r").read().strip()
            except:
                admin_uuid_local = None

        is_admin = (player.get("UUID") == admin_uuid_local)

        if msg.startswith("/ban") and is_admin:
            # interactive ban: /ban <uuid> [minutes]
            parts = msg.split()
            if len(parts) >= 2:
                target_uuid = parts[1].strip()
                minutes = 10
                if len(parts) >= 3:
                    try:
                        minutes = int(parts[2])
                    except:
                        minutes = 10
                ok, info = append_ban(target_uuid, "Unknown", minutes=minutes)
                if ok:
                    slow(f"✅ UUID {target_uuid} dibanned selama {minutes} menit.", 0.02)
                    # also announce to chat
                    # (optional: add a system message)
                else:
                    slow(f"⚠️ Gagal menambahkan ban: {info}", 0.02)
            else:
                slow("Gunakan: /ban <UUID> [minutes]", 0.02)
            time.sleep(0.6)
            display_chats()
            continue

        if msg.startswith("/ban") and not is_admin:
            slow("❌ Kamu bukan admin. Tidak boleh menggunakan /ban.", 0.02)
            time.sleep(0.6)
            display_chats()
            continue

        if msg.startswith("/event") and is_admin:
            # interactive: /event <uuid>;<item>;<qty>
            # if not supplied, ask
            payload = None
            if " " in msg:
                _, rest = msg.split(" ",1)
                # accept two formats: "uuid;item;qty" or "uuid item qty"
                if ";" in rest:
                    parts = rest.split(";")
                else:
                    parts = rest.split()
                if len(parts) >= 2:
                    target_uuid = parts[0].strip()
                    item = parts[1].strip()
                    qty = int(parts[2]) if len(parts) >=3 else 1
                    ok, info = append_event(target_uuid, item, qty, sender=player.get("NAME"))
                    if ok:
                        slow(f"✅ Event dikirim ke {target_uuid}: {qty}x {item}", 0.02)
                    else:
                        slow(f"⚠️ Gagal kirim event: {info}", 0.02)
                else:
                    slow("Format: /event <UUID>;<item>;<qty>  atau /event <UUID> <item> <qty>", 0.02)
            else:
                slow("Format: /event <UUID>;<item>;<qty>", 0.02)
            time.sleep(0.6)
            display_chats()
            continue

        if msg.startswith("/event") and not is_admin:
            slow("❌ Kamu bukan admin. Tidak boleh menggunakan /event.", 0.02)
            time.sleep(0.6)
            display_chats()
            continue

        # normal message -> send
        ok, info = send_chat_message(player, msg)
        if ok:
            slow("✅ Pesan terkirim.", 0.01)
        else:
            slow(f"⚠️ Gagal kirim pesan: {info}", 0.01)
        # small pause then refresh
        time.sleep(1)
        display_chats()

def market_menu(player):
    clear()
    slow("🌐 MARKETPLACE GLOBAL (20 terbaru)\n", 0.01)
    data = fetch_market(limit=20)
    for x in data:
        slow(f"[{x.get('time')}] {x.get('seller')} menjual {x.get('item')} ({x.get('qty')}) — {x.get('loc','-')}", 0.01)
    print()
    pilihan = input("1: Jual item | Enter: Kembali > ").strip()
    if pilihan == "1":
        inv = player.get("inventory", {})
        if not inv:
            slow("Inventory kosong.", 0.02)
            return
        slow("Pilih item yang ingin dijual:", 0.01)
        items = list(inv.items())
        for i, (k, v) in enumerate(items, start=1):
            slow(f"{i}. {k} ({v})", 0.01)
        try:
            c = int(input("Nomor item: ").strip())
            name, qty_have = items[c-1]
            qty_sell = int(input(f"Jumlah jual (max {qty_have}): ").strip())
            if qty_sell < 1 or qty_sell > qty_have:
                slow("Jumlah tidak valid.", 0.02)
                return
            ok, info = post_market_item(player, name, qty_sell)
            if ok:
                player["inventory"][name] -= qty_sell
                if player["inventory"][name] <= 0:
                    del player["inventory"][name]
                slow("Item dikirim ke marketplace global.", 0.02)
            else:
                slow(f"Gagal kirim listing: {info}", 0.02)
        except Exception:
            slow("Input tidak valid.", 0.02)
            return

# ====== MAIN ENTRY ======
if __name__ == "__main__":
    try:
        # pre-check: if admin.txt exists, show admin uuid
        if os.path.exists(ADMIN_FILE):
            try:
                admin_uuid_preview = open(ADMIN_FILE, "r").read().strip()
                slow(f"🔒 Admin UUID registered: {admin_uuid_preview}", 0.005)
            except:
                pass
        # warn about token missing but still allow play offline
        ok, info = check_github_token_valid()
        if not ok:
            slow("📴 Perhatian: gh_token.txt tidak ditemukan atau token tidak valid. Fitur Chat & Marketplace masuk Read-Only.", 0.005)
            time.sleep(0.8)
        else:
            slow("🌐 Token valid. Fitur Chat & Marketplace online aktif.", 0.005)
            time.sleep(0.6)
        show_title()
    except KeyboardInterrupt:
        slow("\nPermainan dihentikan. Sampai jumpa!", 0.02)
