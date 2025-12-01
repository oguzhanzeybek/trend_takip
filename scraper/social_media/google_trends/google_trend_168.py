from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import csv
import os

# --- AYARLAR ---
options = Options()
options.add_argument("--headless=new") # Arka plan modu
options.add_argument("--window-size=1920,1080")
options.add_argument("--disable-gpu")
options.add_argument("--disable-notifications")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")

print("Google Trends tarayıcısı ARKA PLANDA başlatılıyor...")
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

try:
    # Günlük Trendler Sayfası (Bu sayfa 'Sonraki Sayfa' dedikçe geçmiş günlere gider)
    url = "https://trends.google.com/trending?geo=TR&hl=tr&hours=168"
    print(f"Siteye gidiliyor: {url}")
    driver.get(url)

    # 1. ÇEREZLERİ GEÇ
    try:
        cookie_btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//button//*[contains(text(), 'Reddet') or contains(text(), 'Reject') or contains(text(), 'Kabul') or contains(text(), 'Accept')]"))
        )
        cookie_btn.find_element(By.XPATH, "./..").click()
        print("Çerez butonu geçildi.")
        time.sleep(2)
    except:
        print("Çerez ekranı çıkmadı.")

    # 2. ANA DÖNGÜ
    all_trends_data = [] # [Başlık, Hacim, Süre] saklayacağız
    page_number = 1

    while True:
        print(f"\n--- Sayfa {page_number} Taranıyor ---")
        
        # Sayfanın yüklenmesini bekle
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "mZ3RIc"))
            )
        except:
            print("Veri bulunamadı, döngü bitiriliyor.")
            break

        # Sayfayı kaydır
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

        # SATIRLARI OKU
        rows = driver.find_elements(By.XPATH, "//tr[@role='row']")
        
        new_count = 0
        for row in rows:
            try:
                # A) Başlık (mZ3RIc)
                title_el = row.find_element(By.CLASS_NAME, "mZ3RIc")
                title_text = title_el.text.strip()

                # B) Hacim (lqv0Cb)
                try:
                    volume_el = row.find_element(By.CLASS_NAME, "lqv0Cb")
                    volume_text = volume_el.text.strip().replace("\n", "") 
                except:
                    volume_text = "Bilinmiyor"

                # C) Süre / Ne Kadar Önce (vdw3Ld) <-- YENİ EKLENEN KISIM
                try:
                    time_el = row.find_element(By.CLASS_NAME, "vdw3Ld")
                    time_text = time_el.text.strip()
                except:
                    time_text = "Bilinmiyor"

                # Listeye Ekle
                if title_text:
                    already_exists = any(item[0] == title_text for item in all_trends_data)
                    
                    if not already_exists:
                        # Veriyi 3'lü olarak kaydediyoruz
                        all_trends_data.append([title_text, volume_text, time_text])
                        new_count += 1
                        print(f"-> {title_text} | {volume_text} | {time_text}")

            except:
                continue
        
        print(f"Bu sayfadan {new_count} yeni veri eklendi.")

        # SONRAKİ SAYFAYA GEÇİŞ
        try:
            next_button = driver.find_element(By.XPATH, "//*[@aria-label='Sonraki sayfaya git']")
            
            if next_button.get_attribute("aria-disabled") == "true" or not next_button.is_enabled():
                print("Son sayfaya gelindi.")
                break
            
            driver.execute_script("arguments[0].click();", next_button)
            print("Sonraki sayfaya geçiliyor...")
            time.sleep(3)
            page_number += 1
            
        except:
            print("Sonraki sayfa butonu bulunamadı, işlem tamamlandı.")
            break

    driver.quit()

    # 3. CSV KAYDI
    folder_path = r"C:\Users\darks\OneDrive\Masaüstü\trend_takip\scraper\social_media\google_trends"
    os.makedirs(folder_path, exist_ok=True)
    file_path = os.path.join(folder_path, "google_trends_168.csv")

    if all_trends_data:
        with open(file_path, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            # Sütun Başlıkları Güncellendi
            writer.writerow(["Trend Başlık", "Arama Hacmi", "Ne Zaman Başladı"])
            
            for data in all_trends_data:
                writer.writerow(data)
        
        print(f"\n✅ İŞLEM BİTTİ: Toplam {len(all_trends_data)} adet detaylı trend kaydedildi.")
        print(f"Dosya: {file_path}")
    else:
        print("\n❌ Hiç veri çekilemedi.")

except Exception as e:
    print(f"Kritik Hata: {e}")
    try:
        driver.quit()
    except:
        pass