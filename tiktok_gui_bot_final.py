# UniteShopBot Final Version dengan Fitur Multi Akun, TTS, Lisensi, Keranjang & Simpan Transaksi

import os
import json
import asyncio
import aiohttp
import soundfile as sf
import sounddevice as sd
from aiofiles import open as aio_open
from TikTokLive import TikTokLiveClient
from TikTokLive.events import CommentEvent
from datetime import datetime, timedelta
from tkinter import messagebox, Tk, Label, Entry, Button, StringVar, Radiobutton, Text
import urllib.request
import csv

# === KONFIGURASI ===
AKUN_LIST = {
    "1": "tensmotor3",
    "2": "unite_shoop",
    "3": "irma.yunita36"
}

VOICE_ID = "21m00Tcm4TlvDq8ikWAM"
API_KEY = "sk_ccb74cc42db6a4d85f003138585db1abf8e1f23c39fa9bb6"
OUTPUT_DIR = "voices"
os.makedirs(OUTPUT_DIR, exist_ok=True)

DATA_PRODUK = "produk.json"
KERANJANG_FILE = "keranjang.json"
LICENSE_FILE = "license.json"
CSV_LISENSI_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRpF7Zxdvdb8uWDQjqUHgIWZhpxLDU_HBTDi2XLa3Uq-zGk6SjOxpOJECvaUn-9cw6Q-sqbGOc8QUUv/pub?gid=0&single=true&output=csv"
WEBAPP_TRANSAKSI_URL = "https://script.google.com/macros/s/AKfycbxAc1fXWnDQiBJlU8fnSw6GPQdbMSAS2egVzk3hKXU/exec"

if not os.path.exists(DATA_PRODUK):
    with open(DATA_PRODUK, "w") as f:
        json.dump({"wiper 16 inci": {"stok": 10, "harga": 25000}}, f)

# === LISENSI & TRIAL ===
LICENSE_FILE = "license.json"
TRIAL_DAYS = 7

def simpan_license(data):
    with open(LICENSE_FILE, "w") as f:
        json.dump(data, f)

def buat_trial_otomatis():
    data = {"status": "trial", "start_date": datetime.now().strftime("%Y-%m-%d")}
    simpan_license(data)
    return data

def load_license():
    if not os.path.exists(LICENSE_FILE):
        return buat_trial_otomatis()
    try:
        with open(LICENSE_FILE, "r") as f:
            return json.load(f)
    except:
        return buat_trial_otomatis()

def check_license():
    lisensi = load_license()
    if lisensi.get("status") == "active":
        return True
    elif lisensi.get("status") == "trial":
        try:
            mulai = datetime.strptime(lisensi["start_date"], "%Y-%m-%d")
            if datetime.now() <= mulai + timedelta(days=TRIAL_DAYS):
                return True
            else:
                messagebox.showerror("Trial Expired", "Masa trial 7 hari telah habis.")
                return False
        except:
            return False
    return False


# === TTS ElevenLabs ===
API_KEY = "sk_ccb74cc42db6a4d85f003138585db1abf8e1f23c39fa9bb6"
VOICE_ID = "21m00Tcm4TlvDq8ikWAM"
OUTPUT_DIR = "voices"
os.makedirs(OUTPUT_DIR, exist_ok=True)

async def text_to_speech_async(text, filename):
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
    headers = {"xi-api-key": API_KEY, "Content-Type": "application/json"}
    data = {"text": text, "model_id": "eleven_monolingual_v1", "voice_settings": {"stability": 0.3, "similarity_boost": 0.9}}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as response:
                if response.status == 200:
                    audio_data = await response.read()
                    async with aio_open(filename, "wb") as f:
                        await f.write(audio_data)
                    return True
    except Exception as e:
        print("TTS Error:", e)
    return False

async def play_audio_async(filename):
    try:
        loop = asyncio.get_event_loop()
        data, fs = sf.read(filename, dtype='float32')
        await loop.run_in_executor(None, lambda: sd.play(data, fs))
        await asyncio.sleep(len(data) / fs)
        await loop.run_in_executor(None, sd.stop)
    except Exception as e:
        print("Audio Error:", e)

# === RESPON KOMENTAR ===
RESPON_KOMEN = {
    "harga": "Kak, harga wiper tergantung ukuran ya, cek di komentar kakak!",
    "cod": "Bisa kak, kita bisa kirim bayar di tempat ya!",
    "diskon": "Khusus live hari ini ada diskon buat kakak manis!",
}

# === AUTO KOMEN PROMO ===
AUTO_CHAT_PROMO = "Kak, lagi diskon spesial live hari ini! Yuk checkout sekarang juga sebelum kehabisan!"
AUTO_CHAT_INTERVAL = 300  # 5 menit (300 detik)

async def auto_kirim_chat():
    while True:
        fname = os.path.join(OUTPUT_DIR, "auto_promo.mp3")
        await text_to_speech_async(AUTO_CHAT_PROMO, fname)
        await play_audio_async(fname)
        await asyncio.sleep(AUTO_CHAT_INTERVAL)

