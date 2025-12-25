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

print("🚀 Trendyol Scraper (Veritabanı YOK - Sadece CSV) Başlatılıyor...")

def scrape_trendyol():
    try:
        driver = get_chrome_driver()
    except Exception as e:
        print(f"❌ Driver başlatılamadı: {e}")
        return

    all_products = []

    try:
        base_url = "https://www.trendyol.com/cok-satanlar?type=popular"
        
        print(f"🌐 Ana sayfaya gidiliyor: {base_url}")
        driver.get(base_url)
        time.sleep(5)

        try:
            close_btn = driver.find_element(By.CLASS_NAME, "fancybox-close-small")
            close_btn.click()
            print("  ❌ Pop-up kapatıldı.")
        except:
            pass

        print("  📂 Kategori listesi taranıyor...")
        category_names = []
        
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "category-pill"))
            )
            buttons = driver.find_elements(By.CSS_SELECTOR, "button.category-pill")
            
            for btn in buttons:
                txt = btn.text.strip()
                if txt and txt not in category_names:
                    category_names.append(txt)
            
            print(f"  ✅ Hafızaya alınan kategoriler ({len(category_names)}): {category_names}")
                    
        except Exception as e:
            print("  ⚠️ Kategoriler alınamadı, sadece ana sayfa taranacak.")
            category_names = ["Popüler Ürünler"]

        for target_cat_name in category_names:
            print(f"\n--- Sıradaki Hedef: {target_cat_name} ---")
            
            try:
                if target_cat_name != "Popüler Ürünler":
                    driver.get(base_url)
                    time.sleep(3) 

                    current_buttons = driver.find_elements(By.CSS_SELECTOR, "button.category-pill")
                    button_found = False

                    for btn in current_buttons:
                        if btn.text.strip() == target_cat_name:
                            driver.execute_script("arguments[0].click();", btn)
                            button_found = True
                            print(f"  🖱️ '{target_cat_name}' butonuna tıklandı.")
                            break 
                    
                    if not button_found:
                        print(f"  ⚠️ Uyarı: '{target_cat_name}' butonu bu sayfada bulunamadı.")
                        continue

                    time.sleep(3) 
                
                SCROLL_COUNT = 4 
                for i in range(SCROLL_COUNT):
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(1.5)

                product_cards = driver.find_elements(By.CLASS_NAME, "product-card-link")
                print(f"  -> {len(product_cards)} ürün bulundu.")

                for card in product_cards:
                    try:
                        link = card.get_attribute("href")
                        try: brand = card.find_element(By.CLASS_NAME, "product-brand-name").text.strip()
                        except: brand = ""
                        try: name = card.find_element(By.CLASS_NAME, "product-name").text.strip()
                        except: name = ""
                        try: price = card.find_element(By.CLASS_NAME, "current-price").text.strip()
                        except: price = "Sepette İndirimli"

                        all_products.append([target_cat_name, brand, name, price, link])
                    except:
                        continue
            
            except Exception as e:
                print(f"  ❌ Hata ({target_cat_name}): {e}")
                continue

    except Exception as e:
        print(f"❌ Genel Hata: {e}")

    finally:
        try:
            driver.quit()
            print("🛑 Tarayıcı kapatıldı.")
        except: pass

        if all_products:
            file_path = BASE_DIR / "trendyol.csv"
            
            try:
                with open(file_path, "w", newline="", encoding="utf-8-sig") as file:
                    writer = csv.writer(file)
                    # --- Header Güncellendi: Başa 'Rank' eklendi ---
                    writer.writerow(["Rank", "Kategori", "Marka", "Ürün Adı", "Fiyat", "Link"])
                    
                    # --- Veriler 1'den başlayarak numaralandırılıyor ---
                    for i, prod in enumerate(all_products, 1):
                        writer.writerow([i] + prod)

                print(f"\n✅ İŞLEM TAMAMLANDI!")
                print(f"📂 Toplam {len(all_products)} ürün kaydedildi.")
                print(f"📄 Dosya: {file_path}")
            except Exception as e:
                print(f"❌ Dosya yazma hatası: {e}")
        else:
            print("\n⚠️ Hiçbir veri çekilemedi.")

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
    scrape_trendyol()
    auto_add_index_to_csvs()