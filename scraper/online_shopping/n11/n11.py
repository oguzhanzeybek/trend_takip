import sys
import time
import csv
import random
from pathlib import Path
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parent.parent

sys.path.append(str(ROOT_DIR))

try:
    from core.driver_manager import get_chrome_driver
except ImportError:
    sys.path.append(str(ROOT_DIR.parent))
    from scraper.core.driver_manager import get_chrome_driver

BASE_DIR = CURRENT_DIR

print("🚀 N11 Scraper (Veritabanı YOK - Sadece CSV) Başlatılıyor...")

def scrape_n11():
    try:
        driver = get_chrome_driver()
    except Exception as e:
        print(f"❌ Driver başlatılamadı: {e}")
        return

    all_products = []

    try:
        url = "https://www.n11.com/arama?promotions=2015431"
        
        print(f"🌐 Siteye gidiliyor: {url}")
        driver.get(url)
        
        time.sleep(8) 

        try: driver.find_element(By.CLASS_NAME, "btnLater").click() 
        except: pass
        try: driver.find_element(By.ID, "myLocation-close-info").click()
        except: pass

        print("⬇️ Sayfa aşağı kaydırılıyor...")
        
        last_height = driver.execute_script("return document.body.scrollHeight")
        scroll_count = 0
        max_scrolls = 30 
        
        while scroll_count < max_scrolls:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(random.uniform(2, 4)) 
            
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                driver.execute_script("window.scrollBy(0, -500);")
                time.sleep(1)
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)
                new_height_check = driver.execute_script("return document.body.scrollHeight")
                if new_height_check == last_height:
                    print("  ⏹️ Sayfa sonuna gelindi.")
                    break
            
            last_height = new_height
            scroll_count += 1
            if scroll_count % 5 == 0:
                print(f"  -> Kaydırma {scroll_count} kez yapıldı...")

        print("\n📦 Ürünler analiz ediliyor...")
        
        products = driver.find_elements(By.CSS_SELECTOR, "li.column")
        if len(products) == 0:
            products = driver.find_elements(By.CSS_SELECTOR, ".product-item")
        if len(products) == 0:
            products = driver.find_elements(By.CSS_SELECTOR, ".pro")

        print(f"  -> Toplam {len(products)} adet kutu bulundu.")

        if len(products) == 0:
            screenshot_path = BASE_DIR / "hata_goruntusu.png"
            driver.save_screenshot(str(screenshot_path))
            print(f"⚠️ HATA: Hiç ürün bulunamadı. Görüntü kaydedildi: {screenshot_path}")

        for p in products:
            try:
                title = ""
                try: title = p.find_element(By.CSS_SELECTOR, ".productName").text.strip()
                except: 
                    try: title = p.find_element(By.TAG_NAME, "h3").text.strip()
                    except: continue

                price = "Fiyat Yok"
                try: 
                    price = p.find_element(By.CSS_SELECTOR, "ins").text.strip().replace("\n", "")
                except: 
                    try: price = p.find_element(By.CSS_SELECTOR, ".newPrice").text.strip()
                    except: pass

                link = ""
                try: link = p.find_element(By.TAG_NAME, "a").get_attribute("href")
                except: pass

                if title: 
                    all_products.append([title, price, link])
            except: continue

    except Exception as e:
        print(f"❌ Kritik Hata: {e}")

    finally:
        try:
            driver.quit()
            print("🛑 Tarayıcı kapatıldı.")
        except: pass

        if all_products:
            file_path = BASE_DIR / "n11.csv"
            try:
                with open(file_path, "w", newline="", encoding="utf-8-sig") as file:
                    writer = csv.writer(file)
                    writer.writerow(["Rank", "Ürün Adı", "Fiyat", "Link"])
                    
                    for i, prod in enumerate(all_products, 1):
                        writer.writerow([i] + prod)

                print(f"\n✅ BAŞARILI! {len(all_products)} ürün kaydedildi.")
                print(f"📄 Dosya: {file_path}")
            except Exception as e:
                print(f"❌ Dosya yazma hatası: {e}")
        else:
            print("\n⚠️ Veri çekilemediği için dosya oluşturulmadı.")

def auto_add_index_to_csvs():
    import os
    import csv
    
    folder_path = os.path.dirname(os.path.abspath(__file__))
    csv_files = [f for f in os.listdir(folder_path) if f.endswith('.csv')]
    
    print(f"\n🔄 İndeksleme Başladı: {folder_path} klasöründeki dosyalar taranıyor...")

    for filename in csv_files:
        file_path = os.path.join(folder_path, filename)
        rows = []
        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.reader(f)
                rows = list(reader)
            
            if not rows: continue

            header = rows[0]
            data = rows[1:]

            if header and str(header[0]).lower() == "rank":
                print(f"  Start ⏩ {filename} (Zaten indeksli)")
                continue

            new_header = ["Rank"] + header
            new_data = []
            
            for index, row in enumerate(data, 1):
                new_data.append([index] + row)

            with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(new_header)
                writer.writerows(new_data)
            
            print(f"  ✅ İndeks Eklendi: {filename}")

        except Exception as e:
            print(f"  ❌ Hata ({filename}): {e}")

if __name__ == "__main__":
    scrape_n11()
    auto_add_index_to_csvs()