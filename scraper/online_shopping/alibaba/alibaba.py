import sys
import time
import csv
import random
import concurrent.futures
import threading
from pathlib import Path
from selenium.webdriver.common.by import By

CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parent.parent

sys.path.append(str(ROOT_DIR))

try:
    from core.driver_manager import get_chrome_driver
except ImportError:
    sys.path.append(str(ROOT_DIR.parent))
    try:
        from scraper.core.driver_manager import get_chrome_driver
    except ImportError:
        print("⚠️ Core modülü bulunamadı, yol ayarlarını kontrol edin.")
        raise

BASE_DIR = CURRENT_DIR
SAVE_PATH = BASE_DIR
MAX_WORKERS = 1
driver_init_lock = threading.Lock() # Thread güvenliği için kilit

def get_all_category_links():
    print("📋 Kategori listesi hazırlanıyor (Ana bot başlatılıyor)...")
    
    links_data = []
    driver = None
    
    try:
        with driver_init_lock:
            driver = get_chrome_driver()
        
        driver.set_page_load_timeout(60)

        print("🌍 Alibaba Rank sayfasına gidiliyor...")
        driver.get("https://sale.alibaba.com/p/rank/list.html")
        time.sleep(8)
        
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        
        all_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/p/rank/detail']")
        print(f"🔎 Sayfada {len(all_links)} potansiyel link bulundu.")

        seen_urls = set()
        for link in all_links:
            try:
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

def process_batch(category_list, worker_id):
    print(f"⌛ Bot-{worker_id} tarayıcı sırası bekliyor...")
    
    driver = None
    with driver_init_lock:
        try:
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

                    batch_results.append([cat_name, title, price, moq, link])
                    count += 1
                except: continue
                
        except Exception as e:
            print(f"   ⚠️ [Bot-{worker_id}] Sayfa hatası ({cat_name}): {e}")
            continue
            
    if driver:
        try:
            driver.quit()
            print(f"🏁 Bot-{worker_id} kapatıldı.")
        except: pass

    return batch_results

# ==========================================
# OTO-İNDEKSLEME FONKSİYONU
# ==========================================
def auto_add_index_to_csvs():
    import os
    import csv
    
    folder_path = os.path.dirname(os.path.abspath(__file__))
    csv_files = [f for f in os.listdir(folder_path) if f.endswith('.csv')]
    
    print(f"\n🔄 İndeksleme Başladı: {folder_path} klasöründeki dosyalar taranıyor...")

    for filename in csv_files:
        file_path = os.path.join(folder_path, filename)
        rows = []
        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.reader(f)
                rows = list(reader)
            
            if not rows: continue

            header = rows[0]
            data = rows[1:]

            if header and str(header[0]).lower() == "rank":
                print(f"  Start ⏩ {filename} (Zaten indeksli)")
                continue

            new_header = ["Rank"] + header
            new_data = []
            
            for index, row in enumerate(data, 1):
                new_data.append([index] + row)

            with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(new_header)
                writer.writerows(new_data)
            
            print(f"  ✅ İndeks Eklendi: {filename}")

        except Exception as e:
            print(f"  ❌ Hata ({filename}): {e}")

if __name__ == "__main__":
    
    start_time = time.time()
    
    all_categories = get_all_category_links()
    print(f"✅ Toplam {len(all_categories)} kategori listesi hazır.")
    
    if not all_categories:
        print("❌ Hiç kategori bulunamadı, script sonlandırılıyor.")
        sys.exit()

    chunk_size = len(all_categories) // MAX_WORKERS + 1
    chunks = [all_categories[i:i + chunk_size] for i in range(0, len(all_categories), chunk_size)]
    
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

    file_path = SAVE_PATH / "alibaba.csv"
    
    try:
        with open(file_path, "w", newline="", encoding="utf-8-sig") as file:
            writer = csv.writer(file)
            # Header: Başa Rank Eklendi
            writer.writerow(["Rank", "Kategori", "Ürün Başlığı", "Fiyat", "Min. Sipariş", "Link"])
            
            # Veriler enumerate ile numaralandırılarak yazılıyor
            for i, row in enumerate(all_final_data, 1):
                writer.writerow([i] + row)

        duration = time.time() - start_time
        print(f"\n🎉 ALIBABA SCRAPER TAMAMLANDI!")
        print(f"⏱️  Süre: {int(duration)} saniye")
        print(f"📊 Toplam Veri: {len(all_final_data)}")
        print(f"💾 Dosya: {file_path}")
        
    except Exception as e:
        print(f"❌ Dosya kaydetme hatası: {e}")

    # İşlem bittikten sonra klasör taraması yap
    auto_add_index_to_csvs()