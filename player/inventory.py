# player/inventory.py
import time
from core.utils import slow, clear, loading_animation
from core.data_store import DESCRIPTIONS, CRAFTING, ITEMS, WEAPONS, ARMORS
from player.profile import check_level_up
from player.stats import hitung_stat_final

# TAMPILKAN DESKRIPSI ITEM
def tampilkan_deskripsi(nama_item):
    data = DESCRIPTIONS
    found = None
    kategori = None

    for k in ("items", "weapons", "armors"):
        if nama_item in data.get(k, {}):
            found = data[k][nama_item]
            kategori = k
            break

    if not found:
        slow("❌ Deskripsi item tidak ditemukan.", 0.02)
        input("\nTekan Enter untuk kembali...")
        return

    lines = []
    desc = found.get("desc", "Tidak ada deskripsi.")
    lines.append(f"📝 {desc}")

    stats = []
    if "hp" in found and found.get("hp", 0) != 0:
        stats.append(f"❤️ HP: +{found['hp']}")
    if "energy" in found and found.get("energy", 0) != 0:
        stats.append(f"⚡ Energy: +{found['energy']}")
    if "atk" in found:
        stats.append(f"🗡️ ATK: +{found['atk']}")
    if "def" in found:
        stats.append(f"🛡️ DEF: +{found['def']}")
    if "ammo" in found:
        stats.append(f"🔫 Ammo: {found['ammo']}")

    if stats:
        lines.append(" | ".join(stats))

    print("\n".join(lines))
    input("\nTekan Enter untuk kembali...")

# LIHAT DESKRIPSI ITEM DI INVENTORY
def lihat_deskripsi(player):
    clear()
    item_list = [k for k, v in player["inventory"].items() if v > 0]

    if not item_list:
        slow("Inventory kosong.", 0.02)
        time.sleep(1)
        return

    slow("Pilih item untuk melihat deskripsi:\n", 0.02)

    for i, nama in enumerate(item_list, 1):
        print(f"{i}. {nama} ({player['inventory'][nama]})")

    try:
        pilih = int(input("\nNomor item: ").strip())
        if 1 <= pilih <= len(item_list):
            tampilkan_deskripsi(item_list[pilih - 1])
    except:
        slow("Input tidak valid.", 0.02)

# GUNAKAN ITEM
def gunakan_item(player):
    clear()
    slow("Pilih item yang ingin digunakan:\n", 0.01)

    inv = {k: v for k, v in player["inventory"].items() if v > 0}

    if not inv:
        slow("Inventory kosong.", 0.01)
        return

    items_list = list(inv.keys())
    for i, item in enumerate(items_list, 1):
        print(f"{i}. {item} ({inv[item]})")

    pilihan = input("\nNomor item: ").strip()

    if not pilihan.isdigit():
        slow("Input tidak valid.", 0.01)
        return

    pilihan = int(pilihan)
    if not (1 <= pilihan <= len(items_list)):
        slow("Pilihan tidak valid.", 0.01)
        return

    item = items_list[pilihan - 1]

    # 1. Consumable
    if item in ITEMS:
        data = ITEMS[item]
        heal = data.get("heal", data.get("hp", 0))
        energy = data.get("energy", 0)

        if heal:
            player["hp"] = min(player["max_hp"], player["hp"] + heal)
        if energy:
            player["energy"] = min(player["max_energy"], player["energy"] + energy)

        inv[item] -= 1
        if inv[item] <= 0:
            del inv[item]

        slow(f"Kamu menggunakan {item}.", 0.01)
        hitung_stat_final(player)
        return

    # 2. Weapon equip
    if item in WEAPONS:
        old = player.get("weapon")
        if old in WEAPONS:
            inv[old] = inv.get(old, 0) + 1

        player["weapon"] = item

        inv[item] -= 1
        if inv[item] <= 0:
            del inv[item]

        slow(f"Kamu memasang weapon: {item}", 0.01)
        hitung_stat_final(player)
        return

    # 3. Armor equip
    if item in ARMORS:
        old = player.get("armor")
        if old in ARMORS:
            inv[old] = inv.get(old, 0) + 1

        player["armor"] = item

        inv[item] -= 1
        if inv[item] <= 0:
            del inv[item]

        slow(f"Kamu memakai armor: {item}", 0.01)
        hitung_stat_final(player)
        return

    slow("Item ini tidak bisa digunakan.", 0.01)

