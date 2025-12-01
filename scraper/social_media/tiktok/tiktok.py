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

# --- Ayarlar ---
options = Options()
# Tarayıcıyı görünür yapıyoruz (Headless kapalı)
options.add_argument("--start-maximized") 
options.add_argument("--disable-notifications")
options.add_argument("--disable-blink-features=AutomationControlled") 
# Bot gibi görünmemek için User-Agent
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

print("Web sürücüsü başlatılıyor...")
try:
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
except Exception as e:
    print(f"Hata: Web sürücüsü başlatılamadı. {e}")
    exit()

url = "https://www.tiktok.com/tag/trend?lang=tr"
print(f"Sayfaya gidiliyor: {url}")
driver.get(url)

# -----------------------------
# ADIM 1: ÇEREZLERİ KABUL ET ("Tümüne izin ver")
# -----------------------------
try:
    print("Çerez butonu aranıyor...")
    # Fotoğraftaki "Tümüne izin ver" yazısını içeren butonu bul ve tıkla
    cookie_btn = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Tümüne izin ver') or contains(text(), 'Allow all')]"))
    )
    cookie_btn.click()
    print("✅ Çerezler kabul edildi (Butona tıklandı).")
    time.sleep(2) # Tıklama sonrası animasyon için bekle
except Exception as e:
    print("ℹ️ Çerez butonu çıkmadı veya zaten geçildi.")

# -----------------------------
# ADIM 2: "BİR ŞEYLER TERS GİTTİ" HATASINI KONTROL ET VE YENİLE
# -----------------------------
try:
    # Sayfada "Bir şeyler ters gitti" yazısı var mı kontrol et
    error_message = driver.find_elements(By.XPATH, "//*[contains(text(), 'Bir şeyler ters gitti') or contains(text(), 'Something went wrong')]")
    
    if len(error_message) > 0:
        print("⚠️ Hata ekranı tespit edildi ('Bir şeyler ters gitti').")
        print("🔄 Sayfa yenileniyor (Refresh)...")
        driver.refresh()
        time.sleep(5) # Yenileme sonrası yükleme için bekle
    else:
        print("✅ Hata ekranı yok, devam ediliyor.")

except Exception as e:
    print(f"Hata kontrolü sırasında sorun: {e}")

# -----------------------------
# ADIM 3: KAYDIRMA VE VERİ TOPLAMA
# -----------------------------

WAIT_TIMEOUT = 30 
TARGET_SELECTOR = "[data-e2e='challenge-item-desc']" 

# Ana içeriğin yüklenmesini bekle
try:
    WebDriverWait(driver, WAIT_TIMEOUT).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, TARGET_SELECTOR))
    )
    print("İçerikler yüklendi.")
except:
    print("Zaman aşımı! İçerik tam yüklenemedi ama devam ediliyor.")

# Kaydırma Döngüsü
TARGET_SCROLL_COUNT = 100  # Kaydırma sayısı
SCROLL_PAUSE_TIME = 5    # Bekleme süresi

last_height = driver.execute_script("return document.body.scrollHeight")

print("Kaydırma işlemi başlıyor...")
for i in range(TARGET_SCROLL_COUNT):
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(SCROLL_PAUSE_TIME)
    
    new_height = driver.execute_script("return document.body.scrollHeight")
    print(f"Kaydırma: {i+1} / {TARGET_SCROLL_COUNT}")
    
    if new_height == last_height:
        # Belki internet yavaştır, bir şans daha verip tekrar dene
        time.sleep(3)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            print("Sayfa sonuna gelindi.")
            break
    last_height = new_height

# -----------------------------
# VERİLERİ ÇEK VE KAYDET
# -----------------------------
print("Veriler toplanıyor...")
collected_hashtags = set()
desc_elements = driver.find_elements(By.CSS_SELECTOR, TARGET_SELECTOR)

for el in desc_elements:
    try:
        full_text = el.text 
        if not full_text:
            try:
                link_elem = el.find_element(By.TAG_NAME, "a")
                full_text = link_elem.get_attribute("title")
            except:
                continue

        if full_text:
            words = full_text.split()
            for word in words:
                if word.startswith("#") and len(word) > 1:
                    clean_tag = word.strip().replace("\n", "")
                    collected_hashtags.add(clean_tag)
    except:
        continue

driver.quit()

# CSV Kaydı
folder_path = r"C:\Users\darks\OneDrive\Masaüstü\trend_takip\scraper\social_media\tiktok"
os.makedirs(folder_path, exist_ok=True)
file_path = os.path.join(folder_path, "tiktok_trends.csv")

print("-----------------------------")
print(f"Toplam {len(collected_hashtags)} adet BENZERSİZ hashtag bulundu.")

with open(file_path, "w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(["Hashtag"])
    for tag in collected_hashtags:
        writer.writerow([tag])

print(f"Dosya kaydedildi: {file_path} ✅")