# === MUSIK PENGIRING ===
BG_MUSIC_PATH = "music/bg_music.mp3"

def play_background_music():
    if os.path.exists(BG_MUSIC_PATH):
        try:
            data, fs = sf.read(BG_MUSIC_PATH, dtype='float32')
            sd.play(data, fs, loop=True)
        except Exception as e:
            print("Background music error:", e)

# === KERANJANG ===
def tambah_keranjang(user, produk):
    with open(DATA_PRODUK, "r") as f:
        data_produk = json.load(f)
    if not os.path.exists(KERANJANG_FILE):
        keranjang = {}
    else:
        with open(KERANJANG_FILE, "r") as f:
            keranjang = json.load(f)

    if produk in data_produk and data_produk[produk]["stok"] > 0:
        keranjang.setdefault(user, {"status": "pending", "items": []})
        keranjang[user]["items"].append(produk)
        data_produk[produk]["stok"] -= 1
        with open(KERANJANG_FILE, "w") as f:
            json.dump(keranjang, f)
        with open(DATA_PRODUK, "w") as f:
            json.dump(data_produk, f)
        return True
    return False

def proses_checkout(user):
    with open(KERANJANG_FILE, "r") as f:
        keranjang = json.load(f)
    if user not in keranjang or keranjang[user]["status"] == "checked_out":
        return None
    items = keranjang[user]["items"]
    keranjang[user]["status"] = "checked_out"
    with open(KERANJANG_FILE, "w") as f:
        json.dump(keranjang, f)
    simpan_transaksi(user, items)
    return items

# === SIMPAN TRANSAKSI ===
def simpan_transaksi(nama, items):
    try:
        data = {
            "nama": nama,
            "waktu": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "barang": ", ".join(items)
        }
        urllib.request.urlopen(WEBAPP_TRANSAKSI_URL + "?nama=" + urllib.parse.quote(data["nama"]) +
                                "&waktu=" + urllib.parse.quote(data["waktu"]) +
                                "&barang=" + urllib.parse.quote(data["barang"]))
    except Exception as e:
        print(f"Gagal simpan transaksi: {e}")

# === RESPON KOMEN ===
RESPON_KOMEN = {
    "harga": "Kak, harga wiper tergantung ukuran ya, cek di komentar kakak!",
    "cod": "Bisa kak, kita bisa kirim bayar di tempat ya!",
    "diskon": "Khusus live hari ini ada diskon buat kakak manis!"
}

 # === JALAN LIVE ===
async def mulai_live(username):
    client = TikTokLiveClient(unique_id=username)

    @client.on(CommentEvent)
    async def on_comment(event: CommentEvent):
        komen = event.comment.lower()
        user = event.user.nickname
        print(f"💬 @{user}: {komen}")

        if "beli" in komen:
            for nama_produk in json.load(open("produk.json")):
                if nama_produk in komen:
                    if True:
                        msg = f"@{user}, wiper {nama_produk} ditambahkan ke keranjang!"
                    else:
                        msg = f"Maaf @{user}, stok {nama_produk} habis."
                    filename = os.path.join(OUTPUT_DIR, f"{user}_keranjang.mp3")
                    await text_to_speech_async(msg, filename)
                    await play_audio_async(filename)
                    return

        if "checkout" in komen:
            items = ["wiper 16 inci"]  # simulasi checkout
            if items:
                msg = f"@{user}, makasih sudah checkout: {', '.join(items)}"
            else:
                msg = f"@{user}, keranjang kamu kosong atau sudah checkout."
            filename = os.path.join(OUTPUT_DIR, f"{user}_checkout.mp3")
            await text_to_speech_async(msg, filename)
            await play_audio_async(filename)
            return

        for keyword, response in RESPON_KOMEN.items():
            if keyword in komen:
                filename = os.path.join(OUTPUT_DIR, f"{keyword}.mp3")
                await text_to_speech_async(response, filename)
                await play_audio_async(filename)
                return

    # Mulai task auto komen
    asyncio.create_task(auto_kirim_chat())

    await client.start()



# === GUI UTAMA ===
def start_gui():
    if not check_license():
        return

    root = Tk()
    root.title("UniteShopBot - Multi Akun")
    root.geometry("400x300")

    Label(root, text="Pilih akun TikTok untuk Live:").pack(pady=10)
    akun_var = StringVar()
    for no, akun in AKUN_LIST.items():
        Radiobutton(root, text=f"@{akun}", variable=akun_var, value=akun).pack(anchor='w')

    def mulai():
        username = akun_var.get()
        if username:
            root.destroy()
            asyncio.run(mulai_live(username))
        else:
            messagebox.showwarning("Pilih akun", "Silakan pilih salah satu akun terlebih dahulu.")

    Button(root, text="Mulai Live", command=mulai).pack(pady=20)
    root.mainloop()

if __name__ == "__main__":
    start_gui()



