import pandas as pd
import os
from pathlib import Path

def merge_with_source_at_start():
    # 1. Çıktı klasörü (raw.py'nin olduğu yer)
    output_dir = Path(__file__).resolve().parent
    
    # 2. Scraper ana klasörüne çık
    scraper_root = output_dir.parents[1]
    
    # Hedef kategoriler
    target_categories = ["online_shopping", "Rival", "social_media"]

    print(f"--- İşlem Başlıyor: {scraper_root} ---\n")

    for category in target_categories:
        category_path = scraper_root / category
        
        if not category_path.exists():
            print(f"[ATLANDI] '{category}' klasörü bulunamadı.")
            continue

        print(f"📂 Kategori Taranıyor: {category}")
        
        all_csv_files = list(category_path.rglob("*.csv"))
        category_dataframes = []

        for file_path in all_csv_files:
            try:
                # CSV Oku
                try:
                    df = pd.read_csv(file_path, encoding='utf-8')
                except UnicodeDecodeError:
                    df = pd.read_csv(file_path, encoding='latin1')
                
                # --- KRİTİK ADIM: Kaynak bilgisini EN BAŞA (0. İndeks) ekle ---
                # insert(indeks, sütun_adı, değer)
                # Dosya ismini (örn: amazon.csv) ilk sütun yapar.
                source_name = file_path.name 
                df.insert(0, 'KAYNAK', source_name)
                
                category_dataframes.append(df)
                print(f"   Success: {source_name} (Satır: {len(df)})")
                
            except Exception as e:
                print(f"   Error: {file_path.name} okunamadı: {e}")

        # Birleştirme ve Kaydetme
        if category_dataframes:
            merged_df = pd.concat(category_dataframes, ignore_index=True, sort=False)
            
            output_filename = f"{category}.csv"
            save_path = output_dir / output_filename
            
            merged_df.to_csv(save_path, index=False, encoding='utf-8-sig')
            print(f"✅ OLUŞTURULDU: {output_filename} (Toplam {len(merged_df)} satır)\n")
        else:
            print(f"⚠️ '{category}' içinde veri bulunamadı.\n")

if __name__ == "__main__":
    merge_with_source_at_start()