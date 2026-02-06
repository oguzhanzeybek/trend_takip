import os
import json
import pandas as pd
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path
import time
import sys
import warnings
import random
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

# Gereksiz uyarıları sustur
warnings.filterwarnings("ignore")

# --- KÜTÜPHANE KONTROLÜ ---
try:
    from ddgs import DDGS
except ImportError:
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        print("❌ HATA: 'duckduckgo-search' veya 'ddgs' kütüphanesi eksik.")
        print("👉 Çözüm: pip install ddgs")
        sys.exit(1)

BASE_DIR = Path(__file__).resolve().parent

# .env dosyasını bulma
env_path = None
search_dirs = [BASE_DIR] + list(BASE_DIR.parents)[:3]
for d in search_dirs:
    if (d / '.env').exists():
        env_path = d / '.env'
        load_dotenv(dotenv_path=env_path)
        break

api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENROUTER_KEY")

if not api_key:
    print("❌ HATA: API Key bulunamadı! .env dosyasını kontrol et.")
    sys.exit(1)

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key, 
)

MODEL_NAME = "openai/gpt-4o-mini"
BATCH_SIZE = 5     
MAX_WORKERS = 3    

def truncate_text(text, max_chars=1000):
    if len(text) > max_chars: return text[:max_chars] + "..."
    return text

def clean_data(df):
    initial_len = len(df)
    print(f"   🧹 Veri Temizleniyor... (Giriş: {initial_len})")
    
    # Rank'i dosya okunduğu andaki satır sırasına göre sabitliyoruz.
    df['original_index'] = range(2, len(df) + 2)
    
    df = df.dropna(how='all')
    df.columns = df.columns.str.strip()
    
    df_temp = df.copy()
    cols_to_process = [c for c in df_temp.columns if c != 'original_index']
    if cols_to_process:
        df_temp[cols_to_process] = df_temp[cols_to_process].astype(str).apply(
            lambda col: col.apply(lambda x: truncate_text(x, 1000))
        )
    print(f"   ✨ Veri Hazır: {len(df_temp)} satır")
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
    
    cols = [
        'rank', 
        'kaynak_dosya', 
        'urun_adi', 
        'fiyat', 
        'potansiyel_skoru', 
        'trend_durumu',
        'hedef_kitle',
        'risk_analizi',
        'rakip_durumu',
        'pazarlama_fikri',
        'video_ozeti',      
        'manipulasyon_riski', 
        'kalite_puani',     
        'hype_puani',       
        'fiyat_puani',      
        'urun_resmi', 
        'link', 
        'aciklama'          
    ]
    
    for c in cols:
        if c not in df.columns: df[c] = ""
    df = df[cols]

    if not output_path.exists():
        df.to_csv(output_path, index=False, encoding='utf-8-sig', mode='w')
    else:
        df.to_csv(output_path, index=False, encoding='utf-8-sig', mode='a', header=False)

# --- SEARCH GOD MODE ---
def search_god_mode(keyword, rank, retries=0):
    if not keyword or len(keyword) < 2: return None, "Veri yok."
    
    context_accumulator = []
    first_image_url = ""

    is_hashtag = keyword.startswith("#") or "gündem" in keyword.lower() or "olayı" in keyword.lower()

    if is_hashtag:
        queries = [
            f"{keyword} olayı nedir neden gündem oldu",
            f"{keyword} tepkiler twitter ekşi",
            f"{keyword} son durum haberler"
        ]
    else:
        queries = [
            f"{keyword} kronik sorunlar iade nedenleri şikayet", 
            f"{keyword} alınır mı fiyatına değer mi inceleme",   
            f"{keyword} vs rakipleri en iyi alternatifi",        
            f"{keyword} kimler kullanıyor hedef kitle",          
            f"{keyword} fiyat geçmişi indirim trendi"            
        ]

    try:
        with DDGS() as ddgs:
            # A) GÖRSEL
            try:
                res_img = list(ddgs.images(keyword, region='tr-tr', safesearch='off', max_results=1))
                if res_img: first_image_url = res_img[0].get('image', '')
            except: pass

            # B) METİN ARAMA
            for q in queries:
                try:
                    res = list(ddgs.text(q, region='tr-tr', safesearch='off', max_results=2))
                    if res:
                        chunk = " | ".join([f"KAYNAK: {r['title']} -> {r['body']}" for r in res])
                        context_accumulator.append(chunk)
                    time.sleep(random.uniform(0.5, 1.0)) 
                except: continue

            # C) VİDEO ARAMA
            if not is_hashtag:
                try:
                    vid_query = f"{keyword} inceleme review test sakın almayın"
                    res_vid = list(ddgs.videos(vid_query, region='tr-tr', safesearch='off', max_results=3))
                    if res_vid:
                        vid_chunk = " | ".join([f"VIDEO: {r['title']} (Açıklama: {r['description']})" for r in res_vid])
                        context_accumulator.append(f"--- YOUTUBE VERİLERİ ---\n{vid_chunk}")
                except: pass

        final_context = "\n\n".join(context_accumulator)[:10000] 
        
        if not final_context.strip():
            return first_image_url, "VERİ BULUNAMADI"

        return first_image_url, final_context
            
    except Exception as e:
        if retries < 2:
            time.sleep(2)
            return search_god_mode(keyword, rank, retries + 1)
        return "", "Arama Hatası"

