import os
import json
import random
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
    """
    Sorgudan tarih ARALIĞI çeker.
    GÜNCELLENDİ: 'son üç gün', 'son gün', '9 aralık' gibi karmaşık yapıları anlar.
    """
    text = text.lower()
    now = datetime.now()
    
    # Yazı ile yazılan sayıların sözlüğü
    text_numbers = {
        "bir": 1, "iki": 2, "üç": 3, "dört": 4, "beş": 5, 
        "altı": 6, "yedi": 7, "sekiz": 8, "dokuz": 9, "on": 10
    }

    # 1. "Son X Gün" (Rakamla: "son 5 gün")
    match_digits = re.search(r"son (\d+) gün", text)
    if match_digits:
        days = int(match_digits.group(1))
        start_date = now - timedelta(days=days)
        return start_date, now

    # 2. "Son X Gün" (Yazıyla: "son üç gün")
    match_words = re.search(r"son (\w+) gün", text)
    if match_words:
        word = match_words.group(1)
        if word in text_numbers:
            days = text_numbers[word]
            return now - timedelta(days=days), now

    # 3. "Son Gün" veya "Dün"
    if "son gün" in text or "dün" in text:
        # Eğer "dün ve bugün" denmişse
        if "bugün" in text: 
             return now - timedelta(days=1), now
        
        # Sadece "son gün" veya "dün"
        start = now - timedelta(days=1)
        # Bitiş de start olsun ki sadece o günü arasın veya aralığı geniş tutalım
        return start, now 

    # --- SAAT FARKI DÜZELTMESİ EKLENDİ ---
    if "bugün" in text:
        # UTC farkı yüzünden "bugün" denince dünü de kapsıyoruz.
        print("💡 Saat farkı önlemi: Arama aralığı 24 saat geriye çekildi.")
        return now - timedelta(days=1), now

    if "son hafta" in text or "bir hafta" in text:
        return now - timedelta(days=7), now

    # 4. Spesifik Tarih (Ay isimli: "9 Aralık", "10 Aralık")
    months = {
        "ocak": 1, "şubat": 2, "mart": 3, "nisan": 4, "mayıs": 5, "haziran": 6,
        "temmuz": 7, "ağustos": 8, "eylül": 9, "ekim": 10, "kasım": 11, "aralık": 12
    }
    
    # Döngüyle ay ismini metinde ara
    for month_name, month_num in months.items():
        if month_name in text:
            # "9 aralık", "09 aralık" formatını yakala
            match = re.search(r"(\d{1,2})\s*" + month_name, text)
            if match:
                day = int(match.group(1))
                try:
                    target_date = datetime(now.year, month_num, day)
                    
                    # Eğer bugün 11 Aralık ise ve kullanıcı "12 Aralık" dediyse, 
                    # muhtemelen geçen seneyi kastediyordur (geleceği tahmin edemeyeceğimiz için).
                    if target_date > now:
                        target_date = datetime(now.year - 1, month_num, day)
                    
                    # Başlangıç ve bitiş aynı gün (tam gün araması)
                    # Veritabanında saat farkı olabileceği için bitişi gün sonuna kadar esnetmek fetch içinde yapılıyor zaten
                    return target_date, target_date
                except ValueError:
                    # Geçersiz tarih (örn: 35 Şubat)
                    pass
    
    # Hiçbiri yoksa varsayılan olarak SON 3 GÜNÜ dön (Verisiz kalmamak için)
    print("💡 Tarih belirtilmedi, varsayılan olarak son 3 gün taranıyor...")
    return now - timedelta(days=3), now

