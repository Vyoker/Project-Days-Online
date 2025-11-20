# Project_Days_Online v2.6.8
import os, sys, time, random, json, base64, uuid, requests
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich import box
from rich.table import Table
from rich.align import Align
from player.profile import (
    save_game,
    load_game_interactive,
    create_new_game,
    check_level_up,
    ensure_player_quests
)
from player.inventory import (
    inventory_menu,
    lihat_deskripsi,
    gunakan_item,
    buang_item,
    crafting_menu
)
from world.explore import explore_menu
from core.data_store import WEAPONS, MONSTERS, ARMORS
from core.data_store import ITEMS, CRAFTING
from core.data_store import SHOP, CITIES
from core.io_json import load_json, save_json

console = Console()
# ---------------------------
# UI / Colors / Folders
# ---------------------------
HEADER_BG = "grey11 on rgb(85,52,36)"
HIGHLIGHT = "rgb(210,180,140)"
ACCENT = "rgb(182,121,82)"
DATA_PATH = "data"
SAVE_FOLDER = "saves"
ADMIN_FILE = "admin.txt"
TOKEN_FILE = "gh_token.txt"

os.makedirs(SAVE_FOLDER, exist_ok=True)
os.makedirs(DATA_PATH, exist_ok=True)

def hitung_stat_final(player):
    base_atk = player.get("base_atk", player.get("atk", 10))
    base_def = player.get("base_def", player.get("def", 5))
    base_dex = player.get("base_dex", player.get("dex", 3))
    # Weapon
    wname = player.get("weapon", None)
    weapon = WEAPONS.get(wname, {"atk": 0, "bonus": {}})
    w_flat_atk = weapon.get("atk", 0)
    wb = weapon.get("bonus", {})

    atk = base_atk + w_flat_atk + wb.get("atk", 0)
    dex = base_dex + wb.get("dex", 0)
    atk += int(atk * (wb.get("atk_percent", 0) / 100))
    dex += int(dex * (wb.get("dex_percent", 0) / 100))
    # Armor
    aname = player.get("armor", None)
    armor = ARMORS.get(aname, {"def": 0, "bonus": {}})
    a_flat_def = armor.get("def", 0)
    ab = armor.get("bonus", {})

    defense = base_def + a_flat_def + ab.get("def", 0)
    dex += ab.get("dex", 0)
    defense += int(defense * (ab.get("def_percent", 0) / 100))
    dex += int(dex * (ab.get("dex_percent", 0) / 100))

    player["atk_final"] = atk
    player["def_final"] = defense
    player["dex_final"] = dex
# ---------------------------
# GitHub backend helpers (online)
# ---------------------------
GITHUB_REPO = "Vyoker/Project-Days-Online"
API_BASE = f"https://api.github.com/repos/{GITHUB_REPO}/contents"
CHAT_PATH = "chat.json"
MARKET_PATH = "market.json"
BANLIST_PATH = "banlist.json"
EVENTS_PATH = "events.json"
MAX_CHAT_SIZE_KB = 500

def load_token_file():
    if os.path.exists(TOKEN_FILE):
        try:
            return open(TOKEN_FILE).read().strip()
        except:
            return None
    return None

GITHUB_TOKEN = load_token_file()
ONLINE_MODE = True if GITHUB_TOKEN else False

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

def safe_append_and_put(path, new_entry, max_retries=4, backoff_base=1.1):
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
        time.sleep(random.uniform(0.2, 0.6))
        resp, code_or_err = _put_file(path, existing, sha=sha, commit_msg=f"Update {path} by ProjectDays")
        if resp is None:
            last_err = f"PUT exception: {code_or_err}"
            time.sleep(backoff_base * attempt)
            continue
        if isinstance(resp, requests.Response) and resp.status_code in (200, 201):
            return True, "ok"
        elif getattr(resp, "status_code", None) == 409:
            last_err = "409 conflict"
            time.sleep(backoff_base * attempt + random.uniform(0,0.8))
            continue
        else:
            last_err = f"PUT err {getattr(resp,'status_code',resp)}"
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
# --------------
# Quest Backend
# --------------
def fetch_quests():
    data, status = fetch_json_raw("data/quests.json")
    if status == 200:
        return data
    return {"main": {}, "side": {}}

GLOBAL_QUESTS = fetch_quests()

def check_github_token_valid():
    global ONLINE_MODE, GITHUB_TOKEN
    GITHUB_TOKEN = load_token_file()
    if not GITHUB_TOKEN:
        ONLINE_MODE = False
        return False, "Token tidak ditemukan (gh_token.txt)."
    url = f"https://api.github.com/repos/{GITHUB_REPO}"
    headers = {"Accept": "application/vnd.github.v3+json", "Authorization": f"token {GITHUB_TOKEN}"}
    try:
        r = requests.get(url, headers=headers, timeout=8)
        if r.status_code == 200:
            ONLINE_MODE = True
            return True, "Token valid"
    except Exception as e:
        pass
    ONLINE_MODE = False
    return False, f"Token gagal/akses repo."
