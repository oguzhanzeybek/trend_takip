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
SCREENSHOT_DIR.mkdir(exist_ok=True) # Klasör yoksa oluştur

print("🚀 CarrefourSA Scraper (Merkezi Sistem & Gelişmiş Mod) Başlatılıyor...")

try:
    driver = get_chrome_driver()
    wait = WebDriverWait(driver, 15)
except Exception as e:
    print(f"❌ Driver başlatılamadı: {e}")
    sys.exit(1)

try:
    all_products = []
    target_count = 500 # Hedef ürün sayısı
    current_page = 0
    MAX_RETRY = 3 

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
            "li.product-listing-item",       # Klasik yapı
            ".product_list_item",            # Alternatif
            "div.product-card",              # Modern yapı
            ".item-product-card",            # Bazen kullanılan
            "ul.product-listing li"          # Liste bazlı
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
                
                if not title: continue # İsimsiz ürünü geç

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

    if all_products:
        file_path = BASE_DIR / "carrefoursa.csv"
        try:
            with open(file_path, "w", newline="", encoding="utf-8-sig") as file:
                writer = csv.writer(file)
                writer.writerow(["Marka", "Ürün Adı", "Fiyat", "Link"])
                writer.writerows(all_products)
            print(f"\n✅ İŞLEM BAŞARILI!")
            print(f"📄 Dosya: {file_path}")
        except Exception as e:
            print(f"❌ Dosya yazma hatası: {e}")
    else:
        print("\n⚠️ Veri çekilemedi. Lütfen 'debug_carrefour' klasöründeki ekran görüntüsünü kontrol et.")