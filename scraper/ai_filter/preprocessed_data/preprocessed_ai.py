import os
import json
import pandas as pd
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path
import time
import sys

# --- API KEY ve CLIENT AYARLARI ---
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
BATCH_SIZE = 50 
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
    
    df = df.dropna(how='all').drop_duplicates() 
    
    df_temp = df.copy()
    if df_temp.shape[1] > 1:
        # Rank ve Kaynak gibi kritik sütunların verisini koruyarak diğerlerini kısalt
        df_temp.iloc[:, 1:] = df_temp.iloc[:, 1:].astype(str).apply(
            lambda col: col.apply(lambda x: truncate_text(x, 1000))
        )
    
    print(f"   ✨ Veri Hazır (AI Elemesi için): {len(df_temp)} satır")
    return df_temp.astype(str) 

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
    
    # --- GÜNCELLEME BURADA ---
    # 'link' sütunu listeye eklendi. Artık CSV'ye yazılacak.
    cols = ['rank', 'kaynak_dosya', 'urun_adi', 'fiyat', 'potansiyel_skoru', 'link', 'not']
    
    # Gelen veride eksik kolon varsa hata vermesin diye kontrol
    available_cols = [c for c in cols if c in df.columns]
    df = df[available_cols]

    if not output_path.exists():
        df.to_csv(output_path, index=False, encoding='utf-8-sig', mode='w')
    else:
        df.to_csv(output_path, index=False, encoding='utf-8-sig', mode='a', header=False)

def analyze_paid_fast(data_chunk, category, df_columns, retry=0):
    column_names = ", ".join(df_columns) 
    
    # --- PROMPT GÜNCELLEMESİ ---
    # Link kuralı (7. madde) ve JSON şablonuna "link" alanı eklendi.
    prompt = f"""
    Sen, Metro Market'in HORECA sektörüne odaklanmış Stratejik Pazar Analistisin.
    
    GÖREV: Aşağıdaki '{category}' verilerini analiz et.
    Kolon İsimleri: [{column_names}]
    
    **ÇOK ÖNEMLİ KURALLAR (HATA YAPMA):**
    1. **RANK (SIRA) FORMATI:** Ham verideki 'Rank' değerini bul ve **SADECE SAYISAL DEĞERİ** al. 
       - Yanlış: "#3", "No: 1", "Sıra 5"
       - Doğru: "3", "1", "5"
       - Eğer rank verisi yoksa veya boşsa, bu alanı boş bırakma, listedeki sırasını yaz.
    2. Sadece çok tutulan ve trend potansiyeli olan ürünleri seç.
    3. Ürün ismini **KISALT** (Temel nitelik kalsın, gereksiz detayları at).
    4. Her ürün için **Potansiyel Skoru** (0-100) ver.
    5. 'kaynak_dosya' alanına ham verinin ilk sütunundaki bilgiyi aynen yaz.
    6. Yorum/Analiz yapma, sadece JSON döndür.
    7. **LİNK AKTARIMI:** Eğer ham veride 'Link', 'url' veya benzeri bir sütun varsa, o linki 'link' alanına AYNEN kopyala. Link yoksa boş bırak.

    VERİ:
    {data_chunk}

    ÇIKTI FORMATI (JSON):
    [
      {{ 
        "rank": "Sadece sayı (Örn: '1')",
        "kaynak_dosya": "Dosya adı",
        "urun_adi": "Kısaltılmış Ürün Adı", 
        "fiyat": "Fiyat", 
        "potansiyel_skoru": 85,
        "link": "Varsa ürün linki buraya, yoksa boş string",
        "not": "#Etiketler"
      }}
    ]
    """
    
    try:
        completion = client.chat.completions.create(
            extra_headers={"HTTP-Referer": "http://localhost", "X-Title": "ProScraper"},
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
        )
        
        resp = completion.choices[0].message.content
        if "```" in resp:
            resp = resp.split("```json")[-1].split("```")[0].strip()
            resp = resp.replace("```", "").strip()
            
        return json.loads(resp)
    
    except Exception as e:
        err = str(e)
        if "402" in err or "insufficient_quota" in err:
            print("\n❌ HATA: Yetersiz Bakiye!")
            sys.exit(1)
            
        if retry < 3:
            print(f"      ⚠️ Geçici Hata ({err}). Tekrar deneniyor... ({retry+1})")
            time.sleep(2)
            return analyze_paid_fast(data_chunk, category, df_columns, retry + 1)
        
        print(f"❌ 3 deneme başarısız. Son Hata: {err}")
        return []

def process_files():
    
    raw_data_dir = BASE_DIR.parent / "Raw_data"
    output_dir = BASE_DIR / "data"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    target_files = ["Rival.csv", "online_shopping.csv", "social_media.csv"]
    
    print(f"📂 Okunacak Klasör: {raw_data_dir}")
    print(f"💎 Model: {MODEL_NAME} (HAZIR)")
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
            # Rank kaybolmasın diye dtype=str
            df = pd.read_csv(raw_data_dir / filename, dtype=str, low_memory=False).fillna("")
        except Exception as e:
            print(f"❌ Okuma hatası ({filename}): {e}")
            continue
        
        df_clean = clean_data(df)
        total_rows = len(df_clean)
        
        file_key = filename.split('.')[0]
        start_index = get_last_index(file_key)
        
        if start_index >= total_rows:
            print(f"   ✅ Zaten bitmiş.")
            continue
        elif start_index > 0:
            print(f"   ⏩ {start_index}. satırdan devam.")

        df_columns = df_clean.columns.tolist()

        for i in range(start_index, total_rows, BATCH_SIZE):
            batch = df_clean.iloc[i : i + BATCH_SIZE]
            
            # index=False önemli
            batch_str = batch.to_string(header=False, index=False) 
            
            print(f"   ⏳ İşleniyor: {i} - {min(i+BATCH_SIZE, total_rows)} (Toplam: {total_rows})")
            
            results = analyze_paid_fast(batch_str, file_key, df_columns)
            
            if results:
                append_to_csv(results, file_key)
                print(f"      💾 {len(results)} veri EKLENDİ.")
            else:
                print("      ❌ Veri yok.")

            save_progress(file_key, i + BATCH_SIZE)
            time.sleep(WAIT_TIME)

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