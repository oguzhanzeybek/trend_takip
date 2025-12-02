import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
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
options.add_argument("--no-sandbox") # Sandbox güvenlik katmanını aşar (Linux için gerekli)
options.add_argument("--disable-dev-shm-usage") # Bellek hatalarını önler
options.add_argument("--start-maximized")
options.add_argument("--disable-notifications")
options.add_argument("--disable-popup-blocking")
options.page_load_strategy = 'eager'

print("🚀 A101 Scraper (Headless & Dinamik) Başlatılıyor...")

# Headless modda undetected_chromedriver bazen sürüm hatası verebilir,
# bu yüzden version_main parametresi opsiyonel olarak kullanılabilir ama şimdilik standart bırakıyoruz.
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
        
        # Bekleme süresi
        time.sleep(random.uniform(5, 7))

        # --- POP-UP TEMİZLİĞİ ---
        if page == 1:
            try:
                driver.find_element(By.ID, "CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll").click()
                print("  🍪 Çerezler kabul edildi.")
            except: pass
            
            try: driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
            except: pass
            
            try: driver.find_element(By.TAG_NAME, "body").click()
            except: pass

        # 2. KAYDIR (Lazy Load Resimler İçin)
        for i in range(3):
            driver.execute_script(f"window.scrollTo(0, document.body.scrollHeight * {i/3});")
            time.sleep(1.5)

        # 3. ÜRÜNLERİ BUL
        product_cards = driver.find_elements(By.CLASS_NAME, "product-container")
        
        if len(product_cards) == 0:
            print("❌ Bu sayfada ürün bulunamadı. Liste sonuna gelinmiş olabilir.")
            break

        print(f"  -> Bu sayfada {len(product_cards)} ürün kartı bulundu.")

        for card in product_cards:
            try:
                # 1. Başlık
                try:
                    title_el = card.find_element(By.TAG_NAME, "h3")
                    title = title_el.text.strip()
                    if not title:
                        title = title_el.get_attribute("title")
                except:
                    title = "İsim Bulunamadı"

                # 2. Link
                try:
                    link_el = card.find_element(By.TAG_NAME, "a")
                    link = link_el.get_attribute("href")
                except:
                    link = ""

                # 3. Fiyat
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
        
        print(f"  -> Toplam Toplanan: {len(all_products)}")
        page += 1

except Exception as e:
    print(f"❌ Kritik Hata: {e}")

finally:
    # Hata olsa da olmasa da tarayıcıyı kapat
    try:
        driver.quit()
        print("🛑 Tarayıcı kapatıldı.")
    except: pass

    # 4. KAYDET (Finally bloğunda, veri varsa kaydeder)
    if all_products:
        # Dosyayı scriptin olduğu yere kaydeder
        file_path = BASE_DIR / "a101.csv"

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
            print(f"❌ Kayıt hatası: {e}")
    else:
        print("\n⚠️ Hiçbir ürün bulunamadı, kayıt yapılmadı.")