# --- TEK BİR SATIRI İŞLEYEN FONKSİYON ---
def process_single_row(row, file_key, cols_map):
    col_kaynak = cols_map['kaynak']
    col_fiyat = cols_map['fiyat']
    col_link = cols_map['link']
    col_urun = cols_map['urun']
    
    real_original_rank = str(row.get('original_index', 0))
    
    detected_source = file_key 
    if col_kaynak and str(row[col_kaynak]).strip().lower() not in ["nan", "", "none"]:
        detected_source = str(row[col_kaynak]).strip()

    original_link = str(row[col_link]) if col_link else ""
    original_price = str(row[col_fiyat]) if col_fiyat else "Belirtilmemiş"
    
    product_name = ""
    if col_urun: 
        val = str(row[col_urun]).strip()
        if not val.startswith("http") and len(val) > 1:
            product_name = val
    
    if not product_name:
        vals = [str(x) for x in row.values if x != real_original_rank and not str(x).isdigit() and not str(x).startswith("http") and str(x) != detected_source]
        product_name = max(vals, key=len) if vals else "Bilinmeyen Ürün"

    short_name = product_name
    if len(product_name) > 60: short_name = product_name[:57] + "..."

    print(f"      ⚡ Analiz (Rank: {real_original_rank}): {short_name}...")
    
    image_url, search_context = search_god_mode(product_name, real_original_rank)
    
    # EĞER VERİ YOKSA DİREKT ELE (Acımasız Mod)
    if search_context == "VERİ BULUNAMADI":
        print(f"      🗑️  Veri Yok -> ELENDİ (Rank: {real_original_rank})")
        return None

    # --- ACIMASIZ PROMPT ---
    prompt = f"""
    GÖREV: Sen 'Acımasız Bir Tüccar' ve 'Risk Analistisin'.
    Paranı çöpe atmaktan nefret edersin. Önüne gelen her ürünü övme.
    Sadece %10'luk "Elmas Değerindeki" fırsatları arıyorsun.
    
    GİRDİLER:
    KONU: {product_name}
    FİYAT: {original_price}
    MEVCUT_KAYNAK_BILGISI: {detected_source}
    İSTİHBARAT (Web + Video + Haber): {search_context}

    --- KRİTİK DEĞERLENDİRME ---
    1. Ürün hakkında internette şikayet var mı?
    2. Fiyatı piyasaya göre pahalı mı?
    3. Bu ürün gerçekten trend mi yoksa sönmüş bir balon mu?
    
    Eğer ürün vasatsa, sıradansa veya riskliyse DÜŞÜK PUAN VER (40-50).
    Sadece "Vay canına, bu kesin satar" dediğin ürünlere 80+ ver.

    --- ÇIKTI FORMATI (JSON) ---
    0. "kaynak_dosya": '{detected_source}'.
    1. "aciklama": Patron için KISA, NET ve OBJEKTİF bir özet (Max 3 cümle). Olumsuzlukları gizleme.
    2. "trend_durumu": Ürünün yaşam döngüsü (Düşüşte/Stabil/Yükselişte).
    3. "hedef_kitle": Kime satacağız?
    4. "risk_analizi": Neden batabiliriz? (İade, bozulma, modası geçme).
    5. "rakip_durumu": Rakipler daha mı ucuz?
    6. "pazarlama_fikri": Satış sloganı.
    7. "video_ozeti": Videolardaki genel hava (Olumlu/Olumsuz).
    8. "manipulasyon_riski": Yorumlar bot mu?
    9. "kalite_puani": (0-100)
    10. "hype_puani": (0-100)
    11. "fiyat_puani": (0-100)
    12. "potansiyel_skoru": (0-100 Arası Kesin Puan. 70 ALTI BAŞARISIZDIR).

    SADECE JSON DÖNDÜR.
    """
    
    try:
        completion = client.chat.completions.create(
            extra_headers={"HTTP-Referer": "http://localhost"},
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,  # Daha tutarlı ve ciddi olması için düşürdüm
            max_tokens=2000
        )
        resp = completion.choices[0].message.content
        if "```" in resp: resp = resp.split("```json")[-1].split("```")[0].strip()
        ai_data = json.loads(resp)
        
        score = int(ai_data.get("potansiyel_skoru", 0))

        # --- YENİ BARAJ: 70 ---
        # Eskiden 50 idi, şimdi 70. Vasat ürünler elenir.
        if score < 70:
            print(f"      📉 Yetersiz ({score}) (Rank: {real_original_rank}) -> ELENDİ")
            return None

        print(f"      💎 ONAYLANDI (Skor: {score}) (Rank: {real_original_rank}) -> EKLENDİ")
        
        final_source = ai_data.get("kaynak_dosya", detected_source)
        if not final_source: final_source = detected_source

        return {
            "rank": real_original_rank,     
            "kaynak_dosya": final_source, 
            "urun_adi": short_name,
            "fiyat": original_price,
            "potansiyel_skoru": score,
            "kalite_puani": ai_data.get("kalite_puani", 0),
            "hype_puani": ai_data.get("hype_puani", 0),
            "fiyat_puani": ai_data.get("fiyat_puani", 0),
            "trend_durumu": ai_data.get("trend_durumu", "-"),
            "hedef_kitle": ai_data.get("hedef_kitle", "-"),
            "risk_analizi": ai_data.get("risk_analizi", "-"),
            "rakip_durumu": ai_data.get("rakip_durumu", "-"),
            "pazarlama_fikri": ai_data.get("pazarlama_fikri", "-"),
            "video_ozeti": ai_data.get("video_ozeti", "-"),
            "manipulasyon_riski": ai_data.get("manipulasyon_riski", "-"),
            "urun_resmi": image_url,
            "link": original_link,
            "aciklama": ai_data.get("aciklama", "Detay yok.")
        }
        
    except Exception as e:
        print(f"      ⚠️ Hata (Rank: {real_original_rank}): {e}")
        return None

