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
SCREENSHOT_DIR = BASE_DIR / "debug_screenshots"
SCREENSHOT_DIR.mkdir(exist_ok=True) 

print("🚀 A101 Scraper (Veritabanı YOK - Sadece CSV) Başlatılıyor...")

def scrape_a101():
    driver = None
    try:
        driver = get_chrome_driver()
        wait = WebDriverWait(driver, 20) 
    except Exception as e:
        print(f"❌ Driver başlatılamadı: {e}")
        return

    all_products = []

    try:
        page = 1
        MAX_PAGES = 5 

        while page <= MAX_PAGES:
            
            url = f"https://www.a101.com.tr/liste/haftanin-cok-satanlari/?page={page}"
            print(f"\n--- Gidiliyor: Sayfa {page} ---")
            driver.get(url)
            
            time.sleep(random.uniform(5, 8)) 

            try:
                cookie_btn = driver.find_element(By.ID, "CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll")
                cookie_btn.click()
            except: pass
            
            print("⬇️ Sayfa yavaşça kaydırılıyor...")
            for i in range(1, 6): 
                driver.execute_script(f"window.scrollTo(0, document.body.scrollHeight * {i/5});")
                time.sleep(random.uniform(1, 2))

            try:
                print("⏳ Ürünlerin görünmesi bekleniyor...")
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "ul.list-content, .product-container, .product-card")))
            except:
                print("⚠️ Bekleme süresi doldu, yine de devam ediliyor.")

            possible_selectors = [
                "li.product-item-box",       
                ".product-container",        
                "div.product-card",          
                "ul.list-content li",        
                "a[class*='product-link']"   
            ]

            product_cards = []
            for selector in possible_selectors:
                found = driver.find_elements(By.CSS_SELECTOR, selector)
                if len(found) > 0:
                    print(f"✅ Seçici çalıştı: '{selector}' -> {len(found)} adet bulundu.")
                    product_cards = found
                    break 
            
            if len(product_cards) == 0:
                print(f"⚠️ UYARI: Sayfa {page} boş geldi.")
                error_shot = SCREENSHOT_DIR / f"hata_sayfa_{page}.png"
                driver.save_screenshot(str(error_shot))
                print(f"📸 Ekran görüntüsü alındı: {error_shot}")
                
            for card in product_cards:
                try:
                    title, price, link = "İsim Yok", "Fiyat Yok", ""

                    try: title = card.find_element(By.TAG_NAME, "h3").text.strip()
                    except: 
                        try: title = card.find_element(By.CSS_SELECTOR, ".name").text.strip()
                        except: pass

                    try: link = card.find_element(By.TAG_NAME, "a").get_attribute("href")
                    except: pass

                    try:
                        text_content = card.text
                        lines = text_content.split('\n')
                        for line in lines:
                            if "TL" in line or "₺" in line:
                                price = line.strip()
                                break
                    except: pass
                    
                    if title != "İsim Yok":
                        all_products.append([title, price, link])

                except Exception as e:
                    continue
            
            print(f"  -> Toplam Toplanan: {len(all_products)}")
            page += 1

    except Exception as e:
        print(f"❌ Kritik Hata: {e}")

    finally:
        try:
            driver.quit()
            print("🛑 Tarayıcı kapatıldı.")
        except: pass

        # CSV KAYDI (Rank Eklendi)
        if all_products:
            file_path = BASE_DIR / "a101.csv"
            try:
                with open(file_path, "w", newline="", encoding="utf-8-sig") as file:
                    writer = csv.writer(file)
                    # Header: Başa Rank ekledik
                    writer.writerow(["Rank", "Ürün Adı", "Fiyat", "Link"])
                    
                    # Sıra Numarasıyla Yazma
                    for i, prod in enumerate(all_products, 1):
                        writer.writerow([i] + prod)

                print(f"\n✅ BAŞARILI! {len(all_products)} ürün kaydedildi.")
                print(f"📄 Dosya: {file_path}")
            except Exception as e:
                print(f"❌ Dosya yazma hatası: {e}")
        else:
            print("\n⚠️ Ürün listesi boş.")

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
    scrape_a101()
    auto_add_index_to_csvs()