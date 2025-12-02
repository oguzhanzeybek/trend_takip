import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
import time
import csv
import os
import random
from pathlib import Path

# --- DİNAMİK YOL AYARLARI ---
BASE_DIR = Path(__file__).resolve().parent

# --- AYARLAR ---
options = uc.ChromeOptions()

# -----------------------------------------------------------
# KRİTİK AYARLAR (GitHub Actions & Headless Tespiti Önleme)
# -----------------------------------------------------------
# Eski "--headless" yerine bunu kullanın. N11 eski modu hemen yakalar.
options.add_argument("--headless=new") 

# Gerçek bir Windows kullanıcısı gibi görünmek için User-Agent
options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36")

options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--start-maximized")
options.add_argument("--window-size=1920,1080")
options.add_argument("--disable-notifications")
options.add_argument("--disable-popup-blocking")
options.add_argument("--disable-blink-features=AutomationControlled") # Bot bayrağını gizle

print("🚀 N11 Scraper (Gelişmiş Headless) Başlatılıyor...")

# version_main parametresini GitHub Actions'taki Chrome sürümüne göre gerekirse açın
# driver = uc.Chrome(options=options, version_main=130) 
driver = uc.Chrome(options=options)

try:
    # 1. HEDEF URL
    # Not: Reklam parametrelerini (gclid vs) temizledim, bunlar bot korumasını tetikleyebilir.
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
    
    # N11 için alternatif seçiciler (Biri çalışmazsa diğeri devreye girer)
    products = driver.find_elements(By.CSS_SELECTOR, "li.column")
    if len(products) == 0:
        products = driver.find_elements(By.CSS_SELECTOR, ".product-item")
    if len(products) == 0:
        products = driver.find_elements(By.CSS_SELECTOR, ".pro")

    print(f"  -> Toplam {len(products)} adet kutu bulundu.")

    # --- HATA AYIKLAMA (DEBUG) ---
    # Eğer 0 ürün bulursa ne gördüğünün fotoğrafını çeker
    if len(products) == 0:
        screenshot_path = BASE_DIR / "hata_goruntusu.png"
        driver.save_screenshot(str(screenshot_path))
        print(f"⚠️ HATA: Hiç ürün bulunamadı. Sayfanın ne gördüğü şuraya kaydedildi: {screenshot_path}")
        print("💡 İPUCU: Ekran görüntüsünde 'Captcha' veya boş sayfa varsa IP banlanmış olabilir.")

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
        file_path = BASE_DIR / "n11_sonuc.csv"
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