import os
import sys
from supabase import create_client
from dotenv import load_dotenv
from pathlib import Path

class DatabaseManager:
    def __init__(self):
        self.base_dir = Path(__file__).resolve().parent.parent
        env_path = self.base_dir / ".env"
        
        if env_path.exists():
            load_dotenv(dotenv_path=env_path, override=True)
        else:
            print(f"⚠️  UYARI: .env dosyası bulunamadı: {env_path}")
            print("   -> Sistem ortam değişkenleri kullanılacak.")
        
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_KEY")

        if not self.url or not self.key:
            print("❌ HATA: SUPABASE_URL veya SUPABASE_KEY bulunamadı!")
            self.client = None
        else:
            try:
                self.client = create_client(self.url, self.key)
            except Exception as e:
                print(f"❌ Supabase Bağlantı Hatası: {e}")
                self.client = None

    def insert_data(self, table_name, data):
        """
        Verilen tabloya veri ekler.
        table_name: Yazılacak tablo adı (örn: 'processed_data')
        data: Eklenecek veri (dict veya list of dict)
        """
        if not self.client:
            print("⚠️ Client başlatılamadığı için veri yazılamadı.")
            return None

        if not data:
            return None
        
        if isinstance(data, dict):
            data = [data]

        try:
            response = self.client.table(table_name).insert(data).execute()
            
            return response
            
        except Exception as e:
            print(f"❌ SUPABASE HATASI ({table_name}): {e}")
            raise e