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
# En stabil, en hızlı ve maliyeti en düşük model: GPT-4o-mini
MODEL_NAME = "openai/gpt-4o-mini" 

# Stabil ve hızlı işlem için ideal ayarlar
BATCH_SIZE = 50 # Her bir AI isteği için 50 satır veri
WAIT_TIME = 1 # 1 saniye dinlenme

# --- BAĞLANTI ---
BASE_DIR = Path(__file__).resolve().parent

# .env dosyasını bulma ve yükleme
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
    TEMİZLİK VE KIRPMA
    """
    initial_len = len(df)
    print(f"  🧹 Ön temizlik... (Giriş: {initial_len})")
    
    # SADECE tamamen boş satırları ve duplike satırları atar
    df = df.dropna(how='all').drop_duplicates() 
    
    df_temp = df.copy()
    if df_temp.shape[1] > 1:
        # İndeks 1'den (ikinci sütun) sonrası kırpılır.
        df_temp.iloc[:, 1:] = df_temp.iloc[:, 1:].astype(str).apply(
            lambda col: col.apply(lambda x: truncate_text(x, 1000))
        )
    
    print(f"  ✨ Veri Hazır: {len(df_temp)} satır")
    return df_temp.astype(str) 

def get_output_file_path(filename):
    # Data klasörü yoksa oluştur
    output_dir = BASE_DIR / "data"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir / f"analyzed_{filename}.json"

def save_analysis_json(data, filename):
    output_path = get_output_file_path(filename)
    
    # JSON dosyasını oluşturup kaydet
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"  💾 Analiz Sonucu Kaydedildi: {output_path.name}")


# 🚨 GÜNCEL VE ULTRA DETAYLI ANALİZ FONKSİYONU 🚨
def analyze_data_with_ai(data_chunk, df_columns, is_final_analysis=False, retry=0):
    column_names = ", ".join(df_columns) 
    current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # ROL TANIMI: ARTIK "GENEL UZMAN" DEĞİL, "VERİ DEDEKTİFİ"
    role = "**Sen Türkiye'nin en obsesif Veri Madencisi ve Sosyal Medya Dedektifisin. Senin işin genellemeler yapmak değil, önüne gelen veri parçasındaki (batch) benzersiz ve spesifik parmak izlerini bulmaktır. Asla varsayımlarla konuşmazsın, sadece kanıtla konuşursun.**"
    
    if is_final_analysis:
        # FİNAL ANALİZ PROMPT'u
        prompt_goal = "Görevin, sağlanan TÜM ara analiz özetlerini (batch sonuçlarını) birleştirerek, tekrar eden kalıpları değil, verilerin toplamından çıkan BÜYÜK RESMİ, çelişkileri ve nüansları raporlamaktır. **Ezbere cümleler kurma, analiz edilen binlerce satırın gerçek hikayesini anlat.**"
        data_header = "VERİ (Toplu işlerden gelen ara analiz özetleri):"
        analysis_structure = """
    1. **Ana Duygu Durumu:** Tüm parçalara baktığında halkın gerçek ruh hali nedir? (Sadece 'endişe' deyip geçme; öfke mi, bıkkınlık mı, alaycı bir neşe mi? Detaylandır).
    2. **Baskın Gündemler:** Verilerde en çok tekrar eden 3 somut olay/konu nedir?
    3. **Harcama Eğilimi:** İnsanlar neyden şikayet ediyor veya neye para harcıyor? Sektörel bazda (Gıda, Giyim, Teknoloji vb.) çıkarım yap.
    4. **Gelecek Tahmini:** Bu verilere dayanarak önümüzdeki 3 ayda ne olması muhtemel?
    5. ÇIKTI sadece ve sadece tek bir JSON nesnesi olmalıdır.
        """
        json_output_template = f"""
    "analiz_tarihi": "{current_time}",
    "analiz_kaynağı": "social_media.csv",
    "genel_değerlendirme": "Verilerin tamamına dayalı, genellemelerden uzak, çok katmanlı ve derinlemesine bir özet paragraf.",
    "ana_duygular": [
      {{ "duygu": "Duygu Adı 1", "skor": 0-100, "gerekçe": "Bu duygunun kaynağı olan spesifik olaylar ve veriler." }},
      {{ "duygu": "Duygu Adı 2", "skor": 0-100, "gerekçe": "Bu duygunun kaynağı olan spesifik olaylar ve veriler." }}
    ],
    "baskin_gundemler": [
      {{ "konu": "Konu Başlığı 1", "köken": "Bu konuyu tetikleyen sosyal medya içerikleri." }}, 
      {{ "konu": "Konu Başlığı 2", "köken": "Bu konuyu tetikleyen sosyal medya içerikleri." }}
    ],
    "harcama_egilimi_analizi": {{
        "egilim": "Tüketici davranışındaki net değişim.",
        "sektor_etkisi": "Etkilenen sektörler ve nedenleri."
    }},
    "gelecek_tahminleri": [
        {{ "tahmin": "Tahmin 1", "risk_seviyesi": "Yüksek/Orta/Düşük", "neden": "Dayanak noktası." }},
        {{ "tahmin": "Tahmin 2", "risk_seviyesi": "Yüksek/Orta/Düşük", "neden": "Dayanak noktası." }}
    ]
        """
    else:
        # ARA ANALİZ (BATCH) PROMPT'u: BURASI ÇOK KRİTİK DEĞİŞTİRİLDİ
        # Modelin kopya çekmesini engellemek için "örnek içerikleri" kaldırdık.
        prompt_goal = "Görevin, sana verilen **bu spesifik 50 satırlık veri parçasını** incelemektir. **DİKKAT: Asla önceki bildiklerini veya genel geçer 'ekonomi kötü' ezberlerini kullanma.** Sadece bu metinlerde geçen **ÖZEL İSİMLERİ, MARKALARI, OLAYLARI ve HASHTAG'LERİ** raporla. Eğer metinlerde futbol varsa futbol yaz, dizi varsa dizi yaz. Veri ne diyorsa o.SEN BİR TOPLUM BİLİMCİSİ BİR DAHİSİN , İNSANLIĞIN KURTARICI OLARAK TANRI GIBI KUŞBAKIŞI ANALİZ ET Kİ HALKI ANLAYABİLELİM."
        data_header = f"VERİ (Bu Batch İçin Ham Metinler): {data_chunk}"
        analysis_structure = """
    1. **Özet Duygu:** SADECE BU 50 satırda hissedilen en baskın duygu.
    2. **Duygu Gerekçesi:** Neden bu duygu? Metinlerin içinden **spesifik örnekler** vererek açıkla. (Örn: 'X kullanıcısı Y olayına kızdığı için' gibi).
    3. **Özet Konu:** Bu grupta insanlar tam olarak neyden bahsediyor? (Genel 'hayat' deme. 'Zam gelen süt fiyatı' de, 'X dizisindeki karakter' de).
    4. **Konu Gerekçesi:** Bu konuyu kanıtlayan **anahtar kelimeleri** yaz.
    5. ÇIKTI sadece ve sadece tek bir JSON nesnesi olmalıdır.
        """
        # Şablondaki örnek değerleri sildim ki model onları kopyalamasın!
        json_output_template = """
      "ozet_duygu": "BURAYA_BU_VERİDEKİ_BASKIN_DUYGUYU_YAZ ve detaylı acıklama yap",
      "duygu_gerekcesi": "BURAYA_METİNLERDEN_KANIT_VE_ALINTI_İÇEREN_GEREKÇEYİ_YAZ ve acıklama yap",
      "ozet_konu": "BURAYA_BU_VERİDEKİ_SPESİFİK_KONUYU_YAZ ve acıklama yap",
      "konu_gerekcesi": "BURAYA_KONUYU_DESTEKLEYEN_ANAHTAR_KELİMELERİ_YAZ ve acıklama yap"
        """


    # PROMPT Yapısı
    prompt = f"""
    SEN KRİTİK BİR ROLÜ ÜSTLENİYORSUN. SADECE İSTENEN JSON ÇIKTISINI ÜRET. BAŞKA HİÇBİR AÇIKLAMA VEYA GİRİŞ METNİ KULLANMA.
    
    Sen, {role}
    {prompt_goal}
    
    AMACIN: Verideki gürültüyü değil, sinyali yakalamaktır.Halkın nabzını tutarak bir toplum bilimci gibi derinlemesine analiz yap.
    
    GÖREV: Aşağıdaki sosyal medya verilerini **{ 'BÜTÜNSEL' if is_final_analysis else 'ARA (BATCH)' }** olarak analiz et.
    Kolon İsimleri (Sırayla): [{column_names}]
    
    {analysis_structure}
    
    {data_header}
    
    ÇIKTI: {{
      {json_output_template}
    }}
    """
    
    try:
        if retry == 0:
            print(f"    💬 AI Analizi Başlatılıyor... ({'Nihai ÇOK DETAYLI Rapor' if is_final_analysis else 'Batch - Kapsamlı Gerekçeli Özet'})")
        
        completion = client.chat.completions.create(
            extra_headers={"HTTP-Referer": "http://localhost", "X-Title": "SentimentAnalyzer"},
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5, # Maksimum detay ve açıklama için sıcaklık 0.5'e yükseltildi
        )
        
        resp = completion.choices[0].message.content
        
        # JSON Temizleme (Mevcut koddan korundu)
        if "```" in resp:
            match = re.search(r"```json\s*(.*?)\s*```", resp, re.DOTALL)
            if match:
                resp = match.group(1).strip()
            else:
                resp = resp.replace("```", "").strip()
        
        resp = re.sub(r'//.*', '', resp) 
        
        return json.loads(resp)
    
    except Exception as e:
        err = str(e)
        if "402" in err or "insufficient_quota" in err:
            print("\n❌ HATA: Yetersiz Bakiye! Lütfen OpenRouter'a kredi yükleyin.")
            sys.exit(1)
            
        if retry < 2:
            print(f"      ⚠️ Geçici Hata ({e.__class__.__name__}). Tekrar deneniyor... ({retry+1})")
            time.sleep(5)
            return analyze_data_with_ai(data_chunk, df_columns, is_final_analysis, retry + 1)
            
        print(f"\n❌ Kritik Hata. AI'dan analiz alınamadı. Hata: {err}")
        return None

# --- ANA DÖNGÜ (Batch İşleme Mantığı Korundu) ---
def process_social_media_analysis():
    # --- DEĞİŞİKLİK BURADA: Dinamik Dosya Yolu ---
    # Eski sabit yol yerine, scriptin olduğu yerden yola çıkarak raw_data'yı buluyoruz.
    raw_data_dir = BASE_DIR.parent / "ai_filter" / "Raw_data"
    
    # Çıktı klasörü kontrolü (varsa kullan, yoksa oluştur)
    output_dir = BASE_DIR / "data"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    filename = "social_media.csv"
    
    print(f"📂 Okunacak: {raw_data_dir / filename}")
    print(f"💎 Model: {MODEL_NAME} (HAZIR)")
    print("------------------------------------------------")

    if not (raw_data_dir / filename).exists():
        print(f"❌ HATA: {filename} dosyası bulunamadı. Lütfen yolu kontrol edin:")
        print(f"   Aranan Yer: {raw_data_dir / filename}")
        return

    print(f"\n🚀 {filename} TOPLUMSAL NABIZ ANALİZİ BAŞLIYOR...")
    
    try:
        # Tüm veriyi oku
        df = pd.read_csv(raw_data_dir / filename, dtype=str, low_memory=False).fillna("")
    except Exception as e:
        print(f"❌ Dosya okuma hatası: {e}")
        return
    
    # Veriyi temizle ve kırp
    df_clean = clean_data(df)
    total_rows = len(df_clean)
    
    if total_rows == 0:
        print("❌ Temizlenecek veri bulunamadı. Analiz yapılamıyor.")
        return
    
    # --- BATCH İŞLEME MANTIĞI ---
    
    num_batches = math.ceil(total_rows / BATCH_SIZE)
    intermediate_summaries = []
    df_columns = df_clean.columns.tolist()

    print(f"  📝 Toplam {total_rows} satır, {num_batches} toplu iş (batch) halinde işlenecek.")
    
    # Parçaları döngüde işleme
    for i in range(num_batches):
        start_index = i * BATCH_SIZE
        end_index = min((i + 1) * BATCH_SIZE, total_rows)
        
        batch_df = df_clean.iloc[start_index:end_index]
        batch_data_chunk = batch_df.to_string(header=False, index=False)
        
        print(f"\n--- Batch {i+1}/{num_batches} (Satır {start_index} - {end_index-1}) ---")
        
        # Ara analizi yap
        batch_analysis = analyze_data_with_ai(batch_data_chunk, df_columns, is_final_analysis=False)
        
        if batch_analysis:
            # Ara sonuçları listeye ekle (Artık daha detaylı özetler alınıyor)
            summary = (
                f"Batch {i+1} Özeti: Ana Duygu: {batch_analysis.get('detaylı_hissedilen_duygu', 'Bilinmiyor')} "
                f"(Gerekçe: {batch_analysis.get('duygu_gerekcesi', 'Yok')}), "
                f"Ana Konu: {batch_analysis.get('ozet_konu', 'Bilinmiyor')} "
                f"(Gerekçe: {batch_analysis.get('konu_gerekcesi', 'Yok')})"
            )
            intermediate_summaries.append(summary)
            print(f"  ✔️ Batch {i+1} Tamamlandı. Özet: {summary}")
        else:
            print(f"  ❌ Batch {i+1} Analizi başarısız. Atlanıyor.")

        time.sleep(WAIT_TIME)

    if not intermediate_summaries:
        print("\n❌ Hiçbir batch analiz edilemedi. Nihai analiz yapılamıyor.")
        return

    # --- NİHAİ ANALİZ ---
    final_input_data = "\n".join(intermediate_summaries)
    print("\n================================================")
    print("🧠 ARA ANALİZLER BİRLEŞTİRİLİYOR: NIHAI ÇOK DETAYLI ANALİZ BAŞLIYOR...")
    print("================================================")
    
    # Ara özetleri kullanarak nihai bütünsel analizi yap
    final_analysis_result = analyze_data_with_ai(
        data_chunk=final_input_data, 
        df_columns=["ozet_duygu", "duygu_gerekcesi", "ozet_konu", "konu_gerekcesi"], 
        is_final_analysis=True
    )
    
    if final_analysis_result:
        # Sonucu JSON dosyasına kaydet
        save_analysis_json(final_analysis_result, filename.split('.')[0] + "_ultra_detailed_sentiment")
        print("\n🎉 TOPLUMSAL NABIZ ANALİZİ BAŞARIYLA TAMAMLANDI!")
    else:
        print("\n❌ Nihai Bütünsel Analiz başarısız oldu.")


if __name__ == "__main__":
    process_social_media_analysis()