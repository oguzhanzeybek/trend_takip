import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
import time
import csv
import os
import random
import concurrent.futures
import threading
from pathlib import Path

# --- DİNAMİK YOL AYARLARI ---
BASE_DIR = Path(__file__).resolve().parent
SAVE_PATH = BASE_DIR

# --- AYARLAR ---
MAX_WORKERS = 1 # UC ile çoklu işlem risklidir, 1'de kalması en sağlıklısı
driver_init_lock = threading.Lock()

def get_driver():
    """
    GitHub Actions ve Linux sunucular için optimize edilmiş driver ayarları.
    """
    options = uc.ChromeOptions()
    
    # --- KRİTİK SUNUCU AYARLARI ---
    options.add_argument("--headless=new") # Yeni nesil headless mod
    options.add_argument("--no-sandbox") # Root yetkisiyle çalışan runner'lar için şart
    options.add_argument("--disable-dev-shm-usage") # Bellek çökmesini önler
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--blink-settings=imagesEnabled=false") # Resimleri kapat
    options.add_argument("--lang=tr-TR")

    # --- DRIVER BAŞLATMA ---
    # use_subprocess=False ve headless=True sunucu için çok önemlidir.
    driver = uc.Chrome(
        options=options,
        headless=True, # Kütüphanenin kendi headless modu
        use_subprocess=False, # GitHub Actions'ta kilitlenmeyi önler
        version_main=None # Otomatik en son sürümü bulur
    )
    
    return driver

# 1. ADIM: KATEGORİ LİNKLERİNİ TOPLA
def get_all_category_links():
    print("📋 Kategori listesi hazırlanıyor (Ana bot başlatılıyor)...")
    
    links_data = []
    driver = None
    
    try:
        # Kilidi burada kullanıyoruz
        with driver_init_lock:
            driver = get_driver()
        
        # Sayfa yükleme zaman aşımı ayarı (isteğe bağlı ama güvenli)
        driver.set_page_load_timeout(60)

        print("🌍 Alibaba Rank sayfasına gidiliyor...")
        driver.get("https://sale.alibaba.com/p/rank/list.html")
        time.sleep(8)
        
        # Sayfayı aşağı kaydır
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        
        # Linkleri topla
        all_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/p/rank/detail']")
        print(f"🔎 Sayfada {len(all_links)} potansiyel link bulundu.")

        seen_urls = set()
        for link in all_links:
            try:
                # Sadece görsel içeren (gerçek kategori) kutuları al
                if len(link.find_elements(By.TAG_NAME, "img")) > 0:
                    url = link.get_attribute("href")
                    text = link.text.strip().split("\n")[0]
                    if not text: text = "Kategori"
                    
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        links_data.append((text, url))
            except: continue
            
    except Exception as e:
        print(f"❌ Link toplama hatası: {e}")
    finally:
        if driver:
            try:
                driver.quit()
            except: pass
    
    return links_data

# 2. ADIM: İŞÇİ FONKSİYONU
def process_batch(category_list, worker_id):
    print(f"⌛ Bot-{worker_id} tarayıcı sırası bekliyor...")
    
    driver = None
    with driver_init_lock:
        try:
            driver = get_driver()
            print(f"🟢 Bot-{worker_id} tarayıcısı AÇILDI.")
            time.sleep(2)
        except Exception as e:
            print(f"❌ Bot-{worker_id} tarayıcı açılış hatası: {e}")
            return []

    print(f"🚀 Bot-{worker_id} işleme başladı. ({len(category_list)} kategori)")
    
    batch_results = []
    
    for index, (cat_name, cat_url) in enumerate(category_list):
        print(f"   [Bot-{worker_id}] {index+1}/{len(category_list)}: {cat_name}")
        
        try:
            driver.get(cat_url)
            time.sleep(random.uniform(3, 5)) 

            # Kaydırma işlemi
            for _ in range(3):
                driver.execute_script("window.scrollBy(0, 1000);")
                time.sleep(1)

            cards = driver.find_elements(By.CLASS_NAME, "hugo4-pc-grid-item")
            
            count = 0
            for card in cards:
                if count >= 20: break # Her kategori için max 20 ürün
                try:
                    try: 
                        t_el = card.find_element(By.CSS_SELECTOR, ".subject span")
                        title = t_el.get_attribute("title") or t_el.text.strip()
                    except: title = "Başlık Yok"
                    
                    try: price = card.find_element(By.CLASS_NAME, "hugo4-product-price-area").text.strip()
                    except: price = "-"
                    
                    try: moq = card.find_element(By.CLASS_NAME, "moq-pc").text.strip()
                    except: moq = "-"
                    
                    try: 
                        if card.tag_name == 'a': link = card.get_attribute("href")
                        else: link = card.find_element(By.TAG_NAME, "a").get_attribute("href")
                    except: link = ""

                    # Veriyi ekle
                    batch_results.append([cat_name, title, price, moq, link])
                    count += 1
                except: continue
                
        except Exception as e:
            print(f"   ⚠️ [Bot-{worker_id}] Sayfa hatası ({cat_name}): {e}")
            continue
            
    # Temizlik
    if driver:
        try:
            driver.quit()
            print(f"🏁 Bot-{worker_id} kapatıldı.")
        except: pass

    return batch_results

# --- ANA ÇALIŞTIRMA ---
if __name__ == "__main__":
    
    start_time = time.time()
    
    # 1. Linkleri Al
    all_categories = get_all_category_links()
    print(f"✅ Toplam {len(all_categories)} kategori listesi hazır.")
    
    if not all_categories:
        print("❌ Hiç kategori bulunamadı, script sonlandırılıyor.")
        exit()

    # 2. İşleri Böl
    chunk_size = len(all_categories) // MAX_WORKERS + 1
    chunks = [all_categories[i:i + chunk_size] for i in range(0, len(all_categories), chunk_size)]
    
    # 3. Paralel Çalıştır
    all_final_data = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = []
        for i, chunk in enumerate(chunks):
            if chunk:
                futures.append(executor.submit(process_batch, chunk, i+1))
        
        for future in concurrent.futures.as_completed(futures):
            try:    
                data = future.result()
                all_final_data.extend(data)
            except Exception as e:
                print(f"❌ Bir thread çöktü: {e}")

    # 4. Kaydet
    file_path = SAVE_PATH / "alibaba.csv"
    
    try:
        with open(file_path, "w", newline="", encoding="utf-8-sig") as file:
            writer = csv.writer(file)
            writer.writerow(["Kategori", "Ürün Başlığı", "Fiyat", "Min. Sipariş", "Link"])
            for row in all_final_data:
                writer.writerow(row)

        duration = time.time() - start_time
        print(f"\n🎉 ALIBABA SCRAPER TAMAMLANDI!")
        print(f"⏱️  Süre: {int(duration)} saniye")
        print(f"📊 Toplam Veri: {len(all_final_data)}")
        print(f"💾 Dosya: {file_path}")
        
    except Exception as e:
        print(f"❌ Dosya kaydetme hatası: {e}")