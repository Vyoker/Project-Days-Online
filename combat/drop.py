# combat/drop.py
import random, time
from core.utils import slow
from core.data_store import DROP
from core.utils import slow, clear, loading_animation

def drop_item(player, monster_name="default"):
    data = DROP
    # Kalau monster punya loot khusus
    loot = data.get("monsters", {}).get(monster_name, data.get("default", {}))
    chance = loot.get("chance", 0)
    # Tidak dapat apa-apa
    if random.randint(1, 100) > chance:
        return
    items = loot.get("items", {})
    if not items:
        return
    # Pilih item random
    item = random.choice(list(items.keys()))
    min_q, max_q = items[item]
    qty = random.randint(min_q, max_q)
    # Tambahkan ke inventory
    player["inventory"][item] = player["inventory"].get(item, 0) + qty
    slow(f"🎁 Zombie menjatuhkan {qty}x {item}!", 0.02)
    time.sleep(0.6)
