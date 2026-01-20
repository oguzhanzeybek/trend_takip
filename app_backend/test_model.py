import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def check_latest_data():
    print("--- VERİTABANI SON DURUM KONTROLÜ ---")
    
    response = (
        supabase.table("processed_data")
        .select("created_at, data_type, source, content")
        .order("created_at", desc=True)
        .limit(5)
        .execute()
    )
    
    data = response.data
    
    if not data:
        print("❌ Veritabanı BOMBOŞ! Hiç veri yok.")
        return

    print(f"✅ Toplam {len(data)} veri bulundu. İşte son eklenenler:")
    for i, row in enumerate(data):
        print(f"\n[{i+1}]")
        print(f"   📅 Tarih (UTC): {row.get('created_at')}")
        print(f"   🏷️  Tip: {row.get('data_type')} (Kod sadece 'Filtered' veya 'Analyzed' arıyor!)")
        print(f"   🌍 Kaynak: {row.get('source')}")

check_latest_data()