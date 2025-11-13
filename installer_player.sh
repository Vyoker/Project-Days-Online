#!/usr/bin/env bash
# Installer Player v3.1 - public installer (no admin key)
REPO_RAW="https://raw.githubusercontent.com/Vyoker/Project-Days-Online/main"
GAME_DIR="$HOME/Project_Days"
DATA_DIR="$GAME_DIR/data"
mkdir -p "$GAME_DIR/saves" "$DATA_DIR"
FILES=(
"Project_Days_Online.py"
"data/items.json" "data/weapons.json" "data/armors.json" "data/monsters.json"
"data/descriptions.json" "data/crafting.json" "data/cities.json" "data/events.json"
"data/settings.json" "data/dialogs.json" "data/quests.json" "update_projectdays.sh"
)
for f in "${FILES[@]}"; do
  url="$REPO_RAW/$f"
  target="$GAME_DIR/$(basename "$f")"
  [[ "$f" == data/* ]] && target="$DATA_DIR/$(basename "$f")"
  curl -sL --fail "$url" -o "$target"
done
echo "Player installer complete. Run: cd ~/Project_Days && python3 Project_Days_Online.py"
