import os
import sys
import pandas as pd
from datetime import datetime
from pathlib import Path

# --- YOL AYARLARI (GitHub Actions ve Local Uyumlu) ---
# Scriptin bulunduğu konumu al
CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parent if CURRENT_DIR.name == "scraper" else CURRENT_DIR

# DatabaseManager'ı bulabilmek için yolları ekle
sys.path.append(str(CURRENT_DIR))
sys.path.append(str(ROOT_DIR))
sys.path.append(str(ROOT_DIR / "scraper"))

try:
    from scraper.core.database_manager import DatabaseManager
except ImportError:
    # Eğer yukarıdakiler çalışmazsa manuel path eklemesi (Yedek)
    sys.path.append(os.path.join(os.getcwd(), 'scraper'))
    try:
        from scraper.core.database_manager import DatabaseManager
    except ImportError:
        print("❌ HATA: 'database_manager.py' bulunamadı. Lütfen dosya yapısını kontrol et.")
        sys.exit(1)

# --- YÜKLENECEK DOSYALARIN LİSTESİ ---
# GitHub Actions "checkout" yaptığında kök dizinden başlar.
# Dosya yollarını ekran görüntüne göre ayarladım.
TARGET_FILES = [
    "scraper/ai_filter/preprocessed_data/data/filtered_online_shopping.csv",
    "scraper/ai_filter/preprocessed_data/data/filtered_Rival.csv",
    "scraper/ai_filter/preprocessed_data/data/filtered_social_media.csv",
    "scraper/ai_filter/Raw_data/online_shopping.csv",
    "scraper/ai_filter/Raw_data/Rival.csv",
    "scraper/ai_filter/Raw_data/social_media.csv"
]

def get_file_info(filename):
    """Dosya ismine bakarak Kategori ve Veri Tipini belirler."""
    # Örnek: filtered_online_shopping.csv
    
    clean_name = filename.replace(".csv", "")
    
    if "filtered_" in clean_name:
        data_type = "Filtered"
        category = clean_name.replace("filtered_", "")
    else:
        data_type = "Raw"
        category = clean_name
        
    return category, data_type

def upload_single_file(db, file_path):
    full_path = Path(file_path).resolve()
    
    # GitHub Actions'ta bazen path sorunu olabilir, kök dizinden kontrol edelim
    if not full_path.exists():
        # Alternatif: Scriptin çalıştığı yerden arama
        full_path = (ROOT_DIR / file_path).resolve()
    
    if not full_path.exists():
        print(f"⚠️ DOSYA BULUNAMADI (Atlanıyor): {file_path}")
        return

    print(f"\n📂 İşleniyor: {full_path.name}")
    
    try:
        df = pd.read_csv(full_path, encoding="utf-8-sig")
        if df.empty:
            print("⚠️ Dosya boş, atlanıyor.")
            return
            
        print(f"   📊 Okunan Satır: {len(df)}")
    except Exception as e:
        print(f"❌ Okuma Hatası: {e}")
        return

    # Kategori ve Tip belirleme
    category, data_type = get_file_info(full_path.name)
    simdiki_zaman = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    formatted_data = []
    
    for index, row in df.iterrows():
        # NaN değerleri temizle
        row_dict = row.where(pd.notnull(row), None).to_dict()
        
        payload = {
            "category": category,          # Örn: online_shopping
            "data_type": data_type,        # Örn: Filtered veya Raw
            "source": full_path.name,      # Dosya adı
            "created_at_custom": simdiki_zaman,
            "content": row_dict            # Tüm satır verisi JSON içinde
        }
        formatted_data.append(payload)

    # Veritabanına Yükle
    try:
        # 1000'erli paketler halinde yükle (Çok büyük dosyalar için güvenlik)
        batch_size = 1000
        total_inserted = 0
        
        for i in range(0, len(formatted_data), batch_size):
            batch = formatted_data[i:i + batch_size]
            db.insert_data("processed_data", batch)
            total_inserted += len(batch)
            print(f"   ⏳ {total_inserted}/{len(formatted_data)} yüklendi...")
            
        print(f"✅ {full_path.name} BAŞARIYLA YÜKLENDİ.")
        
    except Exception as e:
        print(f"❌ Veritabanı Hatası ({full_path.name}): {e}")

def main():
    print("🚀 TOPLU CSV YÜKLEME BAŞLATILIYOR...")
    
    try:
        db = DatabaseManager()
        if not db.client:
            raise Exception("Supabase bağlantısı yok.")
    except Exception as e:
        print(f"❌ Veritabanı bağlantı hatası: {e}")
        return

    for file_rel_path in TARGET_FILES:
        upload_single_file(db, file_rel_path)

    print("\n🏁 TÜM İŞLEMLER TAMAMLANDI.")

if __name__ == "__main__":
    main()