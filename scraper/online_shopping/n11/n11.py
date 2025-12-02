import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
import time
import csv
import os
from pathlib import Path

# --- DİNAMİK YOL AYARLARI ---
# Scriptin çalıştığı klasörü tam yol olarak alır
BASE_DIR = Path(__file__).resolve().parent

# --- AYARLAR ---
options = uc.ChromeOptions()
# GitHub Actions ve Sunucu ortamları için kritik ayarlar:
options.add_argument("--headless") # Arayüzsüz mod
options.add_argument("--no-sandbox") # Sandbox güvenlik katmanını aşar
options.add_argument("--disable-dev-shm-usage") # Bellek hatalarını önler
options.add_argument("--start-maximized")
options.add_argument("--window-size=1920,1080") # Headless modda kaydırma için ekran boyutu şart
options.add_argument("--disable-notifications")
options.add_argument("--disable-popup-blocking")

print("🚀 N11 Scraper (Headless & Dinamik) Başlatılıyor...")
driver = uc.Chrome(options=options)

try:
    # 1. HEDEF URL
    url = "https://www.n11.com/arama?promotions=2015431&gclsrc=aw.ds&gad_source=1&gad_campaignid=23290547517&gbraid=0AAAAADsJcV04XH0JnMioAnkrQxfXTC7RZ&gclid=Cj0KCQiA0KrJBhCOARIsAGIy9wCySQIDVeXPzxHfMY3m3J1baUwBZndSnVmnu-k50NHsMki9jYpyJrIaAmAIEALw_wcB"
    print("🌐 Siteye gidiliyor...")
    driver.get(url)
    time.sleep(5) 

    # Çerez/Konum kapatma
    try: driver.find_element(By.CLASS_NAME, "btnLater").click() 
    except: pass
    try: driver.find_element(By.XPATH, "//span[contains(text(), 'Kabul Et')]").click()
    except: pass

    # 2. ADIM ADIM KAYDIRMA DÖNGÜSÜ
    print("⬇️ Satır satır aşağı iniliyor (Lazy Load)...")

    # Başlangıç pozisyonu
    current_position = 0
    # Bir satır ürün yaklaşık 400-500 pikseldir
    scroll_step = 400 
    
    while True:
        # Sayfanın mevcut toplam uzunluğunu al
        total_height = driver.execute_script("return document.body.scrollHeight")
        
        # Eğer mevcut pozisyonumuz toplam uzunluğa geldiyse veya geçtiyse dur
        if current_position > total_height:
            print("  ✅ Sayfa sonuna gelindi.")
            break
        
        # Kaydırma İşlemi
        driver.execute_script(f"window.scrollTo(0, {current_position});")
        current_position += scroll_step
        
        # BEKLEME (Headless modda bazen biraz daha uzun beklemek gerekebilir)
        time.sleep(2) 
        
        # Kullanıcıyı bilgilendir (Her 2000px'de bir yazdıralım ki log dolmasın)
        if current_position % 2000 == 0:
            print(f"  Konum: {current_position}px...")

        # --- SAYFA SONU KONTROLÜ ---
        if (total_height - current_position) < 800:
            # Sona yaklaştık, yeni ürünlerin yüklenmesi için biraz daha uzun bekle
            time.sleep(4)
            # Yükseklik güncellendi mi kontrol et
            new_total_height = driver.execute_script("return document.body.scrollHeight")
            if new_total_height == total_height:
                print("  ⏹️ Daha fazla içerik yüklenmiyor. İşlem bitti.")
                break

    # 3. TÜM VERİLERİ TOPLA
    print("\n📦 Tarama bitti, ekrandaki tüm ürünler çekiliyor...")
    products = driver.find_elements(By.CSS_SELECTOR, "li.column")
    all_products = []

    print(f"  -> Toplam {len(products)} adet ürün bulundu.")

    for p in products:
        try:
            try: title = p.find_element(By.CLASS_NAME, "productName").text.strip()
            except: continue 

            try: price = p.find_element(By.CLASS_NAME, "newPrice").text.strip().replace("\n", "")
            except: price = "Fiyat Yok"

            try: link = p.find_element(By.TAG_NAME, "a").get_attribute("href")
            except: link = ""

            all_products.append([title, price, link])
        except: continue

except Exception as e:
    print(f"❌ Kritik Hata: {e}")

finally:
    # Tarayıcıyı kapat
    try:
        driver.quit()
        print("🛑 Tarayıcı kapatıldı.")
    except: pass

    # 4. KAYDET
    if all_products:
        # Dosyayı scriptin olduğu yere kaydeder
        file_path = BASE_DIR / "n11.csv"
        
        try:
            with open(file_path, "w", newline="", encoding="utf-8-sig") as file:
                writer = csv.writer(file)
                writer.writerow(["Ürün Adı", "Fiyat", "Link"])
                for row in all_products:
                    writer.writerow(row)

            print(f"\n✅ İŞLEM TAMAMLANDI!")
            print(f"📂 Toplam {len(all_products)} ürün kaydedildi.")
            print(f"📄 Dosya: {file_path}")
        except Exception as e:
            print(f"❌ Dosya yazma hatası: {e}")
    else:
        print("\n⚠️ Hiçbir ürün bulunamadı.")