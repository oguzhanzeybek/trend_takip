import sys
import time
import csv
import random
import concurrent.futures
import threading
from pathlib import Path
from selenium.webdriver.common.by import By

# --- 1. YOL AYARLARI ---
# Dosya Konumu: scraper/online_shopping/alibaba/alibaba.py
CURRENT_DIR = Path(__file__).resolve().parent
# Scraper kök dizinine çık (alibaba -> online_shopping -> scraper)
# DÜZELTME: 3 tane parent fazla geliyor, 2 tane yeterli.
ROOT_DIR = CURRENT_DIR.parent.parent

# Kök dizini sisteme ekle
sys.path.append(str(ROOT_DIR))

# --- 2. MERKEZİ DRIVER ÇAĞRISI ---
try:
    from core.driver_manager import get_chrome_driver
except ImportError:
    # Eğer yukarıdaki yol çalışmazsa (IDE vs. farklı çalıştırırsa) bir üstü dene
    # Ama normalde yukarıdaki ROOT_DIR doğru olmalı.
    sys.path.append(str(ROOT_DIR.parent))
    try:
        from scraper.core.driver_manager import get_chrome_driver
    except ImportError:
        # Son çare manuel import denemesi
        print("⚠️ Core modülü bulunamadı, yol ayarlarını kontrol edin.")
        raise

# --- AYARLAR ---
BASE_DIR = CURRENT_DIR
SAVE_PATH = BASE_DIR
MAX_WORKERS = 3 
driver_init_lock = threading.Lock() # Thread güvenliği için kilit

# 1. ADIM: KATEGORİ LİNKLERİNİ TOPLA
def get_all_category_links():
    print("📋 Kategori listesi hazırlanıyor (Ana bot başlatılıyor)...")
    
    links_data = []
    driver = None
    
    try:
        # Çakışmayı önlemek için driver açılışını kilitliyoruz
        with driver_init_lock:
            # MERKEZİ SİSTEMDEN DRIVER AL
            driver = get_chrome_driver()
        
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
    # Thread güvenliği için driver açarken kilit kullan
    with driver_init_lock:
        try:
            # MERKEZİ SİSTEMDEN DRIVER AL
            driver = get_chrome_driver()
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
        sys.exit()

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
            writer.writerows(all_final_data)

        duration = time.time() - start_time
        print(f"\n🎉 ALIBABA SCRAPER TAMAMLANDI!")
        print(f"⏱️  Süre: {int(duration)} saniye")
        print(f"📊 Toplam Veri: {len(all_final_data)}")
        print(f"💾 Dosya: {file_path}")
        
    except Exception as e:
        print(f"❌ Dosya kaydetme hatası: {e}")