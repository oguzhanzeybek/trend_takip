from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import csv
import os
import time

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

# YouTube Trends Türkiye
driver.get("https://youtube.trends24.in/turkey")
time.sleep(5)  # sayfanın yüklenmesi için bekle

soup = BeautifulSoup(driver.page_source, "html.parser")

# -----------------------------
# 1) Trending Channels
channels = [span.text.strip() for span in soup.select("span.title")]

# 2) Popular Keywords
keywords = [li.text.strip() for li in soup.select("ol.keywords-list li")]

driver.quit()

# -----------------------------
# CSV kaydı
folder_path = r"C:\Users\darks\OneDrive\Masaüstü\trend_takip\scraper\social_media\youtube"
os.makedirs(folder_path, exist_ok=True)

file_path = os.path.join(folder_path, "youtube_trends.csv")

with open(file_path, "w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    # Başlık
    writer.writerow(["Channels / Keywords"])
    # Kanal isimlerini ekle
    for c in channels:
        writer.writerow([c])
    # Anahtar kelimeleri ekle
    for k in keywords:
        writer.writerow([k])

print("Veriler kaydedildi ✅")



import csv
import os

# -----------------------------
input_file = r"C:\Users\darks\OneDrive\Masaüstü\trend_takip\scraper\social_media\youtube\youtube_trends.csv"
output_file = r"C:\Users\darks\OneDrive\Masaüstü\trend_takip\scraper\social_media\youtube\youtube_trends_tag.csv"

# -----------------------------
# CSV okuma
with open(input_file, "r", encoding="utf-8") as f:
    reader = csv.reader(f)
    rows = [row for row in reader]

# -----------------------------
# Yeni CSV için başlıklar ve satırları oluştur
new_rows = []

for i, row in enumerate(rows):
    if i == 0:
        # Eğer ilk satır başlıksa, değiştirelim
        new_rows.append(["video", "tag"])
    else:
        if i <= 10:
            # İlk 10 satır -> video sütununa veri, tag boş
            new_rows.append([row[0], ""])
        else:
            # Geri kalan satırlar -> tag sütununa veri, video boş
            new_rows.append(["", row[0]])

# -----------------------------
# Yeni CSV yazma
with open(output_file, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerows(new_rows)

print("CSV güncellendi ✅")
