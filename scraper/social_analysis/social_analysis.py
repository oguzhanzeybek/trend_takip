import os
import json
import pandas as pd
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path
import time
import sys
import re
import datetime
import math 

# --- AYARLAR ---
MODEL_NAME = "openai/gpt-4o-mini" 
BATCH_SIZE = 50 
WAIT_TIME = 1 

BASE_DIR = Path(__file__).resolve().parent

# .env yükleme
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

def truncate_text(text, max_chars=1000):
    if len(text) > max_chars:
        return text[:max_chars] + "..."
    return text

def clean_data(df):
    initial_len = len(df)
    print(f" 🧹 Ön temizlik... (Giriş: {initial_len})")
    df = df.dropna(how='all').drop_duplicates() 
    df_temp = df.copy()
    if df_temp.shape[1] > 1:
        df_temp.iloc[:, 1:] = df_temp.iloc[:, 1:].astype(str).apply(
            lambda col: col.apply(lambda x: truncate_text(x, 1000))
        )
    print(f" ✨ Veri Hazır: {len(df_temp)} satır")
    return df_temp.astype(str) 

def save_analysis_json(data, filename):
    output_dir = BASE_DIR / "data"
    output_dir.mkdir(parents=True, exist_ok=True)
    # Dosya ismini standartlaştırdık
    output_path = output_dir / f"analyzed_{filename}.json"
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f" 💾 Analiz Sonucu Kaydedildi: {output_path.name}")

