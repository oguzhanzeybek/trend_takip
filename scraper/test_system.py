import os
import sys
import time
import requests
import json
import datetime
from pathlib import Path

# --- GÜNCELLEME: dotenv'i en başta yükleyelim ---
try:
    from dotenv import load_dotenv
except ImportError:
    print("⚠️  HATA: 'python-dotenv' kütüphanesi eksik. Lütfen 'pip install python-dotenv' çalıştırın.")
    sys.exit(1)

# Renk kodları (Çıktının okunabilir olması için)
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

# Dosya yollarını kesinleştirme
BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"

# .env dosyasını zorla (override) yükle
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH, override=True)

def print_status(step, status, message):
    if status == "OK":
        print(f"{Colors.GREEN}✅ [BAŞARILI] {step}:{Colors.RESET} {message}")
    elif status == "FAIL":
        print(f"{Colors.RED}❌ [HATA]     {step}:{Colors.RESET} {message}")
    elif status == "WARN":
        print(f"{Colors.YELLOW}⚠️  [UYARI]    {step}:{Colors.RESET} {message}")

def run_test():
    print(f"\n{Colors.BLUE}========================================{Colors.RESET}")
    print(f"{Colors.BLUE}   SİSTEM BAĞLANTI VE SAĞLIK TESTİ    {Colors.RESET}")
    print(f"{Colors.BLUE}========================================{Colors.RESET}\n")

    # ---------------------------------------------------------
    # ADIM 1: .env Kontrolü
    # ---------------------------------------------------------
    print(f"{Colors.BLUE}--- ADIM 1: Ortam Değişkenleri (.env) ---{Colors.RESET}")
    
    if ENV_PATH.exists():
        print_status(".env Dosyası", "OK", f"Bulundu: {ENV_PATH}")
    else:
        print_status(".env Dosyası", "WARN", "Dosya bulunamadı! Sistem ortam değişkenlerini kullanacak.")

    # Anahtarları kontrol et
    supa_url = os.getenv("SUPABASE_URL")
    supa_key = os.getenv("SUPABASE_KEY")
    ai_key = os.getenv("OPENROUTER_API_KEY")

    if supa_url and supa_key:
        print_status("Supabase Keys", "OK", "URL ve Key mevcut.")
    else:
        print_status("Supabase Keys", "FAIL", "SUPABASE_URL veya SUPABASE_KEY eksik!")
    
    if ai_key:
        print_status("AI Key", "OK", "OpenRouter Key mevcut.")
    else:
        print_status("AI Key", "FAIL", "OPENROUTER_API_KEY eksik!")

    # ---------------------------------------------------------
    # ADIM 2: OpenRouter (AI) Bağlantı Testi
    # ---------------------------------------------------------
    print(f"\n{Colors.BLUE}--- ADIM 2: AI API Testi (OpenRouter) ---{Colors.RESET}")
    if ai_key:
        try:
            headers = {
                "Authorization": f"Bearer {ai_key}",
                "Content-Type": "application/json",
            }
            data = {
                "model": "openai/gpt-3.5-turbo", 
                "messages": [{"role": "user", "content": "Say 'Test OK'"}],
                "max_tokens": 10
            }
            response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data, timeout=10)
            
            if response.status_code == 200:
                reply = response.json()['choices'][0]['message']['content']
                print_status("AI Bağlantısı", "OK", f"Yanıt alındı: '{reply}'")
            else:
                print_status("AI Bağlantısı", "FAIL", f"Hata Kodu: {response.status_code} - {response.text}")
        except Exception as e:
            print_status("AI Bağlantısı", "FAIL", f"İstek atılamadı: {str(e)}")
    else:
        print_status("AI Bağlantısı", "WARN", "Key olmadığı için test atlandı.")

    # ---------------------------------------------------------
    # ADIM 3: Supabase Veritabanı Yazma Testi (YENİ TABLO)
    # ---------------------------------------------------------
    print(f"\n{Colors.BLUE}--- ADIM 3: Veritabanı Yazma Testi (Supabase) ---{Colors.RESET}")
    
    try:
        sys.path.append(str(BASE_DIR))
        if not (BASE_DIR / "database_manager.py").exists():
             print_status("DB Modülü", "FAIL", "'database_manager.py' dosyası klasörde yok!")
        else:
            try:
                from database_manager import DatabaseManager
                db = DatabaseManager()
                
                # --- GÜNCELLEME: Yeni Tablo Yapısına Uygun Veri ---
                test_payload = {
                    "category": "SYSTEM_TEST",
                    "data_type": "TEST_LOG",
                    "source": "test_system.py",
                    "content": {
                        "title": "Sistem Bağlantı Testi",
                        "message": "Bu kayıt test_system.py tarafından oluşturuldu.",
                        "status": "OK",
                        "timestamp": datetime.datetime.now().isoformat()
                    }
                }
                
                print("   ⏳ 'processed_data' tablosuna test verisi yazılıyor...")
                
                # Hedef tablo: processed_data
                try:
                    result = db.insert_data("processed_data", [test_payload])
                    print_status("DB Yazma", "OK", "Başarıyla yazıldı!")
                    print(f"   ℹ️  Not: 'processed_data' tablosuna test kaydı eklendi.")
                    
                except Exception as e:
                    err_msg = str(e)
                    if "401" in err_msg:
                        print_status("DB Yazma", "FAIL", "YETKİ HATASI (401)! Service Role Key kullandığından emin ol.")
                    elif "relation" in err_msg and "does not exist" in err_msg:
                        print_status("DB Yazma", "FAIL", "Tablo bulunamadı! 'processed_data' tablosunu oluşturduğundan emin ol.")
                    elif "daily_trends" in err_msg:
                        print_status("DB Yazma", "FAIL", "Kod hala eski tabloya (daily_trends) yazmaya çalışıyor. database_manager.py dosyasını kontrol et.")
                        print(f"   🔻 Hata Detayı: {err_msg}")
                    else:
                        print_status("DB Yazma", "FAIL", f"Beklenmedik Hata: {err_msg}")

            except ImportError:
                print_status("DB Modülü", "FAIL", "Modül import edilemedi.")
            except Exception as e:
                print_status("DB Genel", "FAIL", f"Başlatma hatası: {str(e)}")

    except Exception as e:
        print_status("Genel Hata", "FAIL", str(e))

    print(f"\n{Colors.BLUE}========================================{Colors.RESET}")
    print(f"{Colors.BLUE}   TEST TAMAMLANDI   {Colors.RESET}")
    print(f"{Colors.BLUE}========================================{Colors.RESET}\n")

if __name__ == "__main__":
    try:
        import requests
    except ImportError:
        print("⚠️  Eksik kütüphane: 'requests'.")
        sys.exit(1)
        
    run_test()