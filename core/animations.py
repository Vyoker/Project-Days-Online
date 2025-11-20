# core/animations.py
import os
import sys
import time
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich import box

console = Console()

HEADER_BG = "grey11 on rgb(85,52,36)"
HIGHLIGHT = "rgb(210,180,140)"
ACCENT = "rgb(182,121,82)"


def slow(text, delay=0.01):
    for c in str(text):
        sys.stdout.write(c)
        sys.stdout.flush()
        time.sleep(delay)
    print()


def clear():
    os.system("clear" if os.name != "nt" else "cls")
    header = Text(
        " ☣ PROJECT DAYS — APOCALYPSE ☣ ",
        style=f"bold {HIGHLIGHT} on {HEADER_BG}"
    )
    console.print(Panel(header, box=box.DOUBLE, style=HEADER_BG))


def loading_animation(message="Loading", duration=1.2, speed=0.25):
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