# ---------------------
# Ban & Events helpers
# ---------------------
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
    existing, sha, status = _get_file_and_sha(EVENTS_PATH)
    if existing is None:
        return []
    if not isinstance(existing, list):
        existing = []
    deliver = []
    remaining = []
    for e in existing:
        if e.get("to") == player.get("uuid") or e.get("to") == "global":
            deliver.append(e)
        else:
            remaining.append(e)
    try:
        _put_file(EVENTS_PATH, remaining, sha=sha, commit_msg=f"Claim events for {player.get('uuid')}")
    except:
        pass
    for ev in deliver:
        item = ev.get("item")
        qty = int(ev.get("qty", 1))
        if item:
            player["inventory"][item] = player["inventory"].get(item, 0) + qty
    return deliver

def append_event(to_uuid, item, qty=1, sender="SYSTEM"):
    entry = {"to": to_uuid, "item": item, "qty": int(qty), "from": sender, "time": time.strftime("%H:%M:%S")}
    return safe_append_and_put(EVENTS_PATH, entry)
# ---------------
# Chat functions
# ---------------
MAX_CHAT_SIZE_KB = 500

def send_chat_message(player, msg):
    banned, ban_entry = is_banned(player.get("uuid"))
    if banned:
        until_t = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ban_entry.get("until", 0)))
        return False, f"Kamu diblokir sampai {until_t}."
    existing, sha, status = _get_file_and_sha(CHAT_PATH)
    if existing is None:
        existing = []
    try:
        size_kb = len(json.dumps(existing)) / 1024.0
    except:
        size_kb = 0.0
    if size_kb > MAX_CHAT_SIZE_KB:
        sys_msg = {"user": "SYSTEM", "msg": f"Chat direset otomatis ({int(size_kb)} KB).", "time": time.strftime("%H:%M:%S")}
        try:
            _put_file(CHAT_PATH, [sys_msg], sha=None, commit_msg="Auto-reset chat due to size")
        except:
            pass
        existing = [sys_msg]
    new_entry = {"user": player.get("name","Survivor"), "msg": str(msg), "time": time.strftime("%H:%M:%S"), "loc": player.get("location",""), "uuid": player.get("uuid")}
    ok, info = safe_append_and_put(CHAT_PATH, new_entry)
    return ok, info

def show_chat_preview(limit=20):
    data, status = fetch_json_raw(CHAT_PATH)
    if status != 200:
        return []
    return data[-limit:]
# -------
# Market
# -------
def _load_market_local():
    # baca market lokal di data/market.json (dibuat jika belum ada)
    return load_json("market.json", [])

def _save_market_local(data):
    save_json("market.json", data)

def _push_market_to_github(market_list):
    """
    Jika ONLINE_MODE aktif, push market_list ke repo (overwrite market.json).
    Jika gagal atau offline, tetap simpan lokal.
    """
    try:
        # dapatkan sha terlebih dahulu agar _put_file dapat update
        _, sha, status = _get_file_and_sha(MARKET_PATH)
        resp, code_or_err = _put_file(MARKET_PATH, market_list, sha=sha, commit_msg="Update marketplace (Project Days)")
        if resp is None or getattr(resp, "status_code", None) not in (200, 201):
            return False, f"GitHub update failed: {code_or_err}"
        return True, "ok"
    except Exception as e:
        return False, str(e)

def market_refresh():
    """
    Ambil listing market. Jika online, coba fetch dari raw github,
    fallback ke local file data/market.json.
    """
    # coba ambil remote dulu
    remote, status = fetch_json_raw(MARKET_PATH)
    if status == 200 and isinstance(remote, list):
        # sinkronkan juga ke local agar offline nanti up-to-date
        _save_market_local(remote)
        return _load_market_local()
    # fallback ke local
    local = _load_market_local()
    return _load_market_local()

def _list_all_valid_item_names():
    # gabungkan semua nama item/senjata/armor untuk tampilan pilihan saat sell
    names = set()
    names.update(list(ITEMS.keys()))
    names.update(list(WEAPONS.keys()))
    names.update(list(ARMORS.keys()))
    return sorted(names)

