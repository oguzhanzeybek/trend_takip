from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
import csv
from pathlib import Path

# --- AYARLAR ---
def get_driver():
    options = Options()
    # --- KRİTİK GITHUB ACTIONS AYARLARI ---
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-notifications")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(60)
    return driver

# --- ANA İŞLEM ---
channels = []
keywords = []
driver = None

try:
    driver = get_driver()
    driver.get("https://youtube.trends24.in/turkey")
    time.sleep(5)  # Sayfanın yüklenmesi için bekle

    soup = BeautifulSoup(driver.page_source, "html.parser")

    # 1) Trending Channels (Kanallar)
    channels = [span.text.strip() for span in soup.select("span.title")]

    # 2) Popular Keywords (Anahtar Kelimeler)
    keywords = [li.text.strip() for li in soup.select("ol.keywords-list li")]

except Exception as e:
    pass # Hata olsa bile devam et

finally:
    if driver:
        driver.quit()

# --- VERİ HAZIRLAMA (Memory) ---
# 1. Dosya için veri (Hepsi tek sütun)
all_raw_data = channels + keywords

# 2. Dosya için veri (Video ve Tag ayrımı)
tagged_rows = []
# Kanalları 'video' sütununa, Tagleri boş geç
for c in channels:
    tagged_rows.append([c, ""])
# Kelimeleri 'tag' sütununa, videoyu boş geç
for k in keywords:
    tagged_rows.append(["", k])


# --- DOSYA KAYIT (STANDART BLOK) ---
current_dir = Path(__file__).resolve().parent

# DOSYA 1: youtube_trends.csv (Ham Liste)
file_path_raw = current_dir / "youtube_trends.csv"
if all_raw_data:
    with open(file_path_raw, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Channels / Keywords"])
        for item in all_raw_data:
            writer.writerow([item])
    print(f"✅ Dosya kaydedildi: {file_path_raw}")

# DOSYA 2: youtube_trends_tag.csv (Ayrıştırılmış)
file_path_tag = current_dir / "youtube_trends_tag.csv"
if tagged_rows:
    with open(file_path_tag, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["video", "tag"]) # Başlık
        writer.writerows(tagged_rows)
    print(f"✅ Dosya kaydedildi: {file_path_tag}")

if not all_raw_data and not tagged_rows:
    print(f"❌ Veri oluşmadığı için kayıt yapılamadı.")