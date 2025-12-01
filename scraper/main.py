import subprocess
import sys
import os
import time
import datetime  # 📅 Tarih ve saat kaydı için eklendi
from pathlib import Path

# Proje ana dizini (Otomatik algılar)
BASE_DIR = Path(__file__).resolve().parent

# --- LOG SİSTEMİ İÇİN AYAR ---
# Hataları kaydedeceğimiz klasör ve dosya
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True) # Klasör yoksa oluşturur
LOG_FILE = LOG_DIR / "hata_kayitlari.txt"

# ==============================================================================
# 1. AŞAMA: VERİ TOPLAYICILAR (SCRAPERS)
# (Senin güncellediğin tam liste)
# ==============================================================================
SCRAPER_SCRIPTS = [
    # --- Online Shopping ---
    "online_shopping/alibaba/alibaba.py",
    "online_shopping/amazon/amazon.py",
    "online_shopping/n11/n11.py",
    "online_shopping/trendyol/trendyol.py",
    
    # --- Rival (Rakipler) ---
    "Rival/a101/a101.py",
    "Rival/CarrefourSA/carrefoursa.py",
    
    # --- Social Media ---
    "social_media/google_trends/google_trend.py",
    "social_media/google_trends/google_trend_168.py", # ✅ Eklediğin yeni dosya
    "social_media/instagram/instagram.py",
    "social_media/tiktok/tiktok.py",
    "social_media/twitter/twitter_scrapper.py",
    "social_media/youtube/youtube_trend.py"
]

# ==============================================================================
# 2. AŞAMA: VERİ BİRLEŞTİRME (RAW DATA MERGE)
# Dağınık dosyaları toplayıp 3 ana CSV haline getiren kod
# ==============================================================================
MERGER_SCRIPT = "ai_filter/Raw_data/raw.py"

# ==============================================================================
# 3. AŞAMA: AI ANALİZ VE FİNAL İŞLEME
# ==============================================================================
AI_SCRIPTS = [
    # 1. Ürünleri filtrele, puanla ve Supabase'e (veya CSV'ye) yaz
    "ai_filter/preprocessed_data/preprocessed_ai.py",
    
    # 2. Sosyal medya verisine duygu analizi yap
    "social_analysis/social_analysis.py"
]

def log_error(script_name, error_msg):
    """Hataları tarih ve saatle birlikte dosyaya yazar."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] ❌ HATA - {script_name} : {error_msg}\n"
    
    # Konsola da bilgi ver
    print(f"    📝 Hata günlüğe işlendi: logs/hata_kayitlari.txt")
    
    # Dosyaya ekle (append mode)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_entry)

def run_script(rel_path):
    """Verilen Python dosyasını çalıştırır, hata varsa kaydeder ve DEVAM EDER."""
    script_path = BASE_DIR / rel_path
    
    if not script_path.exists():
        msg = f"Dosya bulunamadı: {rel_path}"
        print(f"⚠️ {msg} (Atlanıyor...)")
        log_error(rel_path, msg)
        return

    print(f"\n🚀 BAŞLATILIYOR: {script_path.name}...")
    
    start_time = time.time()
    try:
        # Scripti, sanki kendi klasöründeymiş gibi çalıştır (cwd=parent)
        # Bu sayede script içindeki dosya yolları bozulmaz.
        subprocess.run(
            [sys.executable, str(script_path)], 
            check=True,
            cwd=script_path.parent 
        )
        elapsed = time.time() - start_time
        print(f"✅ TAMAMLANDI: {script_path.name} ({elapsed:.2f} sn)")
        
    except subprocess.CalledProcessError as e:
        # Script çalışırken hata verip kapandıysa (Exit code != 0)
        error_msg = f"Çökme kodu (Exit Code): {e.returncode}"
        print(f"❌ HATA OLUŞTU: {script_path.name} atlanıyor...")
        log_error(script_path.name, error_msg)
        
    except Exception as e:
        # Python veya sistem kaynaklı beklenmedik hata
        print(f"❌ KRİTİK HATA: {script_path.name}")
        log_error(script_path.name, str(e))

def main():
    print("==========================================")
    print("   🛒 TREND TAKİP - HATAYA DAYANIKLI MOD   ")
    print("==========================================")
    
    # --- 1. Veri Toplama ---
    print("\n--- [1/3] VERİ TOPLAMA AŞAMASI ---")
    for script in SCRAPER_SCRIPTS:
        run_script(script)
        time.sleep(1) # Siteler banlamasın diye minik bekleme

    # --- 2. Veri Birleştirme ---
    print("\n--- [2/3] VERİ BİRLEŞTİRME (RAW MERGE) ---")
    run_script(MERGER_SCRIPT)
    
    # --- 3. AI Analiz ---
    print("\n--- [3/3] AI ANALİZ VE FİNAL KAYIT ---")
    for script in AI_SCRIPTS:
        run_script(script)

    print("\n------------------------------------------")
    if LOG_FILE.exists():
        print(f"ℹ️  Hatalar (varsa) şurada: {LOG_FILE}")
    print("🎉 TÜM İŞLEMLER TAMAMLANDI!")

if __name__ == "__main__":
    main()