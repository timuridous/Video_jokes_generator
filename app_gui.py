#!/usr/bin/env python3
import sys
import threading
import random
import textwrap
import subprocess
import tempfile
import traceback
import shutil
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext

if getattr(sys, "frozen", False):
    APP_DIR = Path(sys.executable).parent
    BUNDLE_DIR = Path(getattr(sys, "_MEIPASS", APP_DIR))
else:
    APP_DIR = Path(__file__).parent
    BUNDLE_DIR = APP_DIR

def resolve_existing_path(*parts):
    app_path = APP_DIR.joinpath(*parts)
    if app_path.exists():
        return app_path
    return BUNDLE_DIR.joinpath(*parts)

MUSIC_DIR       = resolve_existing_path("music")
BACKGROUNDS_DIR = resolve_existing_path("backgrounds")
DEFAULT_JOKES_DIR = resolve_existing_path("jokes")
LEGACY_JOKES_FILE = resolve_existing_path("jokes.txt")
OUTPUT_DIR      = APP_DIR / "output"

VIDEO_WIDTH    = 1080
VIDEO_HEIGHT   = 1920
FONT_SIZE      = 70
FONT_COLOR     = "black"
MAX_CHARS_LINE = 20
FADE_DURATION  = 1.0
LINE_SPACING   = 20
PADDING_X      = 60
PADDING_Y      = 55
CORNER_RADIUS  = 60

VIDEO_EXTS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
AUDIO_EXTS = {".mp3", ".wav", ".ogg", ".aac", ".flac", ".m4a"}
_FF_TOOL_CACHE = {}

def load_jokes_from_folder(jokes_dir):
    jokes = []
    txt_files = sorted([p for p in jokes_dir.glob("*.txt") if p.is_file()])
    for txt_file in txt_files:
        raw = txt_file.read_text(encoding="utf-8-sig", errors="replace")
        parts = [j.strip() for j in raw.split("$") if j.strip()]
        if parts:
            jokes.extend(parts)
    return jokes, txt_files

