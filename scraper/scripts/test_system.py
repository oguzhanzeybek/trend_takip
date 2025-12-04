import os
import sys
import time
import requests
import json
import datetime
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent # .../scraper/scripts
ROOT_DIR = CURRENT_DIR.parent             # .../scraper (Proje Kök Dizini)

sys.path.append(str(ROOT_DIR))

ENV_PATH = ROOT_DIR / ".env"

try:
    from dotenv import load_dotenv
    if ENV_PATH.exists():
        load_dotenv(dotenv_path=ENV_PATH, override=True)
except ImportError:
    print("⚠️  HATA: 'python-dotenv' kütüphanesi eksik. Lütfen 'pip install python-dotenv' çalıştırın.")
    sys.exit(1)

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

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

    print(f"{Colors.BLUE}--- ADIM 1: Ortam Değişkenleri (.env) ---{Colors.RESET}")
    
    if ENV_PATH.exists():
        print_status(".env Dosyası", "OK", f"Bulundu: {ENV_PATH}")
    else:
        print_status(".env Dosyası", "WARN", "Dosya bulunamadı! Sistem ortam değişkenlerini kullanacak.")

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
                try:
                    reply = response.json()['choices'][0]['message']['content']
                    print_status("AI Bağlantısı", "OK", f"Yanıt alındı: '{reply}'")
                except:
                    print_status("AI Bağlantısı", "OK", "Yanıt alındı (İçerik parse edilemedi ama 200 OK)")
            else:
                print_status("AI Bağlantısı", "FAIL", f"Hata Kodu: {response.status_code} - {response.text}")
        except Exception as e:
            print_status("AI Bağlantısı", "FAIL", f"İstek atılamadı: {str(e)}")
    else:
        print_status("AI Bağlantısı", "WARN", "Key olmadığı için test atlandı.")

    print(f"\n{Colors.BLUE}--- ADIM 3: Veritabanı Yazma Testi (Supabase) ---{Colors.RESET}")
    
    try:
        db_file_path = ROOT_DIR / "core" / "database_manager.py"
        
        if not db_file_path.exists():
             print_status("DB Modülü", "FAIL", f"'core/database_manager.py' dosyası bulunamadı! Yol: {db_file_path}")
        else:
            try:
                from core.database_manager import DatabaseManager
                db = DatabaseManager()
                
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

            except ImportError as ie:
                print_status("DB Modülü", "FAIL", f"Modül import edilemedi: {ie}")
                print(f"   -> Sys Path: {sys.path}")
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
        print("⚠️  Eksik kütüphane: 'requests'. Lütfen 'pip install requests' çalıştırın.")
        sys.exit(1)
        
    run_test()