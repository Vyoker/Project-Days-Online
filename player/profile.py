# player/profile.py
import os, time, json, uuid
from core.utils import slow, loading_animation, clear
from core.constants import SAVE_FOLDER, ADMIN_FILE
from core.data_store import CITIES
from core.github_api import fetch_and_claim_events_for_player
from core.utils import hitung_stat_final
# SAVE GAME
def save_game(player):
    try:
        loading_animation("📂 Menyimpan")
        filename = os.path.join(SAVE_FOLDER, f"{player['name']}.json")
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(player, f, indent=2, ensure_ascii=False)
        slow(f"💾 Game berhasil disimpan: {filename}", 0.01)
        time.sleep(0.6)
    except Exception as e:
        slow(f"Gagal menyimpan game: {e}", 0.01)
# LOAD GAME — INTERAKTIF + AUTO FIX SAVE LAMA
def load_game_interactive():
    files = [f for f in os.listdir(SAVE_FOLDER) if f.endswith('.json')]
    clear()
    if not files:
        slow("Tidak ada save yang ditemukan.", 0.02)
        time.sleep(1)
        return None
      
    print("\n📂 LOAD GAME 📂")
    for i, f in enumerate(files, start=1):
        print(f"{i}. {f[:-5]}")
    print()
    try:
        num = int(input("Pilih nomor save: ").strip())
        if num < 1 or num > len(files):
            raise ValueError

        path = os.path.join(SAVE_FOLDER, files[num - 1])

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Normalisasi key lowercase
        normalized = {}
        for key, value in data.items():
            normalized[key.lower()] = value
        data = normalized
        # Tambahkan key wajib
        defaults = {
            "name": "Unknown",
            "hp": 100,
            "max_hp": 100,
            "energy": 100,
            "max_energy": 100,
            "atk": 10,
            "def": 5,
            "dex": 3,
            "location": "Jakarta",
            "weapon": "Tangan Kosong",
            "armor": "Pakaian Lusuh",
            "inventory": {},
            "level": 1,
            "exp": 0,
            "exp_to_next": 100
        }

        for k, v in defaults.items():
            if k not in data:
                data[k] = v
        # Hapus key uppercase lama
        for k in list(data.keys()):
            if not k.islower():
                del data[k]
        # Simpan ulang versi bersih
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        slow(f"\n✅ Save berhasil diperbaiki & dimuat: {data.get('name', 'Unknown')}", 0.02)
        time.sleep(0.6)
        return data

    except Exception as e:
        slow(f"❌ Gagal memuat save: {e}", 0.02)
        time.sleep(1)
        return None
# CREATE NEW GAME
def create_new_game():
    # Hapus semua save lama
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

    player_uuid = str(uuid.uuid4())

    player = {
        "name": name,
        "uuid": player_uuid,
        "level": 1,
        "exp": 0,
        "exp_to_next": 100,
        "hp": 100,
        "max_hp": 100,
        "energy": 100,
        "max_energy": 100,
        "atk": 10,
        "def": 5,
        "dex": 3,
        "weapon": "Tangan Kosong",
        "armor": "Pakaian Lusuh",
        "inventory": {
            "Perban": 2, "Minuman": 2, "Makanan": 1,
            "Ammo 9mm": 10, "Ammo 12mm": 2, "Ammo 7.2mm": 1,
            "Tombak": 1
        },
        "location": "Hutan Pinggiran"
    }
    # Auto admin jika nama Vyoker
    if player["name"].lower() == "vyoker":
        if not os.path.exists(ADMIN_FILE):
            try:
                with open(ADMIN_FILE, "w", encoding="utf-8") as af:
                    af.write(player_uuid)
                slow("Admin file dibuat dan UUID-mu didaftarkan sebagai admin.", 0.02)
                time.sleep(0.6)
            except:
                pass
    save_game(player)
    try:
        claimed = fetch_and_claim_events_for_player(player)
        if claimed:
            slow(f"🎁 Kamu menerima {len(claimed)} hadiah event saat membuat akun!", 0.02)
            time.sleep(0.6)
    except:
        pass

    slow(f"\nSelamat, {player['name']}! Karaktermu telah dibuat. UUID kamu: {player['uuid']}", 0.02)
    time.sleep(0.8)
    return player
# LEVEL UP SYSTEM
def check_level_up(player):
    if player.get('level', 1) >= 100:
        player['level'] = 100
        return

    while player.get('exp', 0) >= player.get('exp_to_next', 100):

        if player['level'] >= 100:
            player['level'] = 100
            player['exp'] = 0
            return
        # Naik level
        player['exp'] -= player['exp_to_next']
        player['level'] += 1
        player['exp_to_next'] = int(player.get('exp_to_next',100) * 1.5)
        player['atk'] += 1
        player['def'] += 1
        player['dex'] += 1
        player['max_hp'] += 5
        player['max_energy'] += 2
        player['hp'] = player['max_hp']
        player['energy'] = player['max_energy']
        slow(f"\n🎉 Naik level! Sekarang kamu level {player['level']}", 0.02)
        time.sleep(0.8)
# QUEST HOLDER
def ensure_player_quests(player):
    if "quests" not in player:
        player["quests"] = {
            "main_active": None,
            "side_active": [],
            "completed": []
      }
