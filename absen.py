import json
import os
import sys
import time
import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import ddddocr

load_dotenv()

NPM        = os.getenv("NPM")
PASSWORD   = os.getenv("PASSWORD")
NTFY_TOPIC = os.getenv("NTFY_TOPIC", "")
BASE_URL   = "https://simkuliah.usk.ac.id"
CACHE_FILE = Path("jadwal_cache.json")
WIB        = ZoneInfo("Asia/Jakarta")

def kirim_notif(tipe: str, judul: str, pesan: str):
    if not NTFY_TOPIC:
        return
    topic_map = {
        "sukses": f"{NTFY_TOPIC}-bisa",
        "info":   f"{NTFY_TOPIC}-info",
        "error":  f"{NTFY_TOPIC}-gagal",
    }
    url = f"ntfy.sh/{topic_map.get(tipe, NTFY_TOPIC)}"
    os.system(f'curl -s -H "Title: {judul}" -d "{pesan}" {url}')

def get_jadwal_hari_ini() -> list[dict]:
    if not CACHE_FILE.exists():
        print("jadwal_cache.json tidak ditemukan — absen akan tetap dicoba.")
        return []

    with open(CACHE_FILE, "r") as f:
        data = json.load(f)

    hari_ini = datetime.datetime.now(WIB).date()
    hasil = []
    for mk in data.get("jadwal", []):
        try:
            tanggal = datetime.date.fromisoformat(mk["tanggal"])
            if tanggal == hari_ini:
                hasil.append(mk)
        except Exception:
            pass
    return hasil

def buat_driver() -> webdriver.Chrome:
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    )
    return webdriver.Chrome(options=options)

def main():
    now = datetime.datetime.now(WIB)
    print(f"Waktu: {now.strftime('%A, %d-%m-%Y %H:%M')} WIB")

    if not NPM or not PASSWORD:
        print("NPM atau PASSWORD tidak ditemukan di environment.")
        sys.exit(1)

    jadwal_hari_ini = get_jadwal_hari_ini()
    if jadwal_hari_ini:
        print(f"Jadwal hari ini ({len(jadwal_hari_ini)} sesi):")
        for mk in jadwal_hari_ini:
            print(f"   - {mk['nama_mk']} | {mk['jam']} | {mk['ruang']}")
    else:
        print("Tidak ada jadwal hari ini di cache — tetap mencoba absen.")

    driver = buat_driver()
    ocr = ddddocr.DdddOcr(show_ad=False)

    try:
        print("\nMemulai login...")
        driver.get(BASE_URL)
        wait = WebDriverWait(driver, 10)

        wait.until(EC.presence_of_element_located((By.NAME, "username"))).send_keys(NPM)
        driver.find_element(By.NAME, "password").send_keys(PASSWORD)

        captcha_img = wait.until(EC.presence_of_element_located((By.ID, "captcha-img")))
        captcha_text = ocr.classification(captcha_img.screenshot_as_png).strip().replace(" ", "")
        print(f"CAPTCHA terbaca: {captcha_text}")

        driver.find_element(By.NAME, "captcha_answer").send_keys(captcha_text)
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[type="submit"]'))).click()
        time.sleep(3)

        if "login" in driver.current_url.lower():
            print("Login gagal! CAPTCHA mungkin salah terbaca.")
            kirim_notif("error", "Absen ERROR", "Login gagal, CAPTCHA salah terbaca.")
            sys.exit(1)

        print("Login berhasil!")

        driver.get(f"{BASE_URL}/index.php/absensi")
        time.sleep(2)

        absen_berhasil = 0
        for i in range(2):
            try:
                absen_btn = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, ".btn.btn-success"))
                )
                driver.execute_script("arguments[0].click();", absen_btn)
                time.sleep(2)

                konfirmasi = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CLASS_NAME, "confirm"))
                )
                driver.execute_script("arguments[0].click();", konfirmasi)
                time.sleep(3)

                absen_berhasil += 1
                print(f"Absen #{absen_berhasil} berhasil!")

            except Exception:
                break

        if absen_berhasil == 0:
            print("Tidak ada tombol absen yang tersedia.")
            kirim_notif("info", "Tidak Ada Jadwal", "Bot berjalan tapi tidak ada tombol absen.")
        else:
            pesan = f"{absen_berhasil} absensi berhasil dilakukan."
            print(f"\n{pesan}")
            kirim_notif("sukses", "Absen Berhasil", pesan)

    except Exception as e:
        print(f"Error: {e}")
        kirim_notif("error", "Absen ERROR", f"Error: {e}")
        sys.exit(1)

    finally:
        driver.quit()


if __name__ == "__main__":
    main()