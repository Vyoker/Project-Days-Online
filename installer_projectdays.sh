#!/data/data/com.termux/files/usr/bin/bash
# ==========================================
# ☣ Project Days Online - Auto Installer (Termux)
# Versi: 1.4
# ==========================================
# Warna
GREEN="\033[1;32m"
YELLOW="\033[1;33m"
CYAN="\033[1;36m"
RED="\033[1;31m"
RESET="\033[0m"
# Fungsi animasi loading titik
progress_dots() {
    local message=$1
    echo -ne "${CYAN}${message}${RESET}"
    for i in {1..3}; do
        echo -ne "."
        sleep 0.5
    done
    echo
}
# Header
clear
echo -e "${YELLOW}"
echo "=========================================="
echo "   ☣ PROJECT DAYS ONLINE - INSTALLER ☣"
echo "=========================================="
echo -e "${RESET}"
sleep 1
# Step 1 - Update system
progress_dots "🧩 [1/6] Memperbarui sistem Termux"
pkg update -y >/dev/null 2>&1 && pkg upgrade -y >/dev/null 2>&1
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Sistem berhasil diperbarui${RESET}"
else
    echo -e "${RED}❌ Gagal memperbarui sistem${RESET}"
fi
sleep 0.5
# Step 2 - Install dependencies
progress_dots "📦 [2/6] Menginstal dependensi (Python, pip, curl)"
pkg install python git curl -y >/dev/null 2>&1
pip install requests rich --upgrade >/dev/null 2>&1
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Dependensi berhasil diinstal${RESET}"
else
    echo -e "${RED}❌ Gagal menginstal dependensi${RESET}"
fi
sleep 0.5
# Step 3 - Create game folder
progress_dots "📁 [3/6] Menyiapkan folder game"
cd ~
mkdir -p Project_Days && cd Project_Days
mkdir -p saves
sleep 0.3
echo -e "${GREEN}✅ Folder game siap${RESET}"
# Step 4 - Download game file only
progress_dots "🔽 [4/6] Mengunduh Project_Days_Online.py dari GitHub"
curl -L -# -o Project_Days_Online.py https://raw.githubusercontent.com/Vyoker/Project-Days-Online/main/Project_Days_Online.py
if [ ! -f "Project_Days_Online.py" ]; then
    echo -e "${RED}❌ Gagal mengunduh file Project_Days_Online.py!${RESET}"
    echo "Periksa koneksi internet atau pastikan file tersedia di repo."
    exit 1
else
    echo -e "${GREEN}✅ File Project_Days_Online.py berhasil diunduh${RESET}"
fi
sleep 0.5
# Step 5 - GitHub token input
echo
echo -e "${YELLOW}🔑 [5/6] Token GitHub (opsional untuk mode online)${RESET}"
echo "Buka link ini untuk membuat token:"
echo "👉  ${CYAN}https://github.com/settings/tokens${RESET}"
echo "Centang: public_repo  |  Pilih: No Expiration"
echo
read -p "Tempel token GitHub kamu (atau Enter untuk offline mode): " GH_TOKEN

if [ -n "$GH_TOKEN" ]; then
    echo "$GH_TOKEN" > gh_token.txt
    chmod 600 gh_token.txt
    echo -e "${GREEN}✅ Token disimpan ke gh_token.txt${RESET}"
else
    echo -e "${YELLOW}⚠️ Tidak ada token. Game akan berjalan dalam Mode Read-Only (Offline).${RESET}"
fi
sleep 0.5
# Step 6 - Jalankan game
progress_dots "🚀 [6/6] Menjalankan Project Days Online"
sleep 1
python3 Project_Days_Online.py
# Pesan akhir
echo -e "${YELLOW}"
echo "=========================================="
echo "💾 Instalasi selesai!"
echo "🕹️ Untuk menjalankan ulang game:"
echo "   cd ~/Project_Days"
echo "   python3 Project_Days_Online.py"
echo "=========================================="
echo -e "${RESET}"
