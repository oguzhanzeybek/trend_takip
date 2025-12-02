import pandas as pd
import os
from pathlib import Path

def merge_with_source_at_start():
    # 1. Çıktı klasörü (Bu scriptin olduğu yer: .../ai_filter/Raw_data)
    output_dir = Path(__file__).resolve().parent
    
    # 2. Scraper ana klasörüne çık (.../scraper)
    # Eğer klasör yapısı değişirse burayı .parents[2] vs. yapmak gerekebilir.
    scraper_root = output_dir.parents[1]
    
    # Hedef kategoriler
    target_categories = ["online_shopping", "Rival", "social_media"]

    print(f"--- BİRLEŞTİRME İŞLEMİ BAŞLIYOR ---\n📁 Kök Dizin: {scraper_root}\n")

    for category in target_categories:
        category_path = scraper_root / category
        
        if not category_path.exists():
            print(f"⚠️ [ATLANDI] '{category}' klasörü bulunamadı.")
            continue

        print(f"📂 Kategori Taranıyor: {category}")
        
        # Alt klasörler dahil tüm CSV'leri bul
        all_csv_files = list(category_path.rglob("*.csv"))
        
        if not all_csv_files:
            print(f"   ⚠️ Bu kategoride hiç CSV dosyası yok.")
            continue

        category_dataframes = []

        for file_path in all_csv_files:
            # Oluşturulan birleştirilmiş dosyaları (social_media.csv gibi) tekrar okumamak için kontrol:
            # Eğer okunan dosya output_dir içindeyse (yani zaten oluşturulmuş bir raw dosaysa) atla.
            if file_path.parent == output_dir:
                continue

            try:
                # Boş dosya kontrolü
                if file_path.stat().st_size == 0:
                    print(f"   ⚠️ Boş Dosya Atlandı: {file_path.name}")
                    continue

                # CSV Oku
                try:
                    df = pd.read_csv(file_path, encoding='utf-8')
                except UnicodeDecodeError:
                    df = pd.read_csv(file_path, encoding='latin1')
                except pd.errors.EmptyDataError:
                    print(f"   ⚠️ Veri Yok (EmptyData): {file_path.name}")
                    continue
                
                # Veri çerçevesi boşsa atla
                if df.empty:
                    print(f"   ⚠️ Tablo Boş: {file_path.name}")
                    continue

                # --- KAYNAK BİLGİSİ EKLEME ---
                source_name = file_path.name 
                # 'KAYNAK' sütunu zaten varsa tekrar ekleme
                if 'KAYNAK' not in df.columns:
                    df.insert(0, 'KAYNAK', source_name)
                
                # Tüm sütunları string'e çevir (Veri tipleri karışmasın diye)
                df = df.astype(str)
                
                category_dataframes.append(df)
                print(f"   ✅ Eklendi: {source_name} ({len(df)} satır)")
                
            except Exception as e:
                print(f"   ❌ Hata: {file_path.name} okunamadı: {e}")

        # Birleştirme ve Kaydetme
        if category_dataframes:
            merged_df = pd.concat(category_dataframes, ignore_index=True, sort=False)
            
            output_filename = f"{category}.csv"
            save_path = output_dir / output_filename
            
            merged_df.to_csv(save_path, index=False, encoding='utf-8-sig')
            print(f"🎉 OLUŞTURULDU: {output_filename} (Toplam {len(merged_df)} satır)\n")
        else:
            print(f"⚠️ '{category}' için birleştirilecek geçerli veri bulunamadı.\n")

if __name__ == "__main__":
    merge_with_source_at_start()