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
    
    # Hızlandırma
    options.page_load_strategy = 'eager'

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(60)
    return driver

# --- ANA İŞLEM ---
trends_list = []
driver = None

try:
    driver = get_driver()
    driver.get("https://trends24.in/turkey/")
    time.sleep(5) # Sayfanın oturması için bekle

    soup = BeautifulSoup(driver.page_source, "html.parser")
    # Trendleri seç
    trend_elements = soup.select(".trend-card__list a")
    
    for t in trend_elements:
        trends_list.append(t.text.strip())

except Exception as e:
    pass # Hata olsa bile sessiz kal

finally:
    if driver:
        driver.quit()

# --- VERİ İŞLEME VE TAGLEME (Memory'de Hızlı İşlem) ---
processed_rows = []
header = ["Trend", "Tag"]

for i, trend in enumerate(trends_list):
    # Kullanıcının özel tag mantığı
    if i < 50: tag = 0
    elif i < 200: tag = 1 # 50-199 arası hepsi 1 (Orijinal koddaki mantık)
    elif i < 250: tag = 2
    elif i < 300: tag = 3
    elif i < 350: tag = 4
    elif i < 400: tag = 5
    elif i < 450: tag = 6
    elif i < 500: tag = 7
    elif i < 600: tag = 8
    elif i < 650: tag = 9
    elif i < 700: tag = 10
    elif i < 750: tag = 11
    elif i < 800: tag = 12
    elif i < 850: tag = 13
    elif i < 900: tag = 14
    elif i < 950: tag = 15
    elif i < 1000: tag = 16
    else: tag = 24
    
    processed_rows.append([trend, tag])

# --- DOSYA KAYIT (STANDART BLOK) ---
current_dir = Path(__file__).resolve().parent

# 1. Ham Dosya
file_path_raw = current_dir / "twitter_trends.csv"
if trends_list:
    with open(file_path_raw, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Trend"])
        for t in trends_list:
            writer.writerow([t])
    print(f"✅ Dosya kaydedildi: {file_path_raw}")

# 2. Taglenmiş Dosya
file_path_tagged = current_dir / "twitter_trends_tagged.csv"
if processed_rows:
    with open(file_path_tagged, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(header)
        writer.writerows(processed_rows)
    print(f"✅ Dosya kaydedildi: {file_path_tagged} (Toplam: {len(processed_rows)})")
else:
    print(f"❌ Veri oluşmadığı için kayıt yapılamadı.")