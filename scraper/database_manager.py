import os
import sys
from supabase import create_client
from dotenv import load_dotenv
from pathlib import Path

class DatabaseManager:
    def __init__(self):
        # .env yükleme
        self.base_dir = Path(__file__).resolve().parent
        env_path = self.base_dir / ".env"
        if env_path.exists():
            load_dotenv(dotenv_path=env_path, override=True)
        
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

        # Veri boşsa işlem yapma
        if not data:
            return None
        
        # Tekil veri geldiyse listeye çevir (Supabase liste sever)
        if isinstance(data, dict):
            data = [data]

        try:
            # DİKKAT: Burada hardcoded 'daily_trends' YOK. 
            # Parametre olarak gelen table_name kullanılıyor.
            response = self.client.table(table_name).insert(data).execute()
            
            # Supabase-py kütüphanesinin bazı versiyonlarında hata fırlatılmaz,
            # response içinde error dönerse kontrol edelim:
            if hasattr(response, 'error') and response.error:
                 raise Exception(f"Supabase API Hatası: {response.error}")

            return response
            
        except Exception as e:
            # Hatayı burada yakalayıp ekrana basıyoruz ama çağıran dosya 
            # 'başarılı' sanmasın diye hatayı yukarı fırlatıyoruz (raise).
            print(f"❌ SUPABASE HATASI ({table_name}): {e}")
            raise e