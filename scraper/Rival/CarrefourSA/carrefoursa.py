import sys
import time
import csv
import random
from pathlib import Path
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parent.parent
sys.path.append(str(ROOT_DIR))

try:
    from core.driver_manager import get_chrome_driver
except ImportError:
    sys.path.append(str(ROOT_DIR.parent))
    from scraper.core.driver_manager import get_chrome_driver

BASE_DIR = CURRENT_DIR
SCREENSHOT_DIR = BASE_DIR / "debug_carrefour"
SCREENSHOT_DIR.mkdir(exist_ok=True) 

print("🚀 CarrefourSA Scraper (Veritabanı YOK - Sadece CSV) Başlatılıyor...")

def scrape_carrefoursa():
    try:
        driver = get_chrome_driver()
        wait = WebDriverWait(driver, 15)
    except Exception as e:
        print(f"❌ Driver başlatılamadı: {e}")
        return

    try:
        all_products = []
        target_count = 500 
        current_page = 0
        
        while len(all_products) < target_count:
            
            url = f"https://www.carrefoursa.com/cok-satanlar/c/9124?q=%3AbestSeller&page={current_page}"
            print(f"\n--- Gidiliyor: Sayfa {current_page + 1} ---")
            driver.get(url)
            
            time.sleep(random.uniform(5, 8))

            try:
                buttons = ["onetrust-accept-btn-handler", "btn-accept-all", "close-modal"]
                for btn_id in buttons:
                    try: driver.find_element(By.ID, btn_id).click()
                    except: pass
                
                driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
            except: pass

            print("⬇️ Resimlerin yüklenmesi için kaydırılıyor...")
            for i in range(1, 4):
                driver.execute_script(f"window.scrollTo(0, document.body.scrollHeight * {i/4});")
                time.sleep(1)

            possible_selectors = [
                "li.product-listing-item",      
                ".product_list_item",           
                "div.product-card",             
                ".item-product-card",           
                "ul.product-listing li"         
            ]

            products = []
            
            print("🔍 Ürünler aranıyor...")
            for selector in possible_selectors:
                found = driver.find_elements(By.CSS_SELECTOR, selector)
                if len(found) > 0:
                    products = found
                    print(f"✅ Seçici çalıştı: '{selector}' -> {len(found)} adet bulundu.")
                    break
            
            if len(products) == 0:
                print("❌ HATA: Ürün bulunamadı.")
                shot_path = SCREENSHOT_DIR / f"hata_sayfa_{current_page}.png"
                driver.save_screenshot(str(shot_path))
                print(f"📸 Hata görüntüsü kaydedildi: {shot_path}")
                
                page_source = driver.page_source.lower()
                if "verify you are human" in page_source or "captcha" in page_source:
                    print("⚠️ KRİTİK: Bot korumasına (Cloudflare/WAF) takıldık.")
                    break
                
                if current_page > 0:
                    print("⏹️ Muhtemelen sayfa sonuna gelindi.")
                    break
                else:
                    break

            added_on_this_page = 0
            for p in products:
                if len(all_products) >= target_count: break
                
                try:
                    title = ""
                    try: title = p.find_element(By.CSS_SELECTOR, ".item-name").text.strip()
                    except: 
                        try: title = p.find_element(By.TAG_NAME, "h3").text.strip()
                        except: pass
                    
                    if not title: continue 

                    price = "Fiyat Yok"
                    try: 
                        raw_price = p.find_element(By.CSS_SELECTOR, ".item-price").text
                        price = raw_price.replace("\n", "").strip()
                    except: pass

                    link = ""
                    try: link = p.find_element(By.TAG_NAME, "a").get_attribute("href")
                    except: pass

                    brand = "-"
                    try: brand = p.find_element(By.CSS_SELECTOR, ".item-brand").text.strip()
                    except: pass

                    all_products.append([brand, title, price, link])
                    added_on_this_page += 1

                except Exception as e:
                    continue
            
            print(f"  -> Sayfadan eklenen: {added_on_this_page}")
            print(f"  -> Toplam: {len(all_products)}/{target_count}")
            
            current_page += 1

    except Exception as e:
        print(f"❌ Beklenmedik Hata: {e}")

    finally:
        try:
            driver.quit()
            print("🛑 Tarayıcı kapatıldı.")
        except: pass

        # CSV KAYDI (Rank Eklendi)
        if all_products:
            file_path = BASE_DIR / "carrefoursa.csv"
            try:
                with open(file_path, "w", newline="", encoding="utf-8-sig") as file:
                    writer = csv.writer(file)
                    # Header: Başa Rank ekledik
                    writer.writerow(["Rank", "Marka", "Ürün Adı", "Fiyat", "Link"])
                    
                    # Sıra Numarasıyla Yazma
                    for i, prod in enumerate(all_products, 1):
                        writer.writerow([i] + prod)
                        
                print(f"\n✅ İŞLEM BAŞARILI!")
                print(f"📄 Dosya: {file_path}")
            except Exception as e:
                print(f"❌ Dosya yazma hatası: {e}")
        else:
            print("\n⚠️ Veri çekilemedi. Lütfen 'debug_carrefour' klasöründeki ekran görüntüsünü kontrol et.")

# ==========================================
# OTO-İNDEKSLEME FONKSİYONU
# ==========================================
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
    scrape_carrefoursa()
    auto_add_index_to_csvs()