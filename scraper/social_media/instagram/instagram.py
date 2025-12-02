from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
import csv
from pathlib import Path

# --- AYARLAR ---
def get_driver():
    options = Options()
    # --- KRİTİK GITHUB ACTIONS AYARLARI ---
    options.add_argument("--headless=new") # Ekransız Mod
    options.add_argument("--no-sandbox")   # Linux Güvenlik İzni
    options.add_argument("--disable-dev-shm-usage") # Hafıza Optimizasyonu
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-notifications")
    
    # HIZLANDIRMA TAKTİĞİ: 'eager'
    # Sayfanın tamamen bitmesini (tüm resimler vb.) beklemez, HTML gelince başlar.
    options.page_load_strategy = 'eager' 

    # Driver Kurulumu
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(60) # Maksimum 60 saniye bekle, yoksa hata verip geç
    return driver

# --- ANA İŞLEM ---
all_data = []
driver = None

try:
    driver = get_driver()
    
    for page_num in range(0, 9):  # 0'dan 8'e kadar (Toplam 9 sayfa)
        url = f"https://best-hashtags.com/new-hashtags.php?pageNum_tag={page_num}&totalRows_tag=1000"
        
        try:
            driver.get(url)
            time.sleep(2) # HTML'in oturması için kısa bekleme
        except:
            # Sayfa açılmazsa (timeout yerse) bu sayfayı atla, diğerine geç
            continue 

        soup = BeautifulSoup(driver.page_source, "html.parser")

        # Tablo içindeki satırları seç
        rows = soup.select("table.table.table-striped tbody tr")

        for row in rows:
            try:
                cols = row.find_all("td")
                if len(cols) == 3: 
                    hashtag_id = cols[0].get_text(strip=True)
                    hashtag = cols[1].get_text(strip=True)
                    count = cols[2].get_text(strip=True)
                    if hashtag: 
                        all_data.append([hashtag_id, hashtag, count])
            except:
                continue

except Exception as e:
    pass # Hata olsa bile sessiz kalıp eldeki veriyi kaydetmeyi dene

finally:
    if driver:
        driver.quit()

# --- DOSYA KAYIT (STANDART BLOK) ---
current_dir = Path(__file__).resolve().parent
output_filename = "instagram.csv"
output_path = current_dir / output_filename

if all_data:
    with open(output_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["ID", "Hashtag", "Count"])
        writer.writerows(all_data)
    print(f"✅ Dosya kaydedildi: {output_path} (Toplam: {len(all_data)})")
else:
    print(f"❌ Veri oluşmadığı için '{output_filename}' kaydedilemedi.")