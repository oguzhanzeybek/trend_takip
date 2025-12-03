import sys
import time
import csv
from pathlib import Path
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- 1. YOL AYARLARI ---
# Scriptin bulunduğu klasör
CURRENT_DIR = Path(__file__).resolve().parent
# Scraper kök dizinine çık (google_trends -> social_media -> scraper)
# Eğer dosya yapın farklıysa buradaki .parent sayısını değiştirebilirsin.
# Genelde: proje_root/scraper/social_media/google_trends/google_trends.py
ROOT_DIR = CURRENT_DIR.parent.parent 

sys.path.append(str(ROOT_DIR))

# --- 2. MERKEZİ DRIVER ÇAĞRISI ---
try:
    from core.driver_manager import get_chrome_driver
except ImportError:
    # Yedek yol denemesi (Proje Root)
    sys.path.append(str(ROOT_DIR.parent))
    from scraper.core.driver_manager import get_chrome_driver

# --- AYARLAR ---
BASE_DIR = CURRENT_DIR

def scrape_google_trends():
    print("🚀 Google Trends (168 Saat) Scraper Başlatılıyor...")
    
    try:
        driver = get_chrome_driver()
    except Exception as e:
        print(f"❌ Driver hatası: {e}")
        return

    all_trends_data = []

    try:
        url = "https://trends.google.com/trending?geo=TR&hl=tr&hours=168"
        print(f"🌐 Gidiliyor: {url}")
        driver.get(url)

        # 1. ÇEREZLERİ GEÇ
        try:
            cookie_btn = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button//*[contains(text(), 'Reddet') or contains(text(), 'Reject') or contains(text(), 'Kabul') or contains(text(), 'Accept')]"))
            )
            cookie_btn.find_element(By.XPATH, "./..").click()
            time.sleep(1)
            print("  🍪 Çerezler geçildi.")
        except:
            pass # Çerez çıkmadıysa devam et

        # 2. VERİ ÇEKME DÖNGÜSÜ
        page_number = 1
        
        while True:
            print(f"--- Sayfa {page_number} taranıyor ---")
            
            # Sayfanın yüklenmesini bekle
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "mZ3RIc"))
                )
            except:
                print("  ⚠️ Veri yüklenemedi veya bitti.")
                break 

            # Sayfayı kaydır (Verilerin yüklenmesi için)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)

            # Satırları Oku
            rows = driver.find_elements(By.XPATH, "//tr[@role='row']")
            new_count = 0
            
            for row in rows:
                try:
                    # Başlık (Class isimleri Google güncellemesinde değişebilir, şu anki çalışanlar:)
                    try:
                        title_el = row.find_element(By.CLASS_NAME, "mZ3RIc")
                        title_text = title_el.text.strip()
                    except: continue

                    # Hacim
                    try:
                        volume_el = row.find_element(By.CLASS_NAME, "lqv0Cb")
                        volume_text = volume_el.text.strip().replace("\n", "") 
                    except:
                        volume_text = "Bilinmiyor"

                    # Süre
                    try:
                        time_el = row.find_element(By.CLASS_NAME, "vdw3Ld")
                        time_text = time_el.text.strip()
                    except:
                        time_text = "Bilinmiyor"

                    # Listeye Ekle (Duplicate Kontrolü)
                    if title_text:
                        already_exists = any(item[0] == title_text for item in all_trends_data)
                        if not already_exists:
                            all_trends_data.append([title_text, volume_text, time_text])
                            new_count += 1
                except:
                    continue
            
            print(f"  -> {new_count} yeni trend eklendi.")

            # Sonraki Sayfa Kontrolü
            try:
                # "Sonraki sayfaya git" butonunu bul
                next_button = driver.find_element(By.XPATH, "//*[@aria-label='Sonraki sayfaya git']")
                
                # Buton disabled ise veya tıklanabilir değilse döngüyü kır
                if next_button.get_attribute("aria-disabled") == "true" or not next_button.is_enabled():
                    print("  ⏹️ Son sayfaya ulaşıldı.")
                    break
                
                driver.execute_script("arguments[0].click();", next_button)
                time.sleep(2)
                page_number += 1
            except:
                print("  ⏹️ Sonraki sayfa butonu bulunamadı.")
                break

    except Exception as e:
        print(f"❌ Genel Hata: {e}")

    finally:
        try:
            driver.quit()
            print("🛑 Tarayıcı kapatıldı.")
        except: pass

        # --- DOSYA KAYIT ---
        output_filename = "google_trends_168.csv"
        output_path = BASE_DIR / output_filename

        if all_trends_data:
            try:
                with open(output_path, "w", newline="", encoding="utf-8-sig") as file:
                    writer = csv.writer(file)
                    writer.writerow(["Trend Başlık", "Arama Hacmi", "Ne Zaman Başladı"])
                    writer.writerows(all_trends_data)
                print(f"✅ Dosya kaydedildi: {output_path}")
                print(f"📊 Toplam {len(all_trends_data)} trend bulundu.")
            except Exception as e:
                print(f"❌ Dosya yazma hatası: {e}")
        else:
            print(f"❌ Veri oluşmadığı için '{output_filename}' kaydedilemedi.")

if __name__ == "__main__":
    scrape_google_trends()