import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
import time
import csv
import os
import random
import concurrent.futures
import threading # <-- KİLİT İÇİN GEREKLİ

# --- AYARLAR ---
MAX_WORKERS = 3 
SAVE_PATH = r"C:\Users\darks\OneDrive\Masaüstü\trend_takip\scraper\online_shopping\alibaba"

# Tarayıcı açılışlarını sıraya koymak için kilit (Mutex)
driver_init_lock = threading.Lock()

def get_chrome_options():
    options = uc.ChromeOptions()
    options.add_argument("--headless=new") 
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-notifications")
    options.add_argument("--lang=tr-TR")
    # Resimleri kapatarak hız kazanıyoruz
    options.add_argument('--blink-settings=imagesEnabled=false') 
    return options

# 1. ADIM: KATEGORİ LİNKLERİNİ TOPLA (Burası tek sefer çalışır)
def get_all_category_links():
    print("📋 Kategori listesi hazırlanıyor (Ana bot başlatılıyor)...")
    
    # Ana botu başlatırken de kilit kullanalım ne olur ne olmaz
    with driver_init_lock:
        driver = uc.Chrome(options=get_chrome_options())
        
    links_data = []
    
    try:
        driver.get("https://sale.alibaba.com/p/rank/list.html")
        time.sleep(8)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        
        # Sadece resimli (gerçek) kutuları bul
        all_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/p/rank/detail']")
        
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
        print(f"Link toplama hatası: {e}")
    finally:
        driver.quit()
    
    return links_data

# 2. ADIM: İŞÇİ FONKSİYONU
def process_batch(category_list, worker_id):
    # --- KRİTİK DÜZELTME BURADA ---
    # Tarayıcıyı oluşturma işlemini "Kilit" içine alıyoruz.
    # Bu sayede Bot-1 tarayıcıyı açarken, Bot-2 ve Bot-3 kapıda bekler.
    # Dosya çakışması engellenir.
    
    print(f"⌛ Bot-{worker_id} tarayıcısını başlatmak için sıra bekliyor...")
    
    with driver_init_lock:
        try:
            driver = uc.Chrome(options=get_chrome_options())
            print(f"🟢 Bot-{worker_id} tarayıcısını başarıyla açtı!")
            # Dosya sistemi rahatlasın diye minik bir bekleme
            time.sleep(3) 
        except Exception as e:
            print(f"❌ Bot-{worker_id} başlatılamadı: {e}")
            return []

    # --- ARTIK PARALEL ÇALIŞABİLİRLER ---
    print(f"🚀 Bot-{worker_id} işe başladı ({len(category_list)} kategori)")
    
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
                if count >= 20: break
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
            print(f"   [Bot-{worker_id}] Hata ({cat_name}): {e}")
            continue
            
    driver.quit()
    print(f"🏁 Bot-{worker_id} görevini tamamladı.")
    return batch_results

# --- ANA ÇALIŞTIRMA BLOKU ---
if __name__ == "__main__":
    # Eğer önceden kalan kilitli dosyalar varsa temizlemek gerekebilir ama
    # Kilit mantığı bunu çözecektir.
    
    start_time = time.time()
    
    # 1. Linkleri Al
    all_categories = get_all_category_links()
    print(f"✅ Toplam {len(all_categories)} kategori bulundu. İşlem dağıtılıyor...")
    
    if not all_categories:
        exit()

    # 2. Listeyi Böl
    chunk_size = len(all_categories) // MAX_WORKERS + 1
    chunks = [all_categories[i:i + chunk_size] for i in range(0, len(all_categories), chunk_size)]
    
    # 3. Paralel Başlat
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
                print(f"Bir bot çöktü: {e}")

    # 4. Kaydet
    os.makedirs(SAVE_PATH, exist_ok=True)
    file_path = os.path.join(SAVE_PATH, "alibaba.csv")
    
    with open(file_path, "w", newline="", encoding="utf-8-sig") as file:
        writer = csv.writer(file)
        writer.writerow(["Kategori", "Ürün Başlığı", "Fiyat", "Min. Sipariş", "Link"])
        for row in all_final_data:
            writer.writerow(row)

    duration = time.time() - start_time
    print(f"\n🚀 İŞLEM TAMAMLANDI!")
    print(f"Süre: {int(duration)} saniye")
    print(f"Toplam Veri: {len(all_final_data)}")
    print(f"Dosya: {file_path}")