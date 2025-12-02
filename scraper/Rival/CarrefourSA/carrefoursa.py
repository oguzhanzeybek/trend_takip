import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys # ESC tuşu için
import time
import csv
import random
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
options.add_argument("--disable-notifications")
options.add_argument("--disable-popup-blocking")
options.page_load_strategy = 'eager'

print("🚀 CarrefourSA Scraper (Headless & Dinamik) Başlatılıyor...")
driver = uc.Chrome(options=options)

try:
    all_products = []
    target_count = 200
    current_page = 0

    while len(all_products) < target_count:
        
        # 1. SAYFAYA GİT
        url = f"https://www.carrefoursa.com/cok-satanlar/c/9124?q=%3AbestSeller&page={current_page}"
        print(f"\n--- Gidiliyor: Sayfa {current_page + 1} ---")
        driver.get(url)
        
        # Bekleme ve Pop-up Yönetimi
        time.sleep(6) 

        # --- POP-UP TEMİZLİĞİ ---
        if current_page == 0:
            print("  Pop-up kontrolü yapılıyor...")
            try:
                driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
                time.sleep(1)
            except: pass

            try:
                driver.find_element(By.ID, "onetrust-accept-btn-handler").click()
                print("  🍪 Çerezler geçildi.")
                time.sleep(1)
            except: pass

            try:
                close_buttons = driver.find_elements(By.CSS_SELECTOR, ".close-modal, .modal-close, button[aria-label='Close']")
                for btn in close_buttons:
                    if btn.is_displayed():
                        btn.click()
                        print("  Modals kapatıldı.")
            except: pass
            
            try: driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
            except: pass

        # 2. KAYDIR
        for i in range(3):
            driver.execute_script(f"window.scrollTo(0, document.body.scrollHeight * {i/3});")
            time.sleep(1.5)
        
        # 3. ÜRÜNLERİ BUL
        products = driver.find_elements(By.CSS_SELECTOR, "li.product-listing-item")
        
        if len(products) == 0:
            print("❌ Bu sayfada ürün bulunamadı. (Tekrar deneniyor...)")
            driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
            time.sleep(2)
            products = driver.find_elements(By.CSS_SELECTOR, "li.product-listing-item")
            if len(products) == 0:
                print("❌ Hala ürün yok, işlem bitiriliyor.")
                break
            
        print(f"  -> Bu sayfada {len(products)} ürün var.")

        for p in products:
            if len(all_products) >= target_count:
                break
            try:
                # Veri Çekme
                try: title = p.find_element(By.CSS_SELECTOR, ".item-name").text.strip()
                except: continue

                try: price = p.find_element(By.CSS_SELECTOR, ".item-price").text.strip().replace("\n", " ")
                except: price = "Fiyat Yok"

                try: link = p.find_element(By.TAG_NAME, "a").get_attribute("href")
                except: link = ""

                try: brand = p.find_element(By.CSS_SELECTOR, ".item-brand").text.strip()
                except: brand = "-"

                all_products.append([brand, title, price, link])
            except:
                continue
        
        print(f"  -> Toplam: {len(all_products)}/{target_count}")
        current_page += 1

except Exception as e:
    print(f"❌ Kritik Hata: {e}")

finally:
    # 4. KAPAT VE KAYDET
    try:
        driver.quit()
        print("🛑 Tarayıcı kapatıldı.")
    except: pass

    if all_products:
        # Dosyayı scriptin olduğu yere kaydeder
        file_path = BASE_DIR / "carrefoursa.csv"
        
        try:
            with open(file_path, "w", newline="", encoding="utf-8-sig") as file:
                writer = csv.writer(file)
                writer.writerow(["Marka", "Ürün Adı", "Fiyat", "Link"])
                for row in all_products:
                    writer.writerow(row)

            print(f"\n✅ İŞLEM TAMAMLANDI!")
            print(f"📂 Toplam {len(all_products)} ürün kaydedildi.")
            print(f"📄 Dosya: {file_path}")
        except Exception as e:
            print(f"❌ Dosya yazma hatası: {e}")
    else:
        print("\n⚠️ Hiçbir veri çekilemedi.")