import os
import json
import pandas as pd
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path
import time
import sys

# --- AYARLAR (ÇALIŞAN FİNAL MOD) ---
# En stabil, en hızlı ve maliyeti en düşük model: GPT-4o-mini
MODEL_NAME = "openai/gpt-4o-mini"

# Stabil ve hızlı işlem için ideal ayarlar
BATCH_SIZE = 50 
WAIT_TIME = 1  # 1 saniye dinlenme (Hız için)

# --- BAĞLANTI VE DİNAMİK YOL ---
BASE_DIR = Path(__file__).resolve().parent

env_path = None
search_dirs = [BASE_DIR] + list(BASE_DIR.parents)[:3]
for d in search_dirs:
    if (d / '.env').exists():
        env_path = d / '.env'
        load_dotenv(dotenv_path=env_path)
        break

api_key = os.getenv("OPENROUTER_KEY")
if not api_key:
    print("❌ HATA: OPENROUTER_KEY bulunamadı!")
    sys.exit(1)

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
)

# --- YARDIMCI FONKSİYONLAR ---

def truncate_text(text, max_chars=1000):
    """Token maliyetini düşürmek için metni kısaltır."""
    if len(text) > max_chars:
        return text[:max_chars] + "..."
    return text

def clean_data(df):
    """
    TEMİZLİK VE KIRPMA (Kaynak Sütunu Korumalı)
    ⚠️ YALNIZCA FORMATLAMA VE TOKEN TASARRUFU YAPAR, SATIR ELEME İŞLEMİ AI'YA DEVREDİLDİ.
    """
    initial_len = len(df)
    print(f"   🧹 Ön temizlik... (Giriş: {initial_len})")
    
    # SADECE tamamen boş satırları ve duplike satırları atar
    df = df.dropna(how='all').drop_duplicates() 
    
    # 1. Kırpma İşlemi (SADECE 2. Sütundan itibaren)
    df_temp = df.copy()
    if df_temp.shape[1] > 1:
        # İndeks 1'den (ikinci sütun) sonrası kırpılır.
        df_temp.iloc[:, 1:] = df_temp.iloc[:, 1:].astype(str).apply(
            lambda col: col.apply(lambda x: truncate_text(x, 1000))
        )
    
    print(f"   ✨ Veri Hazır (AI Elemesi için): {len(df_temp)} satır")
    return df_temp.astype(str) 

def get_progress_file_path(filename):
    # Progress dosyaları scriptin olduğu yerdeki 'data' klasöründe tutulur
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
    # Çıktı klasörü: scriptin olduğu yerdeki 'data' klasörü
    output_path = BASE_DIR / "data" / f"filtered_{filename}.csv"
    df = pd.DataFrame(data)
    if not output_path.exists():
        df.to_csv(output_path, index=False, encoding='utf-8-sig', mode='w')
    else:
        df.to_csv(output_path, index=False, encoding='utf-8-sig', mode='a', header=False)

def analyze_paid_fast(data_chunk, category, df_columns, retry=0):
    # Kolon isimlerini prompt'a ekliyoruz ki AI neye baktığını bilsin
    column_names = ", ".join(df_columns) 
    
    # PROMPT (DEĞİŞTİRİLMEDEN KORUNDU)
    prompt = f"""
    Sen, **Metro Market'in HORECA (Otel, Restoran, Catering) Sektörüne odaklanmış Yüksek Seviye Stratejik Pazar Analistisin.** Senin görevin, sadece ürün seçmek değil, piyasadaki **YENİ BAŞLANGIÇ TRENDLERİNİ ERKEN TESPİT ETMEK** ve müşteri ihtiyaçlarına göre **pazarda devrim yaratacak ürün portföyünü** oluşturmaktır.
    potansiyel müşterilerin beklentileri, sektör trendleri ve yenilikçi ürün özellikleri hakkında derinlemesine bilgiye sahipsin.
    potansiyel gördüğün ürünleri yanına #potansiyel etiketiyle beraber yaz asağıdaki kurallara göre.
    GÖREV: Aşağıdaki '{category}' verilerini analiz et.
    Kolon İsimleri (Sırayla): [{column_names}]
    
    1. Sadece **Metro HORECA müşterilerinin (restoran, kafe vb.) menüsüne veya operasyonuna DEVRİM YARATACAK** ve **yeni trend sinyali** taşıyan ürünleri seç.
    2. Çöpleri kesinlikle at. **Uzun ürün ismini, ürünün temel niteliği belli olacak şekilde KISALT.**
    3. Her ürün için **Potansiyel Skoru** (0-100) ver. Bu skor, ürünün *piyasada trend olma hızı* ve *HORECA sektörüne katacağı yenilik değeri* baz alınarak belirlenmelidir.
    4. ÇIKTI JSON'unda **gönderilen ham verinin ilk sütunundaki bilgiyi** "kaynak_dosya" alanına aktar.
    5. JSON döndür. Lütfen uzun analiz veya açıklama YAPMA.

    VERİ (Kolon İsimleri hariçtir, yukarıdaki listeye bakınız):
    {data_chunk}

    ÇIKTI: [{{ 
      "kaynak_dosya": "Ham verinin ilk sütunundaki değer,markası veya benzersiz kimliği.",
      "urun_adi": "Ürün Adı (Mutlaka KISALTILMIŞ ama ürün belirlenebilir olacak şekilde.)", 
      "fiyat": "sayısal değer olarak fiyat ve para birimi(varsa). Yoksa "-" işareti.", 
      "potansiyel_skoru": "0-100 arası tamsayı .Potansiyel Skorunu pazara ve kendi verilerine ve marketlere göre belirle ve bana gerçeğe en yakın skoru ver.",
      "not": "Kısa açıklama/etiket (Örn: Erken Trend Sinyali, Vegan Alternatif, İşletme Verimliliği gibi ürünle alakalı kendi mantığınla ürettiğin  3 kısa etiket oluştur ürünle alakalı.etiketleri # ile başlat.)"
    }}]
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
            print("\n❌ HATA: Yetersiz Bakiye! Lütfen OpenRouter'a kredi yükleyin.")
            sys.exit(1)
            
        if retry < 3:
            print(f"      ⚠️ Geçici Hata. Tekrar deneniyor... ({retry+1})")
            time.sleep(2)
            # Kolon isimlerini tekrar geçerek yeniden dene
            return analyze_paid_fast(data_chunk, category, df_columns, retry + 1)
        return []

# --- ANA DÖNGÜ ---
def process_files():
    # --- DİNAMİK YOL AYARLAMASI ---
    # Kodun Yeri: .../scraper/ai_filter/preprocessed_data/preprocessed_ai.py
    # Verinin Yeri: .../scraper/ai_filter/Raw_data
    # Bu yüzden BASE_DIR.parent (ai_filter) -> Raw_data yapıyoruz.
    
    raw_data_dir = BASE_DIR.parent / "Raw_data"
    
    # Çıktı klasörü (data)
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

        # Kolon isimlerini bir kere al (AI'ya göndermek için)
        df_columns = df_clean.columns.tolist()

        for i in range(start_index, total_rows, BATCH_SIZE):
            batch = df_clean.iloc[i : i + BATCH_SIZE]
            
            # KRİTİK: header=False ile ilk satır (kolon isimleri) gönderilmez
            batch_str = batch.to_string(header=False, index=False) 
            
            print(f"   ⏳ İşleniyor: {i} - {min(i+BATCH_SIZE, total_rows)} (Toplam: {total_rows})")
            
            # Kolon isimlerini analyze_paid_fast fonksiyonuna yolla
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