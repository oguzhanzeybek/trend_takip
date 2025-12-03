import os
import json
from supabase import create_client
from dotenv import load_dotenv
from pathlib import Path

# .env yükle
<<<<<<< HEAD
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_PATH = BASE_DIR / ".env"
load_dotenv(ENV_PATH)

=======
BASE_DIR = Path(__file__).resolve().parent.parent.parent # Ana dizine çıkmak için (projene göre ayarla)
ENV_PATH = BASE_DIR / ".env"
load_dotenv(ENV_PATH)

# Bağlantı
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
    # 1. Tabloyu "processed_data" olarak değiştirdik (Yeni sistem)
>>>>>>> origin/main
    response = supabase.table("processed_data").select("*").order("created_at", desc=True).limit(5).execute()
    data = response.data

    if data:
        for i, item in enumerate(data, 1):
<<<<<<< HEAD
            content = item.get('content', {})
            
            # Eğer content string olarak gelirse (bazen postgreSQL string dönebilir), JSON objesine çevir
=======
            # 2. Yeni yapıda veriler 'content' sütununda JSON olarak duruyor
            content = item.get('content', {})
            
            # Eğer content string olarak gelirse JSON'a çevir
>>>>>>> origin/main
            if isinstance(content, str):
                try:
                    content = json.loads(content)
                except:
<<<<<<< HEAD
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
=======
                    content = {}

            print(f"[{i}] --------------------------------------------------")
            print(f"🆔 ID       : {item.get('id')}")
            print(f"📅 Tarih    : {item.get('created_at')}")
            
            # Ana sütunlar (Varsa)
            print(f"📂 Kategori : {item.get('category', '-')}")
            print(f"🏷️  Kaynak   : {item.get('source', '-')}") # Yeni tabloda 'source' sütunu varsa
            
            # JSON içindeki veriler (content içinden okuyoruz)
            print(f"📦 Başlık   : {content.get('title', '-')}")
            print(f"⏱️  Süre     : {content.get('duration', '-')}")
            print(f"📊 Durum    : {content.get('status', '-')}")
            
            # Hata varsa göster
            if content.get('error_log_snippet'):
                print(f"❌ Hata Logu: {content.get('error_log_snippet')[:100]}...")
            
            print("--------------------------------------------------\n")
    else:
        print("⚠️ Tabloda ('processed_data') henüz hiç veri yok.")

except Exception as e:
    print(f"❌ BEKLENMEYEN HATA: {e}")
    # Eğer tablo yoksa uyaralım
    if "relation" in str(e) and "does not exist" in str(e):
        print("\n💡 İPUCU: Supabase'de 'processed_data' adında bir tablo oluşturmamış olabilirsin.")
>>>>>>> origin/main
