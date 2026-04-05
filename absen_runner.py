import json
import os
import sys
from datetime import datetime, date
from zoneinfo import ZoneInfo
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

WIB = ZoneInfo("Asia/Jakarta")
CACHE_FILE = Path("jadwal_cache.json")


def load_cache() -> list[dict] | None:
    """Baca jadwal_cache.json dari root repo."""
    if not CACHE_FILE.exists():
        print(" jadwal_cache.json tidak ditemukan.")
        return None
    with open(CACHE_FILE, "r") as f:
        data = json.load(f)
    jadwal = data.get("jadwal", [])
    for mk in jadwal:
        if mk.get("tanggal"):
            try:
                mk["tanggal"] = date.fromisoformat(mk["tanggal"])
            except Exception:
                mk["tanggal"] = None
    return jadwal


def get_jadwal_hari_ini(jadwal: list[dict]) -> list[dict]:
    """Filter jadwal berdasarkan tanggal hari ini."""
    hari_ini = datetime.now(WIB).date()
    return [mk for mk in jadwal if mk.get("tanggal") == hari_ini]


def kirim_notif_bisa(judul: str, pesan: str, topic: str):
    if not topic:
        return
    os.system(f'curl -s -H "Title: {judul}" -d "{pesan}" ntfy.sh/{topic}')

def kirim_notif_info(judul: str, pesan: str, topic: str):
    if not topic:
        return
    os.system(f'curl -s -H "Title: {judul}" -d "{pesan}" ntfy.sh/{topic}')

def kirim_notif_gagal(judul: str, pesan: str, topic: str):
    if not topic:
        return
    os.system(f'curl -s -H "Title: {judul}" -d "{pesan}" ntfy.sh/{topic}')


def main():
    print(f" Waktu sekarang: {datetime.now(WIB).strftime('%A, %d-%m-%Y %H:%M')} WIB")

    npm = os.getenv("NPM")
    password = os.getenv("PASSWORD")
    ntfy_topic = os.getenv("NTFY_TOPIC", "")

    if not npm or not password:
        print(" NPM atau PASSWORD tidak ditemukan di environment.")
        sys.exit(1)

    jadwal = load_cache()
    if not jadwal:
        kirim_notif_gagal("Absen ERROR", "jadwal_cache.json tidak ditemukan.", ntfy_topic)
        sys.exit(1)

    jadwal_hari_ini = get_jadwal_hari_ini(jadwal)
    if not jadwal_hari_ini:
        print("  Tidak ada jadwal kuliah hari ini. Skip.")
        kirim_notif_info("Tidak Ada Jadwal", "Bot berjalan, tidak ada MK hari ini.", ntfy_topic)
        sys.exit(0)

    print(f" Jadwal hari ini ({len(jadwal_hari_ini)} sesi):")
    for mk in jadwal_hari_ini:
        print(f"   - {mk['nama_mk']} | {mk['jam']} | {mk['ruang']}")

    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    import ddddocr
    import time

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

    driver = webdriver.Chrome(options=options)
    ocr = ddddocr.DdddOcr(show_ad=False)

    BASE_URL = "https://simkuliah.usk.ac.id"

    try:
        print("\n Memulai login...")
        driver.get(BASE_URL)
        wait = WebDriverWait(driver, 10)

        wait.until(EC.presence_of_element_located((By.NAME, "username"))).send_keys(npm)
        driver.find_element(By.NAME, "password").send_keys(password)

        captcha_img = wait.until(EC.presence_of_element_located((By.ID, "captcha-img")))
        captcha_text = ocr.classification(captcha_img.screenshot_as_png).strip().replace(" ", "")
        print(f" CAPTCHA terbaca: {captcha_text}")

        driver.find_element(By.NAME, "captcha_answer").send_keys(captcha_text)
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[type="submit"]'))).click()
        time.sleep(3)

        if "login" in driver.current_url.lower():
            print(" Login gagal! CAPTCHA mungkin salah terbaca.")
            kirim_notif_gagal("Absen ERROR", "Login gagal, CAPTCHA salah terbaca.", ntfy_topic)
            sys.exit(1)

        print(" Login berhasil!")

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
                print(f" Absen {absen_berhasil} berhasil!")

            except Exception:
                break

        if absen_berhasil == 0:
            print("  Tidak ada tombol absen yang tersedia.")
            kirim_notif_info("Tidak Ada Tombol Absen", "Bot login berhasil tapi tidak ada tombol absen.", ntfy_topic)
        else:
            pesan = f"{absen_berhasil} absensi berhasil dilakukan."
            print(f"\n {pesan}")
            kirim_notif_bisa("Absen Berhasil", pesan, ntfy_topic)

    except Exception as e:
        print(f" Error: {e}")
        kirim_notif_gagal("Absen ERROR", f"Error: {e}", ntfy_topic)
        sys.exit(1)

    finally:
        driver.quit()


if __name__ == "__main__":
    main()