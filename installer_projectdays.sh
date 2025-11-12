#!/data/data/com.termux/files/usr/bin/bash
# ☣ PROJECT DAYS ONLINE - AUTO INSTALLER v3.0
# Mendukung 11 file JSON + Token GitHub + gaya panel game

# === WARNA SESUAI GAME ===
HEADER_BG="\e[48;2;17;17;17m"       # grey11
HIGHLIGHT="\e[38;2;210;180;140m"   # golden tan
ACCENT="\e[38;2;182;121;82m"       # accent brown
GREEN="\e[92m"
RED="\e[91m"
YELLOW="\e[93m"
CYAN="\e[96m"
RESET="\e[0m"

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
  "update_projectdays.sh"
)

# === PANEL GAYA GAME ===
panel() {
  local title="$1"
  echo -e "${HEADER_BG}${HIGHLIGHT}╔══════════════════════════════════════════════════════════════════╗${RESET}"
  printf "${HEADER_BG}${HIGHLIGHT}║ %-64s ║${RESET}\n" "$title"
  echo -e "${HEADER_BG}${HIGHLIGHT}╚══════════════════════════════════════════════════════════════════╝${RESET}"
}

# === SPINNER ===
spinner() {
  local pid=$1
  local spin=('⠋' '⠙' '⠹' '⠸' '⠼' '⠴' '⠦' '⠧' '⠇' '⠏')
  local delay=0.08
  while kill -0 "$pid" 2>/dev/null; do
    for c in "${spin[@]}"; do
      printf "\r${ACCENT}[${c}]${RESET} ${HIGHLIGHT}Memproses...${RESET}"
      sleep $delay
    done
  done
  printf "\r${GREEN}[✓]${RESET} ${HIGHLIGHT}Selesai.${RESET}                    \n"
}

# === HEADER ===
clear
panel "☣ PROJECT DAYS ONLINE — INSTALLER v3.0 ☣"
sleep 1

# === STEP 1: UPDATE TERMUX & DEPENDENCY ===
panel "📦 [1/5] Menyiapkan dependensi Termux"
pkg update -y >/dev/null 2>&1 && pkg upgrade -y >/dev/null 2>&1
pkg install python git curl unzip -y >/dev/null 2>&1
pip install requests rich --upgrade >/dev/null 2>&1
echo -e "${GREEN}✅ Dependensi siap${RESET}"
sleep 0.5

# === STEP 2: BUAT FOLDER GAME ===
panel "📁 [2/5] Membuat struktur folder Project_Days"
mkdir -p "$GAME_DIR/saves"
mkdir -p "$DATA_DIR"
cd "$GAME_DIR"
echo -e "${GREEN}✅ Folder Project_Days siap${RESET}"
sleep 0.3

# === STEP 3: DOWNLOAD SEMUA FILE ===
panel "🔽 [3/5] Mengunduh file game dan data pack"
for f in "${FILES[@]}"; do
  url="$REPO_RAW/$f"
  target="$GAME_DIR/$(basename "$f")"
  [[ "$f" == data/* ]] && target="$DATA_DIR/$(basename "$f")"
  (curl -s -L --fail "$url" -o "$target") &
  pid=$!
  spinner $pid
  if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅${RESET} ${HIGHLIGHT}$(basename "$f") berhasil diunduh.${RESET}"
  else
    echo -e "${RED}❌${RESET} ${HIGHLIGHT}Gagal mengunduh $(basename "$f").${RESET}"
  fi
done
sleep 0.5

# === STEP 4: TOKEN GITHUB OPSIONAL ===
panel "🔑 [4/5] Token GitHub (opsional)"
echo -e "${HIGHLIGHT}Token digunakan untuk mengaktifkan fitur online (chat, market, event).${RESET}"
echo -e "${YELLOW}Buat token di:${RESET} ${CYAN}https://github.com/settings/tokens${RESET}"
echo -e "${ACCENT}Centang: public_repo | Pilih: No Expiration${RESET}"
read -p "Tempel token GitHub kamu (atau tekan Enter untuk offline mode): " GH_TOKEN
if [ -n "$GH_TOKEN" ]; then
  echo "$GH_TOKEN" > "$GAME_DIR/gh_token.txt"
  chmod 600 "$GAME_DIR/gh_token.txt"
  echo -e "${GREEN}✅ Token disimpan ke gh_token.txt${RESET}"
else
  echo -e "${YELLOW}⚠️ Mode offline diaktifkan.${RESET}"
fi
sleep 0.5

# === STEP 5: CEK DATA PACK VERSI ===
if [ -f "$DATA_DIR/settings.json" ]; then
  VERSION=$(grep -o '"version": *"[^"]*"' "$DATA_DIR/settings.json" | head -n1 | cut -d'"' -f4)
  panel "📁 Data Pack Versi ${VERSION}"
else
  panel "⚠️ File settings.json tidak ditemukan!"
fi

# === PENUTUP ===
panel "🚀 Instalasi Selesai!"
echo -e "${GREEN}✅ Semua file game & data pack berhasil dipasang.${RESET}"
echo ""
echo -e "${HIGHLIGHT}Untuk menjalankan game:${RESET}"
echo -e "  ${CYAN}cd ~/Project_Days && python3 Project_Days_Online.py${RESET}"
echo ""
echo -e "${HIGHLIGHT}Untuk update ke versi terbaru gunakan:${RESET}"
echo -e "  ${CYAN}cd ~/Project_Days && bash update_projectdays.sh${RESET}"
echo ""
echo -e "${ACCENT}Selamat datang di dunia Apocalypse, Survivor.${RESET}"
echo ""
