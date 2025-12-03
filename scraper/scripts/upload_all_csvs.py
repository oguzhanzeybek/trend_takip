import os
import sys
import pandas as pd
import json # JSON işlemleri için eklendi
from datetime import datetime
from pathlib import Path

# --- YOL AYARLARI (KESİN ÇÖZÜM) ---

# Scriptin bulunduğu konumu al: C:\...\trend_takip\scraper\scripts
CURRENT_DIR = Path(__file__).resolve().parent

# Projenin ana kök dizinini (trend_takip) hesapla.
PROJECT_ROOT = CURRENT_DIR.parent.parent 

# 'scraper' paketinin bulunduğu dizin (C:\...\trend_takip) 
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

try:
    from scraper.core.database_manager import DatabaseManager
except ImportError as e:
    print("❌ KRİTİK HATA: 'scraper' modülü bulunamadı. Lütfen dosya yapısını kontrol edin.")
    print(f"Python'ın Aradığı Kök Dizin: {PROJECT_ROOT}")
    print(f"Detaylı Hata: {e}")
    sys.exit(1)

# --- YÜKLENECEK DOSYALARIN LİSTESİ ---
TARGET_FILES = [
    # Mevcut CSV dosyaları
    "scraper/ai_filter/preprocessed_data/data/filtered_online_shopping.csv",
    "scraper/ai_filter/preprocessed_data/data/filtered_Rival.csv",
    "scraper/ai_filter/preprocessed_data/data/filtered_social_media.csv",
    "scraper/ai_filter/Raw_data/online_shopping.csv",
    "scraper/ai_filter/Raw_data/Rival.csv",
    "scraper/ai_filter/Raw_data/social_media.csv",
    
    # Yeni JSON dosyası eklendi
    "scraper/social_analysis/data/analyzed_social_media_ultra_detailed_sentiment.json"
]

def get_file_info(filename):
    """Dosya ismine bakarak Kategori ve Veri Tipini belirler."""
    
    clean_name = filename.split('.')[0]
    
    if "analyzed_" in filename and filename.endswith(".json"):
        data_type = "Analyzed"
        category = "social_media_sentiment"
        return category, data_type

    if "filtered_" in clean_name:
        data_type = "Filtered"
        category = clean_name.replace("filtered_", "")
    else:
        data_type = "Raw"
        category = clean_name
            
    return category, data_type

def upload_single_file(db, file_path):
    
    full_path = (PROJECT_ROOT / file_path).resolve()
    
    if not full_path.exists():
        print(f"⚠️ DOSYA BULUNAMADI (Atlanıyor): {file_path}. Tam yol kontrol: {full_path}")
        return

    print(f"\n📂 İşleniyor: {full_path.name}")
    
    formatted_data = []
    
    try:
        if full_path.suffix == '.csv':
            # --- CSV OKUMA ---
            df = pd.read_csv(full_path, encoding="utf-8-sig")
            if df.empty:
                print("⚠️ Dosya boş, atlanıyor.")
                return
            
            for _, row in df.iterrows():
                row_dict = row.where(pd.notnull(row), None).to_dict()
                formatted_data.append(row_dict)

        elif full_path.suffix == '.json':
            # --- JSON OKUMA (UYARILAR KALDIRILDI) ---
            with open(full_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            json_list = []
            
            if isinstance(data, list):
                # Durum 1: JSON doğrudan bir liste ise
                json_list = data
            elif isinstance(data, dict):
                # Durum 2: JSON bir sözlük ise (Liste bir anahtar altında olabilir)
                
                potential_keys = ['analyzed_records', 'results', 'data', 'content']
                found = False
                for key in potential_keys:
                    if key in data and isinstance(data[key], list):
                        json_list = data[key]
                        found = True
                        break
                
                if not found:
                    # Liste bulunamazsa, tüm sözlüğü tek bir kayıt olarak kabul et
                    json_list = [data] 
            else:
                print("⚠️ JSON içeriği ne liste ne de sözlük formatında, atlanıyor.")
                return

            if not json_list:
                 print("⚠️ JSON dosyası boş veya işlenecek kayıt bulunamadı, atlanıyor.")
                 return
                 
            formatted_data = json_list 
            
        else:
            print(f"❌ Desteklenmeyen dosya formatı: {full_path.suffix}. Atlanıyor.")
            return

        # Okunan kayıt sayısını yine de gösteriyoruz
        print(f"   📊 Okunan Kayıt Sayısı: {len(formatted_data)}")
    
    except Exception as e:
        print(f"❌ Okuma Hatası ({full_path.name}): {e}")
        return
        
    # --- VERİ HAZIRLAMA VE YÜKLEME ---
    
    category, data_type = get_file_info(full_path.name)
    simdiki_zaman = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    payloads_for_db = []
    
    for item in formatted_data:
        payload = {
            "category": category,           
            "data_type": data_type,         
            "source": full_path.name,       
            "created_at_custom": simdiki_zaman,
            "content": item 
        }
        payloads_for_db.append(payload)

    # Veritabanına Yükle
    try:
        batch_size = 1000
        total_inserted = 0
        
        for i in range(0, len(payloads_for_db), batch_size):
            batch = payloads_for_db[i:i + batch_size]
            db.insert_data("processed_data", batch)
            total_inserted += len(batch)
            print(f"   ⏳ {total_inserted}/{len(payloads_for_db)} yüklendi...")
            
        print(f"✅ {full_path.name} BAŞARIYLA YÜKLENDİ.")
        
    except Exception as e:
        print(f"❌ Veritabanı Hatası ({full_path.name}): {e}")

def main():
    print("🚀 TOPLU CSV/JSON YÜKLEME BAŞLATILIYOR...")
    
    try:
        db = DatabaseManager() 
        if not db.client:
            raise Exception("Supabase bağlantısı yok.")
    except Exception as e:
        # .env uyarısı DatabaseManager içinden geldiği için burayı değiştirmedik.
        # Çıktıdaki uyarı DatabaseManager'a aittir ve burada kontrol edilemez.
        print(f"❌ Veritabanı bağlantı hatası: {e}")
        return

    for file_rel_path in TARGET_FILES:
        upload_single_file(db, file_rel_path)

    print("\n🏁 TÜM İŞLEMLER TAMAMLANDI.")

if __name__ == "__main__":
    main()