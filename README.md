# 🎬 Generator Filmów z Dowcipami

Program automatycznie generuje filmiki z dowcipami:
losowa muzyka + losowe tło + tekst dowcipu = gotowy film mp4.

---

## 📁 Struktura folderów

joke_video_generator/
│
├── generate.py          ← główny skrypt
├── jokes.txt            ← dowcipy (oddzielane pustą linią)
│
├── music/               ← tutaj wrzucamy pliki audio
│   ├── track1.mp3
│   ├── chill_beat.wav
│   └── ...
│
├── backgrounds/         ← tutaj wrzucamy tła
│   ├── sunset.jpg
│   ├── city.png
│   ├── nature.mp4       ← obsługiwane są również tła wideo!
│   └── ...
│
└── output/              ← tutaj zapisywane są gotowe filmy (tworzy się automatycznie)
    └── joke_1234.mp4

---

## ⚙️ Instalacja

### 1. Python 3.10+
Skrypt używa wyłącznie standardowej biblioteki Python — nic nie trzeba instalować.

### 2. ffmpeg (wymagany)

Windows:
- Pobierz z https://ffmpeg.org/download.html
- Rozpakuj i dodaj folder `bin` do PATH

macOS:
brew install ffmpeg

Ubuntu/Debian:
sudo apt install ffmpeg

---

## 🚀 Uruchamianie

# Generuje film z losową nazwą
python generate.py

# Generuje film z konkretną nazwą
python generate.py my_video.mp4

Gotowy film pojawi się w folderze `output/`.

---

## ✏️ Format jokes.txt

Każdy dowcip to osobny blok tekstu.
Dowcipy są oddzielane pustą linią:

Pierwszy dowcip linia 1
Pierwszy dowcip linia 2

Drugi dowcip linia 1
Drugi dowcip linia 2

Trzeci dowcip...

---

## ⚙️ Ustawienia (w generate.py)

| Parametr | Domyślnie | Opis |
|---|---|---|
| VIDEO_WIDTH | 1080 | Szerokość filmu |
| VIDEO_HEIGHT | 1920 | Wysokość filmu (format pionowy) |
| VIDEO_DURATION | 15 | Czas trwania (sek), jeśli tło jest obrazem |
| FONT_SIZE | 60 | Rozmiar czcionki |
| MAX_CHARS_LINE | 30 | Maksymalna liczba znaków w linii |
| BOX_COLOR | black@0.55 | Tło pod tekstem |
| FADE_DURATION | 1.0 | Czas fade-out muzyki |

---

## 🎞️ Obsługiwane formaty

| Typ | Formaty |
|---|---|
| Tła-obrazki | jpg, jpeg, png, webp, bmp |
| Tła-wideo | mp4, mov, avi, mkv, webm |
| Muzyka | mp3, wav, ogg, aac, flac, m4a |

---

## 💡 Wskazówki

- Format pionowy 1080×1920 idealnie nadaje się do Instagram Reels, TikTok oraz YouTube Shorts
- Jeśli muzyka jest krótsza niż film — zostanie automatycznie przycięta
- Tekst dowcipu pojawia się płynnie (fade-in)
- Dowcipy są wybierane losowo przy każdym uruchomieniu programu