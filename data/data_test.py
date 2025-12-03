import os
import json
from supabase import create_client
from dotenv import load_dotenv
from pathlib import Path

# Renkli çıktılar için
GREEN = '\033[92m'
RED = '\033[91m'
RESET = '\033[0m'

# 1. Ayarları Yükle
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

if not url or not key:
    print(f"{RED}HATA: .env dosyasında SUPABASE_URL veya KEY eksik!{RESET}")
    exit()

# 2. Bağlantı Kur
try:
    supabase = create_client(url, key)
    print(f"{GREEN}✅ Supabase bağlantısı sağlandı.{RESET}")
except Exception as e:
    print(f"{RED}❌ Bağlantı hatası: {e}{RESET}")
    exit()

def test_insert_and_read():
    print("\n--- TEST BAŞLIYOR ---")

    # --- A) VERİ HAZIRLAMA ---
    # Sanki CSV'den okumuşuz gibi bir satır veri uyduralım
    test_veri = {
        "category": "TEST_CATEGORY",     # Kategori sütunu
        "data_type": "TEST_RAW",         # Veri Tipi sütunu
        "source_file": "manuel_test.py", # Hangi dosyadan geldiği
        
        # JSONB Sütunu (Buraya her türlü karmaşık veri girebilir)
        "content": {
            "urun_adi": "Test Laptopu",
            "fiyat": "50.000 TL",
            "ozellikler": {"ram": "16GB", "disk": "512SSD"},
            "stok": True
        }
    }

    # --- B) VERİ EKLEME (INSERT) ---
    print("⏳ Veri tabloya gönderiliyor...")
    try:
        data = supabase.table("daily_trends").insert(test_veri).execute()
        # Supabase kütüphanesinin versiyonuna göre dönen cevap değişebilir, 
        # ama hata vermediyse başarılıdır.
        print(f"{GREEN}✅ BAŞARILI: Veri yazıldı!{RESET}")
    except Exception as e:
        print(f"{RED}❌ YAZMA HATASI: {e}{RESET}")
        return

    # --- C) VERİ OKUMA (SELECT) ---
    print("⏳ Yazılan veri geri okunuyor...")
    try:
        # Son eklenen veriyi çekelim
        response = supabase.table("daily_trends").select("*").eq("category", "TEST_CATEGORY").execute()
        
        kayitlar = response.data
        if len(kayitlar) > 0:
            son_kayit = kayitlar[0]
            print(f"\n{GREEN}✅ OKUMA BAŞARILI! İşte veritabanından gelen veri:{RESET}")
            print("-" * 40)
            print(f"🆔 ID: {son_kayit['id']}")
            print(f"📂 Kategori: {son_kayit['category']}")
            print(f"📄 Kaynak: {son_kayit['source_file']}")
            print(f"📦 İçerik (JSON): {son_kayit['content']}")
            print("-" * 40)
            
            # --- D) TEMİZLİK (İsteğe Bağlı) ---
            # Test verisini silelim ki tablo kirlenmesin
            # Silmek istersen aşağıdaki satırları aç:
            # supabase.table("daily_trends").delete().eq("id", son_kayit['id']).execute()
            # print("🗑️ Test verisi temizlendi.")
            
        else:
            print(f"{RED}❌ Veri yazıldı dendi ama okurken bulunamadı!{RESET}")

    except Exception as e:
        print(f"{RED}❌ OKUMA HATASI: {e}{RESET}")

if __name__ == "__main__":
    test_insert_and_read()