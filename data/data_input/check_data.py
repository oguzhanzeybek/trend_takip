import os
import json
from supabase import create_client
from dotenv import load_dotenv
from pathlib import Path

<<<<<<< HEAD
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_PATH = BASE_DIR / ".env"
load_dotenv(ENV_PATH)

=======
BASE_DIR = Path(__file__).resolve().parent.parent.parent # Ana dizine çıkmak için (projene göre ayarla)
ENV_PATH = BASE_DIR / ".env"
load_dotenv(ENV_PATH)

>>>>>>> origin/main
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

if not url or not key:
<<<<<<< HEAD
    print("❌ HATA: .env dosyasında anahtarlar eksik.")
=======
    print("❌ HATA: .env dosyasında SUPABASE_URL veya SUPABASE_KEY bulunamadı.")
>>>>>>> origin/main
    exit()

supabase = create_client(url, key)

<<<<<<< HEAD
print(f"🔍 'processed_data' içerisindeki HAM JSON verileri çekiliyor...\n")

try:
=======
print(f"🔍 'processed_data' tablosundaki son veriler çekiliyor...\n")

try:
>>>>>>> origin/main
    response = supabase.table("processed_data").select("*").order("created_at", desc=True).limit(5).execute()
    data = response.data

    if data:
        for i, item in enumerate(data, 1):
<<<<<<< HEAD
            content = item.get('content', {})
            
=======
            content = item.get('content', {})
            
>>>>>>> origin/main
            if isinstance(content, str):
                try:
                    content = json.loads(content)
                except:
<<<<<<< HEAD
                    pass # Çevrilemezse olduğu gibi kalsın

            print(f"[{i}] --- KAYIT ID: {item.get('id')} ------------------")
            
            formatted_json = json.dumps(content, indent=4, ensure_ascii=False)
            print(formatted_json)

            print("--------------------------------------------------\n")
    else:
        print("⚠️ Tabloda veri yok.")

except Exception as e:
    print(f"❌ HATA: {e}")
=======
                    content = {}

            print(f"[{i}] --------------------------------------------------")
            print(f"🆔 ID       : {item.get('id')}")
            print(f"📅 Tarih    : {item.get('created_at')}")
            
            print(f"📂 Kategori : {item.get('category', '-')}")
            print(f"🏷️  Kaynak   : {item.get('source', '-')}") # Yeni tabloda 'source' sütunu varsa
            
            print(f"📦 Başlık   : {content.get('title', '-')}")
            print(f"⏱️  Süre     : {content.get('duration', '-')}")
            print(f"📊 Durum    : {content.get('status', '-')}")
            
            if content.get('error_log_snippet'):
                print(f"❌ Hata Logu: {content.get('error_log_snippet')[:100]}...")
            
            print("--------------------------------------------------\n")
    else:
        print("⚠️ Tabloda ('processed_data') henüz hiç veri yok.")

except Exception as e:
    print(f"❌ BEKLENMEYEN HATA: {e}")
    if "relation" in str(e) and "does not exist" in str(e):
        print("\n💡 İPUCU: Supabase'de 'processed_data' adında bir tablo oluşturmamış olabilirsin.")
>>>>>>> origin/main
