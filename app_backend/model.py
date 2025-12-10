import os
import json
import re
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple, Union
from dotenv import load_dotenv

from supabase import create_client, Client
from openai import OpenAI

load_dotenv()

# ---------------------------------------------------------------------------
# AYARLAR VE BAĞLANTILAR
# ---------------------------------------------------------------------------

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
MODEL_NAME = "openai/gpt-4o-mini" 

supabase: Optional[Client] = None
ai_client: Optional[OpenAI] = None

# --- HAFIZA YÖNETİMİ ---
conversation_history = []       # Sohbet metinlerini tutar
last_successful_data = []       # Son bulunan verileri tutar (Bağlam hafızası)
last_date_info = ""             # Son kullanılan tarih bilgisini tutar

if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Supabase Bağlantısı: AKTİF")
    except Exception as e:
        print(f"❌ Supabase Hatası: {e}")

if OPENROUTER_API_KEY:
    try:
        ai_client = OpenAI(api_key=OPENROUTER_API_KEY, base_url=OPENROUTER_BASE_URL)
        print(f"✅ AI Bağlantısı: AKTİF ({MODEL_NAME})")
    except Exception as e:
        print(f"❌ AI Hatası: {e}")

# ---------------------------------------------------------------------------
# YARDIMCI FONKSİYONLAR (STEMMING & PARSING)
# ---------------------------------------------------------------------------

def simple_turkish_stemmer(word: str) -> str:
    """
    Geliştirilmiş Türkçe kök bulucu v4 (Test odaklı hassas ayar).
    """
    word = word.lower().strip()
    
    # Çok kısa kelimelere dokunma (ev, at, su)
    if len(word) < 3:
        return word

    # 1. Çoğul Ekleri (-lar, -ler)
    # Kalan kısım en az 3 harf olmalı (kedi-ler -> kedi)
    if word.endswith(("lar", "ler")):
        if len(word[:-3]) >= 3:
            word = word[:-3]

    # 2. Hal Ekleri (-dan, -den, -tan, -ten, -da, -de, -ta, -te)
    # Ev-de -> Ev (Kalan 2 harf olabilir)
    if len(word) > 4 and word.endswith(("dan", "den", "tan", "ten")):
        word = word[:-3]
    
    if len(word) > 3 and word.endswith(("da", "de", "ta", "te")):
        word = word[:-2]

    # 3. İyelik ve Tamlama Ekleri (-nın, -nin, -nun, -nün, -sı, -si, -su, -sü)
    if len(word) > 4:
        if word.endswith(("nın", "nin", "nun", "nün")):
            word = word[:-3]
        elif word.endswith(("sı", "si", "su", "sü")):
            word = word[:-2]

    # 4. Tek harfli ekler (-ı, -i, -u, -ü, -n, -m)
    # "Kitabın" -> "Kitabı" -> "Kitap" dönüşümü için döngü
    for _ in range(2): 
        # -ı, -i, -u, -ü eklerini atarken kelime en az 5 harfli olmalı ki "Kedi" -> "Ked" olmasın.
        if len(word) > 4: 
            if word.endswith(("ı", "i", "u", "ü")):
                word = word[:-1]
            elif word.endswith("n") and not word.endswith("sun"): 
                word = word[:-1]
        
        # -m eki çok riskli (Kalem -> Kale hatası). Sadece 6 harf ve üzeri kelimelerde at.
        # (Babam -> Baba olur, ama Kalem -> Kalem kalır)
        if len(word) > 5:
            if word.endswith("m") and not word.endswith("yim") and not word.endswith("ğim"):
                word = word[:-1]
    
    # Sert sessiz yumuşaması düzeltme (kitab -> kitap)
    # Sadece belli uzunluktaki kelimelerde yap
    if word.endswith("b") and len(word) > 3: 
        word = word[:-1] + "p"
    if word.endswith("c") and len(word) > 3:
        word = word[:-1] + "ç"
    if word.endswith("d") and len(word) > 3:
        word = word[:-1] + "t"

    return word