def analyze_data_with_ai(data_chunk, df_columns, is_final_analysis=False, retry=0):
    current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Rol Tanımı
    role = "**Sen, verilerin derinliklerindeki hikayeyi okuyan kıdemli bir Toplum Bilimci ve Veri Analistisin.**"

    if is_final_analysis:
        # ============================================================
        # FİNAL ANALİZ (STRATEJİK SKORLAR EKLENDİ)
        # ============================================================
        prompt_goal = """
        GÖREVİN: Sana verilen 'Saha Raporlarını' (Batch Summaries) birleştirerek, uygulamanın beklediği EXACT JSON formatında ama ÇOK DETAYLI bir analiz raporu oluşturmaktır.
        
        KURALLAR:
        1. Asla kısa kesme. "Gerekçe", "Köken" ve "Neden" alanlarını doldururken **spesifik örnekler, marka isimleri ve olay detayları** ver.
        2. Genellemelerden kaçın. "Ekonomi kötü" deme; "Süt fiyatlarındaki %30 artış ve X marketindeki etiketler" de.
        3. Duygu skorlarını (0-100) verilerin yoğunluğuna göre gerçekçi ata.
        
        ÖNEMLİ - STRATEJİK SKORLAMA MANTIĞI:
        - **pazar_sagligi (0-100):** Toplumda öfke ve stres yüksekse düşür, umut ve memnuniyet varsa yükselt.VERİLERDEN YOLA ÇIKARAK ANALİZ ET.
        - **satin_alma_istahi (0-100):** İnsanlar "alamıyoruz" diyorsa düşük, "indirim, alışveriş" konuşuyorsa yüksek ver.VERİLERDEN YOLA ÇIKARAK ANALİZ ET.
        - **viral_etki (0-100):** Konuşulan konular ne kadar yankı uyandırmış? Herkes aynı şeyi konuşuyorsa 90+ ver.VERİLERDEN YOLA ÇIKARAK ANALİZ ET.
        - **firsat_skoru (0-100):** Bu kriz ortamında markalar için boşluk var mı? (Örn: Ucuz ürün ihtiyacı = Yüksek Fırsat).VERİLERDEN YOLA ÇIKARAK ANALİZ ET.
        """
        
        data_header = "VERİ (Toplanan Tüm Parçalı Analizler):"
        
        # --- JSON FORMATI GÜNCELLENDİ: SKORLAR EKLENDİ ---
        json_output_template = f"""
        "analiz_tarihi": "{current_time}",
        "analiz_kaynağı": "social_media.csv",
        
        "stratejik_skorlar": {{
            "pazar_sagligi": 0, 
            "satin_alma_istahi": 0,
            "viral_etki": 0,
            "firsat_skoru": 0
        }},

        "genel_değerlendirme": "BURAYA_DETAYLI_PARAGRAF_GELMELİ (En az 3-4 cümle. Toplumun genel psikolojisini, çelişkileri ve ana motivasyonları edebi ve analitik bir dille özetle).",
        "ana_duygular": [
            {{
                "duygu": "Duygu Adı (Örn: Öfke)",
                "skor": 0-100,
                "gerekçe": "Bu duygunun kaynağı nedir? Hangi olaylar tetikledi? (Detaylı yaz)"
            }},
            {{
                "duygu": "Duygu Adı (Örn: Çaresizlik)",
                "skor": 0-100,
                "gerekçe": "Bu duygunun kaynağı nedir? Hangi olaylar tetikledi? (Detaylı yaz)"
            }},
            {{
                "duygu": "Duygu Adı (Örn: Alaycılık)",
                "skor": 0-100,
                "gerekçe": "Bu duygunun kaynağı nedir? Hangi olaylar tetikledi? (Detaylı yaz)"
            }}
        ],
        "baskin_gundemler": [
            {{
                "konu": "Konu Başlığı 1 (Örn: Kira Zamları)",
                "köken": "Bu konunun tartışılma sebebi, verilen örnekler ve şikayetlerin odak noktası. (Detaylı)"
            }},
            {{
                "konu": "Konu Başlığı 2",
                "köken": "Bu konunun tartışılma sebebi, verilen örnekler ve şikayetlerin odak noktası. (Detaylı)"
            }},
             {{
                "konu": "Konu Başlığı 3",
                "köken": "Bu konunun tartışılma sebebi, verilen örnekler ve şikayetlerin odak noktası. (Detaylı)"
            }}
        ],
        "harcama_egilimi_analizi": {{
            "egilim": "Tüketicinin harcama davranışı (Örn: Lüksten kaçış, stoka yönelim)",
            "sektor_etkisi": "Hangi sektörler nasıl etkileniyor? (Örn: Cafe/Restoran boykotu, Market alışverişi değişimi)"
        }},
        "gelecek_tahminleri": [
            {{
                "tahmin": "Gelecek öngörüsü 1",
                "risk_seviyesi": "Yüksek/Orta/Düşük",
                "neden": "Veriye dayalı dayanak noktası."
            }},
            {{
                "tahmin": "Gelecek öngörüsü 2",
                "risk_seviyesi": "Yüksek/Orta/Düşük",
                "neden": "Veriye dayalı dayanak noktası."
            }}
        ]
        """
        
        analysis_structure = "ÇIKTI FORMATI KESİNLİKLE AŞAĞIDAKİ JSON OLMALIDIR. BAŞKA KEY EKLEME VEYA ÇIKARMA."

    else:
        # ============================================================
        # BATCH (ARA) ANALİZ - Veri Madenciliği
        # ============================================================
        prompt_goal = "Görevin bu 50 satırlık verideki 'Altın Değerindeki' detayları çıkarmaktır. Genelleme yapma, İSİM, MARKA, OLAY ve DUYGU yakala."
        data_header = f"VERİ PARÇASI: {data_chunk}"
        
        analysis_structure = "Sadece aşağıdaki basit yapıyı kullan:"
        
        json_output_template = """
        "ozet_duygu": "Baskın his",
        "tespit_edilen_detaylar": "Metinde geçen Markalar, Kişiler, Yerler, Fiyatlar, Olaylar (Hepsini yaz)",
        "ana_konu": "İnsanlar ne konuşuyor?",
        "detayli_kanit": "Neden böyle düşünüyorlar? (Alıntı yap)"
        """

    prompt = f"""
    SADECE JSON ÇIKTISI ÜRET.
    
    Rol: {role}
    Görev: {prompt_goal}
    
    {analysis_structure}
    
    {data_header}
    
    İstenen JSON Şeması:
    {{
      {json_output_template}
    }}
    """
    
    try:
        if retry == 0:
            print(f"    💬 AI Çalışıyor... ({'FİNAL RAPORLAMA' if is_final_analysis else 'VERİ MADENCİLİĞİ'})")
        
        completion = client.chat.completions.create(
            extra_headers={"HTTP-Referer": "http://localhost", "X-Title": "TrendAI"},
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5 if not is_final_analysis else 0.7, 
        )
        
        resp = completion.choices[0].message.content
        
        if "```" in resp:
            match = re.search(r"```json\s*(.*?)\s*```", resp, re.DOTALL)
            resp = match.group(1).strip() if match else resp.replace("```", "").strip()
        
        resp = re.sub(r'//.*', '', resp)
        
        return json.loads(resp)
    
    except Exception as e:
        if retry < 2:
            time.sleep(3)
            return analyze_data_with_ai(data_chunk, df_columns, is_final_analysis, retry + 1)
        print(f"❌ Hata: {e}")
        return None

