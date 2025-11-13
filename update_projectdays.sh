#!/data/data/com.termux/files/usr/bin/bash
# PROJECT DAYS ONLINE - UPDATER v3.1 (Apocalypse Style)
REPO_RAW="https://raw.githubusercontent.com/Vyoker/Project-Days-Online/main"
GAME_DIR="$HOME/Project_Days"
DATA_DIR="$GAME_DIR/data"

DARK_BG="\e[48;2;20;20;20m"
GOLD="\e[38;2;210;180;140m"
BROWN="\e[38;2;165;110;60m"
GREEN="\e[92m"
YELLOW="\e[93m"
RESET="\e[0m"

spinner() {
  local pid=$!
  local spin=(⠋ ⠙ ⠹ ⠸ ⠼ ⠴ ⠦ ⠧ ⠇ ⠏)
  local i=0
  while kill -0 $pid 2>/dev/null; do
    printf "\r${YELLOW}${spin[$i]}${RESET} $1"
    i=$(( (i+1) % 10 ))
    sleep 0.07
  done
  printf "\r${GREEN}✓${RESET} $1 selesai.\n"
}

clear
echo -e "${DARK_BG}${GOLD}"
echo "╔══════════════════════════════════════════════╗"
echo "║      PROJECT DAYS ONLINE — UPDATER v3.1      ║"
echo "║                 Mode : Online                ║"
echo "╚══════════════════════════════════════════════╝"
echo -e "${RESET}"
sleep 0.5

mkdir -p "$GAME_DIR" "$DATA_DIR"

FILES=(
"Project_Days_Online.py"
"data/items.json" "data/weapons.json" "data/armors.json" "data/monsters.json"
"data/descriptions.json" "data/crafting.json" "data/cities.json" "data/events.json"
"data/settings.json" "data/dialogs.json" "data/quests.json"
)

echo -e "${BROWN}Memeriksa update terbaru...${RESET}"
sleep 0.5

for f in "${FILES[@]}"; do
  url="$REPO_RAW/$f"
  if [[ "$f" == data/* ]]; then
    target="$DATA_DIR/$(basename "$f")"
  else
    target="$GAME_DIR/$(basename "$f")"
  fi
  (curl -sL --fail "$url" -o "$target") & spinner "Mengunduh: $(basename "$f")"
done

echo -e "\n${GREEN}✓ Semua file berhasil diperbarui.${RESET}"
echo -e "${YELLOW}Catatan: admin_key.txt tidak akan diubah oleh updater.${RESET}\n"

echo -e "${DARK_BG}${GOLD}"
echo "╔══════════════════════════════════════════════╗"
echo "║              UPDATE SELESAI!                 ║"
echo "╚══════════════════════════════════════════════╝"
echo -e "${RESET}"
