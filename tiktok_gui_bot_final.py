import os
import urllib.request

# Link ke repo GitHub RAW (bukan HTML halaman biasa!)
VERSION_URL = "https://raw.githubusercontent.com/uniteshop/uniteshop-updater/main/version.txt"
EXE_URL = "https://raw.githubusercontent.com/uniteshop/uniteshop-updater/main/tiktok_gui_bot_final.exe"
LOCAL_VERSION_FILE = "version.txt"
EXE_OUTPUT_FILE = "tiktok_gui_bot_final.exe"

def get_online_version():
    with urllib.request.urlopen(VERSION_URL) as response:
        return response.read().decode('utf-8').strip()

def get_local_version():
    if os.path.exists(LOCAL_VERSION_FILE):
        with open(LOCAL_VERSION_FILE, "r") as f:
            return f.read().strip()
    return "0.0.0"

def download_new_exe():
    print("📥 Mengunduh versi baru...")
    urllib.request.urlretrieve(EXE_URL, EXE_OUTPUT_FILE)
    print("✅ Berhasil mengunduh versi baru.")

def main():
    online_version = get_online_version()
    local_version = get_local_version()

    if online_version != local_version:
        print(f"📢 Versi baru tersedia: {online_version} (lama: {local_version})")
        download_new_exe()
        with open(LOCAL_VERSION_FILE, "w", encoding="utf-8") as f:
            f.write(online_version)
    else:
        print("✅ Versi sudah terbaru.")

if __name__ == "__main__":
    main()