def clean_search_term(text: Union[str, List[str]]) -> str:
    """
    Sorgudan gereksiz dolgu kelimelerini temizler.
    HATA DÜZELTME: Gelen veri liste ise stringe çevirir.
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
        "özellikleri", "tarafında", "öne", "çıkan", "başlıklar", "konuşuldu", "listele", "hepsini", "tümünü",
        "formatında", "cevap", "ver", "json", "yap", "yaz"  # <--- BURAYA YENİ KELİMELER EKLENDİ
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
# AI NİYET ANALİZİ (GÜNCELLENDİ: BUTONLARA ÖZEL INTENTLER)
# ---------------------------------------------------------------------------

def get_search_intent_via_ai(user_prompt: str, history: List[dict] = []) -> dict:
    if not ai_client: return {"intent": "search", "value": user_prompt}

    # Geçmişten son 2 mesajı alarak bağlam oluştur
    history_context = ""
    if history:
        last_turns = history[-2:]
        for msg in last_turns:
            role = "Kullanıcı" if msg['role'] == 'user' else "Asistan"
            history_context += f"{role}: {msg['content']}\n"

    # SİSTEM PROMPTU (BUTONLARA GÖRE GÜNCELLENDİ):
    system_prompt = f"""
    GÖREV: Kullanıcı mesajını ve sohbet geçmişini analiz et. JSON döndür.
    
    GEÇMİŞ SOHBET:
    {history_context}

    ANALİZ KURALLARI (BUTONLARA GÖRE):
    1. **SOHBET (Chat/Advice):** "Selam", "Nasılsın", "Sence bu iş tutar mı?" -> {{"intent": "chat", "value": "chat"}}
    2. **GENEL ARAMA (Search):** "Kahve makinesi", "iPhone fiyatları" -> {{"intent": "search", "value": "anahtar_kelime"}}
    
    3. **FİYAT/İNDİRİM (Buton):** "Fiyat fırsatları", "İndirimler", "En ucuz", "Kampanya" -> {{"intent": "price_analysis", "value": "genel"}}
    4. **PLATFORM ANALİZİ (Buton):** "Trendyol vs Amazon", "Platform karşılaştırması", "Hangi sitede" -> {{"intent": "platform_comparison", "value": "trendyol amazon"}}
    5. **DUYGU/YORUM (Buton):** "Müşteri şikayetleri", "Duygu analizi", "Yorumlar", "Memnuniyet" -> {{"intent": "sentiment_analysis", "value": "genel"}}
    6. **TRENDLER (Buton):** "Yükselen trendler", "Popüler ürünler", "Çok satanlar" -> {{"intent": "trend_analysis", "value": "genel"}}
    
    7. **DEVAM SORUSU (Follow-up):** "Peki ya diğeri?", "Detay ver" -> {{"intent": "search", "value": "context_ref", "is_follow_up": true}}
    8. **MİKTAR:** "5 tane getir", "ilk 10 sonuç" -> {{"quantity": 5}} eklenecek.
    9. **FORMAT:** "JSON ver" -> {{"output_format": "json"}}
    
    ÖRNEK: {{"intent": "price_analysis", "value": "iphone", "quantity": 5}}
    """
    try:
        completion = ai_client.chat.completions.create(
            model=MODEL_NAME, 
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
            temperature=0, max_tokens=150
        )
        clean_json = completion.choices[0].message.content.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(clean_json)
        # Debugging: Niyet analiz sonucunu görelim
        print(f"🧠 AI Niyet Algılandı: {parsed}")
        return parsed
    except:
        return {"intent": "search", "value": user_prompt}

# ---------------------------------------------------------------------------
# AKILLI FİLTRELEME (GÜNCELLENDİ: ÖZEL MODLARA GÖRE FİLTRELEME)
# ---------------------------------------------------------------------------

async def fetch_smart_filtered_data(user_query: str, intent_data: dict) -> Tuple[List[Dict], str]:
    if not supabase: return [], "Veritabanı Yok"

    start_date, end_date = extract_date_range_from_query(user_query)
    
    # Eğer özel bir analiz butonu tıklandıysa ve tarih yoksa, son 1 haftayı al (Verisiz kalmamak için)
    intent_type = intent_data.get("intent", "search")
    if intent_type in ["price_analysis", "platform_comparison", "sentiment_analysis", "trend_analysis"]:
        if "bugün" not in user_query.lower() and "dün" not in user_query.lower():
            print("💡 Özel analiz modu: Tarih aralığı otomatik olarak son 7 güne genişletildi.")
            start_date = datetime.now() - timedelta(days=7)

    if start_date.date() == end_date.date():
        date_info = start_date.strftime('%d %B %Y')
    else:
        date_info = f"{start_date.strftime('%d %B')} - {end_date.strftime('%d %B %Y')}"

    is_follow_up = intent_data.get("is_follow_up", False)

    # 1. Chat ve Garbage Durumları (ERKEN ÇIKIŞ)
    if intent_type == "chat": return [], date_info
    if intent_type == "garbage": return [], date_info 

    raw_value = intent_data.get("value", user_query)
    
    # Eğer "Peki ya diğeri?" gibi bir durumsa ve history yoksa, raw_value 'context_ref' gelir.
    if is_follow_up or raw_value == "context_ref":
        print("💡 Bağlam/Devam sorusu algılandı. Hafıza kontrol edilecek.")
        return [], date_info

    # TÜM VERİYİ ÇEK (Limitsiz)
    raw_rows = await fetch_data_in_range(start_date, end_date)
    if not raw_rows: return [], date_info

    print(f"🕵️ Filtreleme Başlıyor: Mod='{intent_type}'")
    filtered_results = []

    for row in raw_rows:
        content = safe_json_parse(row.get('content'))
        json_str = str(content).lower()
        source = str(row.get('source', '')).lower()
        category = str(row.get('category', '')).lower()
        
        json_kaynak = str(content.get('kaynak', '')).lower()
        json_not = str(content.get('not', '')).lower()
        json_full_text = str(content).lower()

        match = False

        # --- A) FİYAT FIRSATLARI MODU ---
        if intent_type == "price_analysis":
            keywords = ["fiyat", "tl", "indirim", "%", "ucuz", "pahalı", "kampanya", "zam"]
            if any(k in json_str for k in keywords):
                match = True

        # --- B) PLATFORM ANALİZİ MODU ---
        elif intent_type == "platform_comparison":
            platforms = ["trendyol", "amazon", "n11", "hepsiburada", "getir", "yemeksepeti"]
            if any(p in source for p in platforms) or any(p in json_str for p in platforms):
                match = True

        # --- C) MÜŞTERİ DUYGUSU MODU ---
        elif intent_type == "sentiment_analysis":
            sentiment_keys = ["yorum", "şikayet", "memnun", "kötü", "iyi", "duygu", "sentiment", "kaygı"]
            if any(k in json_str for k in sentiment_keys) or "filtered" in str(row.get('data_type')).lower():
                match = True

        # --- D) TREND ANALİZİ MODU ---
        elif intent_type == "trend_analysis":
            if "google" in source or "twitter" in source or "trend" in json_str or "best seller" in json_str:
                match = True
        
        # --- E) NORMAL ARAMA (Eski Kök Bulucu ile) ---
        else:
            cleaned_value = clean_search_term(raw_value)
            search_keywords = cleaned_value.split() if cleaned_value else []

            if not search_keywords:
                # Sadece tarih sorulduysa hepsini al
                match = True
            else:
                for word in search_keywords:
                    if len(word) > 2:
                        stemmed_word = simple_turkish_stemmer(word)
                        if (word in json_full_text or stemmed_word in json_full_text or 
                            word in source or 
                            word in category or 
                            word in json_not or
                            word in json_kaynak):
                            match = True
                            break
        
        if match:
            filtered_results.append(row)

    print(f"✅ Eşleşen Kayıt Sayısı: {len(filtered_results)}")
    return filtered_results, date_info

# ---------------------------------------------------------------------------
# CHAT MOTORU (GÜNCELLENDİ: KATI FİLTRELEME PROMPTU)
# ---------------------------------------------------------------------------

async def chat_with_ai(user_message: str) -> str:
    global conversation_history, last_successful_data, last_date_info
    
    if not ai_client: return "⚠️ AI sistemi bağlı değil."

    # Intent analizi
    intent_data = get_search_intent_via_ai(user_message, conversation_history)
    intent_type = intent_data.get("intent", "search")
    output_format = intent_data.get("output_format", "text") 
    is_follow_up = intent_data.get("is_follow_up", False)
    quantity_limit = intent_data.get("quantity")

    # 1. SOHBET MODU
    if intent_type == "chat":
        chat_system_prompt = """
        Sen TrendAI, hem güçlü bir veri analisti hem de yardımsever, zeki bir danışmansın.
        GÖREVLERİN:
        1. **Genel Sohbet:** Kullanıcı ile samimi ve profesyonel bir dille sohbet et.
        2. **Akıl Danışma:** Kullanıcı veritabanında olmayan genel bir soru sorarsa kendi genel bilginle cevap ver.
        TON: Yardımsever, Profesyonel, Samimi.
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
            return "Sistem yoğun, lütfen tekrar dene."

    # 2. VERİ ÇEKME
    db_data, date_info = await fetch_smart_filtered_data(user_message, intent_data)
    
    # Hafıza Kontrolü
    used_cached_data = False
    if (not db_data or is_follow_up) and last_successful_data:
        print("🔄 Hafızadaki veri kullanılıyor...")
        db_data = last_successful_data
        date_info = last_date_info
        used_cached_data = True
    
    if not db_data:
        if intent_type == "garbage":
            resp = "Tam olarak ne aradığını anlayamadım."
        else:
            resp = f"🔍 **{date_info}** tarih aralığında, **{intent_type}** kriterine uygun veri bulamadım."
            
        conversation_history.append({"role": "user", "content": user_message})
        conversation_history.append({"role": "assistant", "content": resp})
        return resp

    if not used_cached_data:
        last_successful_data = db_data
        last_date_info = date_info

    # 3. Context Hazırlama
    final_limit = 50
    if quantity_limit and isinstance(quantity_limit, int) and quantity_limit > 0:
        final_limit = quantity_limit
        print(f"✂️ Veri Seti Kullanıcı İsteği Üzerine Kesiliyor: {final_limit} adet")
    
    clean_context = []
    for row in db_data[:final_limit]: 
        content = safe_json_parse(row.get('content'))
        src = row.get('source', '').replace('.csv', '').replace('filtered_', '')
        if isinstance(content, dict) and content.get('kaynak'):
             src = content.get('kaynak')
        clean_context.append({"Platform": src, "Veri": content})

    context_str = json.dumps(clean_context, ensure_ascii=False)

    # 4. Veri Analiz Prompt'u (DİNAMİK SEÇİM)
    if output_format == "json":
        system_prompt = """GÖREV: Sadece saf JSON döndür. Markdown yok."""
    else:
        limit_instruction = f"Eğer kullanıcı belirli bir sayıda veri istediyse ({final_limit} tane), sadece onlara odaklan." if quantity_limit else ""

        system_prompt = f"""
        Sen TrendAI, verilerin derinliklerini gören, **Üst Düzey Pazar Araştırmacısı ve Trend Stratejistisin.** 🧐
        
        GÖREVİN: Ham verileri analiz edip **TİCARİ** ve **STRATEJİK** içgörüler sunmak.

        {limit_instruction}
        
        🚨 **ÇOK KATI FİLTRELEME KURALLARI (BUNLARA UY):**
        1. **ÇÖP VERİYİ YOK SAY:** "Maç kaç kaç", "Hava nasıl", "Selam", "Günaydın" gibi günlük sohbetleri veya genel bilgi sorularını **ASLA** rapora dahil etme. Bunları sessizce ele.
        2. **SADECE TİCARİ ODAK:** Sadece şunları analiz et:
           - 🛒 Ürünler ve Markalar (Örn: Airfryer, iPhone, Kedi Maması)
           - 📉 Fiyat ve Ekonomi (Örn: İndirim, pahalılık, zam)
           - 🛍️ Tüketici İsteği (Örn: "Şunu arıyorum", "Bunu tavsiye edin")
        3. **SOSYAL MEDYA İÇERİĞİ:** "Komik kedi videosu" gibi içerikleri, eğer bir **ürün satışı** veya **marka işbirliği** içermiyorsa ELEYEBİLİRSİN.
        4. Eğer analiz edilecek **HİÇBİR** ticari veri kalmazsa, dürüstçe "Ticari değer taşıyan veri bulunamadı" de.

        **RAPOR FORMATI:**
        > 📋 **Sorgu Raporu**
        > * **Tarih:** {date_info}
        
        ## 🚀 {date_info} Stratejik Trend Raporu
        *İncelenen Veri Sayısı: **{{analiz_edilen_veri_sayisi}}** (Gürültülü veriler elendi)*

        ### 🔎 Öne Çıkan Ticari Trendler:

        - 📦 **[Ürün/Konu Başlığı]**
          - 💰 **Fiyat:** [Varsa Fiyat / Yoksa "Belirtilmedi"] 
          - 📈 **Trend Skoru:** [0-100 Arası Tahmini Skor]
          - 🏷️ **Etiketler:** [#Etiket1 #Etiket2]
          - 🧠 **Uzman Yorumu:** [Bu verinin pazarlama veya satış için anlamı ne?]
        
        KAPANIŞ: Stratejik bir soru sor.
        """

    messages = [{"role": "system", "content": system_prompt}]
    if output_format != "json":
        messages.extend(conversation_history[-4:]) 
        
    messages.append({"role": "user", "content": f"VERİ SETİ:\n{context_str}\n\nSORU: {user_message}"})

    try:
        response = ai_client.chat.completions.create(model=MODEL_NAME, messages=messages, temperature=0.7)
        ai_response = response.choices[0].message.content
        
        if output_format == "json":
            ai_response = ai_response.replace("```json", "").replace("```", "").strip()
            
        conversation_history.append({"role": "user", "content": user_message})
        conversation_history.append({"role": "assistant", "content": ai_response})
        return ai_response
    except Exception as e:
        return f"AI Hatası: {e}"

