import pandas as pd
import os
from pathlib import Path

def merge_with_source_at_start():
    output_dir = Path(__file__).resolve().parent
    
    scraper_root = output_dir.parents[1]
    
    target_categories = ["online_shopping", "Rival", "social_media"]

    print(f"--- BİRLEŞTİRME İŞLEMİ BAŞLIYOR ---\n📁 Kök Dizin: {scraper_root}\n")

    for category in target_categories:
        category_path = scraper_root / category
        
        if not category_path.exists():
            print(f"⚠️ [ATLANDI] '{category}' klasörü bulunamadı.")
            continue

        print(f"📂 Kategori Taranıyor: {category}")
        
        all_csv_files = list(category_path.rglob("*.csv"))
        
        if not all_csv_files:
            print(f"   ⚠️ Bu kategoride hiç CSV dosyası yok.")
            continue

        category_dataframes = []

        for file_path in all_csv_files:
            if file_path.parent == output_dir:
                continue

            try:
                if file_path.stat().st_size == 0:
                    print(f"   ⚠️ Boş Dosya Atlandı: {file_path.name}")
                    continue

                try:
                    df = pd.read_csv(file_path, encoding='utf-8')
                except UnicodeDecodeError:
                    df = pd.read_csv(file_path, encoding='latin1')
                except pd.errors.EmptyDataError:
                    print(f"   ⚠️ Veri Yok (EmptyData): {file_path.name}")
                    continue
                
                if df.empty:
                    print(f"   ⚠️ Tablo Boş: {file_path.name}")
                    continue

                source_name = file_path.name 
                if 'KAYNAK' not in df.columns:
                    df.insert(0, 'KAYNAK', source_name)
                
                df = df.astype(str)
                
                category_dataframes.append(df)
                print(f"   ✅ Eklendi: {source_name} ({len(df)} satır)")
                
            except Exception as e:
                print(f"   ❌ Hata: {file_path.name} okunamadı: {e}")

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