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

# 1. HEADLESS MODU AKTİF ETME (Arka Planda Çalıştır)
# "--headless=new" komutu, eski headless moduna göre daha kararlıdır ve bot gibi görünme ihtimalini azaltır.
options.add_argument("--headless=new") 

# 2. PENCERE BOYUTUNU SABİTLEME
# Arka planda çalışsa bile tarayıcıyı geniş ekran gibi tanıtmalıyız.
# Aksi takdirde "Sonraki Sayfa" butonu görünmeyebilir veya elementler kayabilir.
options.add_argument("--window-size=1920,1080")
options.add_argument("--disable-gpu") # GPU kullanımını kapat (Hızlandırır)

# Diğer Bot Koruması Ayarları
options.add_argument("--disable-notifications")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")

print("Google Trends tarayıcısı ARKA PLANDA başlatılıyor...")
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

try:
    # Google Trends Günlük Aramalar (Türkiye)
    url = "https://trends.google.com/trends/trendingsearches/daily?geo=TR&hl=tr"
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
        print("Çerez ekranı çıkmadı (veya arka planda otomatik geçildi).")

    # 2. ANA DÖNGÜ
    all_trends_data = [] # [Başlık, Hacim] şeklinde saklayacağız
    page_number = 1

    while True:
        print(f"\n--- Sayfa {page_number} Taranıyor (Arka Plan) ---")
        
        # Sayfanın yüklenmesini bekle (Başlık sınıfını baz alıyoruz)
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "mZ3RIc"))
            )
        except:
            print("Veri bulunamadı veya yükleme zaman aşımına uğradı, döngü bitiriliyor.")
            break

        # Sayfayı kaydır
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

        # SATIR SATIR OKUMA
        rows = driver.find_elements(By.XPATH, "//tr[@role='row']")
        
        new_count = 0
        for row in rows:
            try:
                # 1. Başlığı bul
                title_el = row.find_element(By.CLASS_NAME, "mZ3RIc")
                title_text = title_el.text.strip()

                # 2. Hacmi bul
                try:
                    volume_el = row.find_element(By.CLASS_NAME, "lqv0Cb")
                    volume_text = volume_el.text.strip().replace("\n", "") 
                except:
                    volume_text = "Bilinmiyor"

                if title_text:
                    already_exists = any(item[0] == title_text for item in all_trends_data)
                    
                    if not already_exists:
                        all_trends_data.append([title_text, volume_text])
                        new_count += 1
                        print(f"-> {title_text} | Hacim: {volume_text}")

            except Exception as e:
                continue
        
        print(f"Bu sayfadan {new_count} yeni veri eklendi.")

        # SONRAKİ SAYFAYA GEÇİŞ
        try:
            next_button = driver.find_element(By.XPATH, "//*[@aria-label='Sonraki sayfaya git']")
            
            if next_button.get_attribute("aria-disabled") == "true" or not next_button.is_enabled():
                print("Son sayfaya gelindi.")
                break
            
            # JavaScript click kullanıyoruz, arka planda daha güvenilirdir.
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
    file_path = os.path.join(folder_path, "google_trends_24.csv")

    if all_trends_data:
        with open(file_path, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["Trend Başlık", "Arama Hacmi"])
            for data in all_trends_data:
                writer.writerow(data)
        
        print(f"\n✅ İŞLEM BİTTİ: Toplam {len(all_trends_data)} adet trend kaydedildi.")
        print(f"Dosya: {file_path}")
    else:
        print("\n❌ Hiç veri çekilemedi.")

except Exception as e:
    print(f"Kritik Hata: {e}")
    try:
        driver.quit()
    except:
        pass