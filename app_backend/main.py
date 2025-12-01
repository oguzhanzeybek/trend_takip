# app_backend/main.py

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from . import model # model.py dosyasını import et

# --- FastAPI Uygulamasını Başlatma ---
app = FastAPI(title="AI Recommendation Microservice")

# --- CORS Ayarları ---
# Flask ön yüz uygulamasının API'ye erişebilmesi için gerekli.
# Deta Space'te geliştirme aşamasında tüm kaynaklara izin vermek için '*' kullanıyoruz.
origins = ["*"] 

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    """Basit bir sağlık kontrolü endpoint'i."""
    return {"message": "AI Recommendation Microservice çalışıyor!"}

# --- Öneri API Uç Noktası ---

@app.get("/recommendations")
def get_recommendations_endpoint(article_id: str, count: int = 5):
    """
    Belirtilen makale ID'sine (key) göre önceden hesaplanmış önerileri döndürür.
    """
    if not article_id:
        raise HTTPException(status_code=400, detail="article_id parametresi gereklidir.")
    
    try:
        # model.py'deki fonksiyonu çağır
        recommendations = model.get_precalculated_recommendations(article_id, count)
        
        if not recommendations:
            # Öneri bulunamadığında 404 döndür.
            raise HTTPException(status_code=404, detail="Bu makale için öneri bulunamadı.")

        return recommendations
    
    except HTTPException:
        # 400 ve 404 gibi FastAPI tarafından tetiklenen hataları yakala
        raise
    except Exception as e:
        # Diğer tüm hataları 500 olarak döndür
        print(f"Öneri hesaplanırken beklenmedik hata oluştu: {e}")
        # Güvenlik nedeniyle detayı gösterme, sadece genel bir hata mesajı ver.
        raise HTTPException(status_code=500, detail="Öneri sistemi bir iç hata ile karşılaştı. Lütfen Base bağlantısını kontrol edin.")