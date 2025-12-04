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

print("🚀 Amazon Scraper (Merkezi Sistem) Başlatılıyor...")

try:
    driver = get_chrome_driver()
except Exception as e:
    print(f"❌ Driver başlatılamadı: {e}")
    sys.exit(1)

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

    all_products = []

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
                            if len(line) < 20: # Fiyat satırı genelde kısadır
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
                writer.writerow(["Kategori", "Sıra", "Ürün Adı", "Fiyat", "Link"])
                for row in all_products:
                    writer.writerow(row)

            print(f"\n✅ İŞLEM TAMAMLANDI!")
            print(f"📂 Toplam {len(all_products)} ürün kaydedildi.")
            print(f"📄 Dosya: {file_path}")
        except Exception as e:
            print(f"❌ Kayıt hatası: {e}")
    else:
        print("\n⚠️ Hiçbir ürün çekilemedi.")