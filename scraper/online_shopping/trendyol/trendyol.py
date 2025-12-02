import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
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
options.add_argument("--headless=new") # Trendyol için 'new' headless modu daha iyidir
options.add_argument("--no-sandbox") # Sandbox güvenlik katmanını aşar
options.add_argument("--disable-dev-shm-usage") # Bellek hatalarını önler
options.add_argument("--start-maximized")
options.add_argument("--window-size=1920,1080") # Elemanların görünür olması için şart
options.add_argument("--disable-notifications")
options.add_argument("--disable-popup-blocking")
options.page_load_strategy = 'eager'

print("🚀 Trendyol Scraper (Headless & Dinamik) Başlatılıyor...")
driver = uc.Chrome(options=options)

try:
    # Hedef Ana URL
    base_url = "https://www.trendyol.com/cok-satanlar?type=popular"
    
    # 1. İlk açılış ve Kategori İsimlerini Hafızaya Alma
    print(f"🌐 Ana sayfaya gidiliyor: {base_url}")
    driver.get(base_url)
    time.sleep(5)

    # Pop-up kapatma
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
            # "Popüler Ürünler" zaten ana sayfa, onu da alabilir veya hariç tutabilirsin.
            if txt and txt not in category_names:
                category_names.append(txt)
        
        print(f"  ✅ Hafızaya alınan kategoriler ({len(category_names)}): {category_names}")
                
    except Exception as e:
        print("  ⚠️ Kategoriler alınamadı, sadece ana sayfa taranacak.")
        category_names = ["Popüler Ürünler"]

    # 3. KATEGORİLERİ GEZ (HER SEFERİNDE ANA SAYFAYA DÖNEREK)
    all_products = []

    for target_cat_name in category_names:
        print(f"\n--- Sıradaki Hedef: {target_cat_name} ---")
        
        try:
            # KRİTİK NOKTA: Her kategori öncesi sayfayı resetle (Ana sayfaya git)
            if target_cat_name != "Popüler Ürünler":
                driver.get(base_url)
                time.sleep(3) # Sayfanın oturmasını bekle

                # Butonu tekrar bul
                current_buttons = driver.find_elements(By.CSS_SELECTOR, "button.category-pill")
                button_found = False

                for btn in current_buttons:
                    if btn.text.strip() == target_cat_name:
                        # Butonu bulduk, tıkla
                        driver.execute_script("arguments[0].click();", btn)
                        button_found = True
                        print(f"  🖱️ '{target_cat_name}' butonuna tıklandı.")
                        break 
                
                if not button_found:
                    print(f"  ⚠️ Uyarı: '{target_cat_name}' butonu bu sayfada bulunamadı.")
                    continue

                time.sleep(3) # Ürünlerin yüklenmesi için bekle
            
            # Kaydırma (Scroll)
            SCROLL_COUNT = 4 
            for i in range(SCROLL_COUNT):
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1.5)

            # Ürünleri Topla
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
    # Tarayıcıyı kapat
    try:
        driver.quit()
        print("🛑 Tarayıcı kapatıldı.")
    except: pass

    # 4. DOSYA KAYDETME
    if all_products:
        # Dosyayı scriptin olduğu yere kaydeder
        file_path = BASE_DIR / "trendyol_kategorili_urunler.csv"
        
        try:
            with open(file_path, "w", newline="", encoding="utf-8-sig") as file:
                writer = csv.writer(file)
                writer.writerow(["Kategori", "Marka", "Ürün Adı", "Fiyat", "Link"])
                for row in all_products:
                    writer.writerow(row)

            print(f"\n✅ İŞLEM TAMAMLANDI!")
            print(f"📂 Toplam {len(all_products)} ürün kaydedildi.")
            print(f"📄 Dosya: {file_path}")
        except Exception as e:
            print(f"❌ Dosya yazma hatası: {e}")
    else:
        print("\n⚠️ Hiçbir veri çekilemedi.")