def market_sell(player):
    """
    Flow:
      - tampilkan semua nama item
      - input: offer item (nama exact)
      - input: offer_qty (int >0)
      - input: want item (nama exact)
      - input: want_qty (int >0)
      - cek player punya offer_qty, hapus dari inventory, post listing (local + github jika online)
    """
    clear()
    console.print(Panel(Text("⚒️  MARKET — SELL (barter)", style=HIGHLIGHT), box=box.ROUNDED, style=HEADER_BG))
    names = _list_all_valid_item_names()
    console.print("Daftar item (ketik nama persis):\n")
    # tampilkan dalam baris-baris ringkas
    per_line = 4
    for i in range(0, len(names), per_line):
        console.print("  ".join(names[i:i+per_line]))
    console.print()
    offer = input("Nama item yang kamu TAWARKAN (ketik exact nama): ").strip()
    if not offer or offer not in names:
        slow("❌ Nama item tidak valid.", 0.02); time.sleep(0.6); return
    try:
        offer_qty = int(input("Kuantiti yang kamu tawarkan (angka): ").strip())
        if offer_qty < 1:
            raise ValueError
    except Exception:
        slow("❌ Kuantiti tidak valid.", 0.02); time.sleep(0.6); return
    # cek punya item cukup
    if player["inventory"].get(offer, 0) < offer_qty:
        slow(f"❌ Kamu tidak punya {offer_qty}x {offer}.", 0.02); time.sleep(0.6); return

    want = input("Nama item yang kamu INGINKAN (ketik exact nama): ").strip()
    if not want or want not in names:
        slow("❌ Nama item yang diinginkan tidak valid.", 0.02); time.sleep(0.6); return
    try:
        want_qty = int(input("Kuantiti yang kamu inginkan (angka): ").strip())
        if want_qty < 1:
            raise ValueError
    except Exception:
        slow("❌ Kuantiti tidak valid.", 0.02); time.sleep(0.6); return
    # konfirmasi (opsional singkat)
    slow(f"\nPosting listing: {player.get('name')} menawarkan {offer_qty}x {offer} ⇒ {want_qty}x {want}", 0.01)
    confirm = input("Ketik 'y' untuk konfirmasi: ").strip().lower()
    if confirm != "y":
        slow("Dibatalkan.", 0.02); time.sleep(0.6); return
    # kurangi inventory player
    player["inventory"][offer] -= offer_qty
    if player["inventory"][offer] <= 0:
        del player["inventory"][offer]

    entry = {
        "seller": player.get("name","Survivor"),
        "offer": offer,
        "offer_qty": int(offer_qty),
        "want": want,
        "want_qty": int(want_qty),
        "time": time.strftime("%H:%M:%S"),
        "loc": player.get("location","")
    }
    # simpan di local
    market_list = _load_market_local()
    market_list.append(entry)
    _save_market_local(market_list)
    # push ke github bila online
    if ONLINE_MODE:
        ok, info = _push_market_to_github(market_list)
        if ok:
            slow("✅ Listing dikirim ke marketplace online.", 0.02)
        else:
            slow(f"⚠️ Listing disimpan lokal (GitHub error: {info})", 0.02)
    else:
        slow("✅ Listing disimpan lokal (offline).", 0.02)

    save_game(player)  # simpan state player karena inventory berubah
    time.sleep(0.8)

