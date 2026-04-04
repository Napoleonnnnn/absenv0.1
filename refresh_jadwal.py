
import json
import os
import re
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
from selenium.common.exceptions import NoSuchElementException
import ddddocr

load_dotenv()

NPM      = os.getenv("NPM")
PASSWORD = os.getenv("PASSWORD")
BASE_URL = "https://simkuliah.usk.ac.id"
CACHE_FILE = Path("jadwal_cache.json")
WIB = ZoneInfo("Asia/Jakarta")


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


def login(driver: webdriver.Chrome, ocr: ddddocr.DdddOcr) -> bool:
    """Login ke SimKuliah. Return True kalau berhasil."""
    print("Membuka SimKuliah...")
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
        return False

    print("Login berhasil!")
    return True


def parse_sel(sel_text: str, kode_mk: str, nama_mk: str, nomor: int) -> dict | None:
    """Parse teks satu sel pertemuan dari tabel jadwal."""
    if not sel_text.strip():
        return None

    hasil = {
        "pertemuan": nomor,
        "kode_mk": kode_mk,
        "nama_mk": nama_mk,
        "dosen": "-",
        "tanggal_str": "-",
        "tanggal": None,
        "hari": "-",
        "ruang": "-",
        "jam": "-",
    }

    match = re.search(r"Nama\s*:\s*(.+)", sel_text)
    if match:
        hasil["dosen"] = match.group(1).strip()

    match = re.search(r"Hari, tanggal\s*:\s*(\w+),\s*(\d{2}-\d{2}-\d{4})", sel_text)
    if match:
        hasil["hari"] = match.group(1).strip()
        hasil["tanggal_str"] = match.group(2).strip()
        try:
            hasil["tanggal"] = datetime.datetime.strptime(
                hasil["tanggal_str"], "%d-%m-%Y"
            ).date().isoformat()
        except ValueError:
            pass

    match = re.search(r"Ruang\s*:\s*(.+)", sel_text)
    if match:
        hasil["ruang"] = match.group(1).strip()

    match = re.search(r"Jam\s*:\s*([\d.]+ - [\d.]+)", sel_text)
    if match:
        hasil["jam"] = match.group(1).strip()

    return hasil


def scrape_jadwal(driver: webdriver.Chrome) -> list[dict]:
    """Scrape seluruh tabel jadwal semester."""
    print("Mengambil jadwal...")
    driver.get(f"{BASE_URL}/index.php/jadwal_kuliah/index")
    time.sleep(3)

    hasil = []

    try:
        rows = driver.find_elements(By.CSS_SELECTOR, "#simpletable tbody tr")
        print(f"Ditemukan {len(rows)} mata kuliah.")

        for row in rows:
            cols = row.find_elements(By.TAG_NAME, "td")
            if len(cols) < 3:
                continue

            kode_mk = cols[0].text.strip()
            nama_mk = cols[1].text.strip().split("\n")[0].strip()

            for i, sel in enumerate(cols[2:18], start=1):
                record = parse_sel(sel.text.strip(), kode_mk, nama_mk, i)
                if record:
                    hasil.append(record)

    except NoSuchElementException:
        print("Tabel jadwal tidak ditemukan.")

    return hasil


def simpan_cache(jadwal: list[dict]):
    data = {
        "scraped_at": datetime.datetime.now(WIB).isoformat(),
        "jadwal": jadwal,
    }
    with open(CACHE_FILE, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Cache disimpan ke {CACHE_FILE} ({len(jadwal)} pertemuan).")



def main():
    print(f"Waktu: {datetime.datetime.now(WIB).strftime('%A, %d-%m-%Y %H:%M')} WIB")

    if not NPM or not PASSWORD:
        print("NPM atau PASSWORD tidak ditemukan di environment.")
        sys.exit(1)

    driver = buat_driver()
    ocr = ddddocr.DdddOcr(show_ad=False)

    try:
        berhasil = login(driver, ocr)
        if not berhasil:
            sys.exit(1)

        jadwal = scrape_jadwal(driver)

        if not jadwal:
            print("Tidak ada data jadwal yang berhasil di-scrape.")
            sys.exit(1)

        simpan_cache(jadwal)
        print("Refresh jadwal selesai.")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

    finally:
        driver.quit()


if __name__ == "__main__":
    main()