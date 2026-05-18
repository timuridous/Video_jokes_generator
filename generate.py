#!/usr/bin/env python3
"""
Joke Video Generator
Поєднує випадкове відео-фон + музику + текст анекдоту → mp4
"""

import sys
import random
import textwrap
import subprocess
import tempfile
from pathlib import Path
from PIL import Image, ImageDraw

# ─── Конфіг ────────────────────────────────────────────────────────────────────

BASE_DIR        = Path(__file__).parent
MUSIC_DIR       = BASE_DIR / "music"
BACKGROUNDS_DIR = BASE_DIR / "backgrounds"
JOKES_FILE      = BASE_DIR/ "Jokes" / "jokes.txt"
OUTPUT_DIR      = BASE_DIR / "output"

VIDEO_WIDTH    = 1080
VIDEO_HEIGHT   = 1920
FONT_SIZE      = 70
FONT_COLOR     = "black"
MAX_CHARS_LINE = 20
FADE_DURATION  = 1.0
LINE_SPACING   = 20
PADDING_X      = 60
PADDING_Y      = 55
CORNER_RADIUS  = 60          # радіус заокруглення кутів

FONT_PATH          = "C:/Windows/Fonts/arialbd.ttf"
FONT_PATH_FALLBACK = "C:/Windows/Fonts/arial.ttf"

VIDEO_EXTS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
AUDIO_EXTS = {".mp3", ".wav", ".ogg", ".aac", ".flac", ".m4a"}

# ───────────────────────────────────────────────────────────────────────────────
def check_ffmpeg():
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
    except FileNotFoundError:
        print("❌  ffmpeg не знайдено. Завантажте: https://ffmpeg.org/download.html")
        sys.exit(1)

def check_pillow():
    try:
        from PIL import Image
    except ImportError:
        print("❌  Pillow не встановлено. Виконайте: pip install Pillow")
        sys.exit(1)

def load_jokes() -> list[str]:
    if not JOKES_FILE.exists():
        print(f"❌  Файл не знайдено: {JOKES_FILE}")
        sys.exit(1)
    jokes = [j.strip() for j in JOKES_FILE.read_text(encoding="utf-8").split("$") if j.strip()]
    if not jokes:
        print("❌  jokes.txt порожній.")
        sys.exit(1)
    return jokes

def pick_random(directory: Path, extensions: set) -> Path:
    if not directory.exists():
        print(f"❌  Папка не знайдена: {directory}")
        sys.exit(1)
    files = [f for f in directory.iterdir() if f.suffix.lower() in extensions]
    if not files:
        print(f"❌  Немає файлів у {directory.name}/")
        sys.exit(1)
    return random.choice(files)

def get_duration(path: Path) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True
    )
    try:
        return float(result.stdout.strip())
    except ValueError:
        return 15.0

def get_font_path() -> str:
    return FONT_PATH if Path(FONT_PATH).exists() else FONT_PATH_FALLBACK

def escape_ffmpeg(text: str) -> str:
    text = text.replace("\\", "\\\\")
    text = text.replace("'",  "\u2019")
    text = text.replace(":",  "\\:")
    text = text.replace("%",  "\\%")
    text = text.replace("[",  "\\[")
    text = text.replace("]",  "\\]")
    return text

