import os
import json
import re
from datetime import datetime
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

from supabase import create_client, Client
from openai import OpenAI

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

MODEL_NAME = "openai/gpt-4o-mini" # Veya "google/gemini-2.0-flash-exp:free"

supabase: Optional[Client] = None
ai_client: Optional[OpenAI] = None

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



async def fetch_large_recent_dataset(limit: int = 300) -> List[Dict]:
    """
    Veritabanından son verileri ham olarak çeker (Yedek/Genel kullanım için).
    """
    if not supabase: return []
    try:
        response = (
            supabase.table("processed_data")
            .select("*")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return response.data if response.data else []
    except Exception as e:
        print(f"Genel Veri Çekme Hatası: {e}")
        return []

async def save_trend(content: Any) -> Optional[List[Any]]:
    """Yeni trend/veri kaydetme fonksiyonu."""
    if not supabase: return None
    try:
        data_to_save = content
        if isinstance(content, str):
            try:
                data_to_save = json.loads(content)
            except:
                data_to_save = {"text": content}

        result = supabase.table("processed_data").insert({
            "content": data_to_save,
            "category": "user_input", 
            "data_type": "User",
            "created_at": datetime.utcnow().isoformat()
        }).execute()
        return result.data
    except Exception as e:
        print(f"Kaydetme Hatası: {e}")
        return None


async def fetch_smart_filtered_data(source_intent: str) -> List[Dict]:
    """
    SQL'de test ettiğimiz mantığı uygular:
    WHERE content ->> 'KAYNAK' LIKE '%youtube%'
    Bu sayede Python'da elemek yerine veritabanından nokta atışı veri isteriz.
    """
    if not supabase: return []

    try:
        query = supabase.table('processed_data').select("*")
        
        if source_intent != 'general':
            print(f"🔍 Supabase Filtresi: content->>KAYNAK içinde '{source_intent}' aranıyor...")
            
            query = query.filter('content->>KAYNAK', 'ilike', f'%{source_intent}%')
            
        else:
            print("🔍 Genel veri akışı (Filtresiz)...")
        
        response = query.order('created_at', desc=True).limit(15).execute()
        
        data = response.data if response.data else []
        print(f"✅ Veritabanından dönen kayıt sayısı: {len(data)}")
        return data
        
    except Exception as e:
        print(f"❌ Akıllı Sorgu Hatası: {e}")
        return []


def get_search_intent_via_ai(user_prompt: str) -> dict:
    
    if not ai_client: return {"source": "general"}

    system_prompt = """
    Sen bir veri sorgu uzmanısın. Kullanıcının sorusunu analiz et ve hangi veri kaynağını (platformu) merak ettiğini JSON olarak döndür.
    
    Tanımlı Kaynaklar:
    - youtube (Video, izlenme, youtube trendleri)
    - twitter (Gündem, hashtag, tweetler)
    - trendyol (Ürün, fiyat, alışveriş)
    - n11 (Alışveriş, n11)
    - amazon (Global alışveriş, amazon)
    - general (Eğer belirli bir platform adı geçmiyorsa veya genel trend soruluyorsa)
    
    Sadece JSON formatında cevap ver: {"source": "youtube"}
    """
    
    try:
        completion = ai_client.chat.completions.create(
            model=MODEL_NAME, 
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0, # Tutarlılık için 0
            max_tokens=50
        )
        response_text = completion.choices[0].message.content
        clean_json = response_text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_json)
    except Exception as e:
        print(f"⚠️ Niyet analizi fallback'e geçti: {e}")
        return {"source": extract_target_platform(user_prompt) or "general"}

def extract_target_platform(text: str) -> str:
    text = text.lower()
    mapping = {
        "youtube": "youtube", "tiktok": "tiktok", "instagram": "instagram",
        "twitter": "twitter", "amazon": "amazon", "trendyol": "trendyol",
        "n11": "n11", "a101": "a101", "carrefour": "carrefour"
    }
    for key, val in mapping.items():
        if key in text: return val
    return ""

def detect_greeting_or_identity(text: str) -> str:
    text = text.lower()
    if any(x in text for x in ["selam", "merhaba", "naber", "günaydın"]): return "greeting"
    if any(x in text for x in ["kimsin", "nesin", "ne yapabilirsin"]): return "identity"
    return "analyze"


async def chat_with_ai(user_message: str) -> str:
    if not ai_client: return "⚠️ AI sistemi bağlı değil."

    intent_type = detect_greeting_or_identity(user_message)
    if intent_type == "greeting":
        return "Selam! 👋 Ben TrendAI. Youtube, Trendyol, Twitter gibi kaynaklardan en güncel verileri senin için analiz edebilirim."
    if intent_type == "identity":
        return "Ben veritabanındaki trendleri analiz eden, Python ve AI tabanlı bir asistanım."

    intent_data = get_search_intent_via_ai(user_message)
    target_source = intent_data.get('source', 'general')
    
    if target_source == "general":
        manual_check = extract_target_platform(user_message)
        if manual_check: target_source = manual_check

    print(f"🤖 Hedef Kaynak: {target_source}")

    db_data = await fetch_smart_filtered_data(target_source)

    if not db_data:
        msg = f"🔍 '{target_source}' kategorisi için tarama yaptım." if target_source != 'general' else "🔍 Veritabanını taradım."
        return f"{msg} Ancak kriterlere uygun güncel ve içeriği dolu kayıt bulamadım. Scraper botların çalışıyor mu?"

    clean_context = [row.get('content') for row in db_data if row.get('content')]
    context_str = json.dumps(clean_context, ensure_ascii=False)
    
    system_prompt = f"""
    Sen profesyonel bir Trend Analistisin. 
    Önünde veritabanından çekilmiş **{target_source}** kaynaklı gerçek veriler var.
    
    GÖREVİN:
    1. Kullanıcının sorusuna bu verilere dayanarak cevap ver.
    2. Verilerdeki ürün adlarını, fiyatları, hashtag'leri veya izlenme sayılarını ön plana çıkar.
    3. Asla "JSON listesinde" veya "Database kaydında" deme. Sanki canlı görüyormuşsun gibi konuş.
    4. Maddeler halinde, okunabilir bir özet sun.
    """

    user_full_prompt = f"""
    Kullanıcı Sorusu: "{user_message}"
    
    BULUNAN VERİLER:
    {context_str}
    """

    try:
        response = ai_client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_full_prompt}
            ],
            temperature=0.7
        )
        return response.choices[0].message.content

    except Exception as e:
        print(f"AI Yanıt Hatası: {e}")
        return "Analiz sırasında beklenmedik bir hata oluştu."

async def process_user_input(text: str) -> str:
    return await chat_with_ai(text)

async def get_filtered_raw_data(categories, limit): return []
async def get_trends(limit=20): return []
async def get_products(): return []
async def get_stats(): return []
async def get_latest_trend_data(): return None