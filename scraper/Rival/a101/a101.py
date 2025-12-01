import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
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

print("A101 Scraper (Görsele Göre Revize) Başlatılıyor...")
driver = uc.Chrome(options=options)

try:
    all_products = []
    page = 1
    MAX_PAGES = 20 # İstersen artır

    while page <= MAX_PAGES:
        
        # 1. SAYFAYA GİT
        url = f"https://www.a101.com.tr/liste/haftanin-cok-satanlari/?page={page}"
        print(f"\n--- Gidiliyor: Sayfa {page} ---")
        driver.get(url)
        
        time.sleep(random.uniform(5, 7))

        # --- POP-UP TEMİZLİĞİ ---
        if page == 1:
            try:
                driver.find_element(By.ID, "CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll").click()
                print("Çerezler kabul edildi.")
            except: pass
            
            try: driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
            except: pass
            
            try: driver.find_element(By.TAG_NAME, "body").click()
            except: pass

        # 2. KAYDIR (Lazy Load Resimler İçin)
        for i in range(3):
            driver.execute_script(f"window.scrollTo(0, document.body.scrollHeight * {i/3});")
            time.sleep(1.5)

        # 3. ÜRÜNLERİ BUL (GÖRSELE GÖRE YENİ YÖNTEM)
        # Görselde en dıştaki kapsayıcıda "product-container" sınıfı var.
        # Bu sınıfı hedefleyip içindeki h3'e gideceğiz.
        
        product_cards = driver.find_elements(By.CLASS_NAME, "product-container")
        
        if len(product_cards) == 0:
            print("❌ Bu sayfada ürün bulunamadı. Liste sonuna gelinmiş olabilir.")
            break

        print(f"-> Bu sayfada {len(product_cards)} ürün kartı bulundu.")

        for card in product_cards:
            try:
                # 1. Başlık (Görseldeki h3 etiketi)
                # h3 etiketi kartın içinde derinlerde ama find_element ile direkt bulabiliriz.
                try:
                    title_el = card.find_element(By.TAG_NAME, "h3")
                    title = title_el.text.strip()
                    # Eğer metin boşsa, görseldeki 'title' özelliğini (attribute) al
                    if not title:
                        title = title_el.get_attribute("title")
                except:
                    title = "İsim Bulunamadı"

                # 2. Link (Görseldeki 'a' etiketi)
                try:
                    link_el = card.find_element(By.TAG_NAME, "a")
                    link = link_el.get_attribute("href")
                except:
                    link = ""

                # 3. Fiyat
                # Fiyat görselde açık değil ama genellikle kartın içinde 'div'lerde yazar.
                # Kartın tüm metnini alıp içinden 'TL' olanı cımbızla çekelim (En garantisi)
                price = "Fiyat Sepette"
                try:
                    card_text = card.text.split('\n')
                    for line in card_text:
                        if "TL" in line:
                            price = line.strip()
                            break
                except: pass

                all_products.append([title, price, link])
                
            except:
                continue
        
        print(f"-> Toplam Toplanan: {len(all_products)}")
        page += 1

    driver.quit()

    # 4. KAYDET
    folder_path = r"C:\Users\darks\OneDrive\Masaüstü\trend_takip\scraper\Rival\a101"
    os.makedirs(folder_path, exist_ok=True)
    file_path = os.path.join(folder_path, "a101.csv")

    with open(file_path, "w", newline="", encoding="utf-8-sig") as file:
        writer = csv.writer(file)
        writer.writerow(["Ürün Adı", "Fiyat", "Link"])
        for row in all_products:
            writer.writerow(row)

    print(f"\n✅ İŞLEM TAMAMLANDI!")
    print(f"Toplam {len(all_products)} ürün kaydedildi.")
    print(f"Dosya: {file_path}")

except Exception as e:
    print(f"Hata: {e}")
    try: driver.quit()
    except: pass