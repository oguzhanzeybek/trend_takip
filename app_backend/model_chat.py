import json
from datetime import datetime
from typing import List, Tuple
from utils import ai_client, MODEL_NAME, extract_date_range_from_query, safe_json_parse
import model_data 

conversation_history = []
last_successful_data = []
last_date_info = ""

def get_search_intent_via_ai(user_prompt: str) -> dict:
    """Kullanıcının ne yapmak istediğini anlar."""
    if not ai_client: return {"intent": "search", "value": user_prompt}

    system_prompt = """
    GÖREV: Kullanıcı mesajını analiz et ve JSON döndür.
    
    INTENTLER:
    1. "chat": "Selam", "Nasılsın", "Teşekkürler".
    2. "search": "iPhone fiyatları", "Son dakika haberleri".
    3. "price_analysis": "İndirimler", "En ucuz", "Fiyat fırsatları".
    4. "trend_analysis": "Neler popüler", "Trendler".
    5. "platform_comparison": "Trendyol vs Amazon", "Hangi site".
    
    ÖRNEK: {"intent": "price_analysis", "value": "telefon"}
    """
    try:
        completion = ai_client.chat.completions.create(
            model=MODEL_NAME, 
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
            temperature=0, max_tokens=100
        )
        clean_json = completion.choices[0].message.content.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_json)
    except:
        return {"intent": "search", "value": user_prompt}

async def fetch_smart_filtered_data(user_query: str, intent_data: dict) -> Tuple[List, str]:
    """Niyet analizine göre model_data üzerinden veri çeker ve filtreler."""
    start_date, end_date = extract_date_range_from_query(user_query)
    date_info = f"{start_date.strftime('%d %B')} - {end_date.strftime('%d %B')}"
    
    raw_rows = await model_data.fetch_data_in_range(start_date, end_date)
    filtered_results = []
    
    search_val = intent_data.get("value", "").lower()
    intent_type = intent_data.get("intent", "search")

    for row in raw_rows:
        content_str = str(row.get('content')).lower()
        source_str = str(row.get('source')).lower()
        
        match = False
        if intent_type == "price_analysis":
            if any(x in content_str for x in ["fiyat", "indirim", "tl", "ucuz"]): match = True
        elif intent_type == "platform_comparison":
            if any(x in source_str for x in ["trendyol", "amazon", "hepsiburada"]): match = True
        else: # Genel Arama
            if search_val in content_str or search_val in source_str: match = True
            
        if match: filtered_results.append(row)
            
    return filtered_results, date_info

async def chat_with_ai(user_message: str) -> str:
    global conversation_history, last_successful_data, last_date_info
    
    if not ai_client: return "⚠️ AI sistemi bağlı değil."
    
    intent_data = get_search_intent_via_ai(user_message)
    intent_type = intent_data.get("intent", "search")
    
    if intent_type == "chat":
        messages = [{"role": "system", "content": "Sen TrendAI adında yardımsever bir asistansın."}]
        messages.extend(conversation_history[-3:])
        messages.append({"role": "user", "content": user_message})
        
        resp = ai_client.chat.completions.create(model=MODEL_NAME, messages=messages)
        ai_reply = resp.choices[0].message.content
        conversation_history.append({"role": "user", "content": user_message})
        conversation_history.append({"role": "assistant", "content": ai_reply})
        return ai_reply

    db_data, date_info = await fetch_smart_filtered_data(user_message, intent_data)
    
    if not db_data:
        return f"🔍 {date_info} tarihleri arasında '{intent_data.get('value')}' ile ilgili veri bulamadım."

    context_str = json.dumps([row['content'] for row in db_data[:30]], ensure_ascii=False)
    
    system_prompt = f"""
    Sen TrendAI, uzman bir veri analistisin.
    
    GÖREV:
    Kullanıcının sorusunu AŞAĞIDAKİ VERİLERE dayanarak cevapla.
    Tarih: {date_info}
    
    KURALLAR:
    - Verilerde olmayan bir şeyi uydurma.
    - Ticari bir dil kullan.
    - Fiyatlardan ve trendlerden bahset.
    
    VERİLER:
    {context_str}
    """
    
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(conversation_history[-2:])
    messages.append({"role": "user", "content": user_message})
    
    try:
        resp = ai_client.chat.completions.create(model=MODEL_NAME, messages=messages, temperature=0.7)
        ai_reply = resp.choices[0].message.content
        
        conversation_history.append({"role": "user", "content": user_message})
        conversation_history.append({"role": "assistant", "content": ai_reply})
        return ai_reply
    except Exception as e:
        return f"AI Hatası: {e}"

async def process_user_input(text: str) -> str:
    return await chat_with_ai(text)

async def analyze_with_ai(prompt: str) -> str:
    """
    Sadece verilen prompt'u AI'ya gönderir ve cevabı döner.
    Sohbet geçmişini veya veritabanı filtrelerini kullanmaz.
    Dashboard stratejik analizleri için kullanılır.
    """
    if not ai_client: 
        return "⚠️ AI sistemi bağlı değil."
    
    try:
        resp = ai_client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "Sen yetenekli bir iş ve e-ticaret danışmanısın."},
                {"role": "user", "content": prompt}
            ]
        )
        return resp.choices[0].message.content
    except Exception as e:
        return f"Analiz Hatası: {str(e)}"