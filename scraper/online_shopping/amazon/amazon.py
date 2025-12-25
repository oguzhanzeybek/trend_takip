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

print("🚀 Amazon Scraper (Veritabanı YOK - Sadece CSV) Başlatılıyor...")

def scrape_amazon():
    try:
        driver = get_chrome_driver()
    except Exception as e:
        print(f"❌ Driver başlatılamadı: {e}")
        return

    all_products = []

    try:
        base_url = "https://www.amazon.com.tr/gp/bestsellers"
        print(f"🌐 Gidiliyor: {base_url}")
        driver.get(base_url)
        time.sleep(5)

        try:
            cookie_accept = driver.find_element(By.ID, "sp-cc-accept")
            cookie_accept.click()
            print("  🍪 Çerezler geçildi.")
        except:
            pass

        print("  📂 Kategoriler taranıyor...")
        category_links = []
        
        try:
            sidebar = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.ID, "zg-left-col"))
            )
            links = sidebar.find_elements(By.TAG_NAME, "a")
            
            for link in links:
                txt = link.text.strip()
                href = link.get_attribute("href")
                if txt and href and "amazon.com.tr" in href:
                    category_links.append((txt, href))
            
            print(f"  ✅ Toplam {len(category_links)} kategori bulundu.")
            
        except Exception as e:
            print(f"❌ Kategori listesi alınamadı (Hata: {e})")
            screenshot_path = BASE_DIR / "hata_kategori.png"
            driver.save_screenshot(str(screenshot_path))

        for cat_name, cat_url in category_links:
            print(f"\n--- İşleniyor: {cat_name} ---")
            
            try:
                driver.get(cat_url)
                time.sleep(random.uniform(3, 5))

                if "Robot" in driver.title or "CAPTCHA" in driver.page_source:
                    print(f"⚠️ {cat_name} kategorisinde Captcha çıktı, atlanıyor.")
                    continue

                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
                time.sleep(1)

                product_cards = driver.find_elements(By.ID, "gridItemRoot")
                if not product_cards:
                    product_cards = driver.find_elements(By.CLASS_NAME, "zg-grid-general-faceout")

                print(f"  -> {len(product_cards)} ürün bulundu.")

                for p in product_cards:
                    try:
                        try: rank = p.find_element(By.CLASS_NAME, "zg-bdg-text").text.strip()
                        except: rank = "-"

                        title = "İsim Bulunamadı"
                        product_link = ""
                        
                        links_in_card = p.find_elements(By.TAG_NAME, "a")
                        for l in links_in_card:
                            l_text = l.text.strip()
                            if len(l_text) > 10: 
                                title = l_text
                                product_link = l.get_attribute("href")
                                break
                        
                        card_text = p.text
                        price = "Fiyat Yok"
                        for line in card_text.split('\n'):
                            if ("TL" in line or "," in line) and any(c.isdigit() for c in line):
                                if len(line) < 20: 
                                    price = line
                                    break

                        all_products.append([cat_name, rank, title, price, product_link])

                    except:
                        continue

            except Exception as e:
                print(f"  Hata: {e}")
                continue

    except Exception as e:
        print(f"❌ Kritik Hata: {e}")

    finally:
        try:
            driver.quit()
            print("🛑 Tarayıcı kapatıldı.")
        except: pass

        if all_products:
            file_path = BASE_DIR / "amazon.csv"
            
            try:
                with open(file_path, "w", newline="", encoding="utf-8-sig") as file:
                    writer = csv.writer(file)
                    
                    # --- Header Güncellendi: Başa 'Rank' eklendi ---
                    writer.writerow(["Rank", "Kategori", "Site Sırası", "Ürün Adı", "Fiyat", "Link"])
                    
                    # --- Veriler 1'den başlayarak numaralandırılıyor ---
                    for i, row in enumerate(all_products, 1):
                        writer.writerow([i] + row)

                print(f"\n✅ İŞLEM TAMAMLANDI!")
                print(f"📂 Toplam {len(all_products)} ürün kaydedildi.")
                print(f"📄 Dosya: {file_path}")
            except Exception as e:
                print(f"❌ Kayıt hatası: {e}")
        else:
            print("\n⚠️ Hiçbir ürün çekilemedi.")

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
    scrape_amazon()
    auto_add_index_to_csvs()