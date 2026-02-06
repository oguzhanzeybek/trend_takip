import pandas as pd
import os
from pathlib import Path

def merge_fix_columns_and_reset_rank():
    # Kodun çalıştığı dizini bul
    current_file_path = Path(__file__).resolve()
    output_dir = current_file_path.parent
    
    # Scraper kök dizini
    scraper_root = output_dir.parents[1] 
    
    # Hedef kategoriler
    target_categories = ["online_shopping", "Rival", "social_media"]

    print(f"--- BİRLEŞTİRME: Ürün Adı Eşitleme ve Rank Sıfırlama ---\n📁 Çalışma Dizini: {scraper_root}\n")

    for category in target_categories:
        category_path = scraper_root / category
        
        if not category_path.exists():
            continue

        print(f"📂 Kategori: {category}")
        
        all_csv_files = list(category_path.rglob("*.csv"))
        category_dataframes = []

        for file_path in all_csv_files:
            # Çıktı dosyasının kendisini okuma
            if file_path.name == f"{category}.csv":
                continue

            try:
                if file_path.stat().st_size == 0:
                    continue

                # Dosyayı oku
                try:
                    df = pd.read_csv(file_path, encoding='utf-8')
                except UnicodeDecodeError:
                    df = pd.read_csv(file_path, encoding='latin1')
                except pd.errors.EmptyDataError:
                    continue
                
                if df.empty:
                    continue

                # --- ADIM 1: Sütun İsimlerini Temizle (Boşlukları sil) ---
                df.columns = [c.strip() for c in df.columns]

                # --- ADIM 2: Ürün Adlarını Eşitle (Alibaba ve Diğerlerini Birleştir) ---
                # Farklı isimleri tek bir standart isme ('Ürün Adı') dönüştür
                rename_map = {
                    'Ürün Başlığı': 'Ürün Adı',  # Alibaba düzeltmesi
                    'Başlık': 'Ürün Adı',
                    'Trend Başlık': 'Ürün Adı',  # Trendler için
                    'Product Name': 'Ürün Adı',
                    'Title': 'Ürün Adı'
                }
                df.rename(columns=rename_map, inplace=True)

                # --- ADIM 3: Rank (Sıralama) Sıfırlama ---
                # Dosyadaki eski Rank/Sıra sütununu silip 1'den başlatıyoruz
                # Böylece 504 gibi sayılar yerine 1,2,3 gelir.
                cols_to_drop = [c for c in df.columns if c.lower() in ['rank', 'sıra', 'sira', 'no', 'site sırası']]
                if cols_to_drop:
                    df.drop(columns=cols_to_drop, inplace=True)
                
                # Yeni temiz Rank oluştur
                df.insert(0, 'Rank', range(1, len(df) + 1))

                # --- ADIM 4: KAYNAK Sütunu Ekle ---
                source_name = file_path.name
                df.insert(0, 'KAYNAK', source_name)

                # Gereksiz tamamen boş sütunları sil (Amazon'daki ,, sorununu çözer)
                df.dropna(how='all', axis=1, inplace=True)
                
                # Veri tiplerini string yap
                df = df.astype(str)

                category_dataframes.append(df)
                print(f"   ✅ Eklendi: {source_name} (Sıralama 1-{len(df)} olarak ayarlandı)")

            except Exception as e:
                print(f"   ❌ Hata: {file_path.name} - {e}")

        # --- BİRLEŞTİRME VE KAYDETME ---
        if category_dataframes:
            # sort=False ile sütun sırasını koru
            merged_df = pd.concat(category_dataframes, ignore_index=True, sort=False)
            
            # Sütunları Düzenle: KAYNAK -> Rank -> Ürün Adı -> Diğerleri
            cols = list(merged_df.columns)
            priority_cols = ['KAYNAK', 'Rank', 'Ürün Adı']
            
            # Öncelikli sütunları listeden çıkarıp başa ekleyeceğiz
            final_cols = []
            for col in priority_cols:
                if col in cols:
                    final_cols.append(col)
                    cols.remove(col)
            
            # Kalan sütunları ekle
            final_cols += cols
            
            merged_df = merged_df[final_cols]
            merged_df = merged_df.fillna("") # Nan değerleri boş yap

            # Kaydet
            output_filename = f"{category}.csv"
            save_path = output_dir / output_filename
            
            merged_df.to_csv(save_path, index=False, encoding='utf-8-sig')
            print(f"🎉 OLUŞTURULDU: {output_filename} (Toplam {len(merged_df)} satır)\n")
        else:
            print(f"⚠️ '{category}' için veri yok.\n")

if __name__ == "__main__":
    merge_fix_columns_and_reset_rank()