# core/utils.py
import os
import sys
import time
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich import box

console = Console()

# Warna & tema header Project Days
HEADER_BG = "grey11 on rgb(85,52,36)"
HIGHLIGHT = "rgb(210,180,140)"
ACCENT = "rgb(182,121,82)"


# -----------------------------------------------------------
# TYPEWRITER TEXT (SLOW PRINT)
# -----------------------------------------------------------
def slow(text, delay=0.01):
    """Menampilkan teks dengan efek mengetik."""
    for c in str(text):
        sys.stdout.write(c)
        sys.stdout.flush()
        time.sleep(delay)
    print()


# -----------------------------------------------------------
# CLEAR SCREEN + HEADER
# -----------------------------------------------------------
def clear():
    """Membersihkan layar dan menampilkan header Project Days."""
    os.system("clear" if os.name != "nt" else "cls")

    header = Text(
        " ☣ PROJECT DAYS — APOCALYPSE ☣ ",
        style=f"bold {HIGHLIGHT} on {HEADER_BG}"
    )
    console.print(
        Panel(header, box=box.DOUBLE, style=HEADER_BG)
    )


# -----------------------------------------------------------
# LOADING ANIMATION
# -----------------------------------------------------------
def loading_animation(message="Loading", duration=1.2, speed=0.25):
    """Animasi loading titik bergantian."""
    end = time.time() + duration
    i = 0
    while time.time() < end:
        dots = "." * ((i % 3) + 1)
        console.print(
            Panel(
                f"[{HIGHLIGHT}]{message}[/]{dots}",
                style=ACCENT,
                box=box.ROUNDED
            )
        )
        time.sleep(speed)
        i += 1
