import os
import json
import pandas as pd
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path
import time
import sys
import warnings

# Gereksiz uyarıları sustur
warnings.filterwarnings("ignore")

# --- YENİ EKLENTİ: ARAMA KÜTÜPHANESİ ---
try:
    from duckduckgo_search import DDGS
except ImportError:
    try:
        from ddgs import DDGS
    except ImportError:
        print("❌ HATA: 'duckduckgo-search' kütüphanesi eksik.")
        print("👉 Çözüm: pip install duckduckgo-search")
        sys.exit(1)

BASE_DIR = Path(__file__).resolve().parent

env_path = None
search_dirs = [BASE_DIR] + list(BASE_DIR.parents)[:3]
for d in search_dirs:
    if (d / '.env').exists():
        env_path = d / '.env'
        load_dotenv(dotenv_path=env_path)
        break

api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENROUTER_KEY")

if not api_key:
    print("❌ HATA: OPENROUTER_API_KEY veya OPENROUTER_KEY bulunamadı! .env dosyasını kontrol et.")
    sys.exit(1)

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key, 
)

MODEL_NAME = "openai/gpt-4o-mini"
BATCH_SIZE = 5 
WAIT_TIME = 1 

def truncate_text(text, max_chars=1000):
    """Token maliyetini düşürmek için metni kısaltır."""
    if len(text) > max_chars:
        return text[:max_chars] + "..."
    return text

def clean_data(df):
    """
    TEMİZLİK VE KIRPMA
    """
    initial_len = len(df)
    print(f"   🧹 Ön temizlik... (Giriş: {initial_len})")
    
    # --- KRİTİK EKLEME: Orijinal Index'i Kaybetmemek İçin Sütuna Çeviriyoruz ---
    # Bu sayede drop_duplicates yapılsa bile orijinal sıra numarası "original_index" sütununda kalır.
    df['original_index'] = df.index 
    
    df = df.dropna(how='all').drop_duplicates(subset=df.columns.difference(['original_index']))
    
    # Kolon isimlerini temizle (boşlukları at)
    df.columns = df.columns.str.strip()
    
    df_temp = df.copy()
    
    # Metin kısaltma işlemi (original_index hariç)
    cols_to_process = [c for c in df_temp.columns if c != 'original_index']
    if cols_to_process:
        df_temp[cols_to_process] = df_temp[cols_to_process].astype(str).apply(
            lambda col: col.apply(lambda x: truncate_text(x, 1000))
        )
    
    print(f"   ✨ Veri Hazır (AI Elemesi için): {len(df_temp)} satır")
    return df_temp 

def get_progress_file_path(filename):
    data_dir = BASE_DIR / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / f"{filename}_progress.txt"

def get_last_index(filename):
    p_file = get_progress_file_path(filename)
    if p_file.exists():
        with open(p_file, "r") as f:
            try: return int(f.read().strip())
            except: return 0
    return 0

def save_progress(filename, index):
    with open(get_progress_file_path(filename), "w") as f:
        f.write(str(index))

def append_to_csv(data, filename):
    output_path = BASE_DIR / "data" / f"filtered_{filename}.csv"
    df = pd.DataFrame(data)
    
    cols = ['rank', 'kaynak_dosya', 'urun_adi', 'fiyat', 'potansiyel_skoru', 'link', 'not', 'aciklama']
    
    available_cols = [c for c in cols if c in df.columns]
    df = df[available_cols]

    if not output_path.exists():
        df.to_csv(output_path, index=False, encoding='utf-8-sig', mode='w')
    else:
        df.to_csv(output_path, index=False, encoding='utf-8-sig', mode='a', header=False)

# --- CANLI ARAMA FONKSİYONU ---
def search_live_context(keyword):
    if not keyword or len(keyword) < 2: return "Veri yok."
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(f"{keyword} fiyatı ne kadar", region='tr-tr', safesearch='off', max_results=2))
            if not results: return "İnternette güncel bilgi bulunamadı."
            context = " | ".join([f"{r['title']}: {r['body']}" for r in results])
            return context[:800] 
    except:
        return "Arama yapılamadı."

