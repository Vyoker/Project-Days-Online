#!/usr/bin/env bash
# PROJECT DAYS — ONLINE UPDATER v3.0 (Full JSON Support + Game-Style Panel)

REPO_RAW="https://raw.githubusercontent.com/Vyoker/Project-Days-Online/main"
GAME_DIR="$HOME/Project_Days"
DATA_DIR="$GAME_DIR/data"

FILES=(
  "Project_Days_Online.py"
  "data/items.json"
  "data/weapons.json"
  "data/armors.json"
  "data/monsters.json"
  "data/descriptions.json"
  "data/crafting.json"
  "data/cities.json"
  "data/events.json"
  "data/settings.json"
  "data/dialogs.json"
  "data/quests.json"
)

# === WARNA ALA GAME ===
HEADER_BG="\e[48;2;17;17;17m"       # grey11
HIGHLIGHT="\e[38;2;210;180;140m"   # golden tan
ACCENT="\e[38;2;182;121;82m"       # accent brown
GREEN_FG="\e[92m"
RED_FG="\e[91m"
YELLOW_FG="\e[93m"
CYAN_FG="\e[96m"
RESET="\e[0m"

# === ANIMASI SPINNER ===
spinner() {
  local pid=$1
  local spin=('⠋' '⠙' '⠹' '⠸' '⠼' '⠴' '⠦' '⠧' '⠇' '⠏')
  local delay=0.08
  while kill -0 "$pid" 2>/dev/null; do
    for c in "${spin[@]}"; do
      printf "\r${ACCENT}[${c}]${RESET} ${HIGHLIGHT}Mengunduh data...${RESET}"
      sleep $delay
    done
  done
  printf "\r${GREEN_FG}[✓]${RESET} ${HIGHLIGHT}Selesai.${RESET}               \n"
}

# === PANEL GAYA GAME ===
panel() {
  local title="$1"
  echo -e "${HEADER_BG}${HIGHLIGHT}╔══════════════════════════════════════════════════════════════════╗${RESET}"
  printf "${HEADER_BG}${HIGHLIGHT}║ %-64s ║${RESET}\n" "$title"
  echo -e "${HEADER_BG}${HIGHLIGHT}╚══════════════════════════════════════════════════════════════════╝${RESET}"
}

# === JUDUL UTAMA ===
clear
panel "☣ PROJECT DAYS — ONLINE UPDATER v3.0 ☣"
echo -e "${HIGHLIGHT}📦 Menyiapkan direktori dan dependensi...${RESET}"
mkdir -p "$DATA_DIR"
pkg install -y python git curl > /dev/null 2>&1
pip install requests rich > /dev/null 2>&1
sleep 0.5

# === LOOP DOWNLOAD ===
for f in "${FILES[@]}"; do
  echo ""
  panel "Mengunduh: $(basename "$f")"
  url="$REPO_RAW/$f"
  target="$GAME_DIR/$(basename "$f")"
  [[ "$f" == data/* ]] && target="$DATA_DIR/$(basename "$f")"

  (curl -s -L --fail "$url" -o "$target") &
  pid=$!
  spinner $pid

  if [ $? -eq 0 ]; then
    echo -e "${GREEN_FG}[OK]${RESET} ${HIGHLIGHT}$(basename "$f") berhasil diunduh.${RESET}"
  else
    echo -e "${RED_FG}[X]${RESET} ${HIGHLIGHT}Gagal mengunduh $(basename "$f").${RESET}"
  fi
done

# === CEK VERSI DATA PACK ===
if [ -f "$DATA_DIR/settings.json" ]; then
  VERSION=$(grep -o '"version": *"[^"]*"' "$DATA_DIR/settings.json" | head -n1 | cut -d'"' -f4)
  echo ""
  panel "📁 DATA PACK: VERSI ${VERSION}"
else
  echo ""
  panel "⚠️  settings.json tidak ditemukan!"
fi

# === TOKEN GITHUB ===
if [ ! -f "$GAME_DIR/gh_token.txt" ]; then
  echo ""
  panel "🔑 Token GitHub Belum Ada"
  echo -e "${YELLOW_FG}Buat token di:${RESET}"
  echo -e "${CYAN_FG}https://github.com/settings/tokens${RESET}"
  echo -e "${HIGHLIGHT}Simpan token di:${RESET} ${CYAN_FG}$GAME_DIR/gh_token.txt${RESET}"
  touch "$GAME_DIR/gh_token.txt"
fi

# === PENUTUP ===
echo ""
panel "✅ UPDATE SELESAI!"
echo -e "${GREEN_FG}Semua file JSON & script telah diperbarui ke versi terbaru.${RESET}"
echo ""
echo -e "${HIGHLIGHT}Untuk menjalankan game:${RESET}"
echo -e "  ${CYAN_FG}cd ~/Project_Days && python3 Project_Days_Online.py${RESET}"
echo ""
echo -e "${ACCENT}Selamat datang kembali di dunia Apocalypse.${RESET}"
echo ""