def market_buy(player):
    """
    Flow buy (exact barter required):
      - input nama item desired (the 'want' in listings)
      - input qty desired (must match listing's want_qty)
      - find listing(s) where want==desired AND want_qty==qty
      - For each matching listing, check if buyer has enough of listing.offer >= offer_qty
      - If found and buyer has enough, perform swap: deduct buyer.offer, add buyer.want,
        remove listing from market, update remote.
    """
    clear()
    console.print(Panel(Text("🛒  MARKET — BUY (barter)", style=HIGHLIGHT), box=box.ROUNDED, style=HEADER_BG))
    market_list = market_refresh()
    if not market_list:
        slow("Marketplace kosong.", 0.02); time.sleep(0.6); return
    # tampilkan market
    console.print("\nCurrent listings:\n")
    for m in market_list:
        console.print(f"{m.get('seller')} : {m.get('offer_qty')}x {m.get('offer')}  ⇒  {m.get('want_qty')}x {m.get('want')}  ({m.get('loc','-')})")

    desired = input("\nKetik NAMA item yang ingin kamu AMBIL (must match 'want' field): ").strip()
    if not desired:
        slow("❌ Input kosong.", 0.02); time.sleep(0.6); return
    try:
        desired_qty = int(input("Kuantiti yang ingin kamu ambil (angka): ").strip())
        if desired_qty < 1:
            raise ValueError
    except Exception:
        slow("❌ Kuantiti tidak valid.", 0.02); time.sleep(0.6); return
    # cari listing yang match exactly want + want_qty
    matches = [m for m in market_list if m.get("want") == desired and int(m.get("want_qty",0)) == desired_qty]

    if not matches:
        slow("❌ Tidak ada listing yang cocok (harus match nama & qty persis).", 0.02); time.sleep(0.8); return
    # tampilkan matches (penjual dan apa yang mereka minta)
    slow("\nListing cocok:")
    for i, m in enumerate(matches, start=1):
        slow(f"{i}. {m.get('seller')} meminta {m.get('offer_qty')}x {m.get('offer')} untuk {m.get('want_qty')}x {m.get('want')}")
    # Pilih seller berdasarkan nomor (lebih aman daripada nama karena bisa multiple)
    try:
        pick = int(input("Pilih nomor listing untuk melakukan barter: ").strip())
    except Exception:
        slow("❌ Input tidak valid.", 0.02); time.sleep(0.6); return
    if pick < 1 or pick > len(matches):
        slow("❌ Nomor tidak valid.", 0.02); time.sleep(0.6); return

    chosen = matches[pick - 1]
    needed_offer_item = chosen.get("offer")
    needed_offer_qty = int(chosen.get("offer_qty", 0))
    # cek apakah buyer punya needed_offer_item dengan jumlah yang tepat (karena kita pilih exact rule)
    if player["inventory"].get(needed_offer_item, 0) < needed_offer_qty:
        slow(f"❌ Kamu tidak punya {needed_offer_qty}x {needed_offer_item} untuk barter.", 0.02); time.sleep(0.6); return
    # Lakukan barter: kurangi buyer offer, tambahkan buyer want
    player["inventory"][needed_offer_item] -= needed_offer_qty
    if player["inventory"][needed_offer_item] <= 0:
        del player["inventory"][needed_offer_item]
    # tambahkan yang diterima
    player["inventory"][desired] = player["inventory"].get(desired, 0) + desired_qty
    # Hapus listing dari market_list (persist perubahan)
    market_full = _load_market_local()
    # hapus entry yang identik (seller, offer, offer_qty, want, want_qty, time)
    def same_entry(a,b):
        keys = ("seller","offer","offer_qty","want","want_qty","time")
        return all(str(a.get(k)) == str(b.get(k)) for k in keys)
    new_market = [m for m in market_full if not same_entry(m, chosen)]
    _save_market_local(new_market)
    # push change ke github jika online; jika gagal, simpan lokal tetap berlaku
    if ONLINE_MODE:
        ok, info = _push_market_to_github(new_market)
        if ok:
            slow("✅ Barter berhasil dan marketplace diupdate online.", 0.02)
        else:
            slow(f"⚠️ Barter berhasil tapi gagal update GitHub: {info}. Disimpan lokal.", 0.02)
    else:
        slow("✅ Barter berhasil. Marketplace diupdate lokal.", 0.02)

    save_game(player)
    time.sleep(0.8)

def market_menu(player):
    """
    Command loop for marketplace:
     - refresh : reload & display listings
     - sell    : create new barter listing
     - buy     : perform barter (exact)
     - exit    : leave market
    No numeric menu; all via command words.
    """
    while True:
        clear()
        header = Text(" ☣ MARKET — BARTER ☣ ", style=f"bold {HIGHLIGHT} on {HEADER_BG}")
        console.print(Panel(header, box=box.DOUBLE, style=HEADER_BG))
        # display current market summary
        market_list = market_refresh()
        if not market_list:
            console.print(Panel(Text("Marketplace kosong.", style=HIGHLIGHT), box=box.ROUNDED, style=ACCENT))
        else:
            # print each listing compact
            for m in market_list:
                console.print(Panel(Text(f"{m.get('seller')} : {m.get('offer_qty')}x {m.get('offer')}  ⇒  {m.get('want_qty')}x {m.get('want')}", style=HIGHLIGHT),
                                   box=box.ROUNDED, style=HEADER_BG))
        console.print("\nCommands: refresh  |  sell  |  buy  |  exit\n")
        cmd = input("market> ").strip().lower()
        if cmd == "refresh":
            # just loop; market_refresh called at top will reload
            slow("↺ Refreshing marketplace...", 0.02)
            time.sleep(0.6)
            continue
        elif cmd == "sell":
            market_sell(player)
            continue
        elif cmd == "buy":
            market_buy(player)
            continue
        elif cmd == "exit":
            slow("Meninggalkan marketplace...", 0.02)
            time.sleep(0.6)
            return
        else:
            slow("Command tidak dikenal. Gunakan: refresh | sell | buy | exit", 0.02)
            time.sleep(0.8)
            continue
