from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
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
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")
    
    # Driver Kurulumu
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

# --- ANA İŞLEM ---
all_trends_data = []

try:
    driver = get_driver()
    url = "https://trends.google.com/trends/trendingsearches/daily?geo=TR&hl=tr"
    driver.get(url)

    # 1. ÇEREZLERİ GEÇ
    try:
        cookie_btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//button//*[contains(text(), 'Reddet') or contains(text(), 'Reject') or contains(text(), 'Kabul') or contains(text(), 'Accept')]"))
        )
        cookie_btn.find_element(By.XPATH, "./..").click()
        time.sleep(1)
    except:
        pass # Çerez çıkmadıysa devam et

    # 2. VERİ ÇEKME DÖNGÜSÜ
    page_number = 1
    
    while True:
        # Sayfanın yüklenmesini bekle
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "mZ3RIc"))
            )
        except:
            break # Veri yoksa çık

        # Sayfayı kaydır
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

        # Satırları Oku
        rows = driver.find_elements(By.XPATH, "//tr[@role='row']")
        
        for row in rows:
            try:
                # Başlık
                title_el = row.find_element(By.CLASS_NAME, "mZ3RIc")
                title_text = title_el.text.strip()

                # Hacim
                try:
                    volume_el = row.find_element(By.CLASS_NAME, "lqv0Cb")
                    volume_text = volume_el.text.strip().replace("\n", "") 
                except:
                    volume_text = "Bilinmiyor"

                # Listeye Ekle (Duplicate Kontrolü)
                if title_text:
                    already_exists = any(item[0] == title_text for item in all_trends_data)
                    if not already_exists:
                        all_trends_data.append([title_text, volume_text])
            except:
                continue
        
        # Sonraki Sayfa Kontrolü
        try:
            next_button = driver.find_element(By.XPATH, "//*[@aria-label='Sonraki sayfaya git']")
            if next_button.get_attribute("aria-disabled") == "true" or not next_button.is_enabled():
                break
            driver.execute_script("arguments[0].click();", next_button)
            time.sleep(2)
            page_number += 1
        except:
            break

    driver.quit()

except Exception as e:
    # Hata olsa bile sessiz kalıp kaydetmeye çalışacağız (varsa)
    try:
        driver.quit()
    except:
        pass

# --- DOSYA KAYIT (STANDART BLOK) ---
current_dir = Path(__file__).resolve().parent
output_filename = "google_trends_24.csv"
output_path = current_dir / output_filename

if all_trends_data:
    with open(output_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Trend Başlık", "Arama Hacmi"])
        writer.writerows(all_trends_data)
    print(f"✅ Dosya kaydedildi: {output_path} (Toplam: {len(all_trends_data)})")
else:
    print(f"❌ Veri oluşmadığı için '{output_filename}' kaydedilemedi.")