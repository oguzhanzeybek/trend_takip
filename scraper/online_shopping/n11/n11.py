import sys
import time
import csv
import random
from pathlib import Path
from selenium.webdriver.common.by import By

# --- 1. YOL AYARLARI (AMAZON İLE AYNI) ---
# Dosya Konumu: scraper/online_shopping/n11/n11.py
CURRENT_DIR = Path(__file__).resolve().parent
# Scraper kök dizinine çık (n11 -> online_shopping -> scraper)
ROOT_DIR = CURRENT_DIR.parent.parent

# Kök dizini sisteme ekle (Böylece 'core' modülü bulunabilir)
sys.path.append(str(ROOT_DIR))

# --- 2. MERKEZİ DRIVER ÇAĞRISI ---
try:
    # Önce doğrudan scraper klasörü içindeymişiz gibi dene
    from core.driver_manager import get_chrome_driver
except ImportError:
    # Olmazsa bir üst dizini (proje ana dizini) ekle ve oradan dene
    sys.path.append(str(ROOT_DIR.parent))
    from scraper.core.driver_manager import get_chrome_driver

# --- AYARLAR ---
BASE_DIR = CURRENT_DIR

print("🚀 N11 Scraper (Merkezi Sistem) Başlatılıyor...")

# Merkezi yöneticiden driver al
try:
    driver = get_chrome_driver()
except Exception as e:
    print(f"❌ Driver başlatılamadı: {e}")
    sys.exit(1)

try:
    # 1. HEDEF URL
    url = "https://www.n11.com/arama?promotions=2015431"
    
    print(f"🌐 Siteye gidiliyor: {url}")
    driver.get(url)
    
    # Sayfanın bot kontrolünü geçmesi için ilk bekleme
    time.sleep(8) 

    # Çerez/Pop-up kapatma denemeleri
    try: driver.find_element(By.CLASS_NAME, "btnLater").click() 
    except: pass
    try: driver.find_element(By.ID, "myLocation-close-info").click()
    except: pass

    # 2. SCROLL (KAYDIRMA) İŞLEMİ
    print("⬇️ Sayfa aşağı kaydırılıyor...")
    
    last_height = driver.execute_script("return document.body.scrollHeight")
    scroll_count = 0
    max_scrolls = 30 # Sonsuz döngüden kaçınmak için güvenlik limiti
    
    while scroll_count < max_scrolls:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(random.uniform(2, 4)) # İnsan gibi rastgele bekleme
        
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            # Belki sayfa takılmıştır, biraz yukarı çıkıp tekrar inelim
            driver.execute_script("window.scrollBy(0, -500);")
            time.sleep(1)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
            new_height_check = driver.execute_script("return document.body.scrollHeight")
            if new_height_check == last_height:
                print(" ⏹️ Sayfa sonuna gelindi.")
                break
        
        last_height = new_height
        scroll_count += 1
        if scroll_count % 5 == 0:
            print(f"  -> Kaydırma {scroll_count} kez yapıldı...")

    # 3. VERİLERİ ÇEKME
    print("\n📦 Ürünler analiz ediliyor...")
    
    # N11 için alternatif seçiciler
    products = driver.find_elements(By.CSS_SELECTOR, "li.column")
    if len(products) == 0:
        products = driver.find_elements(By.CSS_SELECTOR, ".product-item")
    if len(products) == 0:
        products = driver.find_elements(By.CSS_SELECTOR, ".pro")

    print(f"  -> Toplam {len(products)} adet kutu bulundu.")

    # --- HATA AYIKLAMA (DEBUG) ---
    if len(products) == 0:
        screenshot_path = BASE_DIR / "hata_goruntusu.png"
        driver.save_screenshot(str(screenshot_path))
        print(f"⚠️ HATA: Hiç ürün bulunamadı. Görüntü kaydedildi: {screenshot_path}")

    all_products = []
    
    for p in products:
        try:
            # Başlık
            title = ""
            try: title = p.find_element(By.CSS_SELECTOR, ".productName").text.strip()
            except: 
                try: title = p.find_element(By.TAG_NAME, "h3").text.strip()
                except: continue

            # Fiyat
            price = "Fiyat Yok"
            try: 
                # İndirimli fiyat öncelikli
                price = p.find_element(By.CSS_SELECTOR, "ins").text.strip().replace("\n", "")
            except: 
                try: price = p.find_element(By.CSS_SELECTOR, ".newPrice").text.strip()
                except: pass

            # Link
            link = ""
            try: link = p.find_element(By.TAG_NAME, "a").get_attribute("href")
            except: pass

            if title: # Boş satırları ekleme
                all_products.append([title, price, link])
        except: continue

except Exception as e:
    print(f"❌ Kritik Hata: {e}")

finally:
    try:
        driver.quit()
        print("🛑 Tarayıcı kapatıldı.")
    except: pass

    # 4. CSV KAYDI
    if all_products:
        file_path = BASE_DIR / "n11.csv" # Dosya ismini n11.csv yaptım
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
        print("\n⚠️ Veri çekilemediği için dosya oluşturulmadı.")