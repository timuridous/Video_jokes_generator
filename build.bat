@echo off
echo ============================================
echo   Joke Video Generator - Build .exe
echo ============================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Download from https://python.org
    pause
    exit /b 1
)

echo [1/4] Installing dependencies...
pip install pyinstaller pillow
if errorlevel 1 (
    echo ERROR: pip failed
    pause
    exit /b 1
)

echo.
echo [2/4] Checking FFmpeg in bin\...
if not exist "bin\ffmpeg.exe" (
    echo WARNING: bin\ffmpeg.exe not found
    echo Download: https://github.com/BtbN/FFmpeg-Builds/releases
    echo Copy ffmpeg.exe and ffprobe.exe into the bin\ folder
    pause
    exit /b 1
)

echo.
echo [3/4] Building .exe...
if exist "jokes" (
    pyinstaller --onefile --windowed --name "JokeVideoGenerator" --add-data "bin;bin" --add-data "jokes;jokes" --add-data "jokes.txt;." app_gui.py
) else (
    pyinstaller --onefile --windowed --name "JokeVideoGenerator" --add-data "bin;bin" --add-data "jokes.txt;." app_gui.py
)

if errorlevel 1 (
    echo ERROR: PyInstaller failed
    pause
    exit /b 1
)

echo.
echo [4/4] Preparing client folder...
if not exist "dist\client" mkdir "dist\client"
copy /y "dist\JokeVideoGenerator.exe" "dist\client\" >nul
copy /y "jokes.txt" "dist\client\" >nul 2>&1
if not exist "dist\client\bin"         mkdir "dist\client\bin"
if not exist "dist\client\jokes"       mkdir "dist\client\jokes"
if not exist "dist\client\music"       mkdir "dist\client\music"
if not exist "dist\client\backgrounds" mkdir "dist\client\backgrounds"
if not exist "dist\client\output"      mkdir "dist\client\output"
if exist "bin\*"         xcopy /y /q "bin\*"         "dist\client\bin\"         >nul 2>&1
if exist "jokes\*"       xcopy /y /q "jokes\*"       "dist\client\jokes\"       >nul 2>&1
if not exist "dist\client\jokes\default.txt" if exist "jokes.txt" copy /y "jokes.txt" "dist\client\jokes\default.txt" >nul 2>&1
if exist "music\*"       xcopy /y /q "music\*"       "dist\client\music\"       >nul 2>&1
if exist "backgrounds\*" xcopy /y /q "backgrounds\*" "dist\client\backgrounds\" >nul 2>&1

echo.
echo ============================================
echo  DONE! Client folder ready: dist\client\
echo ============================================
pause
