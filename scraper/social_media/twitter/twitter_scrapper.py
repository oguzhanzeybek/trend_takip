import sys
import time
import csv
import os
from pathlib import Path
from bs4 import BeautifulSoup

CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parent.parent 
sys.path.append(str(ROOT_DIR))

try:
    from core.driver_manager import get_chrome_driver
except ImportError:
    sys.path.append(str(ROOT_DIR.parent))
    from scraper.core.driver_manager import get_chrome_driver

BASE_DIR = CURRENT_DIR

def scrape_twitter_trends():
    print("🚀 Twitter Trend Scraper (Trends24.in) Başlatılıyor...")
    
    trends_list = []
    driver = None

    try:
        driver = get_chrome_driver()
        
        url = "https://trends24.in/turkey/"
        print(f"🌐 Gidiliyor: {url}")
        driver.get(url)
        time.sleep(5) 

        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        trend_elements = soup.select(".trend-card__list a")
        
        for t in trend_elements:
            trends_list.append(t.text.strip())
        
        print(f"✅ Sayfadan {len(trends_list)} trend çekildi.")

    except Exception as e:
        print(f"❌ Genel Hata: {e}")

    finally:
        if driver:
            driver.quit()
            print("🛑 Tarayıcı kapatıldı.")

    processed_rows = []
    # Header'a 'Rank' ekledik
    header = ["Rank", "Trend", "Tag"] 

    for i, trend in enumerate(trends_list):
        # Tag mantığın aynen duruyor
        if i < 50: tag = 0
        elif i < 200: tag = 1 
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
        
        # En başa sıra numarasını (i+1) ekledik
        processed_rows.append([i+1, trend, tag])

    if trends_list:
        file_path_raw = BASE_DIR / "twitter_trends.csv"
        try:
            with open(file_path_raw, "w", newline="", encoding="utf-8-sig") as file:
                writer = csv.writer(file)
                # Header'a 'Rank' ekledik
                writer.writerow(["Rank", "Trend"])
                # Döngüde sıra numarası vererek yazıyoruz
                for i, t in enumerate(trends_list, 1):
                    writer.writerow([i, t])
            print(f"✅ Ham Dosya kaydedildi: {file_path_raw}")
        except Exception as e:
            print(f"❌ Ham Dosya yazma hatası: {e}")

    if processed_rows:
        file_path_tagged = BASE_DIR / "twitter_trends_tagged.csv"
        try:
            with open(file_path_tagged, "w", newline="", encoding="utf-8-sig") as file:
                writer = csv.writer(file)
                writer.writerow(header) # Güncel header
                writer.writerows(processed_rows) # Güncel satırlar
            print(f"✅ Taglenmiş Dosya kaydedildi: {file_path_tagged} (Toplam: {len(processed_rows)})")
        except Exception as e:
            print(f"❌ Taglenmiş Dosya yazma hatası: {e}")
    else:
        print(f"❌ Veri oluşmadığı için kayıt yapılamadı.")

if __name__ == "__main__":
    scrape_twitter_trends()