import os
import sys
import pandas as pd
import json 
from datetime import datetime
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent.parent 

if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

try:
    from scraper.core.database_manager import DatabaseManager
except ImportError as e:
    print("❌ KRİTİK HATA: 'scraper' modülü bulunamadı. Lütfen dosya yapısını kontrol edin.")
    print(f"Python'ın Aradığı Kök Dizin: {PROJECT_ROOT}")
    print(f"Detaylı Hata: {e}")
    sys.exit(1)

TARGET_FILES = [
    "scraper/ai_filter/preprocessed_data/data/filtered_online_shopping.csv",
    "scraper/ai_filter/preprocessed_data/data/filtered_Rival.csv",
    "scraper/ai_filter/preprocessed_data/data/filtered_social_media.csv",
    "scraper/ai_filter/Raw_data/online_shopping.csv",
    "scraper/ai_filter/Raw_data/Rival.csv",
    "scraper/ai_filter/Raw_data/social_media.csv",
    
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
            # NaN değerleri boş string yapıyoruz (JSON null hatası vermemesi için)
            df = pd.read_csv(full_path, encoding="utf-8-sig").fillna("")
            
            if df.empty:
                print("⚠️ Dosya boş, atlanıyor.")
                return
            
            # DataFrame'i sözlük listesine çevir
            formatted_data = df.to_dict(orient='records')

        elif full_path.suffix == '.json':
            with open(full_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            json_list = []
            
            if isinstance(data, list):
                json_list = data
            elif isinstance(data, dict):
                potential_keys = ['analyzed_records', 'results', 'data', 'content']
                found = False
                for key in potential_keys:
                    if key in data and isinstance(data[key], list):
                        json_list = data[key]
                        found = True
                        break
                
                if not found:
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

        print(f"   📊 Okunan Kayıt Sayısı: {len(formatted_data)}")
    
    except Exception as e:
        print(f"❌ Okuma Hatası ({full_path.name}): {e}")
        return
        
    
    category, data_type = get_file_info(full_path.name)
    simdiki_zaman = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    payloads_for_db = []
    
    for item in formatted_data:
        # Rank değerini temizle ve integer yap
        rank_val = item.get("Rank") or item.get("rank") or item.get("trend_rank")
        
        final_rank = None
        if rank_val is not None:
            try:
                clean_r = ''.join(filter(str.isdigit, str(rank_val)))
                if clean_r:
                    final_rank = int(clean_r)
            except:
                final_rank = None

        # --- GÜNCELLEME: AÇIKLAMA KONTROLÜ ---
        # Eğer item (satır) içinde 'aciklama' yoksa, boş string olarak ekle.
        # Böylece JSON içinde mutlaka bir "aciklama" alanı olur.
        if "aciklama" not in item:
            item["aciklama"] = ""

        # Veritabanına gidecek paket
        payload = {
            "category": category,           
            "data_type": data_type,         
            "source": full_path.name,       
            "created_at_custom": simdiki_zaman,
            "trend_rank": final_rank, 
            
            # DİKKAT: 'aciklama' burada AYRI bir sütun olarak YOK.
            # 'content' içine 'item'ı koyuyoruz. 'item'ın içinde 'aciklama' zaten var (CSV'den geldi).
            "content": item 
        }
        payloads_for_db.append(payload)

    try:
        # Eski verileri temizleyelim mi? (İsteğe bağlı, duplicate önlemek için iyi olabilir)
        # db.client.table("processed_data").delete().eq("source", full_path.name).execute()

        batch_size = 1000
        total_inserted = 0
        
        for i in range(0, len(payloads_for_db), batch_size):
            batch = payloads_for_db[i:i + batch_size]
            db.insert_data("processed_data", batch)
            total_inserted += len(batch)
            print(f"   ⏳ {total_inserted}/{len(payloads_for_db)} yüklendi...")
            
        print(f"✅ {full_path.name} BAŞARIYLA YÜKLENDİ.")
        
    except Exception as e:
        print(f"❌ Veritabanı Hatası ({full_path.name}): {e}")

def main():
    print("🚀 TOPLU CSV/JSON YÜKLEME BAŞLATILIYOR (JSONB İçine Açıklama Dahil)...")
    
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