# ===================================
# Fungsi Event Otomatis (GitHub JSON)
# ===================================
def check_event(player):
    today = datetime.now().strftime("%d-%m")
    url = "https://raw.githubusercontent.com/Vyoker/Project-Days-Online/main/events.json"
    try:
        data = requests.get(url, timeout=5).json()
        for ev in data:
            if ev["date"] == today:
                print(f"\n🔥 EVENT AKTIF: {ev['name']}")
                print(ev["description"])
                for item, qty in ev["rewards"].items():
                    player["inventory"][item] = player["inventory"].get(item, 0) + qty
                    print(f"🎁 {qty}x {item}")
                print("──────────────────────────────\n")
                break
    except Exception:
        print("(⚠️ Offline mode — tidak bisa memuat event.)")
# -----------
# UI / Menus
# -----------
def show_title():
    clear()
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
            check_event(player)
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
    # Hitung stat final sebelum ditampilkan
    hitung_stat_final(player)
    table = Table.grid(expand=True)
    table.add_column(ratio=2)
    table.add_column(ratio=3)
    stats = (
        f"🔰 Level: {player.get('level',1)}  | EXP: {player.get('exp',0)}/{player.get('exp_to_next',100)}\n"
        f"❤️ HP: {player.get('hp',100)}/{player.get('max_hp',100)}  | ⚡ Energy: {player.get('energy',100)}/{player.get('max_energy',100)}\n"
        f"🗡️ ATK: {player.get('atk_final',10)}  | 🛡️ DEF: {player.get('def_final',5)}  | 🎯 DEX: {player.get('dex_final',3)}"
    )
    table.add_row(
        Panel(Text(f"🧍  Nama: {player.get('name','Survivor')}", style=HIGHLIGHT), box=box.ROUNDED, style=HEADER_BG),
        Panel(Text(stats, style=HIGHLIGHT), box=box.ROUNDED, style=HEADER_BG)
    )
    console.print(table)
    console.print(
        Panel(
            Text(f"⚙️ Weapon: {player.get('weapon','Tangan Kosong')}    🧥 Armor: {player.get('armor','Pakaian Lusuh')}", style=HIGHLIGHT),
            box=box.ROUNDED,
            style=HEADER_BG
        )
    )

def check_event(player):
    import requests, datetime, json
    today = datetime.datetime.now().strftime("%d-%m")
    url = "https://raw.githubusercontent.com/Vyoker/Project-Days-Online/main/events.json"
    try:
        data = requests.get(url, timeout=5).json()
        for ev in data:
            if ev["date"] == today:
                print(f"\n🔥 EVENT AKTIF: {ev['name']}")
                print(ev["description"])
                for item, qty in ev["rewards"].items():
                    player["inventory"][item] = player["inventory"].get(item, 0) + qty
                    print(f"🎁 Kamu mendapat {qty}x {item}!")
                print("─────────────────────────────────────\n")
                break
    except Exception as e:
        print("(Gagal memuat event online, offline mode aktif.)")

def main_menu(player):
    while True:
        tampil_status(player)
        if ONLINE_MODE:
            console.print(Panel("🌐 Mode: [green]Online (Connected to GitHub)[/]", box=box.ROUNDED, style=HEADER_BG))
        else:
            console.print(Panel("📴 Mode: [red]Read-Only (Token tidak ditemukan / Invalid)[/]", box=box.ROUNDED, style=HEADER_BG))
        console.print("\n1. Inventory\n2. Explore\n3. Travel\n4. Toko\n5. Chatting\n6. Quests\n7. Exit (Save & Quit)\n")
        choice = input("Pilih menu: ").strip()
        if choice == "1":
            slow("Membuka inventory...", 0.02)
            inventory_menu(player)
        elif choice == "2":
            slow("Bersiap untuk menjelajah...", 0.02)
            explore_menu(player)
            # === Refresh data player setelah eksplor atau battle ===
            save_path = os.path.join(SAVE_FOLDER, f"{player.get('uuid', 'default')}.json")
            if os.path.exists(save_path):
                with open(save_path, "r", encoding="utf-8") as f:
                    refreshed = json.load(f)
                player.update(refreshed)
        elif choice == "3":
            slow("Mempersiapkan perjalanan...", 0.02)
            travel_menu(player)
        elif choice == "4":
            slow("Menuju toko terdekat...", 0.02)
            shop_menu(player)
        elif choice == "5":
            okmsg, info = check_github_token_valid()
            if not okmsg:
                slow(f"⚠️ {info}\nChat/Marketplace memerlukan token GitHub yang valid di gh_token.txt", 0.02)
                input("Tekan Enter untuk kembali...")
            else:
                chat_menu(player)
        elif choice == "6":
            slow("Membuka menu quests...", 0.02)
            quests_menu(player)
        elif choice == "7":
            save_game(player)
            slow("Sampai jumpa, survivor.", 0.02)
            time.sleep(0.6)
            clear()
            sys.exit()
        else:
            slow("Pilihan tidak valid.", 0.02)
            time.sleep(0.6)
