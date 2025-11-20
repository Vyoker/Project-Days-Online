# world/explore.py
import random
import time
from core.utils import slow, loading_animation, clear
from core.data_store import WEAPONS
from player.profile import check_level_up
from core.constants import SAVE_FOLDER
from player.inventory import gunakan_item
from combat.battle import battle_zombie

# LOOT ITEM EXPLORE
def dapat_item(player, lokasi, reward_exp):
    slow("Kamu menemukan sesuatu di sekitar...\n", 0.02)

    loot_table = {
        "Hutan": ["Kayu", "Batu", "Daun", "Makanan", "Minuman"],
        "Desa": ["Perban", "Kain", "Makanan", "Minuman", "Pisau"],
        "Kota": ["Perban", "Painkiller", "Makanan", "Minuman", "Ammo 9mm"]
    }
    # Loot khusus kota
    if lokasi == "Kota":
        roll = random.randint(1, 100)

        if roll <= 20:
            # Senjata random dari weapons.json
            item = random.choice(list(WEAPONS.keys()))

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
    # EXP explore
    player["exp"] += reward_exp
    slow(f"+{reward_exp} EXP dari eksplorasi!", 0.02)

    check_level_up(player)
    time.sleep(0.6)

# MENU EXPLORE UTAMA
def explore_menu(player):
    while True:
        clear()
        print("🌍  EXPLORE MENU\n")
        print("1. Hutan")
        print("2. Desa")
        print("3. Kota")
        print("4. Kembali\n")

        choice = input("Pilih lokasi: ").strip()

        if choice == "1":
            lokasi = "Hutan"
            energi = 7
            chance_zombie = 30
            chance_item = 80
            reward_exp = 10

        elif choice == "2":
            lokasi = "Desa"
            energi = 15
            chance_zombie = 70
            chance_item = 80
            reward_exp = 20

        elif choice == "3":
            lokasi = "Kota"
            energi = 25
            chance_zombie = 90
            chance_item = 80
            reward_exp = 40

        elif choice == "4":
            return

        else:
            slow("Pilihan tidak valid.", 0.02)
            continue
        # Cek energi
        if player["energy"] < energi:
            slow("⚠️ Energi tidak cukup untuk menjelajah ke sana.", 0.03)
            time.sleep(0.6)
            continue
        # Kurangi energi
        player["energy"] -= energi
        if player["energy"] < 0:
            player["energy"] = 0

        slow(f"⚡ Energi berkurang -{energi}, tersisa {player['energy']}/{player['max_energy']}", 0.03)
        time.sleep(0.5)

        loading_animation(f"🌍 Menjelajah ke {lokasi}...")
        time.sleep(0.6)

        event_roll = random.randint(1, 100)
        # Loot item lebih prioritas
        if event_roll <= chance_item:
            dapat_item(player, lokasi, reward_exp)
        # Kalau tidak dapat item tapi masuk area zombie
        elif event_roll <= chance_item + chance_zombie:
            battle_zombie(player, lokasi, reward_exp)

        else:
            slow("Tidak terjadi apa-apa...", 0.02)
        # Save setelah eksplor
        save_path = SAVE_FOLDER + f"/{player.get('name')}.json"
        try:
            with open(save_path, "w", encoding="utf-8") as f:
                import json
                json.dump(player, f, indent=2, ensure_ascii=False)
        except:
            pass
