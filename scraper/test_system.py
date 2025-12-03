import os
import sys
import time
import requests
import json
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

# --- KRİTİK GÜNCELLEME: .env dosyasını zorla (override) yükle ---
# Bu sayede dosya ismini düzelttiğinde terminali kapatıp açmana gerek kalmaz.
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
    ai_key = os.getenv("OPENROUTER_API_KEY") # Kodun aradığı doğru isim bu

    if supa_url and supa_key:
        print_status("Supabase Keys", "OK", "URL ve Key mevcut.")
    else:
        print_status("Supabase Keys", "FAIL", "SUPABASE_URL veya SUPABASE_KEY eksik!")
    
    if ai_key:
        print_status("AI Key", "OK", "OpenRouter Key mevcut.")
    else:
        print_status("AI Key", "FAIL", f"OPENROUTER_API_KEY eksik! (Mevcut olan: {os.getenv('OPENROUTER_KEY') if os.getenv('OPENROUTER_KEY') else 'Yok'})")
        if os.getenv("OPENROUTER_KEY"):
            print(f"      👉 {Colors.YELLOW}İPUCU: .env dosyasında 'OPENROUTER_KEY' yazıyor, lütfen onu 'OPENROUTER_API_KEY' olarak değiştirin.{Colors.RESET}")

    # ---------------------------------------------------------
    # ADIM 2: OpenRouter (AI) Bağlantı Testi
    # ---------------------------------------------------------
    print(f"\n{Colors.BLUE}--- ADIM 2: AI API Testi (OpenRouter) ---{Colors.RESET}")
    if ai_key:
        try:
            # Basit bir "Merhaba" isteği atalım
            headers = {
                "Authorization": f"Bearer {ai_key}",
                "Content-Type": "application/json",
                # "HTTP-Referer": "http://localhost", # İsteğe bağlı
            }
            data = {
                "model": "openai/gpt-3.5-turbo", # Ucuz model ile test
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
    # ADIM 3: Supabase Veritabanı Yazma Testi
    # ---------------------------------------------------------
    print(f"\n{Colors.BLUE}--- ADIM 3: Veritabanı Yazma Testi (Supabase) ---{Colors.RESET}")
    
    # database_manager.py dosyasını kullanmayı dene
    try:
        sys.path.append(str(BASE_DIR))
        # Dosya var mı kontrol et
        if not (BASE_DIR / "database_manager.py").exists():
             print_status("DB Modülü", "FAIL", "'database_manager.py' dosyası klasörde yok!")
        else:
            try:
                from database_manager import DatabaseManager
                db = DatabaseManager()
                
                # Test verisi
                test_payload = [{
                    "title": "SISTEM_TEST_KAYDI",
                    "price": "0.00",
                    "link": "https://test.com",
                    "category": "TEST_LOG",
                    "ai_analysis": {"durum": "test_ok", "zaman": time.strftime("%Y-%m-%d %H:%M:%S")}
                }]
                
                print("   ⏳ Veritabanına test verisi yazılıyor...")
                
                # SYSTEM tablosuna yazmayı dene
                try:
                    result = db.insert_data("SYSTEM", test_payload)
                    print_status("DB Yazma", "OK", "Başarıyla yazıldı! (401 hatası alınmadı).")
                    print(f"   ℹ️  Not: 'SYSTEM' tablosuna 'SISTEM_TEST_KAYDI' adında bir satır eklendi.")
                    
                except Exception as e:
                    err_msg = str(e)
                    if "401" in err_msg or "cookie" in err_msg.lower():
                        print_status("DB Yazma", "FAIL", "YETKİ HATASI (401)!")
                        print(f"   👉 {Colors.YELLOW}ÇÖZÜM:{Colors.RESET} .env dosyasındaki SUPABASE_KEY 'service_role' key olmalı.")
                    elif "404" in err_msg:
                         print_status("DB Yazma", "FAIL", "TABLO BULUNAMADI. 'SYSTEM' tablosunun varlığından emin olun.")
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
    # Gerekli kütüphane kontrolü
    try:
        import requests
    except ImportError:
        print("⚠️  Eksik kütüphane: 'requests'. Lütfen 'pip install requests' çalıştırın.")
        sys.exit(1)
        
    run_test()