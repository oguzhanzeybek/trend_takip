import sys
import time
import csv
import random
from pathlib import Path
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parent.parent 
sys.path.append(str(ROOT_DIR))

try:
    from core.driver_manager import get_chrome_driver
except ImportError:
    sys.path.append(str(ROOT_DIR.parent))
    from scraper.core.driver_manager import get_chrome_driver

BASE_DIR = CURRENT_DIR

DEBUG_DIR = BASE_DIR / "debug_tiktok_live"
DEBUG_DIR.mkdir(exist_ok=True)


def scrape_tiktok_trends():
    print("🚀 TikTok Trend Scraper (DEBUG MODU AKTİF) Başlatılıyor...")
    
    collected_hashtags = set()
    driver = None

    try:
        driver = get_chrome_driver()
        wait = WebDriverWait(driver, 60)
        
        print("🌍 Konum taklidi (İstanbul) uygulanıyor.")
        driver.execute_cdp_cmd(
            "Emulation.setGeolocationOverride",
            {
                "latitude": 41.0082,
                "longitude": 28.9784,
                "accuracy": 100,
            }
        )

        url = "https://www.tiktok.com/tag/trend?lang=tr"
        print(f"🌐 Gidiliyor: {url}")
        driver.get(url)
        time.sleep(random.uniform(3, 5)) 
        
        screenshot_path_initial = DEBUG_DIR / f"01_initial_load.png"
        driver.save_screenshot(str(screenshot_path_initial))
        print(f"📸 DEBUG: İlk sayfa görüntüsü alındı: {screenshot_path_initial}")


        try:
            print("  🍪 Çerezler bekleniyor...")
            cookie_btn = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Tümüne izin ver') or contains(text(), 'Allow all')]"))
            )
            cookie_btn.click()
            time.sleep(random.uniform(1.5, 3))
            print("  ✅ Çerezler kapatıldı.")
        except:
            pass

        try:
            error_message = driver.find_elements(By.XPATH, "//*[contains(text(), 'Bir şeyler ters gitti') or contains(text(), 'Something went wrong')]")
            if len(error_message) > 0:
                print("  ⚠️ Hata ekranı tespit edildi, sayfa yenileniyor.")
                driver.refresh()
                time.sleep(random.uniform(10, 15)) 
        except:
            pass
        
        screenshot_path_after_refresh = DEBUG_DIR / f"02_after_refresh.png"
        driver.save_screenshot(str(screenshot_path_after_refresh))
        print(f"📸 DEBUG: Yenileme sonrası görüntü alındı: {screenshot_path_after_refresh}")


        TARGET_SELECTOR = "[data-e2e='challenge-item-desc']"

        try:
            print("  ⏳ İlk içerik yüklenmesi bekleniyor...")
            wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, TARGET_SELECTOR))
            )
            print("  ✅ İlk içerik yüklendi.")
        except:
            print("  ⚠️ İçerik yüklenmesi zaman aşımına uğradı. Kaydırmaya geçiliyor.")
            pass 

        TARGET_SCROLL_COUNT = 40
        SCROLL_PAUSE_TIME_RANGE = (2.5, 4.5)
        
        last_height = driver.execute_script("return document.body.scrollHeight")
        
        print(f"⬇️ {TARGET_SCROLL_COUNT} kez kaydırma döngüsü başlatılıyor...")
        for i in range(TARGET_SCROLL_COUNT):
            scroll_by = random.randint(500, 1000)
            driver.execute_script(f"window.scrollBy(0, {scroll_by});")
            time.sleep(random.uniform(*SCROLL_PAUSE_TIME_RANGE))

            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                time.sleep(random.uniform(1, 2))
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    print("  ⏹️ Sayfa sonuna ulaşıldı.")
                    break
            last_height = new_height
            
            if (i + 1) % 10 == 0:
                print(f"  -> {i + 1}. kaydırma tamamlandı.")

        print("📦 Hashtag'ler toplanıyor...")
        desc_elements = driver.find_elements(By.CSS_SELECTOR, TARGET_SELECTOR)
        print(f"  -> Toplam {len(desc_elements)} potansiyel açıklama bulundu.")

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
        print(f"❌ Kritik Hata: {e}")

    finally:
        if driver:
            driver.quit()
            print("🛑 Tarayıcı kapatıldı.")

        output_filename = "tiktok_trends.csv"
        output_path = BASE_DIR / output_filename

        if collected_hashtags:
            try:
                with open(output_path, "w", newline="", encoding="utf-8-sig") as file:
                    writer = csv.writer(file)
                    writer.writerow(["Hashtag"])
                    for tag in collected_hashtags:
                        writer.writerow([tag])
                print(f"✅ Dosya kaydedildi: {output_path}")
                print(f"📊 Toplam {len(collected_hashtags)} benzersiz hashtag toplandı.")
            except Exception as e:
                print(f"❌ Dosya yazma hatası: {e}")
        else:
            print(f"❌ Veri oluşmadığı için '{output_filename}' kaydedilemedi.")

if __name__ == "__main__":
    scrape_tiktok_trends()