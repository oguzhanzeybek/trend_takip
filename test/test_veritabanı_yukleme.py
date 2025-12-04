import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime  # <-- 1. Tarih kütüphanesini ekledik

try:
    import pandas as pd
except ImportError:
    print("❌ HATA: 'pandas' kütüphanesi eksik.")
    print("💡 ÇÖZÜM: Terminale şunu yazıp enter'a bas: pip install pandas")
    sys.exit(1)

current_file_path = Path(__file__).resolve()
parent_dir = current_file_path.parent
grandparent_dir = current_file_path.parent.parent

sys.path.append(str(parent_dir))
sys.path.append(str(grandparent_dir))

possible_paths = [
    grandparent_dir / "scraper",
    parent_dir / "scraper",
    Path(r"C:\Users\darks\OneDrive\Masaüstü\trend_takip\scraper")
]

for path in possible_paths:
    if path.exists():
        sys.path.append(str(path))

try:
    from database_manager import DatabaseManager
except ImportError:
    print(f"❌ HATA: 'database_manager.py' dosyası bulunamadı.")
    sys.exit(1)

def upload_csv_to_db(csv_path):
    print(f"\n🚀 CSV Yükleme İşlemi Başlatılıyor: {csv_path}")
    
    try:
        db = DatabaseManager()
    except Exception as e:
        print(f"❌ DatabaseManager başlatılamadı: {e}")
        return

    if not db.client:
        print("❌ Veritabanı bağlantısı kurulamadı (.env veya API Key hatası).")
        return

    try:
        df = pd.read_csv(csv_path, encoding="utf-8-sig")
        print(f"📊 Toplam {len(df)} satır veri okundu.")
    except Exception as e:
        print(f"❌ CSV okuma hatası: {e}")
        return

    formatted_data = []
    
    simdiki_zaman = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        for index, row in df.iterrows():
            row_dict = row.where(pd.notnull(row), None).to_dict()
            
            payload = {
                "category": "deneme",         # İstersen burayı "RIVAL_ANALYSIS" yapabilirsin
                "data_type": "test",          # İstersen burayı "CSV_DATA" yapabilirsin
                "source": f"csv_upload_{os.path.basename(csv_path)}",
                "created_at_custom": simdiki_zaman,  # <-- 2. YENİ EKLENEN TARİH DAMGASI
                "content": row_dict
            }
            formatted_data.append(payload)
    except Exception as e:
        print(f"❌ Veri dönüştürme hatası: {e}")
        return

    print("⏳ Veriler veritabanına gönderiliyor...")
    try:
        db.insert_data("processed_data", formatted_data)
        print(f"✅ BAŞARILI: {len(formatted_data)} adet kayıt 'processed_data' tablosuna yüklendi.")
        print(f"🕒 Kayıt Tarihi Etiketi: {simdiki_zaman}")
    except Exception as e:
        print(f"❌ Yükleme sırasında hata oluştu: {e}")
        if "relation" in str(e) and "does not exist" in str(e):
             print("💡 İPUCU: 'processed_data' tablosu yok. Supabase'de tabloyu oluşturman gerek.")

if __name__ == "__main__":
    target_csv_path = r"C:\Users\darks\OneDrive\Masaüstü\trend_takip\scraper\social_media\youtube\youtube_trends_tag.csv"
    
    if os.path.exists(target_csv_path):
        print(f"📂 Hedef dosya bulundu: {target_csv_path}")
        try:
            upload_csv_to_db(target_csv_path)
        except Exception as e:
            print(f"❌ Yükleme sırasında hata oluştu: {e}")
    else:
        print(f"❌ Dosya bulunamadı: {target_csv_path}")
        print("Lütfen dosya yolunu kontrol et.")
        
        
        
        
        
     