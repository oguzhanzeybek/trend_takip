import sys
import time
import csv
from pathlib import Path
from bs4 import BeautifulSoup
import os 

CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parent.parent 
sys.path.append(str(ROOT_DIR))

try:
    from core.driver_manager import get_chrome_driver
except ImportError:
    sys.path.append(str(ROOT_DIR.parent))
    from scraper.core.driver_manager import get_chrome_driver

BASE_DIR = CURRENT_DIR

def scrape_youtube_trends():
    print("🚀 YouTube Trend Scraper Başlatılıyor...")
    
    channels = []
    keywords = []
    driver = None

    try:
        driver = get_chrome_driver()
        
        url = "https://youtube.trends24.in/turkey"
        print(f"🌐 Gidiliyor: {url}")
        driver.get(url)
        time.sleep(5) # Sayfanın yüklenmesi için bekle

        soup = BeautifulSoup(driver.page_source, "html.parser")

        channels = [span.text.strip() for span in soup.select("span.title")]
        print(f"  ✅ {len(channels)} trend kanal bulundu.")

        keywords = [li.text.strip() for li in soup.select("ol.keywords-list li")]
        print(f"  ✅ {len(keywords)} popüler anahtar kelime bulundu.")

    except Exception as e:
        print(f"❌ Genel Hata: {e}")

    finally:
        if driver:
            driver.quit()
            print("🛑 Tarayıcı kapatıldı.")

    
    all_raw_data = channels + keywords

    tagged_rows = []
    
    # --- DEĞİŞİKLİK BURADA BAŞLIYOR (Sıra Numarası Ekleme) ---
    # Global bir sayaç tutuyoruz ki kanallardan sonra kelimeler kaldığı yerden devam etsin
    current_rank = 1 
    
    for c in channels:
        # Listenin başına 'current_rank' ekledik
        tagged_rows.append([current_rank, c, ""]) 
        current_rank += 1
        
    for k in keywords:
        # Listenin başına 'current_rank' ekledik
        tagged_rows.append([current_rank, "", k])
        current_rank += 1
    # ---------------------------------------------------------

    
    file_path_raw = BASE_DIR / "youtube_trends.csv"
    if all_raw_data:
        try:
            with open(file_path_raw, "w", newline="", encoding="utf-8-sig") as file:
                writer = csv.writer(file)
                # Header'a "Rank" ekledik
                writer.writerow(["Rank", "Channels / Keywords"]) 
                
                # enumerate ile her satıra numara vererek yazıyoruz
                for i, item in enumerate(all_raw_data, 1):
                    writer.writerow([i, item])
                    
            print(f"✅ Dosya kaydedildi: {file_path_raw}")
        except Exception as e:
            print(f"❌ Ham Dosya yazma hatası: {e}")

    file_path_tag = BASE_DIR / "youtube_trends_tag.csv"
    if tagged_rows:
        try:
            with open(file_path_tag, "w", newline="", encoding="utf-8-sig") as file:
                writer = csv.writer(file)
                # Header'a "rank" ekledik
                writer.writerow(["rank", "video", "tag"]) 
                writer.writerows(tagged_rows)
            print(f"✅ Dosya kaydedildi: {file_path_tag}")
        except Exception as e:
            print(f"❌ Taglenmiş Dosya yazma hatası: {e}")

    if not all_raw_data and not tagged_rows:
        print(f"❌ Veri oluşmadığı için kayıt yapılamadı.")

if __name__ == "__main__":
    scrape_youtube_trends()