# -------
# Quests
# -------
def quests_menu(player):
    ensure_player_quests(player)
    q = player["quests"]
    MQ = GLOBAL_QUESTS["main"]
    SQ = GLOBAL_QUESTS["side"]

    clear()
    console.print(Panel(Text("🗒️ QUESTS 🗒️", style=HIGHLIGHT), box=box.DOUBLE, style=HEADER_BG))
    # =====================
    # TAMPILKAN QUEST AKTIF
    # =====================
    console.print("Misi Utama Aktif:", style=HIGHLIGHT)
    if q["main_active"]:
        code = q["main_active"]
        console.print(f"❎ {MQ[code]['name']} — {MQ[code]['desc']}")
    else:
        console.print("❎ Tidak ada misi utama aktif.")

    console.print("\nMisi Sampingan Aktif:", style=HIGHLIGHT)
    if q["side_active"]:
        for code in q["side_active"]:
            console.print(f"❎ {SQ[code]['name']} — {SQ[code]['desc']}")
    else:
        console.print("❎ Tidak ada misi sampingan aktif.")
    # ==============
    # QUEST SELESAI
    # ==============
    console.print("\n_______________")
    console.print("Quest Terselesaikan:", style=HIGHLIGHT)
    if q["completed"]:
        for code in q["completed"]:
            name = (
                MQ[code]["name"]
                if code in MQ else
                SQ[code]["name"]
            )
            console.print(f"✅ {name}")
    else:
        console.print("(Belum ada)")
    console.print("_______________\n")
    # =====
    # MENU
    # =====
    console.print("1. Lihat Daftar Misi")
    console.print("2. Ambil Misi Utama (berurutan)")
    console.print("3. Ambil Misi Sampingan")
    console.print("4. Cek & Selesaikan Misi")
    console.print("5. Kembali\n")

    pilih = input("Pilih: ").strip()
    # ==========================
    # 1. LIST QUEST dari GitHub
    # ==========================
    if pilih == "1":
        clear()
        console.print(Panel(Text("📜 Daftar Misi Global", style=HIGHLIGHT), box=box.ROUNDED, style=HEADER_BG))

        console.print("\nMisi Utama:")
        for code, data in MQ.items():
            console.print(f"{code} — {data['name']}")

        console.print("\nMisi Sampingan:")
        for code, data in SQ.items():
            console.print(f"{code} — {data['name']}")

        input("\nTekan Enter...")
        return
    # ===============================
    # 2. AMBIL MISI UTAMA (berurutan)
    # ===============================
    elif pilih == "2":
        if q["main_active"]:
            slow("❌ Kamu sudah punya misi utama aktif.", 0.02)
            return
        # cari misi pertama yang belum selesai
        for code, data in MQ.items():
            if code not in q["completed"]:
                q["main_active"] = code
                save_game(player)
                slow(f"📌 Misi utama '{data['name']}' diambil!", 0.02)
                return

        slow("Semua misi utama telah selesai!", 0.02)
        return
    # ========================
    # 3. AMBIL MISI SAMPINGAN
    # ========================
    elif pilih == "3":
        kode = input("Masukkan kode misi sampingan (contoh: S001): ").strip().upper()

        if kode not in SQ:
            slow("❌ Kode tidak ditemukan.", 0.02)
            return

        if kode in q["side_active"] or kode in q["completed"]:
            slow("❌ Misi sudah aktif atau sudah selesai.", 0.02)
            return

        q["side_active"].append(kode)
        save_game(player)
        slow(f"📌 Misi '{SQ[kode]['name']}' diambil!", 0.02)
        return
    # ========================
    # 4. CEK & SELESAIKAN MISI
    # ========================
    elif pilih == "4":
        # ----- Misi Utama -----
        if q["main_active"]:
            code = q["main_active"]
            req = MQ[code]["requirements"]
            # requirement: LOCATION
            if "location" in req:
                if player["location"] == req["location"]:
                    # Selesaikan quest
                    q["completed"].append(code)
                    q["main_active"] = MQ[code].get("next")
                    # Reward
                    reward = MQ[code]["rewards"]
                    player["exp"] += reward["exp"]

                    for item, qty in reward["items"].items():
                        player["inventory"][item] = player["inventory"].get(item, 0) + qty

                    save_game(player)
                    slow(f"🎉 Misi utama '{MQ[code]['name']}' selesai!", 0.02)
                    return
            # requirement: ITEMS
            if "items" in req:
                ok = True
                for item, qty in req["items"].items():
                    if player["inventory"].get(item, 0) < qty:
                        ok = False
                if ok:
                    # Ambil item
                    for item, qty in req["items"].items():
                        player["inventory"][item] -= qty
                        if player["inventory"][item] <= 0:
                            del player["inventory"][item]
                    # Selesaikan
                    q["completed"].append(code)
                    q["main_active"] = MQ[code].get("next")

                    reward = MQ[code]["rewards"]
                    player["exp"] += reward["exp"]

                    for item, qty in reward["items"].items():
                        player["inventory"][item] = player["inventory"].get(item, 0) + qty

                    save_game(player)
                    slow(f"🎉 Misi utama '{MQ[code]['name']}' selesai!", 0.02)
                    return
        # ----- Misi Sampingan -----
        for code in list(q["side_active"]):
            req = SQ[code]["requirements"]
            # Location type
            if "location" in req:
                if player["location"] == req["location"]:
                    # complete
                    q["completed"].append(code)
                    q["side_active"].remove(code)

                    reward = SQ[code]["rewards"]
                    player["exp"] += reward["EXP"]
                    for item, qty in reward["items"].items():
                        player["inventory"][item] = player["inventory"].get(item, 0) + qty

                    save_game(player)
                    slow(f"🎉 Misi '{SQ[code]['name']}' selesai!", 0.02)
                    return
            # Items type
            if "items" in req:
                ok = True
                for item, qty in req["items"].items():
                    if player["inventory"].get(item, 0) < qty:
                        ok = False

                if ok:
                    # remove items
                    for item, qty in req["items"].items():
                        player["inventory"][item] -= qty
                        if player["inventory"][item] <= 0:
                            del player["inventory"][item]

                    q["completed"].append(code)
                    q["side_active"].remove(code)

                    reward = SQ[code]["rewards"]
                    player["exp"] += reward["exp"]
                    for item, qty in reward["items"].items():
                        player["inventory"][item] = player["inventory"].get(item, 0) + qty

                    save_game(player)
                    slow(f"🎉 Misi '{SQ[code]['name']}' selesai!", 0.02)
                    return

        slow("❌ Tidak ada misi yang bisa diselesaikan saat ini.", 0.02)
        return
    # ===========
    # 5. KEMBALI
    # ===========
    elif pilih == "5":
        return