# ─── Генерація PNG з заокругленим прямокутником ───────────────────────────────
def create_rounded_box_png(lines: list[str], out_path: str) -> tuple[int, int, int, int]:
    """
    Малює прозорий PNG розміром VIDEO_WIDTH x VIDEO_HEIGHT
    з білим заокругленим прямокутником по центру.
    Повертає (box_x, box_y, box_w, box_h).
    """
    line_height = FONT_SIZE + LINE_SPACING
    box_w = VIDEO_WIDTH - 2 * PADDING_X
    box_h = len(lines) * line_height + 2 * PADDING_Y
    box_x = PADDING_X
    box_y = (VIDEO_HEIGHT - box_h) // 2

    # Прозоре полотно
    img = Image.new("RGBA", (VIDEO_WIDTH, VIDEO_HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Заокруглений прямокутник
    draw.rounded_rectangle(
        [box_x, box_y, box_x + box_w, box_y + box_h],
        radius=CORNER_RADIUS,
        fill=(255, 255, 255, 255)
    )

    img.save(out_path, "PNG")
    return box_x, box_y, box_w, box_h

# ─── Побудова ffmpeg фільтра ───────────────────────────────────────────────────
def build_filter(lines: list[str], box_y: int, overlay_input_idx: int) -> str:
    font_path = get_font_path().replace(":", "\\:")
    line_height = FONT_SIZE + LINE_SPACING

    # Накладаємо PNG overlay
    filters = [
        f"[0:v]scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:"
        f"force_original_aspect_ratio=decrease,"
        f"pad={VIDEO_WIDTH}:{VIDEO_HEIGHT}:(ow-iw)/2:(oh-ih)/2:black[scaled]",
        f"[scaled][{overlay_input_idx}:v]overlay=0:0[boxed]",
    ]

    # Кожен рядок — окремий drawtext
    prev = "boxed"
    for i, line in enumerate(lines):
        escaped = escape_ffmpeg(line)
        y = box_y + PADDING_Y + i * line_height
        curr = f"txt{i}"
        filters.append(
            f"[{prev}]drawtext="
            f"fontfile='{font_path}':"
            f"text='{escaped}':"
            f"fontsize={FONT_SIZE}:"
            f"fontcolor={FONT_COLOR}:"
            f"x=(w-text_w)/2:"
            f"y={y}"
            f"[{curr}]"
        )
        prev = curr

    return filters, prev   # повертаємо список фільтрів і назву останнього виходу

# ─── Головна функція ───────────────────────────────────────────────────────────
def generate_single_joke(joke: str, output_name: str):
    check_ffmpeg()
    check_pillow()
    OUTPUT_DIR.mkdir(exist_ok=True)

    bg_file    = pick_random(BACKGROUNDS_DIR, VIDEO_EXTS)
    music_file = pick_random(MUSIC_DIR, AUDIO_EXTS)

    print(f"🎬  Фон:     {bg_file.name}")
    print(f"🎵  Музика:  {music_file.name}")
    print(f"😂  Анекдот: {joke[:70]}…" if len(joke) > 70 else f"😂  Анекдот: {joke}")

    duration       = get_duration(bg_file)
    music_duration = get_duration(music_file)
    final_duration = min(duration, music_duration)

    out_path = OUTPUT_DIR / output_name

    lines = textwrap.wrap(joke, width=MAX_CHARS_LINE)

    # Генеруємо тимчасовий PNG з заокругленим боксом
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp_png = tmp.name

    box_x, box_y, box_w, box_h = create_rounded_box_png(lines, tmp_png)
    print(f"🖼️   Бокс:    {box_w}x{box_h} px, заокруглення {CORNER_RADIUS}px")

    # overlay_input_idx = 2 (0=відео, 1=музика, 2=PNG)
    filter_list, last_out = build_filter(lines, box_y, overlay_input_idx=2)

    filter_complex = ";".join(filter_list)
    filter_complex += f";[1:a]afade=t=out:st={max(0, final_duration - FADE_DURATION)}:d={FADE_DURATION}[aout]"

    cmd = [
        "ffmpeg", "-y",
        "-i", str(bg_file),           # 0: відео
        "-stream_loop", "-1",
        "-i", str(music_file),         # 1: музика
        "-i", tmp_png,                 # 2: PNG overlay
        "-filter_complex", filter_complex,
        "-map", f"[{last_out}]",
        "-map", "[aout]",
        "-t", str(final_duration),
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        str(out_path),
    ]

    print("\n⚙️   Генерація відео…")
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")

    # Видаляємо тимчасовий файл
    Path(tmp_png).unlink(missing_ok=True)

    if result.returncode != 0:
        print("❌  Помилка ffmpeg:")
        print(result.stderr[-3000:])
        sys.exit(1)

    print(f"\n✅  Готово! Відео збережено: {out_path}")
    return out_path

def generate_all_jokes():
    jokes = load_jokes()
    total = len(jokes)
    print(f"📝  Знайдено анекдотів: {total}")

    generated_paths = []
    for idx, joke in enumerate(jokes, start=1):
        output_name = f"joke_{idx:03d}.mp4"
        print(f"\n--- [{idx}/{total}] Генеруємо {output_name} ---")
        generated_paths.append(generate_single_joke(joke, output_name))

    print(f"\n🎉  Згенеровано відео: {len(generated_paths)}")
    return generated_paths


if __name__ == "__main__":
    generate_all_jokes()