def process_social_media_analysis():
    raw_data_dir = BASE_DIR.parent / "ai_filter" / "Raw_data"
    filename = "social_media.csv"
    
    debug_file_path = BASE_DIR / "data" / "batch_summaries_debug.txt"
    
    print(f"🚀 {filename} ANALİZ SÜRECİ BAŞLATILIYOR...")
    
    try:
        df = pd.read_csv(raw_data_dir / filename, dtype=str, low_memory=False).fillna("")
    except:
        print("❌ Dosya okunamadı.")
        return
    
    df_clean = clean_data(df)
    total_rows = len(df_clean)
    
    if total_rows == 0: return

    num_batches = math.ceil(total_rows / BATCH_SIZE)
    intermediate_summaries = []
    
    with open(debug_file_path, "w", encoding="utf-8") as f: f.write("")

    print(f" 📝 {total_rows} satır veri, {num_batches} aşamada işlenecek.")
    
    for i in range(num_batches):
        start = i * BATCH_SIZE
        end = min((i + 1) * BATCH_SIZE, total_rows)
        batch_df = df_clean.iloc[start:end]
        
        batch_res = analyze_data_with_ai(batch_df.to_string(index=False), [], is_final_analysis=False)
        
        if batch_res:
            summary_text = (
                f"RAPOR {i+1}:\n"
                f"Konu: {batch_res.get('ana_konu')}\n"
                f"Tespit Edilen Varlıklar/Markalar: {batch_res.get('tespit_edilen_detaylar')}\n"
                f"Duygu: {batch_res.get('ozet_duygu')}\n"
                f"Kanıt/Detay: {batch_res.get('detayli_kanit')}\n"
            )
            intermediate_summaries.append(summary_text)
            print(f"  ✔️ Batch {i+1} Tamam: {batch_res.get('ana_konu')}")
            
            with open(debug_file_path, "a", encoding="utf-8") as f:
                f.write(summary_text + "\n---\n")
        
        time.sleep(WAIT_TIME)

    if not intermediate_summaries:
        return

    print("\n🧠 TÜM VERİLER TOPLANDI. FİNAL FORMATI OLUŞTURULUYOR...")
    
    final_input = "\n".join(intermediate_summaries)
    
    final_res = analyze_data_with_ai(final_input, [], is_final_analysis=True)
    
    if final_res:
        save_analysis_json(final_res, "social_media_ultra_detailed_sentiment")
        print("\n🎉 ANALİZ TAMAMLANDI! Çıktı formatı uygulamanızla uyumludur.")
    else:
        print("❌ Final rapor oluşturulamadı.")

if __name__ == "__main__":
    process_social_media_analysis()