#!/data/data/com.termux/files/usr/bin/bash
# ============================================
# PROJECT DAYS ONLINE — INSTALLER PLAYER v3.1
# ============================================

# ---------- COLOR STYLE ----------
WHITE="\e[97m"
GREEN="\e[92m"
YELLOW="\e[93m"
RED="\e[91m"
BLUE="\e[94m"
GRAY="\e[90m"
RESET="\e[0m"

# ---------- SPINNER FUNCTION ----------
spinner() {
    local pid=$!
    local spin=(⠋ ⠙ ⠹ ⠸ ⠼ ⠴ ⠦ ⠧ ⠇ ⠏)
    local i=0
    while kill -0 $pid 2>/dev/null; do
        printf "\r${YELLOW}${spin[$i]}${RESET} $1"
        i=$(( (i+1) % 10 ))
        sleep 0.1
    done
    printf "\r${GREEN}✓${RESET} $1 selesai.\n"
}

clear
echo -e "${BLUE}"
echo "==============================================="
echo "      PROJECT DAYS ONLINE — INSTALLER v3.1"
echo "               Public Player Mode"
echo "==============================================="
echo -e "${RESET}"

# -----------------------------------
# 1. UPDATE TERMUX
# -----------------------------------
echo -e "${WHITE}[1/6] Updating Termux...${RESET}"
(pkg update -y && pkg upgrade -y) > /dev/null 2>&1 &
spinner "Memperbarui Termux"

echo ""

# -----------------------------------
# 2. INSTALL DEPENDENCIES
# -----------------------------------
echo -e "${WHITE}[2/6] Installing dependencies...${RESET}"

PKGS=(
    python
    python-pip
    git
    curl
    openssl
    libxml2
    libxslt
)

for p in "${PKGS[@]}"; do
    (pkg install -y $p > /dev/null 2>&1) &
    spinner "Menginstall paket: $p"
done

echo ""

# -----------------------------------
# 3. PYTHON MODULES
# -----------------------------------
echo -e "${WHITE}[3/6] Installing Python modules...${RESET}"

(pip install --upgrade pip > /dev/null 2>&1) &
spinner "Upgrade pip"

(pip install requests rich --upgrade > /dev/null 2>&1) &
spinner "Menginstall pip modules"

echo ""

# -----------------------------------
# 4. PREPARE DIRECTORIES
# -----------------------------------
echo -e "${WHITE}[4/6] Preparing directories...${RESET}"

mkdir -p "$HOME/Project_Days"
mkdir -p "$HOME/Project_Days/saves"
mkdir -p "$HOME/Project_Days/data"

echo -e "${GREEN}✓${RESET} Folder siap."
echo ""

# -----------------------------------
# 5. DOWNLOAD GAME FILES
# -----------------------------------
echo -e "${WHITE}[5/6] Downloading game files...${RESET}"

REPO_RAW="https://raw.githubusercontent.com/Vyoker/Project-Days-Online/main"
GAME_DIR="$HOME/Project_Days"
DATA_DIR="$GAME_DIR/data"

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

    (curl -sL --fail "$url" -o "$target") &
    spinner "Mengunduh: $f"
done

chmod +x "$GAME_DIR/update_projectdays.sh"

echo ""

# -----------------------------------
# 6. INSTALL COMPLETE
# -----------------------------------
echo -e "${WHITE}[6/6] Installation Completed!${RESET}"
sleep 0.3
echo ""
echo -e "${GREEN}==============================================="
echo "            PROJECT DAYS ONLINE v3.1"
echo "                  Installed!"
echo -e "===============================================${RESET}"
echo ""
echo -e "${BLUE}Untuk menjalankan game:${RESET}"
echo "  cd ~/Project_Days"
echo "  python3 Project_Days_Online.py"
echo ""
echo -e "${BLUE}Untuk update game:${RESET}"
echo "  cd ~/Project_Days"
echo "  bash update_projectdays.sh"
echo ""
echo -e "${YELLOW}Selamat datang di dunia Apocalypse, Survivor!${RESET}"
echo ""
