import os
import json
import re
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
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
    """Türkçe kelime kökü bulucu."""
    word = word.lower().strip()
    suffixes = [
        "lar", "ler", "nın", "nin", "nun", "nün", "dan", "den", "tan", "ten",
        "da", "de", "ta", "te", "ı", "i", "u", "ü", "a", "e", "n", "m", "sı", "si", "su", "sü"
    ]
    if len(word) < 4: return word
    for suffix in suffixes:
        if word.endswith(suffix):
            if len(word) - len(suffix) >= 3:
                return word[:-len(suffix)]
    return word

def safe_json_parse(content: Any) -> Any:
    if isinstance(content, dict): return content
    if isinstance(content, str):
        try: return json.loads(content)
        except: return {}
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

    # 2. Göreli Tarihler
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

def clean_search_term(text: str) -> str:
    text = text.lower()
    months = ["ocak", "şubat", "mart", "nisan", "mayıs", "haziran", "temmuz", "ağustos", "eylül", "ekim", "kasım", "aralık"]
    for m in months:
        text = re.sub(r"\d+\s+" + m, "", text)
    text = re.sub(r"son \d+ gün", "", text)
    text = text.replace("dün", "").replace("bugün", "")

    stopwords = ["neler", "oldu", "var", "mi", "mu", "hakkında", "ile", "ilgili", "durum", "ne", 
                 "tarihinde", "günü", "fiyatları", "fiyatı", "verileri", "getir", "göster", "ve", "veya", 
                 "en", "ucuz", "pahalı", "hangisi", "peki", "bunların", "şunların", "onların", "içinde", 
                 "arasında", "olan", "kadar", "daha", "çok", "az", "yüksek", "düşük", "şu", "bu", "o",
                 "özellikleri", "tarafında", "öne", "çıkan", "başlıklar", "konuşuldu", "listele"]
    for word in stopwords:
        text = text.replace(f" {word} ", " ").replace(f" {word}", "").replace(f"{word} ", "")
    
    return text.strip()

# ---------------------------------------------------------------------------
# VERİTABANI İŞLEMLERİ (LİMİTSİZ ÇEKİM)
# ---------------------------------------------------------------------------

async def fetch_data_in_range(start_date: datetime, end_date: datetime) -> List[Dict]:
    if not supabase: return []
    try:
        start_str = start_date.replace(hour=0, minute=0, second=0).isoformat()
        end_str = end_date.replace(hour=23, minute=59, second=59).isoformat()

        print(f"📡 Veri Çekiliyor: {start_str} -> {end_str}")

        response = (
            supabase.table("processed_data")
            .select("*")
            .in_("data_type", ["Filtered", "Analyzed"]) 
            .filter("created_at", "gte", start_str)
            .filter("created_at", "lte", end_str)
            .order("created_at", desc=True)
            .limit(100000) 
            .execute()
        )
        data = response.data if response.data else []
        print(f"✅ Çekilen Ham Veri Sayısı: {len(data)}")
        return data
    except Exception as e:
        print(f"❌ Veri Çekme Hatası: {e}")
        return []

# ---------------------------------------------------------------------------
# AI NİYET ANALİZİ (GÜNCELLENDİ: CHAT MODU EKLENDİ)
# ---------------------------------------------------------------------------

