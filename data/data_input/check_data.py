import os
import json
from supabase import create_client
from dotenv import load_dotenv
from pathlib import Path

# .env yükle
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_PATH = BASE_DIR / ".env"
load_dotenv(ENV_PATH)

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

if not url or not key:
    print("❌ HATA: .env dosyasında anahtarlar eksik.")
    exit()

supabase = create_client(url, key)

print(f"🔍 'processed_data' içerisindeki HAM JSON verileri çekiliyor...\n")

try:
    response = supabase.table("processed_data").select("*").order("created_at", desc=True).limit(5).execute()
    data = response.data

    if data:
        for i, item in enumerate(data, 1):
            content = item.get('content', {})
            
            # Eğer content string olarak gelirse (bazen postgreSQL string dönebilir), JSON objesine çevir
            if isinstance(content, str):
                try:
                    content = json.loads(content)
                except:
                    pass # Çevrilemezse olduğu gibi kalsın

            print(f"[{i}] --- KAYIT ID: {item.get('id')} ------------------")
            
            # --- İŞTE İSTEDİĞİN KISIM ---
            # Content içindeki her şeyi (title, status, message, timestamp vb.) okunaklı basar.
            formatted_json = json.dumps(content, indent=4, ensure_ascii=False)
            print(formatted_json)
            # ---------------------------

            print("--------------------------------------------------\n")
    else:
        print("⚠️ Tabloda veri yok.")

except Exception as e:
    print(f"❌ HATA: {e}")