# -----------------------
# Travel & Shop & Barter
# -----------------------
def travel_menu(player):
    clear()
    console.print(Panel(Text("🚗  TRAVEL MENU", style=HIGHLIGHT), box=box.ROUNDED, style=HEADER_BG))
    console.print(f"\n📍 Lokasi saat ini : {player['location']}\n⚡ Energi         : {player['energy']}/{player['max_energy']}\n")
    konfirmasi = input("Ingin melakukan perjalanan ke kota lain? (y/n): ").strip().lower()
    if konfirmasi != "y":
        slow("Perjalanan dibatalkan.", 0.02)
        time.sleep(0.6)
        return
    kota_indonesia = list(CITIES.keys())
    tujuan = random.choice([k for k in kota_indonesia if k != player["location"]])
    biaya = random.randint(25, 50)
    if player["energy"] < biaya:
        slow("Energi kamu tidak cukup untuk melakukan perjalanan jauh.", 0.02)
        time.sleep(0.6)
        return
    loading_animation(f"🌍 Menjelajah ke {tujuan}")
    player["energy"] -= biaya
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
    slow(f"\nKamu memasuki kios barter di {player['location']}.\n", 0.02)
    time.sleep(0.6)
    # Ambil tipe kota dari cities.json
    city_type = CITIES.get(player["location"], {}).get("type", "wild")
    # Ambil stok pedagang dari shop.json
    stok_pedagang = SHOP.get(city_type, SHOP.get("wild", []))
    while True:
        clear()
        console.print(Panel(Text(f"🤝  KIOS BARTER — {player['location']}", style=HIGHLIGHT),
                             box=box.ROUNDED, style=HEADER_BG))
        # Tampilkan stok pedagang
        for i, item in enumerate(stok_pedagang, 1):
            console.print(f"{i}. {item}")
        console.print("6. Kembali")
        # Inventory player
        console.print(Panel(Text("Inventory kamu:", style=HIGHLIGHT),
                             box=box.ROUNDED, style=HEADER_BG))
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
        # Pilih barang untuk barter
        console.print(Panel(Text("Barang kamu untuk barter:", style=HIGHLIGHT),
                             box=box.ROUNDED, style=HEADER_BG))
        inv_list = list(player["inventory"].items())
        for i, (item, jumlah) in enumerate(inv_list, 1):
            console.print(f"{i}. {item} ({jumlah})")
        pilih_barter = input("Pilih barangmu untuk ditukar: ").strip()
        if not pilih_barter.isdigit() or int(pilih_barter) < 1 or int(pilih_barter) > len(inv_list):
            slow("Pilihan tidak valid.", 0.02)
            continue
        item_player = inv_list[int(pilih_barter) - 1][0]
        # Sistem barter (70% sukses)
        if random.randint(1, 100) <= 70:
            if player["inventory"].get(item_player, 0) > 1:
                player["inventory"][item_player] -= 1
            else:
                del player["inventory"][item_player]
            player["inventory"][item_toko] = player["inventory"].get(item_toko, 0) + 1
            slow(f"Barter berhasil! Kamu menukar 1x {item_player} dengan 1x {item_toko}.", 0.02)
        else:
            slow(f"Pedagang menolak menukar {item_player}.", 0.02)
        time.sleep(0.6)