def get_search_intent_via_ai(user_prompt: str) -> dict:
    if not ai_client: return {"intent": "search", "value": user_prompt}

    # GÜNCELLEME: "chat" niyeti eklendi
    system_prompt = """
    Kullanıcı mesajını analiz et ve JSON döndür.
    
    1. SOHBET (Chat): "Selam", "Nasılsın", "Kimsin", "Teşekkürler", "Ne yapabilirsin?" -> {"intent": "chat", "value": "chat"}
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
# AKILLI FİLTRELEME (STEMMING + DEEP SEARCH)
# ---------------------------------------------------------------------------

async def fetch_smart_filtered_data(user_query: str, intent_data: dict) -> Tuple[List[Dict], str]:
    if not supabase: return [], "Veritabanı Yok"

    start_date, end_date = extract_date_range_from_query(user_query)
    
    if start_date.date() == end_date.date():
        date_info = start_date.strftime('%d %B %Y')
    else:
        date_info = f"{start_date.strftime('%d %B')} - {end_date.strftime('%d %B %Y')}"

    intent_type = intent_data.get("intent", "search")
    
    # EĞER NİYET SOHBET İSE VERİ ÇEKMEYE GEREK YOK
    if intent_type == "chat":
        return [], date_info

    raw_value = intent_data.get("value", user_query).lower().strip().replace("#", "")
    
    cleaned_value = clean_search_term(raw_value) if intent_type == "search" else raw_value
    search_keywords = cleaned_value.split() if cleaned_value else []

    if intent_type == "search" and not search_keywords:
        if "aralık" in user_query.lower() or "dün" in user_query.lower() or "bugün" in user_query.lower() or "gün" in user_query.lower():
             # Tarih var ama kelime yok, veriyi çekmeliyiz
             pass
        else:
             print("💡 Arama terimi bulunamadı (Devam sorusu), hafıza kullanılacak...")
             return [], date_info

    raw_rows = await fetch_data_in_range(start_date, end_date)
    if not raw_rows: return [], date_info

    print(f"🕵️ Filtreleme: Niyet='{intent_type}', Kelimeler={search_keywords}")
    
    # Sadece tarih sorulduysa tümünü dön
    if intent_type == "search" and not search_keywords:
        print("💡 Sadece tarih/zaman soruldu, tüm veriler özetleniyor...")
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
# CHAT MOTORU (GELİŞMİŞ HAFIZA, SOHBET VE BAĞLAM)
# ---------------------------------------------------------------------------

async def chat_with_ai(user_message: str) -> str:
    global conversation_history, last_successful_data, last_date_info
    
    if not ai_client: return "⚠️ AI sistemi bağlı değil."

    # 1. Niyet Analizi
    intent_data = get_search_intent_via_ai(user_message)
    intent_type = intent_data.get("intent", "search")

    # --- SOHBET MODU (YENİ EKLENDİ) ---
    # Eğer niyet 'chat' ise veritabanı işlemlerini atla ve direkt sohbet et
    if intent_type == "chat":
        chat_system_prompt = """
        Sen TrendAI, yardımcı ve arkadaş canlısı bir veri asistanısın.
        
        GÖREVİN:
        1. Kullanıcının selamına veya sohbetine nazikçe karşılık ver.
        2. Kendini tanıt: "Ben TrendAI, sosyal medya, e-ticaret ve trendleri analiz eden yapay zeka asistanıyım."
        3. Kullanıcıya ne aramak istediğini sor (Örn: "Bugün Trendyol'da neler olduğunu merak ediyor musun?").
        4. Kısa ve samimi cevaplar ver.
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

    # 2. Veri Çekme (Sohbet değilse)
    db_data, date_info = await fetch_smart_filtered_data(user_message, intent_data)
    
    # --- BAĞLAM KONTROLÜ ---
    used_cached_data = False
    
    # Yeni veri yoksa + Hafıza varsa -> Hafızayı kullan
    if not db_data and last_successful_data:
        print("🔄 Yeni arama boş döndü, önceki BAĞLAM (Hafıza) kullanılıyor...")
        db_data = last_successful_data
        date_info = last_date_info
        used_cached_data = True
    
    count_found = len(db_data)

    if not db_data:
        response_msg = f"🔍 {date_info} tarih aralığında aradığınız kriterlere uygun veri bulamadım."
        conversation_history.append({"role": "user", "content": user_message})
        conversation_history.append({"role": "assistant", "content": response_msg})
        return response_msg

    if not used_cached_data:
        last_successful_data = db_data
        last_date_info = date_info

    # 3. Context Hazırlama
    clean_context = []
    for row in db_data[:150]: 
        content = safe_json_parse(row.get('content'))
        src = row.get('source', '').replace('.csv', '').replace('filtered_', '')
        if isinstance(content, dict) and content.get('kaynak'):
             src = content.get('kaynak')
        clean_context.append({"Platform": src, "Veri": content})

    context_str = json.dumps(clean_context, ensure_ascii=False)

    # 4. Veri Analiz Prompt'u
    system_prompt = f"""
    Sen TrendAI, profesyonel bir veri analistisin.
    
    RAPOR:
    - Tarih: {date_info}
    - Toplam Veri: {count_found} adet
    - Hafıza Kullanımı: {'EVET' if used_cached_data else 'HAYIR'}
    
    KURALLAR:
    1. Kullanıcıyla sohbet et. Önceki konuşmaları hatırla.
    2. Cevaba mutlaka "{date_info} tarihlerinde toplam {count_found} adet veri buldum." gibi bir özetle başla.
    3. JSON verilerini analiz et. Hangi platformdan (Trendyol, Twitter) ne geldiğini belirterek anlat.
    4. "JSON listesi" deme. "Güncel verilere göre..." de.
    5. Kullanıcı "peki fiyatlar?" gibi devam sorusu sorarsa elindeki bu verileri tekrar analiz et.
    """

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(conversation_history[-4:]) 
    
    messages.append({
        "role": "user", 
        "content": f"MEVCUT VERİ SETİ:\n{context_str}\n\nKullanıcı Sorusu: {user_message}"
    })

    try:
        response = ai_client.chat.completions.create(
            model=MODEL_NAME, messages=messages, temperature=0.7
        )
        ai_response = response.choices[0].message.content
        
        conversation_history.append({"role": "user", "content": user_message})
        conversation_history.append({"role": "assistant", "content": ai_response})
        
        return ai_response

    except Exception as e:
        return f"AI Hatası: {e}"

async def process_user_input(text: str) -> str:
    return await chat_with_ai(text)

# Hata önleyici boş fonksiyonlar
async def fetch_large_recent_dataset(limit: int = 50): return []
async def save_trend(content: Any): return None
async def get_filtered_raw_data(categories, limit): return []
async def get_trends(limit=20): return []
async def get_products(): return []
async def get_stats(): return []
async def get_latest_trend_data(): return None