async def process_user_input(text: str) -> str:
    return await chat_with_ai(text)

# Hata almamak için boş placeholder fonksiyonlar
async def fetch_large_recent_dataset(limit: int = 50): return []
async def save_trend(content: Any): return None
async def get_filtered_raw_data(categories, limit): return []
async def get_trends(limit=20): return []
async def get_products(): return []
async def get_stats(): return []
async def get_latest_trend_data(): return None










import os
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

from supabase import create_client, Client
from openai import OpenAI

load_dotenv()

# AYARLAR
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
MODEL_NAME = "openai/gpt-4o-mini" 

supabase: Optional[Client] = None
ai_client: Optional[OpenAI] = None

# BAĞLANTILAR
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Supabase: AKTİF")
    except Exception as e:
        print(f"❌ Supabase Hatası: {e}")

if OPENROUTER_API_KEY:
    try:
        ai_client = OpenAI(api_key=OPENROUTER_API_KEY, base_url=OPENROUTER_BASE_URL)
        print("✅ AI: AKTİF")
    except Exception as e:
        print(f"❌ AI Hatası: {e}")

def safe_json_parse(content: Any) -> Any:
    if isinstance(content, dict): return content
    if isinstance(content, str):
        try: return json.loads(content)
        except: return {}
    return {}

