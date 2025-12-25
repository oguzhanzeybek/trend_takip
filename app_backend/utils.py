import os
import json
import re
from datetime import datetime, timedelta
from typing import Any, Tuple, Union, List
from dotenv import load_dotenv
from supabase import create_client, Client
from openai import OpenAI

load_dotenv()

# --- BAĞLANTILAR ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
MODEL_NAME = "openai/gpt-4o-mini"

supabase: Client = None
ai_client: OpenAI = None

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

# --- YARDIMCI FONKSİYONLAR ---

def safe_json_parse(content: Any) -> Any:
    if isinstance(content, dict): return content
    if isinstance(content, str):
        try: return json.loads(content)
        except: return {}
    return {}

def simple_turkish_stemmer(word: str) -> str:
    """Basit Türkçe kök bulucu."""
    word = word.lower().strip()
    if len(word) < 3: return word
    suffixes = ["lar", "ler", "dan", "den", "tan", "ten", "nın", "nin", "nun", "nün"]
    for suffix in suffixes:
        if word.endswith(suffix) and len(word) > len(suffix) + 2:
            word = word[:-len(suffix)]
            break
    return word

def extract_date_range_from_query(text: str) -> Tuple[datetime, datetime]:
    """Metinden tarih aralığı çıkarır."""
    text = text.lower()
    now = datetime.now()
    
    if "bugün" in text:
        return now - timedelta(days=1), now
    if "dün" in text:
        return now - timedelta(days=2), now - timedelta(days=1)
    if "son hafta" in text or "bu hafta" in text:
        return now - timedelta(days=7), now
    if "son ay" in text:
        return now - timedelta(days=30), now
        
    # Varsayılan: Son 3 gün
    return now - timedelta(days=3), now