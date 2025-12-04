import sys
import time
import csv
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

def scrape_google_trends_24():
    print("🚀 Google Trends (Günlük/24s) Scraper Başlatılıyor...")
    
    try:
        driver = get_chrome_driver()
    except Exception as e:
        print(f"❌ Driver hatası: {e}")
        return

    all_trends_data = []

    try:
        url = "https://trends.google.com/trends/trendingsearches/daily?geo=TR&hl=tr"
        print(f"🌐 Gidiliyor: {url}")
        driver.get(url)

        try:
            cookie_btn = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button//*[contains(text(), 'Reddet') or contains(text(), 'Reject') or contains(text(), 'Kabul') or contains(text(), 'Accept')]"))
            )
            cookie_btn.find_element(By.XPATH, "./..").click()
            time.sleep(1)
            print("  🍪 Çerezler geçildi.")
        except:
            pass 

        page_number = 1
        
        while True:
            print(f"--- Sayfa {page_number} taranıyor ---")
            
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "mZ3RIc"))
                )
            except:
                print("  ⚠️ Veri bulunamadı veya sayfa yüklenemedi.")
                break 

            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)

            rows = driver.find_elements(By.XPATH, "//tr[@role='row']")
            new_count = 0
            
            for row in rows:
                try:
                    try:
                        title_el = row.find_element(By.CLASS_NAME, "mZ3RIc")
                        title_text = title_el.text.strip()
                    except: continue

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
                except:
                    continue
            
            print(f"  -> {new_count} yeni trend eklendi.")

            try:
                next_button = driver.find_element(By.XPATH, "//*[@aria-label='Sonraki sayfaya git']")
                if next_button.get_attribute("aria-disabled") == "true" or not next_button.is_enabled():
                    print("  ⏹️ Son sayfaya gelindi.")
                    break
                driver.execute_script("arguments[0].click();", next_button)
                time.sleep(2)
                page_number += 1
            except:
                break

    except Exception as e:
        print(f"❌ Genel Hata: {e}")

    finally:
        try:
            driver.quit()
            print("🛑 Tarayıcı kapatıldı.")
        except: pass

        output_filename = "google_trends_24.csv"
        output_path = BASE_DIR / output_filename

        if all_trends_data:
            try:
                with open(output_path, "w", newline="", encoding="utf-8-sig") as file:
                    writer = csv.writer(file)
                    writer.writerow(["Trend Başlık", "Arama Hacmi"])
                    writer.writerows(all_trends_data)
                print(f"✅ Dosya kaydedildi: {output_path}")
                print(f"📊 Toplam {len(all_trends_data)} kayıt.")
            except Exception as e:
                print(f"❌ Dosya yazma hatası: {e}")
        else:
            print(f"❌ Veri oluşmadığı için '{output_filename}' kaydedilemedi.")

if __name__ == "__main__":
    scrape_google_trends_24()