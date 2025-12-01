import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys # ESC tuşu için
import time
import csv
import os
import random

# --- AYARLAR ---
options = uc.ChromeOptions()
options.add_argument("--start-maximized")
options.add_argument("--disable-notifications")
options.add_argument("--disable-popup-blocking")
options.page_load_strategy = 'eager'

print("CarrefourSA Scraper Başlatılıyor...")
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
        
        # İlk sayfa açılışında pop-up temizliği yap (Sadece 1 kere yeterli olabilir ama her sayfada denemek güvenlidir)
        time.sleep(6) 

        # --- POP-UP TEMİZLİĞİ (GÜNCELLENDİ) ---
        if current_page == 0:
            print("Pop-up kontrolü yapılıyor...")
            try:
                # 1. Yöntem: ESC Tuşuna bas (Genelde tüm pop-up'ları kapatır)
                driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
                time.sleep(1)
            except: pass

            try:
                # 2. Yöntem: Çerezleri Kabul Et
                driver.find_element(By.ID, "onetrust-accept-btn-handler").click()
                print("Çerezler geçildi.")
                time.sleep(1)
            except: pass

            try:
                # 3. Yöntem: Teslimat/Konum Pop-up'ı Kapatma Butonu (Genel Classlar)
                # CarrefourSA'da bazen 'close' ikonlu butonlar olur
                close_buttons = driver.find_elements(By.CSS_SELECTOR, ".close-modal, .modal-close, button[aria-label='Close']")
                for btn in close_buttons:
                    if btn.is_displayed():
                        btn.click()
                        print("Bir pop-up kapatıldı.")
            except: pass
            
            # Sayfanın kendine gelmesi için tekrar ESC
            try: driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
            except: pass

        # 2. KAYDIR
        for i in range(3):
            driver.execute_script(f"window.scrollTo(0, document.body.scrollHeight * {i/3});")
            time.sleep(1.5)
        
        # 3. ÜRÜNLERİ BUL
        products = driver.find_elements(By.CSS_SELECTOR, "li.product-listing-item")
        
        if len(products) == 0:
            print("❌ Bu sayfada ürün bulunamadı. (Pop-up engellemiş olabilir mi?)")
            # Pop-up yüzünden göremediyse bir şans daha verip ESC basıp tekrar dene
            driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
            time.sleep(2)
            products = driver.find_elements(By.CSS_SELECTOR, "li.product-listing-item")
            if len(products) == 0:
                print("Hala ürün yok, işlem bitiriliyor.")
                break
            
        print(f"-> Bu sayfada {len(products)} ürün var.")

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
        
        print(f"-> Toplam: {len(all_products)}/{target_count}")
        current_page += 1

    driver.quit()

    # 4. KAYDET (Rival Klasörü)
    folder_path = r"C:\Users\darks\OneDrive\Masaüstü\trend_takip\scraper\Rival\CarrefourSA"
    os.makedirs(folder_path, exist_ok=True)
    file_path = os.path.join(folder_path, "carrefoursa.csv")

    with open(file_path, "w", newline="", encoding="utf-8-sig") as file:
        writer = csv.writer(file)
        writer.writerow(["Marka", "Ürün Adı", "Fiyat", "Link"])
        for row in all_products:
            writer.writerow(row)

    print(f"\n✅ İŞLEM TAMAMLANDI!")
    print(f"Toplam {len(all_products)} ürün kaydedildi.")
    print(f"Dosya: {file_path}")

except Exception as e:
    print(f"Hata: {e}")
    try: driver.quit()
    except: pass