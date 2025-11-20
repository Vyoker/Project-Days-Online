# core/constants.py
import os
from rich.console import Console

console = Console()

# Warna header Project Days
HEADER_BG = "grey11 on rgb(85,52,36)"
HIGHLIGHT = "rgb(210,180,140)"
ACCENT = "rgb(182,121,82)"

# Lokasi folder default
DATA_PATH = "data"
SAVE_FOLDER = "saves"
ADMIN_FILE = "admin.txt"
TOKEN_FILE = "gh_token.txt"

# Pengaturan sistem lain
MAX_CHAT_SIZE_KB = 500

# Pastikan folder penting ada
os.makedirs(DATA_PATH, exist_ok=True)
os.makedirs(SAVE_FOLDER, exist_ok=True)