# --- GÜNCELLENEN ANALİZ FONKSİYONU ---
def analyze_paid_fast(df_chunk, file_key, df_columns, retry=0):
    results_list = []
    
    cols_lower = {c.lower(): c for c in df_chunk.columns}
    
    # Kritik Sütunları Belirle
    col_kaynak = cols_lower.get("kaynak") or cols_lower.get("source")
    col_fiyat = cols_lower.get("fiyat") or cols_lower.get("price")
    col_link = cols_lower.get("link") or cols_lower.get("url")

    # Ürün Sütununu Akıllı Bulma
    possible_names = ["urun", "urun_adi", "ürün adı", "ürün başlığı", "product_name", "product", "name", "title", "trend"]
    col_urun = None
    for name in possible_names:
        if name in cols_lower:
            col_urun = cols_lower[name]
            break

    # SATIR SATIR İŞLE
    for _, row in df_chunk.iterrows():
        
        # --- KRİTİK DÜZELTME: ORİJİNAL INDEX'İ SÜTUNDAN AL ---
        # Artık loop indexini değil, clean_data'da sakladığımız 'original_index' değerini kullanıyoruz.
        real_original_rank = row.get('original_index', 0) 
        
        original_source = str(row[col_kaynak]) if col_kaynak else file_key 
        original_link = str(row[col_link]) if col_link else ""
        original_price = str(row[col_fiyat]) if col_fiyat else ""
        
        product_name = ""
        if col_urun:
            product_name = str(row[col_urun])
        else:
            vals = [str(x) for x in row.values if x != real_original_rank and not str(x).isdigit() and not str(x).startswith("http")]
            product_name = max(vals, key=len) if vals else "Bilinmeyen Ürün"

        # İsim Kısaltma
        short_name = product_name
        if len(product_name) > 60:
            short_name = product_name[:57] + "..."

        # Canlı Arama
        print(f"      🔎 Analiz Ediliyor (Orj Index: {real_original_rank}): {short_name}...")
        search_context = search_live_context(product_name) 
        time.sleep(1)

        # --- GÜNCELLENMİŞ, DAHA SERT SKORLAMA PROMPT'U ---
        prompt = f"""
        Sen acımasız, gerçekçi bir tüccar ve pazar analistisin. 
        Hayal satma, gerçek verilere ve ticari mantığa odaklan.

        ÜRÜN: {product_name}
        MEVCUT FİYAT (Varsa): {original_price}
        İNTERNET VERİSİ: {search_context}
        
        GÖREV:
        Bu ürün al-sat (arbitraj) yapmak veya stoklamak için KARLI MI?
        
        PUANLAMA ALGORİTMASI (0-100):
        - 0-50: Çöp. Her yerde var, kâr marjı yok, modası geçmiş veya kimsenin almayacağı ürün.
        - 51-74: Riskli. Belki satar ama uğraşmaya değmez.
        - 75-89: İyi Fırsat. Talep var, fiyat rekabetçi olabilir.
        - 90-100: Altın Yumurtlayan Tavuk. Kesinlikle listeye girmeli.

        KURALLAR:
        1. Ürün çok yaygınsa (market raf ürünü vb.) düşük puan ver.
        2. Fiyat bilgisi yoksa internet verisine bak, tahmin et.
        
        ÇIKTI FORMATI (Sadece JSON):
        {{ 
            "aciklama": "Neden mantıklı veya değil? (Net, kısa, ticari yorum)", 
            "not": "#İlgiliHashtagler", 
            "potansiyel_skoru": (Sayısal Puan) 
        }}
        """
        
        try:
            completion = client.chat.completions.create(
                extra_headers={"HTTP-Referer": "http://localhost"},
                model=MODEL_NAME,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
            )
            resp = completion.choices[0].message.content
            if "```" in resp: resp = resp.split("```json")[-1].split("```")[0].strip()
            ai_data = json.loads(resp)
            
            score = int(ai_data.get("potansiyel_skoru", 0))

            # --- EŞİK DEĞERİ ---
            if score < 65:
                print(f"      🗑️  Düşük Puan ({score}): {short_name} -> ELENDİ.")
                continue 

            print(f"      ✅  Yüksek Puan ({score}): {short_name} -> EKLENİYOR.")
            
            final_obj = {
                "rank": real_original_rank,             # --- DÜZELTİLDİ: Kesinlikle orijinal index ---
                "kaynak_dosya": original_source,
                "urun_adi": short_name,
                "fiyat": original_price,
                "potansiyel_skoru": score,
                "link": original_link,
                "not": ai_data.get("not", ""),
                "aciklama": ai_data.get("aciklama", "Açıklama yok.")
            }
            results_list.append(final_obj)
            
        except Exception as e:
            print(f"      ⚠️ AI Hatası (Satır atlandı): {e}")
            continue

    return results_list

