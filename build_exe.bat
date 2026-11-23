@echo off
setlocal
chcp 65001 >nul
title Build kasir-by-Fiano v4

REM ============================================================
REM  build_exe.bat - Build aplikasi Kasir menjadi file .exe
REM  Nama output : kasir-by-Fiano-v4.exe   (ubah di APP_NAME)
REM  Virtual env : .venv
REM  Cara pakai  : klik dua kali file ini, hasil ada di folder dist\
REM ============================================================

set "APP_NAME=kasir-by-Fiano-v4"
set "VENV_DIR=.venv"
set "ICON=database\icon.ico"

cd /d "%~dp0"

REM --- 1. Buat virtual environment jika belum ada ---
if not exist "%VENV_DIR%\Scripts\python.exe" (
    echo [1/6] Membuat virtual environment %VENV_DIR% ...
    where py >nul 2>nul
    if %errorlevel%==0 (
        py -3 -m venv %VENV_DIR%
    ) else (
        python -m venv %VENV_DIR%
    )
    if errorlevel 1 (
        echo.
        echo [GAGAL] Tidak bisa membuat venv. Pastikan Python 3.10+ sudah terinstall dan ada di PATH.
        goto :error
    )
) else (
    echo [1/6] Virtual environment %VENV_DIR% sudah ada.
)

REM --- 2. Aktifkan venv ---
call "%VENV_DIR%\Scripts\activate.bat"
if errorlevel 1 goto :error

REM --- 3. Install dependensi + PyInstaller ---
echo [2/6] Update pip ...
python -m pip install --upgrade pip
if errorlevel 1 goto :error

if not exist req.txt (
    echo [GAGAL] File req.txt tidak ditemukan di folder ini.
    goto :error
)

echo [3/6] Install dependensi dari req.txt ke %VENV_DIR% ...
python -m pip install -r req.txt
if errorlevel 1 goto :error

echo [4/6] Install PyInstaller ke %VENV_DIR% ...
python -m pip install pyinstaller
if errorlevel 1 goto :error

REM --- 4. Bersihkan hasil build lama ---
echo [5/6] Membersihkan build lama ...
if exist build rmdir /s /q build
if exist dist\%APP_NAME%.exe del /q dist\%APP_NAME%.exe
if exist %APP_NAME%.spec del /q %APP_NAME%.spec

REM --- 5. Build exe ---
echo [6/6] Build %APP_NAME%.exe ...
pyinstaller --noconfirm --clean --onefile --windowed ^
    --name "%APP_NAME%" ^
    --icon "%ICON%" ^
    --add-data "database\icon.ico;database" ^
    main.py
if errorlevel 1 goto :error

REM --- Salin icon di samping exe (aplikasi membaca database\icon.ico secara relatif) ---
if not exist dist\database mkdir dist\database
copy /y "database\icon.ico" "dist\database\icon.ico" >nul

echo.
echo ============================================================
echo  BUILD BERHASIL
echo  File  : dist\%APP_NAME%.exe
echo  Catatan: folder dist\database\ (berisi icon.ico) harus
echo           tetap berada di samping file .exe.
echo           Database ^& folder invoice dibuat otomatis di
echo           folder tempat .exe dijalankan.
echo ============================================================
echo.
call deactivate 2>nul
pause
exit /b 0

:error
echo.
echo ============================================================
echo  BUILD GAGAL - periksa pesan error di atas.
echo ============================================================
pause
exit /b 1
