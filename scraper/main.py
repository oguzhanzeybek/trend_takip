import subprocess
import sys
import os
import time
import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

sys.path.append(str(BASE_DIR))

try:
    from dotenv import load_dotenv
    ENV_PATH = BASE_DIR / ".env"
    if ENV_PATH.exists():
        load_dotenv(dotenv_path=ENV_PATH, override=True)
except ImportError:
    print("⚠️ dotenv kütüphanesi yüklü değil, sistem değişkenleri kullanılacak.")

try:
    from core.database_manager import DatabaseManager
except ImportError as e:
    print(f"⚠️ DatabaseManager yüklenemedi: {e}")
    DatabaseManager = None

if not os.getenv("OPENROUTER_API_KEY") and os.getenv("OPENROUTER_KEY"):
    os.environ["OPENROUTER_API_KEY"] = os.getenv("OPENROUTER_KEY")
    print("✅ Github Secret Eşleşmesi Sağlandı: OPENROUTER_KEY -> OPENROUTER_API_KEY")


LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "hata_kayitlari.txt"


SCRAPER_SCRIPTS = [
    "scripts/test_system.py",  # YENİ YERİ: scripts klasörü
    "online_shopping/alibaba/alibaba.py",
    "online_shopping/amazon/amazon.py",
    "online_shopping/n11/n11.py",
    "online_shopping/trendyol/trendyol.py",
    "Rival/a101/a101.py",
    "Rival/CarrefourSA/carrefoursa.py",
    "social_media/google_trends/google_trend.py",
    "social_media/google_trends/google_trend_168.py",
    "social_media/instagram/instagram.py",
    "social_media/tiktok/tiktok.py",
    "social_media/twitter/twitter_scrapper.py",
    "social_media/youtube/youtube_trend.py",
]

MERGER_SCRIPT = "ai_filter/Raw_data/raw.py"

AI_SCRIPTS = [
    "ai_filter/preprocessed_data/preprocessed_ai.py",
    "social_analysis/social_analysis.py"
]

UPLOAD_SCRIPT = "scripts/upload_all_csvs.py"


def log_error(script_name, error_msg):
    """Hataları dosyaya kaydeder."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    separator = "-" * 50
    log_entry = f"\n{separator}\n[{timestamp}] ❌ HATA - {script_name}\n{separator}\n{error_msg}\n{separator}\n"
    
    print(f"\n⚠️  HATA DETAYI LOGLANDI: {LOG_FILE}")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_entry)

def run_script(rel_path):
    """
    Scripti çalıştırır ve çıktıları ANLIK (CANLI) olarak ekrana basar.
    """
    script_path = BASE_DIR / rel_path
    
    if not script_path.exists():
        msg = f"Dosya bulunamadı: {script_path}"
        print(f"⚠️  {msg} (Atlanıyor...)")
        log_error(rel_path, msg)
        return

    print(f"\n" + "="*60)
    print(f"🚀 BAŞLATILIYOR: {script_path.name}")
    print(f"📂 Konum: {script_path.parent}")
    print("-" * 60)
    
    start_time = time.time()
    current_env = os.environ.copy()

    python_path = current_env.get("PYTHONPATH", "")
    current_env["PYTHONPATH"] = f"{BASE_DIR}{os.pathsep}{python_path}"

    try:
        process = subprocess.Popen(
            [sys.executable, str(script_path)],
            cwd=script_path.parent,  # Scripti kendi klasöründe çalıştır
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            errors='replace',
            env=current_env,
            bufsize=1
        )

        for line in process.stdout:
            print(line, end='')

        process.wait()

        if process.returncode == 0:
            elapsed = time.time() - start_time
            print("-" * 60)
            print(f"✅ TAMAMLANDI: {script_path.name} | Süre: {elapsed:.2f} sn")
            print("=" * 60 + "\n")
        else:
            print(f"\n❌ İŞLEM HATALI BİTTİ: {script_path.name}")
            log_error(script_path.name, f"Process exited with code {process.returncode}")

    except Exception as e:
        print(f"\n❌ KRİTİK SİSTEM HATASI: {script_path.name}")
        print(f"🔻 Detay: {str(e)}")
        log_error(script_path.name, str(e))

def save_system_report(start_time):
    """Sistem çalışması bitince veritabanına özet rapor atar."""
    if DatabaseManager is None:
        return

    end_time = time.time()
    duration = end_time - start_time
    
    error_content = ""
    if LOG_FILE.exists():
        try:
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                content = f.read()
                if len(content.strip()) > 0:
                      error_content = content[-2000:]
        except: pass

    status = "SUCCESS" if not error_content else "COMPLETED_WITH_ERRORS"
    
    report_payload = {
        "category": "SYSTEM_LOG",
        "data_type": "AUTO_REPORT",
        "source": "main.py", 
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
        db.insert_data("processed_data", [report_payload]) 
        print("✅ Rapor başarıyla processed_data tablosuna kaydedildi.")
    except Exception as e:
        print(f"⚠️ Rapor gönderme hatası: {e}")


def main():
    if LOG_FILE.exists():
        open(LOG_FILE, 'w').close()

    global_start = time.time()
    
    print("\n**************************************************")
    print(" 🛠️  TREND TAKİP OTOMASYONU - BAŞLATILIYOR")
    print("**************************************************")
    
    if DatabaseManager:
        print("✅ DatabaseManager (Core) aktif.")
    else:
        print("⚠️ DatabaseManager pasif (Sadece log tutulacak).")

    print("\n┌──────────────────────────────┐")
    print("│ [1/4] VERİ TOPLAMA AŞAMASI   │")
    print("└──────────────────────────────┘")
    for script in SCRAPER_SCRIPTS:
        run_script(script)
        time.sleep(1)
    
    print("\n┌───────────────────────────────────┐")
    print("│ [2/4] VERİ BİRLEŞTİRME (MERGE)    │")
    print("└───────────────────────────────────┘")
    run_script(MERGER_SCRIPT)

    print("\n┌───────────────────────────────────┐")
    print("│ [3/4] AI ANALİZ VE FİNAL KAYIT    │")
    print("└───────────────────────────────────┘")
    for script in AI_SCRIPTS:
        run_script(script)

    print("\n┌───────────────────────────────────┐")
    print("│ [4/4] CSV DOSYALARI YÜKLENİYOR    │")
    print("└───────────────────────────────────┘")
    
    run_script(UPLOAD_SCRIPT)

    save_system_report(global_start)

    print("\n🎉 TÜM İŞLEMLER SONA ERDİ!")
    if LOG_FILE.exists() and os.path.getsize(LOG_FILE) > 0:
        print(f"ℹ️  DİKKAT: İşlem sırasında hatalar oluştu. Logları kontrol edin: logs/hata_kayitlari.txt")

if __name__ == "__main__":
    main()