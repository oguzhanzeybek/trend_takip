import subprocess
import sys
import os
import time
import datetime
from pathlib import Path

# --- AYARLAR ---
BASE_DIR = Path(__file__).resolve().parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "hata_kayitlari.txt"

# ==============================================================================
# LİSTELER (Senin listelerin aynı kalıyor)
# ==============================================================================
SCRAPER_SCRIPTS = [
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
    "social_media/youtube/youtube_trend.py"
]

MERGER_SCRIPT = "ai_filter/Raw_data/raw.py"

AI_SCRIPTS = [
    "ai_filter/preprocessed_data/preprocessed_ai.py",
    "social_analysis/social_analysis.py"
]

def log_error(script_name, error_msg):
    """Hataları dosyaya kaydeder."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    separator = "-" * 50
    log_entry = f"\n{separator}\n[{timestamp}] ❌ HATA - {script_name}\n{separator}\n{error_msg}\n{separator}\n"
    
    # Hata oluştuğunda ekrana kırmızımsı bir uyarı bas (ANSI renk kodları destekleniyorsa)
    print(f"\n⚠️  HATA DETAYI LOGLANDI: {LOG_FILE}")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_entry)

def run_script(rel_path):
    """
    Scripti çalıştırır ve çıktıları ANLIK (CANLI) olarak ekrana basar.
    Hata olursa stderr'i yakalayıp loglar.
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
    
    # Popen kullanarak işlemi başlatıyoruz, bu sayede çıktıları anlık okuyabiliriz
    try:
        process = subprocess.Popen(
            [sys.executable, str(script_path)],
            cwd=script_path.parent,
            stdout=sys.stdout,      # Çıktıyı direkt ana konsola ver (Canlı izleme için)
            stderr=subprocess.PIPE, # Hataları yakala (Loglamak için)
            text=True,              # String olarak işle
            encoding='utf-8',       # Türkçe karakter sorunu olmasın
            errors='replace'        # Okunamayan karakter olursa patlamasın
        )

        # İşlemin bitmesini bekle
        # stdout zaten sys.stdout'a bağlı olduğu için printler anında ekrana düşecek.
        stdout, stderr = process.communicate()

        if process.returncode == 0:
            elapsed = time.time() - start_time
            print("-" * 60)
            print(f"✅ TAMAMLANDI: {script_path.name} | Süre: {elapsed:.2f} sn")
            print("=" * 60 + "\n")
        else:
            # Hata durumu (Exit code != 0)
            raise subprocess.CalledProcessError(process.returncode, script_path.name, output=stdout, stderr=stderr)

    except subprocess.CalledProcessError as e:
        print(f"\n❌ İŞLEM BAŞARISIZ: {script_path.name}")
        
        # Hata mesajını oluştur
        error_details = f"Çıkış Kodu (Exit Code): {e.returncode}\n\n"
        error_details += "--- HATA DETAYI (STDERR) ---\n"
        error_details += e.stderr if e.stderr else "Hata çıktısı yakalanamadı."
        
        # Ekrana hatanın son satırını bas (kullanıcı görsün)
        if e.stderr:
            print(f"🔻 Hata Özeti: {e.stderr.strip().splitlines()[-1]}")
        
        log_error(script_path.name, error_details)
        
    except Exception as e:
        print(f"\n❌ KRİTİK SİSTEM HATASI: {script_path.name}")
        print(f"🔻 Detay: {str(e)}")
        log_error(script_path.name, str(e))

def main():
    print("\n**************************************************")
    print(" 🛠️  TREND TAKİP OTOMASYONU - BAŞLATILIYOR")
    print("**************************************************")
    
    # --- 1. Veri Toplama ---
    print("\n┌──────────────────────────────┐")
    print("│ [1/3] VERİ TOPLAMA AŞAMASI   │")
    print("└──────────────────────────────┘")
    for script in SCRAPER_SCRIPTS:
        run_script(script)
        # Sistem nefes alsın diye 1 sn bekleme
        time.sleep(1)
  
    # --- 2. Veri Birleştirme ---
    print("\n┌───────────────────────────────────┐")
    print("│ [2/3] VERİ BİRLEŞTİRME (MERGE)    │")
    print("└───────────────────────────────────┘")
    run_script(MERGER_SCRIPT)

    # --- 3. AI Analiz ---
    print("\n┌───────────────────────────────────┐")
    print("│ [3/3] AI ANALİZ VE FİNAL KAYIT    │")
    print("└───────────────────────────────────┘")
    for script in AI_SCRIPTS:
        run_script(script)

    print("\n🎉 TÜM İŞLEMLER SONA ERDİ!")
    if LOG_FILE.exists():
        print(f"ℹ️  Hatalar (varsa) şuraya kaydedildi: logs/hata_kayitlari.txt")

if __name__ == "__main__":
    main()