# ---------------------------------------------------------------------------
# DASHBOARD ENGINE (ASLA BOŞ KALMAYAN AI ANALİZİ)
# ---------------------------------------------------------------------------
async def get_dashboard_stats(time_range: str = "24h"):
    if not supabase: return None

    # Saati SQL'e göndermek için hesapla
    hours = 24
    if time_range == "7d": hours = 168
    if time_range == "30d": hours = 720

    try:
        # 1. SQL FONKSİYONUNU ÇAĞIR (Sayılar ve Grafikler)
        response = supabase.rpc('get_trend_dashboard_stats', {'lookback_hours': hours}).execute()
        data = response.data 
        if not data: return None

        # 2. AI İÇGÖRÜSÜ (GARANTİLİ DOLULUK)
        ai_insight = "Veriler analiz ediliyor..."
        
        if ai_client:
            # ADIM A: Önce seçili tarih aralığındaki verileri çek
            start_date_iso = (datetime.now() - timedelta(hours=hours)).isoformat()
            
            rows_query = supabase.table("processed_data")\
                .select("content, source")\
                .filter("created_at", "gte", start_date_iso)\
                .order("created_at", desc=True)\
                .limit(200)\
                .execute()
            
            raw_rows = rows_query.data or []

            # ADIM B: Eğer tarih aralığında hiç veri yoksa, TARİH SINIRINI KALDIR ve son 50 veriyi çek (Fallback)
            if not raw_rows:
                print("⚠️ Seçili aralıkta veri yok, son verilere bakılıyor...")
                rows_query = supabase.table("processed_data")\
                    .select("content, source")\
                    .order("created_at", desc=True)\
                    .limit(50)\
                    .execute()
                raw_rows = rows_query.data or []

            # E-Ticaret Anahtar Kelimeleri
            ecommerce_keys = ["trendyol", "amazon", "n11", "alibaba", "a101", "carrefour", "migros", "getir", "online_shopping", "market", "fiyat"]
            
            shopping_pool = []
            general_pool = []
            
            for r in raw_rows:
                c = safe_json_parse(r.get('content'))
                
                # Kaynak ismini belirle
                src_raw = str(r.get('source', '')).lower()
                if isinstance(c, dict) and c.get('kaynak'):
                    src_raw = str(c.get('kaynak')).lower()
                
                # Veriyi okunabilir hale getir
                info = ""
                if isinstance(c, dict):
                    # Ürün/Fiyat/Başlık yakalamaya çalış
                    p_name = str(c.get('urun_adi', c.get('product_name', c.get('title', c.get('baslik', '')))))
                    price = str(c.get('fiyat', c.get('price', '')))
                    
                    if len(p_name) > 2:
                        info = f"{p_name} ({price})" if len(price) > 1 else p_name
                    else:
                        info = str(c.get('not', ''))[:100] # Yedek
                
                if len(info) > 5:
                    clean_src = src_raw.upper().replace('.CSV','').replace('FILTERED_','')
                    entry = f"[{clean_src}] {info}"
                    
                    # Havuzlara dağıt
                    general_pool.append(entry)
                    if any(k in src_raw for k in ecommerce_keys):
                        shopping_pool.append(entry)

            # ADIM C: Hangi havuzu kullanacağız?
            # Öncelik E-Ticaret, yoksa Genel Havuz
            final_pool = shopping_pool if shopping_pool else general_pool
            is_shopping_focus = len(shopping_pool) > 0

            if final_pool:
                # Rastgele 20 tanesini seç
                selected_items = random.sample(final_pool, min(len(final_pool), 20))
                summary_text = "\n".join(selected_items)
                
                period_name = "son 24 saat" if time_range == "24h" else "bu hafta" if time_range == "7d" else "bu ay"
                focus_role = "E-Ticaret Analistisin" if is_shopping_focus else "Pazar Analistisin"

                prompt = f"""
                Sen Kıdemli {focus_role}. Aşağıda {period_name} içinde veritabanına giren 
                gerçek verilerden rastgele seçilmiş bir numune var.
                
                VERİLER:
                {summary_text}
                
                GÖREV:
                Bu verilere bakarak Yöneticiler için 2-3 cümlelik, ÇARPICI bir "Pazar Özeti" yaz.
                - Hangi ürünlerde/konularda hareketlilik var?
                - Fiyat veya müşteri şikayeti trendi ne yönde?
                
                Sayı verme ("5 ürün var" deme), genel trendi yorumla. Asla sistem mesajlarından bahsetme.
                """
                try:
                    completion = ai_client.chat.completions.create(
                        model=MODEL_NAME, messages=[{"role": "user", "content": prompt}],
                        temperature=0.7, max_tokens=250
                    )
                    ai_insight = completion.choices[0].message.content.replace('"', '').strip()
                except: 
                    ai_insight = "AI servisine ulaşılamadı."
            else:
                ai_insight = "Veritabanında analiz edilecek anlamlı veri bulunamadı."

        data['ai_insight'] = ai_insight
        data['system_status'] = "Stabil"
        return data

    except Exception as e:
        print(f"Stats Error: {e}")
        return None
    
    
    
    
    
    

    # ---------------------------------------------------------------------------

