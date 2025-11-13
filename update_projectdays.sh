#!/usr/bin/env bash
# update_projectdays.sh v3.1
REPO_RAW="https://raw.githubusercontent.com/Vyoker/Project-Days-Online/main"
GAME_DIR="$HOME/Project_Days"
DATA_DIR="$GAME_DIR/data"
FILES=(
  "Project_Days_Online.py"
  "data/items.json" "data/weapons.json" "data/armors.json" "data/monsters.json"
  "data/descriptions.json" "data/crafting.json" "data/cities.json" "data/events.json"
  "data/settings.json" "data/dialogs.json" "data/quests.json"
)
mkdir -p "$DATA_DIR"
for f in "${FILES[@]}"; do
  url="$REPO_RAW/$f"
  target="$GAME_DIR/$(basename "$f")"
  [[ "$f" == data/* ]] && target="$DATA_DIR/$(basename "$f")"
  curl -sL --fail "$url" -o "$target" && echo "[OK] Updated $(basename "$f")" || echo "[!E] Failed $(basename "$f")"
done
echo "Update complete. Note: admin_key.txt is not modified by this updater."