def get_ffmpeg_path(tool="ffmpeg"):
    if tool in _FF_TOOL_CACHE:
        return _FF_TOOL_CACHE[tool]

    tool_name = tool + ".exe"
    candidates = [
        APP_DIR / "bin" / tool_name,
        BUNDLE_DIR / "bin" / tool_name,
    ]
    path_tool = shutil.which(tool) or tool

    def _is_working(executable):
        try:
            result = subprocess.run(
                [str(executable), "-version"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            return result.returncode == 0
        except Exception:
            return False

    for candidate in candidates:
        if candidate.exists() and _is_working(candidate):
            _FF_TOOL_CACHE[tool] = str(candidate)
            return _FF_TOOL_CACHE[tool]

    if _is_working(path_tool):
        _FF_TOOL_CACHE[tool] = str(path_tool)
        return _FF_TOOL_CACHE[tool]

    # Let subprocess raise a meaningful error later if nothing is available.
    _FF_TOOL_CACHE[tool] = tool
    return _FF_TOOL_CACHE[tool]

def pick_random(directory, extensions):
    files = [f for f in directory.iterdir() if f.suffix.lower() in extensions]
    if not files:
        raise FileNotFoundError("No files in " + str(directory))
    return random.choice(files)

def get_duration(path):
    result = subprocess.run(
        [get_ffmpeg_path("ffprobe"), "-v", "error",
         "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True
    )
    try:
        return float(result.stdout.strip())
    except ValueError:
        return 15.0

def get_font_path():
    for p in [
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/arial.ttf",
    ]:
        if Path(p).exists():
            return p
    return ""

def escape_ffmpeg(text):
    text = text.replace("\\", "\\\\")
    text = text.replace("'",  "\u2019")
    text = text.replace(":",  "\\:")
    text = text.replace("%",  "\\%")
    text = text.replace("[",  "\\[")
    text = text.replace("]",  "\\]")
    return text

def create_rounded_box_png(lines, out_path):
    from PIL import Image, ImageDraw
    line_height = FONT_SIZE + LINE_SPACING
    box_w = VIDEO_WIDTH - 2 * PADDING_X
    box_h = len(lines) * line_height + 2 * PADDING_Y
    box_x = PADDING_X
    box_y = (VIDEO_HEIGHT - box_h) // 2
    img = Image.new("RGBA", (VIDEO_WIDTH, VIDEO_HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle(
        [box_x, box_y, box_x + box_w, box_y + box_h],
        radius=CORNER_RADIUS,
        fill=(255, 255, 255, 255)
    )
    img.save(out_path, "PNG")
    return box_x, box_y, box_w, box_h

def build_filter(lines, box_y, overlay_input_idx):
    font_path = get_font_path().replace("\\", "/").replace(":", "\\:")
    line_height = FONT_SIZE + LINE_SPACING
    filters = [
        "[0:v]scale=%d:%d:force_original_aspect_ratio=decrease,pad=%d:%d:(ow-iw)/2:(oh-ih)/2:black[scaled]" % (VIDEO_WIDTH, VIDEO_HEIGHT, VIDEO_WIDTH, VIDEO_HEIGHT),
        "[scaled][%d:v]overlay=0:0[boxed]" % overlay_input_idx,
    ]
    prev = "boxed"
    for i, line in enumerate(lines):
        escaped = escape_ffmpeg(line)
        y = box_y + PADDING_Y + i * line_height
        curr = "txt%d" % i
        filters.append(
            "[%s]drawtext=fontfile='%s':text='%s':fontsize=%d:fontcolor=%s:x=(w-text_w)/2:y=%d[%s]"
            % (prev, font_path, escaped, FONT_SIZE, FONT_COLOR, y, curr)
        )
        prev = curr
    return filters, prev

def generate_video(joke, output_name, log_fn, progress_fn):
    global OUTPUT_DIR
    OUTPUT_DIR.mkdir(exist_ok=True)
    bg_file    = pick_random(BACKGROUNDS_DIR, VIDEO_EXTS)
    music_file = pick_random(MUSIC_DIR, AUDIO_EXTS)
    log_fn("BG: " + bg_file.name)
    log_fn("Music: " + music_file.name)
    log_fn("Joke: " + joke[:70])

    duration       = get_duration(bg_file)
    music_duration = get_duration(music_file)
    final_duration = min(duration, music_duration)

    lines = textwrap.wrap(joke, width=MAX_CHARS_LINE)

    tmp_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    tmp_png  = tmp_file.name
    tmp_file.close()

    box_x, box_y, box_w, box_h = create_rounded_box_png(lines, tmp_png)

    filter_list, last_out = build_filter(lines, box_y, overlay_input_idx=2)
    filter_complex = ";".join(filter_list)
    filter_complex += ";[1:a]afade=t=out:st=%f:d=%f[aout]" % (max(0, final_duration - FADE_DURATION), FADE_DURATION)

    out_path = OUTPUT_DIR / output_name
    cmd = [
        get_ffmpeg_path("ffmpeg"), "-y",
        "-i", str(bg_file),
        "-stream_loop", "-1",
        "-i", str(music_file),
        "-i", tmp_png,
        "-filter_complex", filter_complex,
        "-map", "[%s]" % last_out,
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

    log_fn("Generating video...")
    progress_fn(50)
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    Path(tmp_png).unlink(missing_ok=True)

    if result.returncode != 0:
        err_tail = (result.stderr or "").strip()[-3000:]
        out_tail = (result.stdout or "").strip()[-2000:]
        details = err_tail or out_tail or "ffmpeg failed without stderr/stdout output."
        raise RuntimeError("ffmpeg failed for output '%s'.\n%s" % (output_name, details))

    progress_fn(100)
    log_fn("Done! Saved: " + str(out_path))
    return out_path


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Joke Video Generator")
        self.resizable(False, False)
        self.configure(bg="#1a1a2e")
        self._jokes = []
        self._jokes_dir = DEFAULT_JOKES_DIR if DEFAULT_JOKES_DIR.exists() else APP_DIR
        self._build_ui()
        self._load_jokes()

    def _build_ui(self):
        BG   = "#1a1a2e"
        CARD = "#16213e"
        ACC  = "#e94560"
        FG   = "#eaeaea"
        FG2  = "#a0a0b0"

        # --- Header ---
        hdr = tk.Frame(self, bg=ACC)
        hdr.pack(fill="x")
        tk.Label(hdr, text="Joke Video Generator",
                 bg=ACC, fg="white",
                 font=("Segoe UI", 15, "bold"),
                 pady=12).pack()

        # --- Card ---
        card = tk.Frame(self, bg=CARD)
        card.pack(fill="both", expand=True, padx=12, pady=12)

        tk.Label(card, text="Mode", bg=CARD, fg=FG2,
                 font=("Segoe UI", 9)).grid(row=0, column=0, sticky="w", padx=12, pady=4)

        self.mode_var = tk.StringVar(value="Random joke")
        mode_cb = ttk.Combobox(card, textvariable=self.mode_var, state="readonly", width=38,
                               values=["Random joke",
                                       "Choose from list",
                                       "All jokes from folder"])
        mode_cb.grid(row=1, column=0, columnspan=2, sticky="ew", padx=12, pady=4)
        mode_cb.bind("<<ComboboxSelected>>", self._on_mode_change)

        self._lbl_pick = tk.Label(card, text="Choose joke", bg=CARD, fg=FG2, font=("Segoe UI", 9))
        self._lbl_pick.grid(row=2, column=0, sticky="w", padx=12, pady=4)
        self._lbl_pick.grid_remove()

        self.joke_var = tk.StringVar()
        self.joke_cb  = ttk.Combobox(card, textvariable=self.joke_var, state="readonly", width=38)
        self.joke_cb.grid(row=3, column=0, columnspan=2, sticky="ew", padx=12, pady=4)
        self.joke_cb.grid_remove()

        tk.Label(card, text="Jokes folder (.txt)", bg=CARD, fg=FG2,
                 font=("Segoe UI", 9)).grid(row=4, column=0, sticky="w", padx=12, pady=4)

        self.jokes_dir_var = tk.StringVar(value=str(self._jokes_dir))
        self.jokes_dir_entry = tk.Entry(card, textvariable=self.jokes_dir_var, width=30,
                                        bg="#0f3460", fg=FG, insertbackground=FG,
                                        relief="flat", font=("Segoe UI", 10))
        self.jokes_dir_entry.grid(row=5, column=0, sticky="ew", padx=12, pady=4)
        self.jokes_dir_entry.configure(state="readonly")

        ttk.Button(card, text="Browse", command=self._pick_jokes_dir)\
            .grid(row=5, column=1, padx=4, pady=4)

        tk.Label(card, text="Output filename (.mp4)", bg=CARD, fg=FG2,
                 font=("Segoe UI", 9)).grid(row=6, column=0, sticky="w", padx=12, pady=4)

        self.out_var = tk.StringVar(value="joke_001.mp4")
        self.out_entry = tk.Entry(card, textvariable=self.out_var, width=30,
                                  bg="#0f3460", fg=FG, insertbackground=FG,
                                  relief="flat", font=("Segoe UI", 10))
        self.out_entry.grid(row=7, column=0, sticky="ew", padx=12, pady=4)

        ttk.Button(card, text="Folder", command=self._pick_output_dir)\
            .grid(row=7, column=1, padx=4, pady=4)

        self.progress = ttk.Progressbar(card, mode="determinate")
        self.progress.grid(row=8, column=0, columnspan=2, sticky="ew", padx=12, pady=8)

        self.btn_gen = ttk.Button(card, text="Generate video", command=self._on_generate)
        self.btn_gen.grid(row=9, column=0, columnspan=2, sticky="ew", padx=12, pady=4)

        card.columnconfigure(0, weight=1)

        # --- Log ---
        log_frame = tk.Frame(self, bg=BG)
        log_frame.pack(fill="both", expand=True, padx=12, pady=6)

        tk.Label(log_frame, text="Log", bg=BG, fg=FG2,
                 font=("Segoe UI", 9)).pack(anchor="w")

        self.log_box = scrolledtext.ScrolledText(
            log_frame, height=10, width=54, wrap="word",
            bg="#0d0d1a", fg="#00ff88", insertbackground="#00ff88",
            font=("Consolas", 9), relief="flat", state="disabled"
        )
        self.log_box.pack(fill="both", expand=True)

        self.status_var = tk.StringVar(value="Ready")
        tk.Label(self, textvariable=self.status_var,
                 bg="#0d0d1a", fg=FG2,
                 font=("Segoe UI", 8), anchor="w", padx=8)\
            .pack(fill="x", side="bottom")

        self.geometry("520x680")

    def _load_jokes(self):
        self._jokes = []
        jokes_dir = self._jokes_dir
        if jokes_dir.exists() and jokes_dir.is_dir():
            self._jokes, txt_files = load_jokes_from_folder(jokes_dir)
        else:
            txt_files = []

        if not self._jokes and LEGACY_JOKES_FILE.exists():
            raw = LEGACY_JOKES_FILE.read_text(encoding="utf-8")
            self._jokes = [j.strip() for j in raw.split("$") if j.strip()]
            self._log("Using legacy jokes file: " + str(LEGACY_JOKES_FILE))

        short = [j[:60].replace("\n", " ") + ("..." if len(j) > 60 else "") for j in self._jokes]
        self.joke_cb["values"] = short
        if short:
            self.joke_cb.current(0)
            self._log("Loaded jokes: %d from %d file(s)" % (len(self._jokes), len(txt_files)))
        else:
            self._log("No jokes found. Choose a folder with .txt files.")

    def _on_mode_change(self, _=None):
        mode = self.mode_var.get()
        for w in [self.joke_cb, self._lbl_pick]:
            w.grid_remove()
        if mode == "Choose from list":
            self._lbl_pick.grid()
            self.joke_cb.grid()
        self.out_entry.configure(state="disabled" if mode == "All jokes from folder" else "normal")

    def _pick_jokes_dir(self):
        d = filedialog.askdirectory(title="Choose folder with jokes .txt files")
        if not d:
            return
        self._jokes_dir = Path(d)
        self.jokes_dir_var.set(str(self._jokes_dir))
        self._log("Jokes folder: " + str(self._jokes_dir))
        self._load_jokes()

    def _pick_output_dir(self):
        global OUTPUT_DIR
        d = filedialog.askdirectory(title="Choose output folder")
        if d:
            OUTPUT_DIR = Path(d)
            self._log("Output folder: " + str(OUTPUT_DIR))

    def _log(self, msg):
        if threading.current_thread() is not threading.main_thread():
            self.after(0, self._log, msg)
            return
        self.log_box.configure(state="normal")
        self.log_box.insert("end", msg + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def _set_progress(self, val):
        if threading.current_thread() is not threading.main_thread():
            self.after(0, self._set_progress, val)
            return
        self.progress["value"] = val
        self.update_idletasks()

    def _set_status(self, text):
        if threading.current_thread() is not threading.main_thread():
            self.after(0, self._set_status, text)
            return
        self.status_var.set(text)

    def _set_generate_enabled(self, enabled):
        if threading.current_thread() is not threading.main_thread():
            self.after(0, self._set_generate_enabled, enabled)
            return
        self.btn_gen.configure(state="normal" if enabled else "disabled")

    def _on_generate(self):
        self._set_generate_enabled(False)
        self.progress["value"] = 0
        self._set_status("Generating...")

        mode = self.mode_var.get()

        for d, name in [(MUSIC_DIR, "music"), (BACKGROUNDS_DIR, "backgrounds")]:
            if not d.exists():
                messagebox.showerror("Error", "Folder not found: " + name)
                self._set_generate_enabled(True)
                return

        def _run():
            try:
                if mode == "All jokes from folder":
                    if not self._jokes:
                        self._log("ERROR: jokes folder is empty or missing .txt files")
                        return
                    total = len(self._jokes)
                    for i, joke in enumerate(self._jokes, 1):
                        self._log("\n--- [%d/%d] ---" % (i, total))
                        generate_video(joke, "joke_%03d.mp4" % i,
                                       self._log,
                                       lambda v, i=i: self._set_progress(int((i - 1 + v / 100) / total * 100)))
                    self._set_progress(100)
                else:
                    if mode == "Random joke":
                        if not self._jokes:
                            self._log("ERROR: jokes folder is empty or missing .txt files")
                            return
                        joke = random.choice(self._jokes)
                    elif mode == "Choose from list":
                        idx = self.joke_cb.current()
                        if idx < 0:
                            self._log("ERROR: no joke selected")
                            return
                        joke = self._jokes[idx]
                    else:
                        self._log("ERROR: unknown mode selected")
                        return

                    out_name = self.out_var.get().strip() or "output.mp4"
                    if not out_name.endswith(".mp4"):
                        out_name += ".mp4"
                    generate_video(joke, out_name, self._log, self._set_progress)

                self._set_status("Done!")
            except Exception as e:
                self._log("ERROR: " + (str(e) or e.__class__.__name__))
                self._log(traceback.format_exc())
                self._set_status("Error")
            finally:
                self._set_generate_enabled(True)

        threading.Thread(target=_run, daemon=True).start()


if __name__ == "__main__":
    app = App()
    app.mainloop()