def safe_json_parse(content: Any) -> Any:
    if isinstance(content, dict): return content
    if isinstance(content, str):
        try:
            return json.loads(content)
        except:
            return {}
    return {}

def extract_date_range_from_query(text: str) -> Tuple[datetime, datetime]:
    """Sorgudan tarih ARALIĞI çeker."""
    text = text.lower()
    now = datetime.now()
    
    # 1. "Son X Gün" Mantığı
    match_days = re.search(r"son (\d+) gün", text)
    if match_days:
        days = int(match_days.group(1))
        start_date = now - timedelta(days=days)
        return start_date, now

    if "son hafta" in text or "bir hafta" in text:
        return now - timedelta(days=7), now

    # 2. Göreli Tarihler (ÖNCELİK SIRASI DÜZELTİLDİ)
    # Önce "dün ve bugün" kontrolü yapılmalı
    if "dün" in text and "bugün" in text:
        start = now - timedelta(days=1)
        return start, now 

    if "dün" in text:
        start = now - timedelta(days=1)
        return start, start 
    
    if "bugün" in text:
        return now, now
    
    # 3. Ay İsimli Tarihler
    months = {
        "ocak": 1, "şubat": 2, "mart": 3, "nisan": 4, "mayıs": 5, "haziran": 6,
        "temmuz": 7, "ağustos": 8, "eylül": 9, "ekim": 10, "kasım": 11, "aralık": 12
    }
    for month_name, month_num in months.items():
        if month_name in text:
            match = re.search(r"(\d+)\s+" + month_name, text)
            if match:
                day = int(match.group(1))
                try:
                    dt = datetime(now.year, month_num, day)
                    if dt > now + timedelta(days=1):
                        dt = datetime(now.year - 1, month_num, day)
                    return dt, dt
                except:
                    pass
    
    return now, now

def clean_search_term(text: Union[str, List[str]]) -> str:
    """
    Sorgudan gereksiz dolgu kelimelerini temizler.
    HATA DÜZELTME: Gelen veri liste ise stringe çevirir (Test 49 Hatası Çözümü).
    """
    # Eğer liste gelirse stringe çevir
    if isinstance(text, list):
        text = " ".join(text)
        
    text = str(text).lower() # Her ihtimale karşı stringe zorla
    
    months = ["ocak", "şubat", "mart", "nisan", "mayıs", "haziran", "temmuz", "ağustos", "eylül", "ekim", "kasım", "aralık"]
    for m in months:
        text = re.sub(r"\d+\s+" + m, "", text)
        text = re.sub(r"\b" + m + r"\b", "", text) 

    text = re.sub(r"son \d+ gün", "", text)
    text = text.replace("dün", "").replace("bugün", "")

    stopwords = [
        "neler", "oldu", "var", "mi", "mu", "hakkında", "ile", "ilgili", "durum", "ne", 
        "tarihinde", "günü", "fiyatları", "fiyatı", "verileri", "getir", "göster", "ve", "veya", 
        "en", "ucuz", "pahalı", "hangisi", "peki", "bunların", "şunların", "onların", "içinde", 
        "arasında", "olan", "kadar", "daha", "çok", "az", "yüksek", "düşük", "şu", "bu", "o",
        "özellikleri", "tarafında", "öne", "çıkan", "başlıklar", "konuşuldu", "listele", "hepsini", "tümünü"
    ]
    for word in stopwords:
        text = re.sub(r'\b' + word + r'\b', '', text)
    
    return text.strip()

# ---------------------------------------------------------------------------
# VERİTABANI İŞLEMLERİ (LİMİTSİZ ÇEKİM)
# ---------------------------------------------------------------------------

