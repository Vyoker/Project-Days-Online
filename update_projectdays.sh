#!/usr/bin/env bash
# PROJECT DAYS — RECURSIVE AUTO UPDATER v1.0.0
# Repo: Vyoker/Project-Days-Online

set -euo pipefail

REPO="Vyoker/Project-Days-Online"
BRANCH="main"
API_URL="https://api.github.com/repos/${REPO}/git/trees/${BRANCH}?recursive=1"
RAW_BASE="https://raw.githubusercontent.com/${REPO}/${BRANCH}"
GAME_DIR="${HOME}/Project_Days"
TMP_DIR="${GAME_DIR}/.upd_tmp"
TOKEN_FILE="${GAME_DIR}/gh_token.txt"

# UI Colors
BROWN_BG="\e[48;2;45;28;18m"
TAN_FG="\e[38;2;205;170;125m"
GREEN_FG="\e[92m"
RED_FG="\e[91m"
YELLOW_FG="\e[93m"
CYAN_FG="\e[96m"
RESET="\e[0m"

spinner() {
  local pid=$1
  local spin_chars=('⠋' '⠙' '⠹' '⠸' '⠼' '⠴' '⠦' '⠧' '⠇' '⠏')
  local delay=0.06

  while kill -0 "$pid" 2>/dev/null; do
    for c in "${spin_chars[@]}"; do
      printf "\r${YELLOW_FG}[${c}]${RESET} Mengunduh..."
      sleep $delay
    done
  done

  printf "\r${GREEN_FG}[✓]${RESET} Selesai.                     \n"
}

panel() {
  local title="$1"
  echo -e "${BROWN_BG}${TAN_FG}┌────────────────────────────────────────────────────────────────┐${RESET}"
  printf "${BROWN_BG}${TAN_FG}│ %-64s │${RESET}\n" "$title"
  echo -e "${BROWN_BG}${TAN_FG}└────────────────────────────────────────────────────────────────┘${RESET}"
}

ensure_requirements() {
  command -v curl >/dev/null || { echo -e "${RED_FG}curl tidak ditemukan. Install pkg install curl${RESET}"; exit 1; }
  command -v python3 >/dev/null || { echo -e "${RED_FG}python3 tidak ditemukan. Install pkg install python${RESET}"; exit 1; }
}

get_auth_header() {
  if [ -n "${GH_TOKEN-}" ]; then
    echo "-H" "Authorization: token ${GH_TOKEN}"
    return
  fi

  if [ -f "${TOKEN_FILE}" ]; then
    local t
    t=$(sed -n '1p' "$TOKEN_FILE" | tr -d '[:space:]')
    if [ -n "$t" ]; then
      echo "-H" "Authorization: token ${t}"
      return
    fi
  fi

  echo ""
}

ensure_requirements
mkdir -p "$GAME_DIR"
mkdir -p "$TMP_DIR"

panel "PROJECT DAYS — AUTO UPDATER (repo: ${REPO})"
echo ""

panel "Mengambil daftar file dari GitHub API"
AUTH_HEADER="$(get_auth_header)"

if [ -n "$AUTH_HEADER" ]; then
  eval "curl -s -L ${AUTH_HEADER} \"${API_URL}\" -o \"${TMP_DIR}/tree.json\""
else
  curl -s -L "$API_URL" -o "$TMP_DIR/tree.json"
fi

# Extract file list
mapfile -t FILES < <(python3 - <<'PY'
import sys, json
t = json.load(open(sys.argv[1]))
for e in t.get("tree", []):
    if e.get("type") == "blob":
        print(e.get("path"))
PY
"$TMP_DIR/tree.json")

total=${#FILES[@]}

if [ "$total" -eq 0 ]; then
  echo -e "${RED_FG}Daftar file kosong! API bermasalah atau repo salah.${RESET}"
  exit 1
fi

panel "Mulai mengunduh semua file (total: ${total})"

count=0
for path in "${FILES[@]}"; do
  count=$((count+1))

  # Skip .git files
  [[ "$path" == .git* ]] && continue

  target_dir="${GAME_DIR}/$(dirname "$path")"
  target="${GAME_DIR}/${path}"
  tmp_target="${TMP_DIR}/$(echo "$path" | sed 's|/|_|g').tmp"

  mkdir -p "$target_dir"

  url="${RAW_BASE}/${path}"

  panel "(${count}/${total}) Mengunduh: ${path}"

  if [ -n "$AUTH_HEADER" ]; then
    eval "curl -s -L ${AUTH_HEADER} \"${url}\" -o \"${tmp_target}\" &"
  else
    curl -s -L "$url" -o "$tmp_target" &
  fi

  pid=$!
  spinner $pid
  wait $pid || true

  if [ ! -s "$tmp_target" ]; then
    echo -e "${RED_FG}[X] Gagal mengunduh: ${path}${RESET}"
    rm -f "$tmp_target"
    continue
  fi

  mv -f "$tmp_target" "$target"
  echo -e "${GREEN_FG}[OK]${RESET} ${path} diperbarui."
done

rm -rf "$TMP_DIR"

panel "UPDATE SELESAI"
echo -e "${GREEN_FG}Semua file diperbarui.${RESET}"
echo -e "${CYAN_FG}cd $GAME_DIR && python3 Project_Days_Online.py${RESET}"
