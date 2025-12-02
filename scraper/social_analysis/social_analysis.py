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
    
    # ROL TANIMI VE TALİMATLAR, DETAY VE UZATMA ODAKLI GÜÇLENDİRİLDİ
    role = "**Türkiye'nin en üst düzey Sosyal Medya ve Toplumsal Nabız Baş Analisti'sin. Hazırladığın rapor, siyaset ve iş dünyası için kritik bir 'Sosyal Zeka Raporu'dur. Her bir konuyu en az 4-5 cümle ile detaylandır.**"
    
    if is_final_analysis:
        # FİNAL ANALİZ PROMPT'u: ÇOK DETAYLI, UZUN VE GEREKÇELİ ANALİZ TALEP EDİLİYOR
        prompt_goal = "Görevin, sağlanan TÜM ara analiz özetlerini okuyarak, halkın güncel duygu durumunu, temel eğilimlerini, beklentilerini ve **geleceğe yönelik tahminleri içeren BÜTÜNSEL, GEREKÇELİ ve AZAMİ DETAYDA** bir sosyal zeka raporu hazırlamaktır. **HER ALANI EN UZUN ŞEKİLDE, TÜM ANALİZ EDİLEN VERİLERİ YANSITARAK DOLDUR.**"
        data_header = "VERİ (Toplu işlerden gelen ara analiz özetleri):"
        analysis_structure = """
    1. **Ana Duygu Durumu ve Gerekçesi:** Tüm özetlerde baskın olan nihai duygu nedir? Her bir duygu için 0-100 arası bir güç skoru ver. Bu skorların **nedenini ve toplumsal yansımasını ÇOK DETAYLI** açıkla.
    2. **Baskın Gündemler ve Kökenleri:** En çok tekrar eden/öne çıkan 3 temel konu ne? Her bir konunun sosyal medya verilerindeki **tetikleyicisini/kökenini, alt başlıklarını ve etki alanlarını** detaylıca açıkla.
    3. **Harcama Eğilimi ve Etkisi (Makro Analiz):** Genel ruh haline bakarak, harcama eğilimleri hakkında **ÇOK DETAYLI bir çıkarım** yap. Bu eğilimin **tüketici davranışını ve hangi sektörleri nasıl etkileyeceğini** kapsamlıca belirt.
    4. **Gelecek Tahmini ve Riskler (3 Aylık Perspektif):** Önümüzdeki 3 ay için toplumsal tepki ve eğilimler konusunda 3-4 **somut, gerekçeli ve detaylı tahmin**de bulun. Tahminlerin doğruluk/gerçekleşme **risklerini** ve bu riskleri azaltma/yönetme önerilerini belirt.
    5. ÇIKTI sadece ve sadece tek bir JSON nesnesi olmalıdır. Lütfen açıklama veya analiz metni YAPMA. SADECE JSON döndür.
        """
        json_output_template = f"""
    "analiz_tarihi": "{current_time}",
    "analiz_kaynağı": "social_media.csv",
    "genel_değerlendirme": "Verilere göre halkın anlık durumunu ve genel toplumsal nabzı özetleyen, **minimum 5-7 cümlelik, derinlemesine ve kapsamlı** bir paragraf. Analiz edilen tüm verilerin özeti bu paragrafta yer almalıdır.",
    "ana_duygular": [
      {{ "duygu": "Endişe", "skor": 75, "gerekçe": "Endişe skorunun yüksek olmasının ardındaki temel 3-4 gerekçe. Halkın yaşam kalitesine etkileri, ekonomik kaygılar ve belirsizlik algısı bu bölümde ÇOK DETAYLI açıklanmalıdır." }},
      {{ "duygu": "Neşe/Pozitiflik", "skor": 40, "gerekçe": "Pozitiflik seviyesini belirleyen unsurların kısa açıklaması. Bu duyguların geçici mi kalıcı mı olduğu, hangi sosyal aktivitelerle tetiklendiği ve genel endişeyi nasıl dengelemeye çalıştığı detaylandırılmalıdır." }}
    ],
    "baskin_gundemler": [
      {{ "konu": "Ekonomi ve Enflasyon", "köken": "Sosyal medyada en çok paylaşılan enflasyon ve hayat pahalılığı ile ilgili somut veriler/tepkiler. Bu konunun alt başlıkları (gıda, kira, akaryakıt) ve siyasi yansımaları kapsamlıca açıklanmalıdır." }}, 
      {{ "konu": "Sosyal Hayat ve Kaçış", "köken": "Halkın stres yönetimi için yöneldiği kaçış temalı içeriklerin (gezi, dizi, oyun vb.) oranı. Bu kaçışın sosyal ve psikolojik nedenleri ve bu içeriklere olan yüksek talebin ardındaki toplumsal boşluk detaylandırılmalıdır." }},
      {{ "konu": "Sağlık, Güvenlik ve Kurumsal Güven", "köken": "Pandemi sonrası sağlık endişelerinin kalıcılığı ve güvenlik konularının (özellikle siber/bireysel güvenlik) sosyal medyada artan paylaşımları. Kurumlara olan güvenin bu konularla nasıl ilişkilendiği açıklanmalıdır." }}
    ],
    "harcama_egilimi_analizi": {{
        "egilim": "Halkın harcama davranışındaki ana kaymalar ve bu kaymaların ardındaki psikoloji. Tasarruf eğiliminin hangi gelir gruplarında ve nasıl kendini gösterdiği ÇOK DETAYLI belirtilmelidir.",
        "sektor_etkisi": "Perakende, HORECA, Teknoloji ve Temel Gıda sektörlerindeki hacim düşüşleri/artışları ve bu durumun nedenleri. Özellikle hangi alt sektörlerin (örn: lüks kahve, ikinci el ürünler) öne çıktığı detaylı analiz edilmelidir."
    }},
    "gelecek_tahminleri": [
        {{ "tahmin": "Önümüzdeki 3 ayda X konusundaki toplumsal tepkiler artacaktır.", "risk_seviyesi": "Orta/Yüksek", "neden": "Bu tahmine neden olan temel veri sinyali ve sosyo-ekonomik göstergeler. Bu tahmini destekleyen spesifik sosyal medya trendleri belirtilmelidir." }},
        {{ "tahmin": "Y sektörüne yönelik ilgi, toplumsal kaçış ihtiyacından dolayı bir miktar ivme kazanacaktır. Ancak, Z faktörü bu ivmeyi sınırlandıracaktır.", "risk_seviyesi": "Düşük/Orta", "neden": "Bu tahmine neden olan temel veri sinyali. Bu durumun hangi demografik gruplarda daha belirgin olduğu detaylandırılmalıdır." }},
        {{ "tahmin": "Kurumsal ve bireysel güvenlik talepleri sosyal medyada daha fazla gündem olacak ve bu alanda hizmet beklentisi artacaktır.", "risk_seviyesi": "Orta", "neden": "Bu tahmine neden olan temel veri sinyali ve beklentinin kaynağı detaylıca açıklanmalıdır." }}
    ]
        """
    else:
        # ARA ANALİZ (BATCH) PROMPT'u: Detaylı ve Kapsamlı Gerekçe Odaklı
        prompt_goal = "Görevin, sağlanan sosyal medya verilerinden yola çıkarak bu küçük veri grubunun (batch) genel duygu durumunu ve eğilimlerini analiz etmektir. **Nihai Bütünsel Analiz için kullanılacak ÇOK DETAYLI ve KAPSAMLI gerekçeli bir ön-özet** üret. Halkın anlık beklentisi, ne istediği ve hangi somut olaylara tepki verdiği her açıdan değerlendirilmelidir."
        data_header = f"VERİ (Kolon İsimleri hariçtir, yukarıdaki listeye bakınız): {data_chunk}"
        analysis_structure = """
    1. **Özet Duygu:** Bu veri parçacığında baskın olan ana duygu nedir? 
    2. **Duygu Gerekçesi:** Bu duygunun neden baskın olduğunu açıklayan **minimum 3 cümlelik, çok somut ve detaylı bir gerekçe**.
    3. **Özet Konu:** Bu veri parçacığında en çok konuşulan ana konu nedir? 
    4. **Konu Gerekçesi:** Bu konunun neden öne çıktığını ve halkın bu konudaki **ana beklentisini** açıklayan **minimum 3 cümlelik, çok somut ve detaylı bir gerekçe**.
    5. ÇIKTI sadece ve sadece tek bir JSON nesnesi olmalıdır.
        """
        json_output_template = """
      "ozet_duygu": "Endişe",
      "duygu_gerekcesi": "Verilerde sürekli olarak ekonomik zorluklar, yüksek enflasyonun bireylerin satın alma gücünü nasıl tükettiği ve fatura ödeme zorlukları gibi somut yaşam zorlukları geçmektedir. Bu, birikim yapamama ve gelecek kaygısı şeklinde kendini gösteriyor.",
      "ozet_konu": "Hayat Pahalılığı ve Temel İhtiyaçlar",
      "konu_gerekcesi": "Veri setindeki gönderilerin %70'inden fazlası direkt olarak gıda fiyatları, kira artışları ve akaryakıt zamlarına değinmektedir. Halkın ana beklentisi, temel yaşam maliyetlerinin kontrol altına alınması ve alım gücünün stabilize edilmesidir. Bu konunun öne çıkma nedeni, günlük yaşamı en direkt etkileyen unsur olmasıdır."
        """


    # PROMPT Yapısı
    prompt = f"""
    SEN KRİTİK BİR ROLÜ ÜSTLENİYORSUN. SADECE İSTENEN JSON ÇIKTISINI ÜRET. BAŞKA HİÇBİR AÇIKLAMA VEYA GİRİŞ METNİ KULLANMA.
    
    Sen, {role}
    {prompt_goal}
    
    AMACIN: Bu veriyi okuyarak, toplumu anlayan bir iş zekası üretmektir.
    
    GÖREV: Aşağıdaki sosyal medya verilerini **{ 'BÜTÜNSEL' if is_final_analysis else 'ARA' }** olarak analiz et.
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
                f"Batch {i+1} Özeti: Ana Duygu: {batch_analysis.get('ozet_duygu', 'Bilinmiyor')} "
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