# --- PARALEL İŞLEM YÖNETİCİSİ ---
def analyze_god_mode_ai(df_chunk, file_key, df_columns):
    results_list = []
    
    cols_lower = {c.lower(): c for c in df_chunk.columns}
    cols_map = {
        'kaynak': cols_lower.get("kaynak") or cols_lower.get("source"),
        'fiyat': cols_lower.get("fiyat") or cols_lower.get("price"),
        'link': cols_lower.get("link") or cols_lower.get("url"),
        'urun': None
    }
    
    possible_names = ["urun", "urun_adi", "ürün adı", "ürün başlığı", "product_name", "title", "trend", "hashtag"]
    for name in possible_names:
        if name in cols_lower:
            cols_map['urun'] = cols_lower[name]
            break

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = []
        for _, row in df_chunk.iterrows():
            futures.append(executor.submit(process_single_row, row, file_key, cols_map))
        
        for future in as_completed(futures):
            res = future.result()
            if res:
                results_list.append(res)
    
    results_list.sort(key=lambda x: int(x['rank']) if str(x['rank']).isdigit() else 999999)

    return results_list

def process_files():
    raw_data_dir = BASE_DIR.parent / "Raw_data"
    output_dir = BASE_DIR / "data"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    target_files = ["Rival.csv", "online_shopping.csv", "social_media.csv"]
    
    print(f"📂 Veritabanı: {raw_data_dir}")
    print(f"👑 MOD: ACIMASIZ & HIZLI (Baraj: 70)")
    print("------------------------------------------------")

    if not raw_data_dir.exists():
        print("❌ Klasör yok!")
        return

    for filename in target_files:
        if not (raw_data_dir / filename).exists(): continue

        print(f"\n🚀 {filename} ANALİZ BAŞLIYOR...")
        
        try:
            df = pd.read_csv(
                raw_data_dir / filename, 
                dtype=str, 
                low_memory=False, 
                index_col=False
            ).fillna("")
        except: continue
        
        df_clean = clean_data(df)
        total_rows = len(df_clean)
        file_key = filename.split('.')[0]
        start_index = get_last_index(file_key)
        
        if start_index >= total_rows:
            print("   ✅ Tamamlanmış.")
            continue

        df_columns = df_clean.columns.tolist()

        for i in range(start_index, total_rows, BATCH_SIZE):
            batch_df = df_clean.iloc[i : i + BATCH_SIZE]
            print(f"   ⏳ Batch İşleniyor: {i} - {min(i+BATCH_SIZE, total_rows)}")
            
            results = analyze_god_mode_ai(batch_df, file_key, df_columns)
            
            if results:
                append_to_csv(results, file_key)
                print(f"      💾 {len(results)} Adet Fırsat Kaydedildi.")
            else:
                print(f"      🗑️  Bu gruptan hiçbiri barajı geçemedi.")

            save_progress(file_key, i + BATCH_SIZE)

        print(f"🎉 {filename} Bitti!")

if __name__ == "__main__":
    process_files()
    for fk in ["Rival", "online_shopping", "social_media"]:
        pp = get_progress_file_path(fk)
        if pp.exists(): pp.unlink()
    print("🏁 YÖNETİM RAPORU TAMAMLANDI.")