def process_files():
    
    raw_data_dir = BASE_DIR.parent / "Raw_data"
    output_dir = BASE_DIR / "data"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    target_files = ["Rival.csv", "online_shopping.csv", "social_media.csv"]
    
    print(f"📂 Okunacak Klasör: {raw_data_dir}")
    print(f"💎 Model: {MODEL_NAME} (HAZIR)")
    print(f"🌍 Mod: Orijinal Index Korumalı + Sert Filtre")
    print("------------------------------------------------")

    if not raw_data_dir.exists():
        print(f"❌ HATA: Raw data klasörü bulunamadı: {raw_data_dir}")
        return

    for filename in target_files:
        if not (raw_data_dir / filename).exists():
            print(f"⚠️ Dosya bulunamadı, atlanıyor: {filename}")
            continue

        print(f"\n🚀 {filename} İŞLENİYOR...")
        
        try:
            # Sütun isimleri ne olursa olsun okur
            df = pd.read_csv(raw_data_dir / filename, dtype=str, low_memory=False).fillna("")
        except Exception as e:
            print(f"❌ Okuma hatası ({filename}): {e}")
            continue
        
        df_clean = clean_data(df)
        total_rows = len(df_clean)
        
        file_key = filename.split('.')[0]
        start_index = get_last_index(file_key) # Buradaki index artık işlenen satır sayısıdır
        
        if start_index >= total_rows:
            print(f"   ✅ Zaten bitmiş.")
            continue
        elif start_index > 0:
            print(f"   ⏩ {start_index}. sıradaki veriden devam ediliyor.")

        df_columns = df_clean.columns.tolist()

        for i in range(start_index, total_rows, BATCH_SIZE):
            batch_df = df_clean.iloc[i : i + BATCH_SIZE]
            
            print(f"   ⏳ İşleniyor (Batch): {i} - {min(i+BATCH_SIZE, total_rows)}")
            
            results = analyze_paid_fast(batch_df, file_key, df_columns)
            
            if results:
                append_to_csv(results, file_key)
                print(f"      💾 {len(results)} Fırsat Ürünü EKLENDİ.")
            else:
                print("      ❌ Bu partide uygun ürün çıkmadı.")

            save_progress(file_key, i + BATCH_SIZE)

        print(f"🎉 {filename} TAMAMLANDI!")

if __name__ == "__main__":
    process_files()
    
    print("\n🧹 Tüm işlemler bitti, geçici progress dosyaları temizleniyor...")
    
    files_to_clean = ["Rival", "online_shopping", "social_media"]
    
    for file_key in files_to_clean:
        progress_path = get_progress_file_path(file_key)
        
        if progress_path.exists():
            try:
                progress_path.unlink()
                print(f"   🗑️  SİLİNDİ: {progress_path.name}")
            except Exception as e:
                print(f"   ⚠️ SİLİNEMEDİ: {progress_path.name} -> {e}")
        else:
            print(f"   ℹ️  Zaten yok: {progress_path.name}")

    print("🏁 PROGRAM SONLANDI.")