async def fetch_data_in_range(start_date: datetime, end_date: datetime) -> List[Dict]:
    """Limitsiz (Pagination) veri çekimi."""
    if not supabase: return []
    
    all_data = []
    chunk_size = 1000 
    offset = 0
    
    try:
        start_str = start_date.replace(hour=0, minute=0, second=0).isoformat()
        end_str = end_date.replace(hour=23, minute=59, second=59).isoformat()

        print(f"📡 Veri Çekiliyor (Limitsiz Mod): {start_str} -> {end_str}")

        while True:
            response = (
                supabase.table("processed_data")
                .select("*")
                .in_("data_type", ["Filtered", "Analyzed"]) 
                .filter("created_at", "gte", start_str)
                .filter("created_at", "lte", end_str)
                .order("created_at", desc=True)
                .range(offset, offset + chunk_size - 1)
                .execute()
            )
            
            batch = response.data if response.data else []
            if not batch: break
                
            all_data.extend(batch)
            print(f"   ↳ {len(batch)} satır çekildi (Toplam: {len(all_data)})")
            
            if len(batch) < chunk_size: break
            offset += chunk_size

        print(f"✅ TOPLAM ÇEKİLEN VERİ SAYISI: {len(all_data)}")
        return all_data
    except Exception as e:
        print(f"❌ Veri Çekme Hatası: {e}")
        return []

# ---------------------------------------------------------------------------
# AI NİYET ANALİZİ
# ---------------------------------------------------------------------------

def get_search_intent_via_ai(user_prompt: str) -> dict:
    if not ai_client: return {"intent": "search", "value": user_prompt}

    # SOHBET MODU EKLENDİ
    system_prompt = """
    Kullanıcı mesajını analiz et ve JSON döndür.
    
    1. SOHBET (Chat): "Selam", "Nasılsın", "Kimsin", "Teşekkürler", "Ne haber" -> {"intent": "chat", "value": "chat"}
    2. Sentiment: "Halk ne hissediyor?", "Duygu", "Kaygı" -> {"intent": "sentiment", "value": "sentiment"}
    3. Kategori: "Sosyal medya", "Alışveriş" -> {"intent": "category", "value": "social_media"} (veya online_shopping)
    4. Platform: "Trendyol", "Twitter" -> {"intent": "platform", "value": "trendyol"}
    5. Erken Trend: "Erken trend", "Yeni çıkan" -> {"intent": "early_trend", "value": "true"}
    6. Genel Arama: "iPhone", "Beşiktaş", "Termos" -> {"intent": "search", "value": "aranan_kelime"}
    """
    try:
        completion = ai_client.chat.completions.create(
            model=MODEL_NAME, 
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
            temperature=0, max_tokens=60
        )
        clean_json = completion.choices[0].message.content.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_json)
    except:
        return {"intent": "search", "value": user_prompt}

# ---------------------------------------------------------------------------
# AKILLI FİLTRELEME
# ---------------------------------------------------------------------------

