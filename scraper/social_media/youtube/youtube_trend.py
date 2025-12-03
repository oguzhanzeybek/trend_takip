import sys
import time
import csv
from pathlib import Path
from bs4 import BeautifulSoup
import os # sys.path için gerekli

# --- 1. YOL AYARLARI ---
# Dosya Konumu: scraper/social_media/youtube/youtube_trend.py
CURRENT_DIR = Path(__file__).resolve().parent
# Scraper kök dizinine çık (youtube -> social_media -> scraper)
ROOT_DIR = CURRENT_DIR.parent.parent 
sys.path.append(str(ROOT_DIR))

# --- 2. MERKEZİ DRIVER ÇAĞRISI ---
try:
    from core.driver_manager import get_chrome_driver
except ImportError:
    # Yedek yol denemesi (Proje Root)
    sys.path.append(str(ROOT_DIR.parent))
    from scraper.core.driver_manager import get_chrome_driver

BASE_DIR = CURRENT_DIR

def scrape_youtube_trends():
    print("🚀 YouTube Trend Scraper Başlatılıyor...")
    
    channels = []
    keywords = []
    driver = None

    try:
        # Merkezi driver'ı başlat
        driver = get_chrome_driver()
        
        url = "https://youtube.trends24.in/turkey"
        print(f"🌐 Gidiliyor: {url}")
        driver.get(url)
        time.sleep(5) # Sayfanın yüklenmesi için bekle

        # BeautifulSoup ile hızlı çekim
        soup = BeautifulSoup(driver.page_source, "html.parser")

        # 1) Trending Channels (Kanallar)
        channels = [span.text.strip() for span in soup.select("span.title")]
        print(f"  ✅ {len(channels)} trend kanal bulundu.")

        # 2) Popular Keywords (Anahtar Kelimeler)
        keywords = [li.text.strip() for li in soup.select("ol.keywords-list li")]
        print(f"  ✅ {len(keywords)} popüler anahtar kelime bulundu.")

    except Exception as e:
        print(f"❌ Genel Hata: {e}")

    finally:
        if driver:
            driver.quit()
            print("🛑 Tarayıcı kapatıldı.")

    # -----------------------------------------------
    ## 📝 Veri Hazırlama ve Etiketleme
    # -----------------------------------------------
    
    # 1. Ham Dosya için veri
    all_raw_data = channels + keywords

    # 2. Ayrıştırılmış Dosya için veri
    tagged_rows = []
    
    # Kanallar (video sütununda)
    for c in channels:
        tagged_rows.append([c, ""])
        
    # Kelimeler (tag sütununda)
    for k in keywords:
        tagged_rows.append(["", k])


    # -----------------------------------------------
    ## 💾 Dosya Kayıt
    # -----------------------------------------------
    
    # DOSYA 1: youtube_trends.csv (Ham Liste)
    file_path_raw = BASE_DIR / "youtube_trends.csv"
    if all_raw_data:
        try:
            with open(file_path_raw, "w", newline="", encoding="utf-8-sig") as file:
                writer = csv.writer(file)
                writer.writerow(["Channels / Keywords"])
                writer.writerows([[item] for item in all_raw_data])
            print(f"✅ Dosya kaydedildi: {file_path_raw}")
        except Exception as e:
            print(f"❌ Ham Dosya yazma hatası: {e}")

    # DOSYA 2: youtube_trends_tag.csv (Ayrıştırılmış)
    file_path_tag = BASE_DIR / "youtube_trends_tag.csv"
    if tagged_rows:
        try:
            with open(file_path_tag, "w", newline="", encoding="utf-8-sig") as file:
                writer = csv.writer(file)
                writer.writerow(["video", "tag"]) 
                writer.writerows(tagged_rows)
            print(f"✅ Dosya kaydedildi: {file_path_tag}")
        except Exception as e:
            print(f"❌ Taglenmiş Dosya yazma hatası: {e}")

    if not all_raw_data and not tagged_rows:
        print(f"❌ Veri oluşmadığı için kayıt yapılamadı.")

if __name__ == "__main__":
    scrape_youtube_trends()