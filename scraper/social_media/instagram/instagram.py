from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
import csv
import os  # <--- EKLENDI: Dosya yolu işlemleri için gerekli

# Chrome ayarları
options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

all_data = []

try:
    for page_num in range(0, 9):  # 0'dan 8'e kadar
        url = f"https://best-hashtags.com/new-hashtags.php?pageNum_tag={page_num}&totalRows_tag=1000"
        print(f"📄 Sayfa yükleniyor: {url}")
        driver.get(url)
        time.sleep(2)  # sayfanın yüklenmesini bekle

        soup = BeautifulSoup(driver.page_source, "html.parser")

        # Tablo içindeki satırları seç
        rows = soup.select("table.table.table-striped tbody tr")

        for row in rows:
            cols = row.find_all("td")
            if len(cols) == 3: 
                hashtag_id = cols[0].get_text(strip=True)
                hashtag = cols[1].get_text(strip=True)
                count = cols[2].get_text(strip=True)
                if hashtag: 
                    all_data.append([hashtag_id, hashtag, count])

    # CSV'ye yaz
    if all_data:
        # --- DÜZELTME BAŞLANGICI ---
        # Python dosyasının olduğu klasörü bul
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Tam dosya yolunu oluştur (Windows/Mac/Linux uyumlu olur)
        file_path = os.path.join(current_dir, "instagram.csv")

        print(f"💾 Dosya şuraya kaydedilecek: {file_path}")

        with open(file_path, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["ID", "Hashtag", "Count"])
            writer.writerows(all_data)
        # --- DÜZELTME SONU ---

        print(f"✅ Toplam {len(all_data)} hashtag kaydedildi.")
    else:
        print("❌ Hiç hashtag bulunamadı.")

finally:
    driver.quit()