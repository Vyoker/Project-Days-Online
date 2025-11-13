#!/data/data/com.termux/files/usr/bin/bash
# PROJECT DAYS ONLINE - PLAYER INSTALLER v3.1 (FINAL)
# Public installer: installs dependencies, downloads game files, sets up environment
REPO_RAW="https://raw.githubusercontent.com/Vyoker/Project-Days-Online/main"
GAME_DIR="$HOME/Project_Days"
DATA_DIR="$GAME_DIR/data"

# Colors
YELLOW="\e[93m"
GREEN="\e[92m"
CYAN="\e[96m"
RESET="\e[0m"

spinner() {
  local pid=$!
  local spin=(⠋ ⠙ ⠹ ⠸ ⠼ ⠴ ⠦ ⠧ ⠇ ⠏)
  local i=0
  while kill -0 $pid 2>/dev/null; do
    printf "\r${YELLOW}${spin[$i]}${RESET} $1"
    i=$(( (i+1) % 10 ))
    sleep 0.08
  done
  printf "\r${GREEN}✓${RESET} $1 selesai.\n"
}

echo -e "\n${CYAN}PROJECT DAYS ONLINE — INSTALLER (PLAYER) v3.1${RESET}\n"

echo -e "${YELLOW}[1/6] Memperbarui paket Termux...${RESET}"
(pkg update -y && pkg upgrade -y) > /dev/null 2>&1 & spinner "Updating Termux"
echo ""

echo -e "${YELLOW}[2/6] Menginstall paket dependency...${RESET}"
PKGS=(python git curl openssl clang libxml2 libxslt)
for p in "${PKGS[@]}"; do
  (pkg install -y $p > /dev/null 2>&1) & spinner "Install paket: $p"
done
echo ""

echo -e "${YELLOW}[3/6] Menginstall module Python...${RESET}"
(pip install --upgrade pip > /dev/null 2>&1) & spinner "Upgrade pip"
(pip install requests rich --upgrade > /dev/null 2>&1) & spinner "Install python modules"
echo ""

echo -e "${YELLOW}[4/6] Menyiapkan direktori game...${RESET}"
mkdir -p "$GAME_DIR" "$GAME_DIR/saves" "$DATA_DIR"
echo -e "${GREEN}✓ Direktori siap: $GAME_DIR${RESET}\n"

echo -e "${YELLOW}[5/6] Mengunduh file game dan data...${RESET}"
FILES=(
"Project_Days_Online.py"
"data/items.json" "data/weapons.json" "data/armors.json" "data/monsters.json"
"data/descriptions.json" "data/crafting.json" "data/cities.json" "data/events.json"
"data/settings.json" "data/dialogs.json" "data/quests.json"
"update_projectdays.sh"
)

for f in "${FILES[@]}"; do
  url="$REPO_RAW/$f"
  if [[ "$f" == data/* ]]; then
    target="$DATA_DIR/$(basename "$f")"
  else
    target="$GAME_DIR/$(basename "$f")"
  fi
  (curl -sL --fail "$url" -o "$target") & spinner "Mengunduh: $f"
done
chmod +x "$GAME_DIR/update_projectdays.sh"

echo -e "\n${YELLOW}[6/6] Selesai.${RESET}"
echo -e "${GREEN}Project Days v3.1 terpasang di: $GAME_DIR${RESET}"
echo -e "Jalankan game: cd ~/Project_Days && python3 Project_Days_Online.py\n"
