import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time
import csv
import random
from pathlib import Path

# --- DİNAMİK YOL AYARLARI ---
BASE_DIR = Path(__file__).resolve().parent
SCREENSHOT_DIR = BASE_DIR / "debug_carrefour"
SCREENSHOT_DIR.mkdir(exist_ok=True)

# --- AYARLAR ---
options = uc.ChromeOptions()
# CarrefourSA için kritik güncelleme: --headless=new
options.add_argument("--headless=new") 
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--start-maximized")
options.add_argument("--window-size=1920,1080") # Headless modda boyutu sabitlemek önemlidir
options.add_argument("--disable-notifications")
options.add_argument("--disable-popup-blocking")
# Gerçekçi User-Agent
options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

print("🚀 CarrefourSA Scraper (Gelişmiş Mod) Başlatılıyor...")
driver = uc.Chrome(options=options)
wait = WebDriverWait(driver, 15)

try:
    all_products = []
    target_count = 500
    current_page = 0
    MAX_RETRY = 3 # Aynı sayfayı kaç kez denesin

    while len(all_products) < target_count:
        
        url = f"https://www.carrefoursa.com/cok-satanlar/c/9124?q=%3AbestSeller&page={current_page}"
        print(f"\n--- Gidiliyor: Sayfa {current_page + 1} ---")
        driver.get(url)
        
        # Sayfa yüklenmesi için dinamik bekleme
        time.sleep(random.uniform(5, 8))

        # --- ÇEREZ GEÇME ---
        try:
            # En yaygın buton ID'leri
            buttons = ["onetrust-accept-btn-handler", "btn-accept-all", "close-modal"]
            for btn_id in buttons:
                try: driver.find_element(By.ID, btn_id).click()
                except: pass
            
            # ESC tuşu ile kapatma (garanti olsun)
            driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
        except: pass

        # --- KAYDIRMA (Lazy Load tetikleme) ---
        print("⬇️ Resimlerin yüklenmesi için kaydırılıyor...")
        for i in range(1, 4):
            driver.execute_script(f"window.scrollTo(0, document.body.scrollHeight * {i/4});")
            time.sleep(1)

        # --- ÜRÜNLERİ BUL (ÇOKLU SEÇİCİ) ---
        # CarrefourSA bazen yapıyı değiştirir, bu liste en yaygın kapsayıcıları içerir
        possible_selectors = [
            "li.product-listing-item",       # Klasik yapı
            ".product_list_item",            # Alternatif
            "div.product-card",              # Modern yapı
            ".item-product-card",            # Bazen kullanılan
            "ul.product-listing li"          # Liste bazlı
        ]

        products = []
        used_selector = ""
        
        print("🔍 Ürünler aranıyor...")
        for selector in possible_selectors:
            found = driver.find_elements(By.CSS_SELECTOR, selector)
            if len(found) > 0:
                products = found
                used_selector = selector
                print(f"✅ Seçici çalıştı: '{selector}' -> {len(found)} adet bulundu.")
                break
        
        # --- HATA ANALİZİ (0 Ürün Geldiyse) ---
        if len(products) == 0:
            print("❌ HATA: Ürün bulunamadı.")
            
            # Sayfanın ekran görüntüsünü al
            shot_path = SCREENSHOT_DIR / f"hata_sayfa_{current_page}.png"
            driver.save_screenshot(str(shot_path))
            print(f"📸 Hata görüntüsü kaydedildi: {shot_path}")
            
            # Eğer kaynak kodda "robot" veya "captcha" geçiyorsa
            page_source = driver.page_source.lower()
            if "verify you are human" in page_source or "captcha" in page_source:
                print("⚠️ KRİTİK: Bot korumasına (Cloudflare/WAF) takıldık.")
                break
            
            # Son sayfaya gelmiş olabiliriz
            if current_page > 0:
                print("⏹️ Muhtemelen sayfa sonuna gelindi.")
                break
            else:
                # İlk sayfada bile bulamadıysa sorun büyüktür
                break

        # --- VERİLERİ ÇEK ---
        added_on_this_page = 0
        for p in products:
            if len(all_products) >= target_count: break
            
            try:
                # Ürün Adı
                title = ""
                try: title = p.find_element(By.CSS_SELECTOR, ".item-name").text.strip()
                except: 
                    try: title = p.find_element(By.TAG_NAME, "h3").text.strip()
                    except: pass
                
                if not title: continue # İsimsiz ürünü geç

                # Fiyat (Karmaşık yapıdan temizleme)
                price = "Fiyat Yok"
                try: 
                    # Carrefour fiyatları bazen parça parça span'larda olur, tüm metni alıp temizleyelim
                    raw_price = p.find_element(By.CSS_SELECTOR, ".item-price").text
                    price = raw_price.replace("\n", "").strip()
                except: pass

                # Link
                link = ""
                try: link = p.find_element(By.CSS_SELECTOR, "a").get_attribute("href")
                except: pass

                # Marka (Varsa)
                brand = "-"
                try: brand = p.find_element(By.CSS_SELECTOR, ".item-brand").text.strip()
                except: pass

                all_products.append([brand, title, price, link])
                added_on_this_page += 1

            except Exception as e:
                continue
        
        print(f"  -> Sayfadan eklenen: {added_on_this_page}")
        print(f"  -> Toplam: {len(all_products)}/{target_count}")
        
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