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
    options.add_argument("--headless=new") 
    options.add_argument("--no-sandbox")   
    options.add_argument("--disable-dev-shm-usage") 
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

# --- ANA İŞLEM ---
collected_hashtags = set()
driver = None

try:
    driver = get_driver()
    url = "https://www.tiktok.com/tag/trend?lang=tr"
    driver.get(url)

    # 1. ÇEREZLERİ GEÇ
    try:
        cookie_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Tümüne izin ver') or contains(text(), 'Allow all')]"))
        )
        cookie_btn.click()
        time.sleep(2)
    except:
        pass

    # 2. HATA EKRANI KONTROLÜ
    try:
        error_message = driver.find_elements(By.XPATH, "//*[contains(text(), 'Bir şeyler ters gitti') or contains(text(), 'Something went wrong')]")
        if len(error_message) > 0:
            driver.refresh()
            time.sleep(5)
    except:
        pass

    # 3. İÇERİK BEKLEME VE KAYDIRMA
    WAIT_TIMEOUT = 30
    TARGET_SELECTOR = "[data-e2e='challenge-item-desc']"

    try:
        WebDriverWait(driver, WAIT_TIMEOUT).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, TARGET_SELECTOR))
        )
    except:
        pass # Devam etmeyi dene

    # Kaydırma Ayarları
    TARGET_SCROLL_COUNT = 50  # Arka planda çok zorlamamak için biraz düşürdük
    SCROLL_PAUSE_TIME = 3
    last_height = driver.execute_script("return document.body.scrollHeight")

    for i in range(TARGET_SCROLL_COUNT):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(SCROLL_PAUSE_TIME)
        
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            time.sleep(2)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
        last_height = new_height

    # 4. VERİ TOPLAMA
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

except Exception as e:
    pass

finally:
    if driver:
        driver.quit()

# --- DOSYA KAYIT (STANDART BLOK) ---
current_dir = Path(__file__).resolve().parent
output_filename = "tiktok_trends.csv"
output_path = current_dir / output_filename

if collected_hashtags:
    with open(output_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Hashtag"])
        for tag in collected_hashtags:
            writer.writerow([tag])
    print(f"✅ Dosya kaydedildi: {output_path} (Toplam: {len(collected_hashtags)})")
else:
    print(f"❌ Veri oluşmadığı için '{output_filename}' kaydedilemedi.")