def safe_json_parse(content: Any) -> Any:
    if isinstance(content, dict): return content
    if isinstance(content, str):
        try: return json.loads(content)
        except: return {}
    return {}

# ---------------------------------------------------------------------------
# 1. TREND HAVUZU (LİSTELEME SAYFASI İÇİN)
# ---------------------------------------------------------------------------
async def get_top_trends(period: str = "daily"):
    """TrendsPage.tsx için verileri çeker."""
    if not supabase: return []
    
    days = 1
    if period == "weekly": days = 7
    if period == "monthly": days = 30
    
    try:
        response = supabase.rpc('get_top_trends', {'lookback_days': days}).execute()
        return response.data or []
    except Exception as e:
        print(f"Trends Error: {e}")
        return []

# ---------------------------------------------------------------------------
# 2. DASHBOARD ENGINE (AI ANALİZİ - DOSYA İSİMLERİNE GÖRE)
# ---------------------------------------------------------------------------
async def get_dashboard_stats(time_range: str = "24h"):
    print(f"\n--- [DEBUG] Dashboard İsteği: {time_range} ---")
    if not supabase: return None

    # Saati SQL'e göndermek için hesapla
    hours = 24
    if time_range == "7d": hours = 168
    if time_range == "30d": hours = 720

    try:
        # A) SQL VERİLERİ (Grafikler ve Sayılar)
        response = supabase.rpc('get_trend_dashboard_stats', {'lookback_hours': hours}).execute()
        data = response.data 
        if not data: return None

        # B) AI STRATEJİK İÇGÖRÜ (SON 50 VERİ ANALİZİ)
        ai_insight = "Veriler analiz ediliyor..."
        
        # Period ismi
        period_name = "son 24 saat"
        if time_range == "7d": period_name = "son 1 hafta"
        if time_range == "30d": period_name = "son 1 ay"
        
        if ai_client:
            print("🔍 Filtresiz son 50 veri çekiliyor...")
            
            # Sistem testlerini hariç tut, gerisini al
            query = supabase.table("processed_data")\
                .select("content, source")\
                .not_.ilike("source", "%test%")\
                .not_.ilike("source", "%system%")\
                .order("created_at", desc=True)\
                .limit(50)\
                .execute()
            
            raw_rows = query.data or []
            
            analysis_pool = []
            
            # --- GÜNCELLENMİŞ KAYNAK HARİTASI (SENİN DOSYALARINA GÖRE) ---
            source_map = {
                "trendyol": "Trendyol", 
                "amazon": "Amazon", 
                "n11": "N11", 
                "alibaba": "Alibaba", 
                "a101": "A101", 
                "carrefour": "CarrefourSA", 
                "google": "Google Trends",
                "instagram": "Instagram",
                "tiktok": "TikTok",
                "twitter": "Twitter",
                "youtube": "YouTube"
            }

            for r in raw_rows:
                c = safe_json_parse(r.get('content'))
                
                # Kaynağı Bul (Önce JSON içindeki 'kaynak', yoksa 'source' dosya adı)
                raw_src = str(r.get('source', '')).lower()
                if isinstance(c, dict) and c.get('kaynak'):
                    raw_src = str(c.get('kaynak')).lower()
                
                # Kaynağı Temiz İsimle Eşleştir
                clean_source = "Genel"
                for key, val in source_map.items():
                    if key in raw_src: # örn: 'trendyol_kategorili.csv' içinde 'trendyol' var mı?
                        clean_source = val
                        break
                
                # İçeriği Formatla (AI'ya göndermek için özetle)
                info = ""
                if isinstance(c, dict):
                    # Olası tüm veri alanlarını kontrol et
                    parts = []
                    
                    # Ürün / Başlık
                    p_name = c.get('urun_adi') or c.get('product_name') or c.get('title') or c.get('baslik') or c.get('query')
                    if p_name: parts.append(str(p_name))
                    
                    # Fiyat
                    price = c.get('fiyat') or c.get('price')
                    if price: parts.append(f"Fiyat: {price}")
                    
                    # Sosyal Medya Metni
                    text = c.get('text') or c.get('tweet') or c.get('icerik')
                    if text: parts.append(f"İçerik: {str(text)[:100]}...") # Çok uzunsa kes
                    
                    # Eğer hiçbiri yoksa 'not' kısmına bak
                    if not parts and c.get('not'):
                        parts.append(str(c.get('not'))[:100])
                        
                    if parts:
                        info = " | ".join(parts)
                    else:
                        info = str(c)[:150] # Hiçbir yapı yoksa ham JSON'ın başını al

                if len(info) > 5:
                    analysis_pool.append(f"[{clean_source}] {info}")

            print(f"📊 AI İçin Hazırlanan Veri Sayısı: {len(analysis_pool)}")

            # C) AI ANALİZİ
            if analysis_pool:
                # Rastgele 20 tanesini seç (Çeşitlilik için)
                sample_size = min(len(analysis_pool), 20)
                selected_items = random.sample(analysis_pool, sample_size)
                summary_text = "\n".join(selected_items)
                
                prompt = f"""
                Sen Kıdemli Veri Stratejistisin. Aşağıda veritabanına giren SON GERÇEK VERİLER listelenmiştir.
                Her satırın başında [KAYNAK] belirtilmiştir (Örn: [Trendyol], [Twitter]).
                
                VERİLER:
                {summary_text}
                
                GÖREV:
                Bu verilere bakarak Yöneticiler için 2-3 cümlelik, SOMUT ve ÇARPICI bir "Durum Özeti" yaz.
                - Hangi platformda (Trendyol, Twitter vb.) ne tür bir hareketlilik var?
                - Öne çıkan bir ürün, konu veya fiyat değişimi var mı?
                
                Marka veya platform ismi vererek konuş. Asla 'veri yok' deme.
                """
                try:
                    completion = ai_client.chat.completions.create(
                        model=MODEL_NAME, messages=[{"role": "user", "content": prompt}],
                        temperature=0.7, max_tokens=300
                    )
                    ai_insight = completion.choices[0].message.content.replace('"', '').strip()
                except: 
                    ai_insight = "AI servisine bağlanılamadı."
            else:
                ai_insight = "Veritabanında analiz edilecek anlamlı veri bulunamadı (Veriler test verisi olabilir)."

        data['ai_insight'] = ai_insight
        data['system_status'] = "Stabil"
        return data

    except Exception as e:
        print(f"❌ Dashboard Hatası: {e}")
        return None
    

   
    
    

    