import sys
import time
import csv
import random
from pathlib import Path
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- 1. YOL AYARLARI ---
# Dosya Konumu: scraper/online_shopping/a101/a101.py
CURRENT_DIR = Path(__file__).resolve().parent
# Scraper kök dizinine çık (a101 -> online_shopping -> scraper)
ROOT_DIR = CURRENT_DIR.parent.parent
sys.path.append(str(ROOT_DIR))

# --- 2. MERKEZİ DRIVER ÇAĞRISI ---
try:
    from core.driver_manager import get_chrome_driver
except ImportError:
    # Yedek yol denemesi
    sys.path.append(str(ROOT_DIR.parent))
    from scraper.core.driver_manager import get_chrome_driver

# --- AYARLAR ---
BASE_DIR = CURRENT_DIR
SCREENSHOT_DIR = BASE_DIR / "debug_screenshots"
SCREENSHOT_DIR.mkdir(exist_ok=True) # Klasör yoksa oluştur

print("🚀 A101 Scraper (Merkezi Sistem & Gelişmiş Mantık) Başlatılıyor...")

# Merkezi driver'ı başlat
try:
    driver = get_chrome_driver()
    wait = WebDriverWait(driver, 20) # 20 saniye bekleme limiti
except Exception as e:
    print(f"❌ Driver başlatılamadı: {e}")
    sys.exit(1)

try:
    all_products = []
    page = 1
    MAX_PAGES = 5 # İstersen artırabilirsin

    while page <= MAX_PAGES:
        
        url = f"https://www.a101.com.tr/liste/haftanin-cok-satanlari/?page={page}"
        print(f"\n--- Gidiliyor: Sayfa {page} ---")
        driver.get(url)
        
        # 1. YAVAŞLATMA: İnsan taklidi
        time.sleep(random.uniform(5, 8)) 

        # --- POP-UP KAPATMA DENEMELERİ ---
        try:
            cookie_btn = driver.find_element(By.ID, "CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll")
            cookie_btn.click()
        except: pass
        
        # 2. KAYDIRMA: Yavaşça aşağı in
        print("⬇️ Sayfa yavaşça kaydırılıyor...")
        for i in range(1, 6): # Çok abartmadan 5 adımda inelim
            driver.execute_script(f"window.scrollTo(0, document.body.scrollHeight * {i/5});")
            time.sleep(random.uniform(1, 2))

        # 3. BEKLEME: Ürünlerin yüklenmesini bekle
        try:
            print("⏳ Ürünlerin görünmesi bekleniyor...")
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "ul.list-content, .product-container, .product-card")))
        except:
            print("⚠️ Bekleme süresi doldu, yine de devam ediliyor.")

        # 4. ÜRÜNLERİ TOPLA (Senin Gelişmiş Seçici Listen)
        possible_selectors = [
            "li.product-item-box",       # Yaygın yapı
            ".product-container",        # Eski yapı
            "div.product-card",          # Alternatif
            "ul.list-content li",        # Liste elemanları
            "a[class*='product-link']"   # Link içeren ürünler
        ]

        product_cards = []
        for selector in possible_selectors:
            found = driver.find_elements(By.CSS_SELECTOR, selector)
            if len(found) > 0:
                print(f"✅ Seçici çalıştı: '{selector}' -> {len(found)} adet bulundu.")
                product_cards = found
                break 
        
        # --- HATA AYIKLAMA (SCREENSHOT) ---
        if len(product_cards) == 0:
            print(f"⚠️ UYARI: Sayfa {page} boş geldi.")
            error_shot = SCREENSHOT_DIR / f"hata_sayfa_{page}.png"
            driver.save_screenshot(str(error_shot))
            print(f"📸 Ekran görüntüsü alındı: {error_shot}")
            # Eğer üst üste boş gelirse döngüyü kırmak mantıklı olabilir, şimdilik devam etsin.
            
        for card in product_cards:
            try:
                # Veri çekme kısmı (Hata toleranslı)
                title, price, link = "İsim Yok", "Fiyat Yok", ""

                # İsim
                try: title = card.find_element(By.TAG_NAME, "h3").text.strip()
                except: 
                    try: title = card.find_element(By.CSS_SELECTOR, ".name").text.strip()
                    except: pass

                # Link
                try: link = card.find_element(By.TAG_NAME, "a").get_attribute("href")
                except: pass

                # Fiyat (Metin Analizi)
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

    if all_products:
        file_path = BASE_DIR / "a101.csv"
        try:
            with open(file_path, "w", newline="", encoding="utf-8-sig") as file:
                writer = csv.writer(file)
                writer.writerow(["Ürün Adı", "Fiyat", "Link"])
                writer.writerows(all_products)
            print(f"\n✅ BAŞARILI! {len(all_products)} ürün kaydedildi.")
            print(f"📄 Dosya: {file_path}")
        except Exception as e:
            print(f"❌ Dosya yazma hatası: {e}")
    else:
        print("\n⚠️ Ürün listesi boş.")