# BUANG ITEM
def buang_item(player):
    inv = {k: v for k, v in player["inventory"].items() if v > 0}

    if not inv:
        slow("Tidak ada item untuk dibuang.", 0.02)
        time.sleep(1)
        return

    clear()
    print("Pilih item yang ingin dibuang:\n")

    items = list(inv.items())
    for i, (item, jumlah) in enumerate(items, 1):
        print(f"{i}. {item} ({jumlah})")

    try:
        pilih = int(input("\nNomor item: ").strip())
        item, jumlah = items[pilih - 1]
        del player["inventory"][item]
        slow(f"{item} dibuang.", 0.02)
    except:
        slow("Pilihan tidak valid.", 0.02)

    time.sleep(0.6)

# CRAFTING
def crafting_menu(player):
    clear()
    print("⚒️ MENU CRAFTING")

    resep_list = list(CRAFTING.keys())

    if not resep_list:
        slow("Tidak ada resep crafting.", 0.02)
        return

    for i, nama in enumerate(resep_list, 1):
        bahan = ", ".join(f"{b} x{j}" for b, j in CRAFTING[nama]["bahan"].items())
        print(f"{i}. {nama} (Butuh: {bahan})")

    print(f"{len(resep_list)+1}. Kembali")

    pilihan = input("\nPilih resep: ").strip()
    if not pilihan.isdigit():
        slow("Input tidak valid.", 0.02)
        return

    pilihan = int(pilihan)
    if pilihan == len(resep_list) + 1:
        return

    if not (1 <= pilihan <= len(resep_list)):
        slow("Pilihan tidak valid.", 0.02)
        return

    nama_resep = resep_list[pilihan - 1]
    resep = CRAFTING[nama_resep]

    bahan = resep["bahan"]
    hasil = resep["hasil"]
    exp_reward = resep.get("exp", 0)

    # Periksa bahan cukup
    for item, qty in bahan.items():
        if player["inventory"].get(item, 0) < qty:
            slow("❌ Bahan tidak cukup!", 0.02)
            return

    # Kurangi bahan
    for item, qty in bahan.items():
        player["inventory"][item] -= qty
        if player["inventory"][item] <= 0:
            del player["inventory"][item]

    # Tambahkan hasil
    for item, qty in hasil.items():
        player["inventory"][item] = player["inventory"].get(item, 0) + qty

    loading_animation(f"Membuat {nama_resep}")
    slow(f"Berhasil membuat {nama_resep}!", 0.02)

    if exp_reward:
        player["exp"] += exp_reward
        slow(f"+{exp_reward} EXP!", 0.02)
        check_level_up(player)

    time.sleep(0.6)

# MENU INVENTORY UTAMA
def inventory_menu(player):
    while True:
        clear()
        print(f"📦 INVENTORY — {player['name']}\n")

        if not player["inventory"]:
            print("Inventory kosong.\n")
        else:
            for i, (item, qty) in enumerate(player["inventory"].items(), 1):
                print(f"{i}. {item} ({qty})")

        print("\n1. Lihat deskripsi item")
        print("2. Gunakan item")
        print("3. Buang item")
        print("4. Crafting")
        print("5. Kembali\n")

        pilih = input("Pilih: ").strip()

        if pilih == "1":
            lihat_deskripsi(player)
        elif pilih == "2":
            gunakan_item(player)
        elif pilih == "3":
            buang_item(player)
        elif pilih == "4":
            crafting_menu(player)
        elif pilih == "5":
            return
        else:
            slow("Pilihan tidak valid.", 0.02)
