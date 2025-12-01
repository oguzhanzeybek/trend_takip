from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
import csv
import os

# -----------------------------
# Headless mod ayarları
options = Options()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
# -----------------------------

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

driver.get("https://trends24.in/turkey/")
time.sleep(5)

soup = BeautifulSoup(driver.page_source, "html.parser")
trends = soup.select(".trend-card__list a")

# Klasörü oluştur
folder_path = r"C:\Users\darks\OneDrive\Masaüstü\trend_takip\scraper\social_media\twitter"
os.makedirs(folder_path, exist_ok=True)

# Dosya yolu
file_path = os.path.join(folder_path, "twitter_trends.csv")

with open(file_path, "w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(["Trend"])
    for t in trends:
        writer.writerow([t.text.strip()])

driver.quit()
print("Kaydedildi ✅ (Headless modda)")
import csv
import os

# Dosya yolu
file_path = r"C:\Users\darks\OneDrive\Masaüstü\trend_takip\scraper\social_media\twitter\twitter_trends.csv"
output_path = r"C:\Users\darks\OneDrive\Masaüstü\trend_takip\scraper\social_media\twitter\twitter_trends_tagged.csv"

# Veriyi oku
with open(file_path, "r", encoding="utf-8") as file:
    reader = csv.reader(file)
    rows = list(reader)

header = rows[0]  # Başlık satırı
data = rows[1:]   # Veri satırları

# Yeni başlık ekle
header.append("Tag")

# Döngüsel sayı ekle
new_rows = [header]
for i, row in enumerate(data):
    if i < 50:
        tag = 0
    elif i < 100:
        tag=1
        
    elif i < 150:
        tag=1
        
    elif i < 200:
        tag=1
    elif i < 250:
        tag=2
    elif i < 300:
        tag=3
    elif i < 350:
        tag=4
    elif i < 400:
        tag=5
    elif i < 450:
        tag=6
    elif i < 500:
         tag=7
    elif i < 600:
        tag=8
    elif i < 650:
        tag=9
    elif i < 700:
        tag=10
    elif i < 750:
        tag=11
    elif i < 800:
        tag=12
    elif i < 850:
        tag=13
    elif i < 900:
        tag=14
    elif i < 950:
        tag=15
    elif i < 1000:
        tag=16
    else:    
        tag=24    
    
    row.append(tag)
    new_rows.append(row)

# Yeni CSV kaydet
with open(output_path, "w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerows(new_rows)

print("Yeni CSV kaydedildi ✅")
