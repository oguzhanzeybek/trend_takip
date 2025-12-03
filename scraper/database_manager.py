import os
from supabase import create_client, Client
import json

class DatabaseManager:
    def __init__(self):
        # GitHub Secrets'tan okuyacak
        url: str = os.environ.get("SUPABASE_URL")
        key: str = os.environ.get("SUPABASE_KEY")
        
        if not url or not key:
            print("⚠️ Supabase anahtarları yok! DB modu pasif.")
            self.supabase = None
        else:
            self.supabase: Client = create_client(url, key)

    def insert_data(self, source, data_list):
        """
        source: 'N11', 'Amazon', 'Twitter' vb.
        data_list: İçinde title, price, link, ai_data olan sözlük listesi
        """
        if not self.supabase:
            return

        formatted_data = []
        for item in data_list:
            # Veriyi Supabase tablosuna uygun formata çeviriyoruz
            formatted_data.append({
                "source": source,
                "title": item.get("title", ""),
                "price": item.get("price", ""),
                "link": item.get("link", ""),
                "category": item.get("category", "Genel"),
                # AI verisi varsa ekle, yoksa boş JSON {}
                "ai_data": item.get("ai_analysis", {}) 
            })

        try:
            # daily_trends tablosuna toplu ekleme
            self.supabase.table("daily_trends").insert(formatted_data).execute()
            print(f"✅ SUPABASE: {len(formatted_data)} adet veri '{source}' kaynağından yüklendi.")
        except Exception as e:
            print(f"❌ SUPABASE HATASI: {e}")