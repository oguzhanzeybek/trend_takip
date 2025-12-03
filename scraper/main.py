import subprocess
import sys
import os
import time
import datetime
from pathlib import Path

# --- 1. ORTAM DEĞİŞKENLERİ VE AYARLAR ---
BASE_DIR = Path(__file__).resolve().parent

<<<<<<< HEAD
# .env Dosyasını Yükleme
=======
# .env Dosyasını Yükleme (Lokal Çalışma İçin)
>>>>>>> origin/main
try:
    from dotenv import load_dotenv
    ENV_PATH = BASE_DIR / ".env"
    if ENV_PATH.exists():
<<<<<<< HEAD
=======
        # Override=True ile .env'deki değişikliği anında algılamasını sağlarız
>>>>>>> origin/main
        load_dotenv(dotenv_path=ENV_PATH, override=True)
except ImportError:
    print("⚠️ dotenv kütüphanesi yüklü değil, sistem değişkenleri kullanılacak.")

# GITHUB ACTIONS ANAHTAR UYUMU
if not os.getenv("OPENROUTER_API_KEY") and os.getenv("OPENROUTER_KEY"):
    os.environ["OPENROUTER_API_KEY"] = os.getenv("OPENROUTER_KEY")
    print("✅ Github Secret Eşleşmesi Sağlandı: OPENROUTER_KEY -> OPENROUTER_API_KEY")

<<<<<<< HEAD
# --- 2. MODÜLLERİN KONTROLÜ ---
# DatabaseManager'ı sadece raporlama için import etmeye çalışıyoruz
try:
    sys.path.append(str(BASE_DIR))
    sys.path.append(str(BASE_DIR / "scraper")) # Scraper klasörünü de ekle
    from database_manager import DatabaseManager
except ImportError:
    print("⚠️ DatabaseManager modülü yüklenemedi. Sistem raporu veritabanına yazılamayacak.")
    DatabaseManager = None

=======
# --- 2. MODÜLLERİN YÜKLENMESİ ---

# Veritabanı Yöneticisi
try:
    sys.path.append(str(BASE_DIR))
    from database_manager import DatabaseManager
except ImportError:
    print("⚠️ DatabaseManager modülü yüklenemedi. Raporlama devre dışı.")
    DatabaseManager = None

# CSV Yükleyici
try:
    from upload_csvs import upload_files
except ImportError:
    print("⚠️ upload_csvs.py bulunamadı. CSV yükleme adımı çalışmayacak.")
    upload_files = None

>>>>>>> origin/main
# --- 3. SABİTLER VE LİSTELER ---
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "hata_kayitlari.txt"

<<<<<<< HEAD
# NOT: Dosyaların 'scraper/' klasörü altında olduğu varsayılmıştır.
# Eğer main.py dosyan scraper klasörünün içindeyse, baştaki 'scraper/' kısımlarını sil.

=======
# Çalıştırılacak Scriptler
>>>>>>> origin/main
SCRAPER_SCRIPTS = [
    "scraper/test_system.py",
    "scraper/online_shopping/alibaba/alibaba.py",
    "scraper/online_shopping/amazon/amazon.py",
    "scraper/online_shopping/n11/n11.py",
    "scraper/online_shopping/trendyol/trendyol.py",
    "scraper/Rival/a101/a101.py",
    "scraper/Rival/CarrefourSA/carrefoursa.py",
    "scraper/social_media/google_trends/google_trend.py",
    "scraper/social_media/google_trends/google_trend_168.py",
    "scraper/social_media/instagram/instagram.py",
    "scraper/social_media/tiktok/tiktok.py",
    "scraper/social_media/twitter/twitter_scrapper.py",
    "scraper/social_media/youtube/youtube_trend.py",
]

MERGER_SCRIPT = "scraper/ai_filter/Raw_data/raw.py"

AI_SCRIPTS = [
    "scraper/ai_filter/preprocessed_data/preprocessed_ai.py",
    "scraper/social_analysis/social_analysis.py"
]

<<<<<<< HEAD
# YENİ EKLENEN TOPLU YÜKLEME SCRİPTİ
UPLOAD_SCRIPT = "scraper/upload_all_csvs.py"

=======
>>>>>>> origin/main
# --- 4. YARDIMCI FONKSİYONLAR ---

