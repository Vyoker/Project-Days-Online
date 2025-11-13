#!/usr/bin/env bash
# PROJECT DAYS — ONLINE SIMPLE UPDATER v2.5

REPO_RAW="https://raw.githubusercontent.com/Vyoker/Project-Days-Online/main"
GAME_DIR="$HOME/Project_Days"
DATA_DIR="$GAME_DIR/data"
FILES=(
  "Project_Days_Online.py"
  "data/items.json"
  "data/weapons.json"
  "data/armors.json"
  "data/monsters.json"
  "data/events.json"
  "data/descriptions.json"
  "installer_projectdays.sh"
)

# === Warna Gaya Apocalypse ===
BROWN_BG="\e[48;2;45;28;18m"
TAN_FG="\e[38;2;205;170;125m"
GREEN_FG="\e[92m"
RED_FG="\e[91m"
YELLOW_FG="\e[93m"
CYAN_FG="\e[96m"
RESET="\e[0m"

# === Spinner Animasi ===
spinner() {
  local pid=$1
  local spin=('⠋' '⠙' '⠹' '⠸' '⠼' '⠴' '⠦' '⠧' '⠇' '⠏')
  local delay=0.08
  while kill -0 "$pid" 2>/dev/null; do
    for c in "${spin[@]}"; do
      printf "\r${YELLOW_FG}[${c}]${RESET} Mengunduh..."
      sleep $delay
    done
  done
  printf "\r${GREEN_FG}[✓]${RESET} Selesai.           \n"
}

# === Panel Header ===
draw_panel() {
  local title="$1"
  echo -e "${BROWN_BG}${TAN_FG}┌──────────────────────────────────────────────────────────────┐${RESET}"
  printf "${BROWN_BG}${TAN_FG}│ %-60s │${RESET}\n" "$title"
  echo -e "${BROWN_BG}${TAN_FG}└──────────────────────────────────────────────────────────────┘${RESET}"
}

# === Start ===
clear
echo -e "${BROWN_BG}${TAN_FG}┌──────────────────────────────────────────────────────────────┐${RESET}"
echo -e "${BROWN_BG}${TAN_FG}│ ☣  PROJECT DAYS — ONLINE: DATA UPDATER (FAST MODE) ☣ │${RESET}"
echo -e "${BROWN_BG}${TAN_FG}└──────────────────────────────────────────────────────────────┘${RESET}"
echo ""

echo -e "${TAN_FG}📦 Menyiapkan direktori dan dependensi...${RESET}"
mkdir -p "$DATA_DIR"
pkg install -y python git curl > /dev/null 2>&1
pip install requests rich > /dev/null 2>&1
sleep 0.5

# === Loop Unduh ===
for f in "${FILES[@]}"; do
  echo ""
  draw_panel "Mengunduh: $(basename "$f")"
  url="$REPO_RAW/$f"
  target="$GAME_DIR/$(basename "$f")"
  [[ "$f" == data/* ]] && target="$DATA_DIR/$(basename "$f")"

  (curl -s -L --fail "$url" -o "$target") &
  pid=$!
  spinner $pid

  if [ $? -eq 0 ]; then
    echo -e "${GREEN_FG}[OK]${RESET} $(basename "$f") berhasil diunduh."
  else
    echo -e "${RED_FG}[X]${RESET} Gagal mengunduh $(basename "$f")."
  fi
done

# === Cek Token GitHub ===
if [ ! -f "$GAME_DIR/gh_token.txt" ]; then
  echo ""
  draw_panel "Token GitHub belum ditemukan!"
  echo -e "${YELLOW_FG}Buat token di:${RESET}"
  echo -e "${CYAN_FG}https://github.com/settings/tokens${RESET}"
  echo -e "${TAN_FG}dan simpan di:${RESET} ${CYAN_FG}$GAME_DIR/gh_token.txt${RESET}"
  touch "$GAME_DIR/gh_token.txt"
fi

# === Selesai ===
echo ""
draw_panel "UPDATE SELESAI!"
echo -e "${GREEN_FG}Game telah diperbarui ke versi terbaru.${RESET}"
echo -e "Untuk menjalankan game:"
echo -e "  ${CYAN_FG}cd ~/Project_Days && python3 Project_Days_Online.py${RESET}"
echo ""
echo -e "${TAN_FG}Selamat datang kembali di dunia Apocalypse.${RESET}"
echo ""
