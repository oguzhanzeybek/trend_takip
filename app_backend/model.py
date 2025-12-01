# app_backend/model.py

import os
from deta import Deta
from typing import List, Dict, Optional

# Deta Proje Anahtarını ortam değişkeninden al.
# Deta Space'te dağıtıldığında bu, Micro'ya otomatik olarak sağlanır.
DETA_KEY: Optional[str] = os.getenv("DETA_PROJECT_KEY") 
deta = Deta(DETA_KEY)

# Scraper'ınızın öneri verilerini kaydettiği Base adını kullanın. 
# Önemli: Bu adı, scraper'ınızın kullandığı Base adı ile değiştirin.
DB = deta.Base("recommendation_data") 


def get_precalculated_recommendations(article_key: str, count: int = 5) -> List[Dict]:
    """
    Deta Base'den verilen makale anahtarına (key) ait önceden hesaplanmış önerileri çeker.

    Args:
        article_key: Önerilerin istendiği ana makalenin anahtarı (key).
        count: Dönülecek maksimum öneri sayısı.
    
    Returns:
        Başlık, URL ve anahtar içeren öneri listesi (örneğin: [{'title': '...', 'url': '...', 'key': '...'}])
    """
    
    # 1. Ana makaleyi Deta Base'den key ile çek
    result = DB.get(article_key)
    
    if not result:
        # Makale Base'de yoksa, boş liste döndür
        return []

    # 2. Scraper'ın makale nesnesi içine kaydettiği öneri listesini kontrol et.
    # Varsayım: Scraper, önerileri 'suggestions' adlı bir listede saklıyor.
    if 'suggestions' in result and isinstance(result['suggestions'], list):
        # En fazla 'count' kadar öneri döndür
        return result['suggestions'][:count]
    else:
        # Eğer öneri alanı yoksa veya liste değilse
        print(f"Uyarı: Key {article_key} için geçerli öneri listesi ('suggestions') bulunamadı.")
        return []