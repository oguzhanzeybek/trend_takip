import sys
import time
import csv
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

def scrape_instagram_hashtags():
    print("🚀 Instagram Hashtag Scraper (Best-Hashtags) Başlatılıyor...")
    
    try:
        driver = get_chrome_driver()
    except Exception as e:
        print(f"❌ Driver hatası: {e}")
        return

    all_data = []

    try:
        for page_num in range(0, 9):
            url = f"https://best-hashtags.com/new-hashtags.php?pageNum_tag={page_num}&totalRows_tag=1000"
            print(f"🌐 Taranıyor: Sayfa {page_num}...")
            
            try:
                driver.get(url)
                time.sleep(3) 
            except Exception as e:
                print(f"  ⚠️ Sayfa yüklenemedi, geçiliyor: {e}")
                continue 

            soup = BeautifulSoup(driver.page_source, "html.parser")

            rows = soup.select("table.table.table-striped tbody tr")
            
            page_count = 0
            for row in rows:
                try:
                    cols = row.find_all("td")
                    if len(cols) == 3: 
                        hashtag_id = cols[0].get_text(strip=True)
                        hashtag = cols[1].get_text(strip=True)
                        count = cols[2].get_text(strip=True)
                        
                        if hashtag: 
                            all_data.append([hashtag_id, hashtag, count])
                            page_count += 1
                except:
                    continue
            
            print(f"  -> {page_count} hashtag bulundu.")

    except Exception as e:
        print(f"❌ Genel Hata: {e}")

    finally:
        try:
            driver.quit()
            print("🛑 Tarayıcı kapatıldı.")
        except: pass

        output_filename = "instagram.csv"
        output_path = BASE_DIR / output_filename

        if all_data:
            try:
                with open(output_path, "w", newline="", encoding="utf-8-sig") as file:
                    writer = csv.writer(file)
                    writer.writerow(["ID", "Hashtag", "Count"])
                    writer.writerows(all_data)
                print(f"✅ Dosya kaydedildi: {output_path}")
                print(f"📊 Toplam {len(all_data)} hashtag toplandı.")
            except Exception as e:
                print(f"❌ Dosya yazma hatası: {e}")
        else:
            print(f"❌ Veri oluşmadığı için '{output_filename}' kaydedilemedi.")

if __name__ == "__main__":
    scrape_instagram_hashtags()