def log_error(script_name, error_msg):
    """Hataları dosyaya kaydeder."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    separator = "-" * 50
    log_entry = f"\n{separator}\n[{timestamp}] ❌ HATA - {script_name}\n{separator}\n{error_msg}\n{separator}\n"
    
<<<<<<< HEAD
=======
    print(f"\n⚠️  HATA DETAYI LOGLANDI: {LOG_FILE}")
>>>>>>> origin/main
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_entry)

def run_script(rel_path):
    """
    Scripti çalıştırır ve çıktıları ANLIK (CANLI) olarak ekrana basar.
    """
    script_path = BASE_DIR / rel_path
    
    # Dosya yolu kontrolü
    if not script_path.exists():
        # Belki 'scraper/' ön eki olmadan denenmeli?
        alt_path = BASE_DIR / rel_path.replace("scraper/", "")
        if alt_path.exists():
            script_path = alt_path
        else:
            msg = f"Dosya bulunamadı: {rel_path}"
            print(f"⚠️  {msg} (Atlanıyor...)")
            log_error(rel_path, msg)
            return

    print(f"\n" + "="*60)
    print(f"🚀 BAŞLATILIYOR: {script_path.name}")
    print(f"📂 Konum: {script_path.parent}")
    print("-" * 60)
    
    start_time = time.time()
    current_env = os.environ.copy()

<<<<<<< HEAD
    # Python yolu ayarları (Modül import hatalarını önlemek için)
    python_path = current_env.get("PYTHONPATH", "")
    current_env["PYTHONPATH"] = f"{BASE_DIR}{os.pathsep}{BASE_DIR}/scraper{os.pathsep}{python_path}"

=======
>>>>>>> origin/main
    try:
        # Popen ile işlemi başlatıyoruz (stdout=PIPE ile çıktıyı yakalıyoruz)
        process = subprocess.Popen(
            [sys.executable, str(script_path)],
            cwd=script_path.parent,
<<<<<<< HEAD
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, # Hataları da aynı kanaldan al
            text=True,
            encoding='utf-8',
            errors='replace',
            env=current_env,
            bufsize=1 # Satır satır bufferla
        )

        # Çıktıyı CANLI olarak okuyup ekrana basma döngüsü
        for line in process.stdout:
            print(line, end='') # line zaten \n içerir

        process.wait() # İşlem bitene kadar bekle
=======
            stdout=sys.stdout,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            errors='replace',
            env=current_env          
        )

        stdout, stderr = process.communicate()
>>>>>>> origin/main

        if process.returncode == 0:
            elapsed = time.time() - start_time
            print("-" * 60)
            print(f"✅ TAMAMLANDI: {script_path.name} | Süre: {elapsed:.2f} sn")
            print("=" * 60 + "\n")
        else:
<<<<<<< HEAD
            print(f"\n❌ İŞLEM HATALI BİTTİ: {script_path.name}")
            log_error(script_path.name, f"Process exited with code {process.returncode}")

=======
            raise subprocess.CalledProcessError(process.returncode, script_path.name, output=stdout, stderr=stderr)

    except subprocess.CalledProcessError as e:
        print(f"\n❌ İŞLEM BAŞARISIZ: {script_path.name}")
        error_details = f"Çıkış Kodu: {e.returncode}\n"
        error_details += f"Hata Özeti: {e.stderr.strip().splitlines()[-1] if e.stderr else 'Yok'}"
        
        if e.stderr:
            print(f"🔻 {e.stderr.strip().splitlines()[-1]}")
        
        log_error(script_path.name, e.stderr if e.stderr else error_details)
        
>>>>>>> origin/main
    except Exception as e:
        print(f"\n❌ KRİTİK SİSTEM HATASI: {script_path.name}")
        print(f"🔻 Detay: {str(e)}")
        log_error(script_path.name, str(e))

def save_system_report(start_time):
<<<<<<< HEAD
    """Sistem çalışması bitince veritabanına özet rapor atar."""
=======
    """Sistem çalışması bitince YENİ veritabanı yapısına uygun log atar."""
>>>>>>> origin/main
    if DatabaseManager is None:
        return

    end_time = time.time()
    duration = end_time - start_time
    
<<<<<<< HEAD
    # Hata var mı kontrol et
=======
    # Log dosyasını oku (Son hatalar)
>>>>>>> origin/main
    error_content = ""
    if LOG_FILE.exists():
        try:
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                content = f.read()
<<<<<<< HEAD
                # Eğer son çalıştırmadan kalma taze hata varsa al
                # Basit kontrol: Dosya boş değilse hata vardır kabul ediyoruz
                if len(content.strip()) > 0:
                     error_content = content[-2000:]
=======
                error_content = content[-2000:] if content else ""
>>>>>>> origin/main
        except: pass

    status = "SUCCESS" if not error_content else "COMPLETED_WITH_ERRORS"
    
<<<<<<< HEAD
    report_payload = {
        "category": "SYSTEM_LOG",
        "data_type": "AUTO_REPORT",
        "source": "main.py", 
=======
    # --- VERİTABANI GÜNCELLEMESİ BURADA YAPILDI ---
    # Yeni yapı: category, data_type, source, content (JSONB)
    report_payload = {
        "category": "SYSTEM_LOG",
        "data_type": "AUTO_REPORT",
        "source": "main.py",  # Yeni standartta 'source_file' yerine 'source' kullanıyoruz
>>>>>>> origin/main
        "content": {
            "title": f"Sistem Çalışma Raporu - {datetime.datetime.now().strftime('%Y-%m-%d')}",
            "duration_seconds": round(duration, 2),
            "status": status,
            "error_log_snippet": error_content,
            "timestamp": datetime.datetime.now().isoformat(),
            "environment": "GitHub Actions" if os.getenv("GITHUB_ACTIONS") else "Local Environment"
        }
    }
    
    try:
        print("\n📝 Sistem raporu veritabanına gönderiliyor...")
        db = DatabaseManager()
<<<<<<< HEAD
        db.insert_data("processed_data", [report_payload]) 
=======
        
        # HEDEF TABLO GÜNCELLENDİ: 'daily_trends' yerine 'processed_data'
        # Eğer 'logs' adında ayrı bir tablonuz varsa burayı "logs" olarak değiştirebilirsiniz.
        db.insert_data("processed_data", [report_payload]) 
        
>>>>>>> origin/main
        print("✅ Rapor başarıyla processed_data tablosuna kaydedildi.")
    except Exception as e:
        print(f"⚠️ Rapor gönderme hatası: {e}")

# --- 5. ANA FONKSİYON ---

def main():
    # Başlangıçta log dosyasını temizleyelim ki eski hatalar karışmasın
    if LOG_FILE.exists():
        open(LOG_FILE, 'w').close()

    global_start = time.time()
    
    print("\n**************************************************")
    print(" 🛠️  TREND TAKİP OTOMASYONU - BAŞLATILIYOR")
    print("**************************************************")
    
<<<<<<< HEAD
=======
    if DatabaseManager:
        print("✅ DatabaseManager aktif.")
    else:
        print("⚠️ DatabaseManager pasif (Sadece log tutulacak).")

>>>>>>> origin/main
    # --- 1. Veri Toplama ---
    print("\n┌──────────────────────────────┐")
    print("│ [1/4] VERİ TOPLAMA AŞAMASI   │")
    print("└──────────────────────────────┘")
    for script in SCRAPER_SCRIPTS:
        run_script(script)
        time.sleep(1)
    
    # --- 2. Veri Birleştirme ---
    print("\n┌───────────────────────────────────┐")
    print("│ [2/4] VERİ BİRLEŞTİRME (MERGE)    │")
    print("└───────────────────────────────────┘")
    run_script(MERGER_SCRIPT)

    # --- 3. AI Analiz ---
    print("\n┌───────────────────────────────────┐")
    print("│ [3/4] AI ANALİZ VE FİNAL KAYIT    │")
    print("└───────────────────────────────────┘")
    for script in AI_SCRIPTS:
        run_script(script)

    # --- 4. CSV Yükleme (FİNAL ADIM) ---
    print("\n┌───────────────────────────────────┐")
    print("│ [4/4] CSV DOSYALARI YÜKLENİYOR    │")
    print("└───────────────────────────────────┘")
<<<<<<< HEAD
    
    # Yeni upload_all_csvs.py scriptini çalıştırıyoruz
    run_script(UPLOAD_SCRIPT)
=======
    if upload_files:
        upload_files()
    else:
        print("⚠️ Yükleme modülü bulunamadığı için bu adım atlandı.")
>>>>>>> origin/main

    # --- SON: Raporlama ---
    save_system_report(global_start)

    print("\n🎉 TÜM İŞLEMLER SONA ERDİ!")
    if LOG_FILE.exists() and os.path.getsize(LOG_FILE) > 0:
        print(f"ℹ️  DİKKAT: İşlem sırasında hatalar oluştu. Logları kontrol edin: logs/hata_kayitlari.txt")

if __name__ == "__main__":
    main()