# -----------------
# Chatting & Admin
# -----------------
def chat_menu(player):
    clear()
    slow("📻 RADIO SURVIVOR — Chat Global (Ketik /exit untuk keluar)\n", 0.01)
    slow("Perintah admin: /ban  /gift  (hanya admin)\n", 0.01)

    def display_chats():
        # Cek apakah ada hadiah event untuk player (gift)
        deliveries = fetch_and_claim_events_for_player(player)
        if deliveries:
            for ev in deliveries:
                item = ev.get("item")
                qty = ev.get("qty", 1)
                slow(f"🎁 Kamu menerima {qty}x {item} dari {ev.get('from','SYSTEM')}!", 0.01)
            save_game(player)
            
        chats = show_chat_preview(limit=20)
        clear()
        slow("📻 RADIO SURVIVOR — Chat Global\n", 0.01)
        for c in chats:
            user = c.get('user','?')
            time_s = c.get('time','')
            loc = c.get('loc','-')
            msg = c.get('msg','')
            slow(f"[{time_s}] [{loc}] {user}: {msg}", 0.005)
        slow("\nKetik pesan. /exit untuk keluar.", 0.005)
    # tampil awal
    display_chats()
    while True:
        msg = input("Pesan: ").strip()
        if msg == "":
            continue
        # keluar
        if msg.lower() == "/exit":
            clear()
            slow("📻 Kamu meninggalkan radio survivor...\n", 0.02)
            time.sleep(0.5)
            return
        # ================
        # CHECK ADMIN FIX
        # ================
        admin_uuid_local = None
        if os.path.exists(ADMIN_FILE):
            try:
                admin_uuid_local = open(ADMIN_FILE,"r", encoding="utf-8").read().strip()
            except:
                admin_uuid_local = None
        player_uuid = player.get("uuid") or player.get("UUID")
        is_admin = (player_uuid == admin_uuid_local)
        # ===================================================
        # COMMAND: /ban <uuid> <minutes>
        # ===================================================
        if msg.startswith("/ban"):
            if not is_admin:
                slow("❌ Kamu bukan admin. Tidak boleh menggunakan /ban.", 0.02)
                time.sleep(0.6)
                display_chats()
                continue

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
                else:
                    slow(f"⚠️ Gagal menambahkan ban: {info}", 0.02)
            else:
                slow("Gunakan: /ban <uuid> [minutes]", 0.02)

            time.sleep(0.6)
            display_chats()
            continue
        # ===================================================
        # COMMAND: /gift <uuid>;<item>;<qty>
        # ===================================================
        if msg.startswith("/gift"):
            if not is_admin:
                slow("❌ Kamu bukan admin. Tidak boleh menggunakan /event.", 0.02)
                time.sleep(0.6)
                display_chats()
                continue

            if " " in msg:
                _, rest = msg.split(" ",1)
                sep = ";" if ";" in rest else " "
                parts = rest.split(sep)
                if len(parts) >= 2:
                    target_uuid = parts[0].strip()
                    item = parts[1].strip()
                    qty = int(parts[2]) if len(parts) >= 3 else 1
                    ok, info = append_event(target_uuid, item, qty, sender=player.get("name"))
                    if ok:
                        slow(f"✅ Item dikirim ke {target_uuid}: {qty}x {item}", 0.02)
                    else:
                        slow(f"⚠️ Gagal kirim event: {info}", 0.02)
                else:
                    slow("Format: /gift <uuid>;<item>;<qty>", 0.02)
            else:
                slow("Format: /gift <uuid>;<item>;<qty>", 0.02)

            time.sleep(0.6)
            display_chats()
            continue
        # ============
        # NORMAL CHAT
        # ============
        ok, info = send_chat_message(player, msg)
        if ok:
            slow("✅ Pesan terkirim.", 0.01)
        else:
            slow(f"⚠️ Gagal kirim pesan: {info}", 0.01)

        time.sleep(1)
        display_chats()
# -----------
# Main entry
# -----------
if __name__ == "__main__":
    try:
        if os.path.exists(ADMIN_FILE):
            try:
                admin_uuid_preview = open(ADMIN_FILE,"r", encoding="utf-8").read().strip()
                slow(f"🔒 Admin UUID registered: {admin_uuid_preview}", 0.005)
            except:
                pass
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
