#!/data/data/com.termux/files/usr/bin/bash
# =================================================
# PROJECT DAYS ONLINE — UPDATER v3.1
# =================================================

# ---------- COLOR STYLE ----------
DARK_BG="\e[48;2;20;20;20m"
GOLD="\e[38;2;210;180;140m"
BROWN="\e[38;2;165;110;60m"
GREEN="\e[92m"
YELLOW="\e[93m"
RED="\e[91m"
RESET="\e[0m"

# ---------- SPINNER ----------
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
echo "║        Mode: Online (Firebase Hybrid)        ║"
echo "╚══════════════════════════════════════════════╝"
echo -e "${RESET}"
sleep 0.5

# ---------- GAME FOLDER ----------
GAME_DIR="$HOME/Project_Days"
DATA_DIR="$GAME_DIR/data"

mkdir -p "$GAME_DIR"
mkdir -p "$DATA_DIR"

REPO_RAW="https://raw.githubusercontent.com/Vyoker/Project-Days-Online/main"

# ---------- FILE LIST ----------
FILES=(
"Project_Days_Online.py"
"data/items.json" "data/weapons.json" "data/armors.json" "data/monsters.json"
"data/descriptions.json" "data/crafting.json" "data/cities.json" "data/events.json"
"data/settings.json" "data/dialogs.json" "data/quests.json"
)

echo -e "${GOLD}Memeriksa update terbaru...${RESET}"
sleep 0.5

echo ""
echo -e "${BROWN}===========================================${RESET}"
echo -e "${GOLD}        🔄 MEMULAI PROSES UPDATE…${RESET}"
echo -e "${BROWN}===========================================${RESET}"
echo ""

# ---------- DOWNLOAD LOOP ----------
for f in "${FILES[@]}"; do
    url="$REPO_RAW/$f"

    if [[ "$f" == data/* ]]; then
        target="$DATA_DIR/$(basename "$f")"
    else
        target="$GAME_DIR/$(basename "$f")"
    fi

    (curl -sL --fail "$url" -o "$target") &
    spinner "Mengunduh: $(basename "$f")"

done

echo ""
echo -e "${GREEN}✓ Semua file berhasil diperbarui.${RESET}"
echo -e "${YELLOW}Catatan: admin_key.txt tidak disentuh oleh updater.${RESET}"
echo ""

# ---------- FINAL DISPLAY ----------
echo -e "${DARK_BG}${GOLD}"
echo "╔══════════════════════════════════════════════╗"
echo "║              UPDATE SELESAI!                 ║"
echo "╠══════════════════════════════════════════════╣"
echo "║   Gunakan perintah berikut untuk bermain:    ║"
echo "║    cd ~/Project_Days                         ║"
echo "║    python3 Project_Days_Online.py            ║"
echo "╚══════════════════════════════════════════════╝"
echo -e "${RESET}"

echo ""
echo -e "${BROWN}Selamat kembali ke dunia apocalypse, Survivor.${RESET}"
echo ""