async def fetch_smart_filtered_data(user_query: str, intent_data: dict) -> Tuple[List[Dict], str]:
    if not supabase: return [], "Veritabanı Yok"

    start_date, end_date = extract_date_range_from_query(user_query)
    
    if start_date.date() == end_date.date():
        date_info = start_date.strftime('%d %B %Y')
    else:
        date_info = f"{start_date.strftime('%d %B')} - {end_date.strftime('%d %B %Y')}"

    intent_type = intent_data.get("intent", "search")
    if intent_type == "chat": return [], date_info

    raw_value = intent_data.get("value", user_query)
    
    # HATA DÜZELTME: raw_value burada liste gelse bile clean_search_term onu stringe çevirir.
    cleaned_value = clean_search_term(raw_value) if intent_type == "search" else str(raw_value).lower().strip().replace("#", "")
    search_keywords = cleaned_value.split() if cleaned_value else []

    # Hafıza kontrolü için boş arama
    if intent_type == "search" and not search_keywords:
        if "aralık" in user_query.lower() or "dün" in user_query.lower() or "bugün" in user_query.lower() or "gün" in user_query.lower():
             pass
        else:
             print("💡 Arama terimi bulunamadı (Devam sorusu), hafıza kullanılacak...")
             return [], date_info

    # TÜM VERİYİ ÇEK (Limitsiz)
    raw_rows = await fetch_data_in_range(start_date, end_date)
    if not raw_rows: return [], date_info

    print(f"🕵️ Filtreleme: Niyet='{intent_type}', Kelimeler={search_keywords}")
    
    # Sadece tarih sorulduysa tümünü dön
    if intent_type == "search" and not search_keywords:
        print("💡 Sadece tarih/zaman soruldu, tüm veriler analiz edilecek...")
        return raw_rows, date_info

    filtered_results = []

    for row in raw_rows:
        category = str(row.get('category', '')).lower()
        source_col = str(row.get('source', '')).lower()
        data_type = str(row.get('data_type', '')).lower()
        content = safe_json_parse(row.get('content'))
        
        json_kaynak = str(content.get('kaynak', '')).lower()
        json_not = str(content.get('not', '')).lower()
        json_full_text = str(content).lower()

        match = False

        if intent_type == "sentiment":
            if "analyzed" in data_type or "sentiment" in category or "kaygı" in json_full_text:
                match = True

        elif intent_type == "category":
            if cleaned_value in category or cleaned_value in source_col:
                match = True

        elif intent_type == "platform":
            if cleaned_value in source_col or cleaned_value in json_kaynak or cleaned_value in category:
                match = True
            if cleaned_value == "trendyol" and "online_shopping" in source_col:
                match = True 

        elif intent_type == "early_trend":
            if "erkentrend" in json_not or "erken" in json_full_text:
                match = True

        else:
            found_keyword = False
            for word in search_keywords:
                if len(word) > 2:
                    stemmed_word = simple_turkish_stemmer(word)
                    if (word in json_full_text or stemmed_word in json_full_text or 
                        word in source_col or 
                        word in category or 
                        word in json_not or
                        word in json_kaynak):
                        found_keyword = True
                        break
            if found_keyword:
                match = True

        if match:
            filtered_results.append(row)

    print(f"✅ Eşleşen Kayıt Sayısı: {len(filtered_results)}")
    return filtered_results, date_info

# ---------------------------------------------------------------------------
# CHAT MOTORU
# ---------------------------------------------------------------------------

