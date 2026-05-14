# 🎬 Joke Video Generator

The program automatically generates joke videos:
random music + random background + joke text = ready mp4 video.

---

```text
joke_video_generator/
├── generate.py
├── jokes.txt
├── music/
├── backgrounds/
└── output/
```
---

## ⚙️ Installation

### 1. Python 3.10+

The script uses only the standard Python library — nothing needs to be installed.

### 2. ffmpeg (required)

Windows:

* Download from https://ffmpeg.org/download.html
* Extract and add the `bin` folder to PATH

macOS:
brew install ffmpeg

Ubuntu/Debian:
sudo apt install ffmpeg

---

## 🚀 Running

# Generates a video with a random name

python generate.py

# Generates a video with a specific name

python generate.py my_video.mp4

The finished video will appear in the `output/` folder.

---

## ✏️ jokes.txt Format

Each joke is a separate block of text.
Jokes are separated by an empty line:

First joke line 1
First joke line 2

Second joke line 1
Second joke line 2

Third joke...

---

## ⚙️ Settings (in generate.py)

| Parameter      | Default    | Description                                  |
| -------------- | ---------- | -------------------------------------------- |
| VIDEO_WIDTH    | 1080       | Video width                                  |
| VIDEO_HEIGHT   | 1920       | Video height (vertical format)               |
| VIDEO_DURATION | 15         | Duration (sec) if the background is an image |
| FONT_SIZE      | 60         | Font size                                    |
| MAX_CHARS_LINE | 30         | Maximum number of characters per line        |
| BOX_COLOR      | black@0.55 | Background behind the text                   |
| FADE_DURATION  | 1.0        | Music fade-out duration                      |

---

## 🎞️ Supported Formats

| Type              | Formats                       |
| ----------------- | ----------------------------- |
| Image backgrounds | jpg, jpeg, png, webp, bmp     |
| Video backgrounds | mp4, mov, avi, mkv, webm      |
| Music             | mp3, wav, ogg, aac, flac, m4a |

---

## 💡 Tips

* The vertical 1080×1920 format is perfect for Instagram Reels, TikTok, and YouTube Shorts
* If the music is shorter than the video — it will be automatically trimmed
* The joke text appears smoothly (fade-in)
* Jokes are randomly selected every time the program is launched
