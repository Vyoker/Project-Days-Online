import random, time, sys
from core.utils import slow, loading_animation, hitung_stat_final
from core.data_store import WEAPONS, MONSTERS, ARMORS
from combat.drop import drop_item
from player.inventory import gunakan_item
from player.profile import check_level_up

def battle_zombie(player, lokasi, reward_exp):
    # Pastikan stat final sudah dihitung
    hitung_stat_final(player, WEAPONS=WEAPONS, ARMORS=ARMORS)

    loading_animation(f"☣ Zombie mendekat di {lokasi}")
    # Pilih monster random dari monsters.json
    zname = random.choice(list(MONSTERS.keys()))
    ztype = MONSTERS.get(zname, {})
    zombie = {
        "name": zname,
        "hp": random.randint(40, 80) * ztype.get("hp_mod", 1.0),
        "atk": random.randint(6, 14) * ztype.get("atk_mod", 1.0),
        "def": random.randint(0, 8) * ztype.get("def_mod", 1.0),
        "dodge": ztype.get("dodge", 0),
        "exp": reward_exp + random.randint(5, 15)
    }
    # ===== SCALING MONSTER 2% PER LEVEL =====
    player_level = min(player.get("level", 1), 100)
    scaling = 1 + (player_level - 1) * 0.02

    zombie["hp"] = int(zombie["hp"] * scaling)
    zombie["atk"] = int(zombie["atk"] * scaling)
    zombie["def"] = int(zombie["def"] * scaling)

    slow(f"Kamu bertemu dengan {zombie['name']}!", 0.02)
    slow(
        f"• HP: {int(zombie['hp'])} | ATK: {int(zombie['atk'])} | "
        f"DEF: {int(zombie['def'])} | DODGE: {zombie['dodge']}%\n",
        0.01
    )
    time.sleep(0.6)
    # ===== LOOP PERTEMPURAN =====
    while player["hp"] > 0 and zombie["hp"] > 0:
        print(f"\n⚔️  {zombie['name']} — ❤️  {int(zombie['hp'])}")
        print(f"🧍  {player['name']} — ❤️  {player['hp']} / {player['max_hp']}")
        print("1. Serang\n2. Gunakan Item\n3. Kabur\n")

        action = input("Pilih aksi: ").strip()
        # 1. SERANG
        if action == "1":
            hitung_stat_final(player, WEAPONS=WEAPONS, ARMORS=ARMORS)

            player_atk = player.get("atk_final", 10)
            weapon_name = player.get("weapon", "Tangan Kosong")
            weapon_data = WEAPONS.get(weapon_name, {})

            damage = int(player_atk)
            # Senjata tipe GUN membutuhkan peluru
            if weapon_data.get("type") == "gun":
                ammo = weapon_data.get("ammo")
                if player["inventory"].get(ammo, 0) <= 0:
                    slow(f"Tidak ada peluru {ammo}! Serangan gagal!", 0.02)
                    damage = 0
                else:
                    player["inventory"][ammo] -= 1
                    slow(
                        f"🔫 {weapon_name} digunakan, tersisa {player['inventory'].get(ammo,0)} peluru",
                        0.02,
                    )

            # Hitung damage setelah DEF zombie
            dmg_after_def = max(1, damage - int(zombie["def"]))
            zombie["hp"] -= dmg_after_def
            slow(f"Kamu menyerang dan memberi {dmg_after_def} damage!", 0.02)
            # Jika zombie belum mati → zombie menyerang
            if zombie["hp"] > 0:
                # ===== Dodge Player =====
                player_dodge = player.get("dex_final", 0) * 0.2
                if player_dodge > 70:
                    player_dodge = 70

                if random.random() < (player_dodge / 100.0):
                    slow("Kamu berhasil menghindari serangan!", 0.02)
                else:
                    zombie_atk = int(zombie["atk"])
                    def_points = player.get("def_final", 0)

                    # 1 DEF = 0.3% reduce (MAX 70%)
                    damage_reduce_pct = def_points * 0.3
                    if damage_reduce_pct > 70:
                        damage_reduce_pct = 70

                    reduction_amount = zombie_atk * (damage_reduce_pct / 100)
                    final_dmg = max(1, int(zombie_atk - reduction_amount))

                    player["hp"] -= final_dmg
                    slow(
                        f"{zombie['name']} menyerangmu dan memberi {final_dmg} damage!",
                        0.02,
                    )
        # 2. GUNAKAN ITEM
        elif action == "2":
            gunakan_item(player)
            hitung_stat_final(player, WEAPONS=WEAPONS, ARMORS=ARMORS)
            continue
        # 3. KABUR
        elif action == "3":
            if random.random() < 0.5:
                slow("Kamu berhasil kabur!", 0.02)
                return
            else:
                slow("Gagal kabur!", 0.02)
        else:
            slow("Pilihan tidak valid.", 0.02)
            continue
        # HASIL
        if zombie["hp"] <= 0:
            slow(f"\n{zombie['name']} dikalahkan!", 0.03)
            gained_exp = int(zombie["exp"])
            player["exp"] += gained_exp
            slow(f"Kamu mendapat {gained_exp} EXP!", 0.02)

            drop_item(player, zname)

            check_level_up(player)

            time.sleep(0.6)
            return

        if player["hp"] <= 0:
            slow("\nKamu tumbang... Game Over!\n", 0.03)
            time.sleep(2)
            sys.exit()