async def chat_with_ai(user_message: str) -> str:
    global conversation_history, last_successful_data, last_date_info
    
    if not ai_client: return "⚠️ AI sistemi bağlı değil."

    intent_data = get_search_intent_via_ai(user_message)
    intent_type = intent_data.get("intent", "search")

    # 1. SOHBET MODU
    if intent_type == "chat":
        chat_system_prompt = """
        Sen TrendAI, yardımcı ve arkadaş canlısı bir veri asistanısın.
        
        GÖREVİN:
        1. Kullanıcının selamına veya sohbetine nazikçe ve profesyonelce karşılık ver.
        2. Kendini tanıt: "Ben TrendAI, sosyal medya, e-ticaret ve trendleri analiz eden yapay zeka asistanıyım."
        3. Kullanıcıya ne aramak istediğini sor.
        4. Kısa, samimi ve Markdown formatında (bold, italik, liste) düzenli cevaplar ver.
        """
        
        messages = [{"role": "system", "content": chat_system_prompt}]
        messages.extend(conversation_history[-4:])
        messages.append({"role": "user", "content": user_message})
        
        try:
            response = ai_client.chat.completions.create(model=MODEL_NAME, messages=messages, temperature=0.7)
            ai_response = response.choices[0].message.content
            conversation_history.append({"role": "user", "content": user_message})
            conversation_history.append({"role": "assistant", "content": ai_response})
            return ai_response
        except:
            return "Merhaba! Şu an sohbet sistemimde bir yoğunluk var, ama verileri sorgulayabilirim."

    # 2. VERİ ÇEKME
    db_data, date_info = await fetch_smart_filtered_data(user_message, intent_data)
    
    # Hafıza Kontrolü
    used_cached_data = False
    if not db_data and last_successful_data:
        print("🔄 Hafızadaki veri kullanılıyor...")
        db_data = last_successful_data
        date_info = last_date_info
        used_cached_data = True
    
    count_found = len(db_data)

    if not db_data:
        response_msg = f"🔍 **{date_info}** tarih aralığında uygun veri bulamadım."
        conversation_history.append({"role": "user", "content": user_message})
        conversation_history.append({"role": "assistant", "content": response_msg})
        return response_msg

    if not used_cached_data:
        last_successful_data = db_data
        last_date_info = date_info

    # 3. Context Hazırlama
    clean_context = []
    # Token limiti için en güncel 200 veriyi analiz et
    for row in db_data[:200]: 
        content = safe_json_parse(row.get('content'))
        src = row.get('source', '').replace('.csv', '').replace('filtered_', '')
        if isinstance(content, dict) and content.get('kaynak'):
             src = content.get('kaynak')
        clean_context.append({"Platform": src, "Veri": content})

    context_str = json.dumps(clean_context, ensure_ascii=False)

    # 4. Veri Analiz Prompt'u (FORMAT GÜNCELLEMESİ)
    # 4. Veri Analiz Prompt'u (TABLO FORMATI GÜNCELLEMESİ)
    system_prompt = f"""
    Sen TrendAI, verilerin derinliklerini gören, **Üst Düzey Pazar Araştırmacısı ve Trend Stratejistisin.** 🧐
    Kullanıcıya ham veri değil, **işlenebilir içgörüler** ve **stratejik analizler** sunmalısın.
    
    **ZORUNLU GİRİŞ FORMATI:**
    
    > 📋 **Sorgu Raporu**
    > * **Tarih:** {date_info}
    
    
    
    **GÖRSEL VE ANALİZ KURALLARI (KESİN UY):**
    
    1. **BAŞLIK:** `## 🚀 {date_info} Stratejik Trend Raporu`
       Altına italik bir özet: *"Toplam **{count_found}** veri noktası tarandı ve piyasa hareketleri analiz edildi."*

    2. **PLATFORM GRUPLAMASI:** Verileri platformlarına göre ayır (Örn: `### 🛍️ Trendyol Analizi`).

    3. **HİYERARŞİK LİSTE FORMATI (ZORUNLU):**
       Her ürünü bir ana madde, özelliklerini ise girintili (indented) alt maddeler olarak yaz. 
       Veri içindeki etiketlerden (hashtag) yola çıkarak kısa bir "Uzman Yorumu" ekle.
       
       **Şu formatı birebir uygula:**
       
       - 📦 **Ürün:[Ürün Adı]**
         - 💰 **Fiyat:** [Fiyat] 
         - 📈 **Trend Skoru:** [Skor] / 100
         - 🏷️ **Etiketler:** [Not/Hashtagler]
         - 🧠 **Uzman Yorumu:** [Buraya ürünün neden trend olduğuna dair 1 cümlelik keskin bir analiz yaz.] [.Yeni ürüne geçmeden önce 1 boş satır bırak. ve  bir satır boyunca yatay çizgi koy ve tekrar bir satır boşluk bırak]
         

    4. cevabın okunabılır olsun.
    

    5. **TON:** Profesyonel, kendinden emin ama anlaşılır. Teknik terim (JSON vb.) yasak.
    
    6. **KAPANIŞ:** "Hangi ürünün pazar analizini derinleştirelim?" gibi stratejik bir soru sor.
    """

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(conversation_history[-4:]) 
    messages.append({"role": "user", "content": f"VERİ SETİ:\n{context_str}\n\nSORU: {user_message}"})

    try:
        response = ai_client.chat.completions.create(model=MODEL_NAME, messages=messages, temperature=0.7)
        ai_response = response.choices[0].message.content
        conversation_history.append({"role": "user", "content": user_message})
        conversation_history.append({"role": "assistant", "content": ai_response})
        return ai_response
    except Exception as e:
        return f"AI Hatası: {e}"

async def process_user_input(text: str) -> str:
    return await chat_with_ai(text)

async def fetch_large_recent_dataset(limit: int = 50): return []
async def save_trend(content: Any): return None
async def get_filtered_raw_data(categories, limit): return []
async def get_trends(limit=20): return []
async def get_products(): return []
async def get_stats(): return []
async def get_latest_trend_data(): return None