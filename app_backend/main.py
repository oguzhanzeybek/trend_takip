from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from dotenv import load_dotenv

import model  # model.py dosyası (Yanında duran dosya)

load_dotenv()

app = FastAPI(title="Trend Takip AI Analiz Servisi")

class ChatRequest(BaseModel):
    message: str

class AnalyzeRequest(BaseModel):
    message: str
    categories: Optional[List[str]] = []

class TrendSaveRequest(BaseModel):
    content: str

origins = [
    "*", 
    "http://localhost:3000",
    "http://localhost:5173", # Vite Frontend Portu
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Trend Takip AI Analiz Servisi (GPT-4o) aktif 🚀"}


@app.post("/api/save-trend")
async def save_trend_endpoint(request: TrendSaveRequest):
    if not request.content:
        raise HTTPException(status_code=400, detail="content alanı boş olamaz")

    result = await model.save_trend(request.content)
    return {"status": "success", "saved": result}


@app.get("/api/get-trends")
async def get_trends_endpoint(limit: int = 20):
    try:
        trends = await model.get_trends(limit)
        return {"status": "success", "trends": trends}
    except Exception as e:
        print(f"❌ Trend listeleme hatası: {e}")
        raise HTTPException(status_code=500, detail="Trendler alınamadı.")


@app.get("/api/products")
async def get_products_endpoint():
    try:
        products = await model.get_products()
        return {"status": "success", "products": products}
    except Exception as e:
        print(f"❌ Ürün listeleme hatası: {e}")
        raise HTTPException(status_code=500, detail="Ürünler alınamadı.")


@app.get("/api/stats")
async def get_stats_endpoint():
    try:
        stats = await model.get_stats()
        return {"status": "success", "stats": stats}
    except Exception as e:
        print(f"❌ İstatistik listeleme hatası: {e}")
        raise HTTPException(status_code=500, detail="İstatistikler alınamadı.")


@app.get("/api/raw-data")
async def get_raw_data_endpoint(
    category: Optional[List[str]] = Query(default=None),
    limit: int = 40
):
    """
    Örnek: /api/raw-data?category=social_media&limit=20
    """
    try:
        items = await model.get_filtered_raw_data(category or [], limit)
        return {"status": "success", "raw_data": items}
    except Exception as e:
        print(f"❌ Raw data hatası: {e}")
        raise HTTPException(status_code=500, detail="Raw data alınamadı.")


@app.post("/api/analyze")
async def analyze_custom_endpoint(request: AnalyzeRequest):
    """
    JSON Body:
    { "message": "...", "categories": ["social_media"] }
    """
    try:
        if not request.message:
            raise HTTPException(status_code=400, detail="message gerekli")

        analysis = await model.chat_with_ai(request.message)

        return {
            "status": "success",
            "analysis": analysis,
            "categories": request.categories
        }
    except Exception as e:
        print(f"❌ Analyze endpoint hatası: {e}")
        raise HTTPException(status_code=500, detail="Analiz hatası oluştu.")


@app.get("/api/analyze-trends")
async def analyze_trends_endpoint():
    try:
        latest = await model.get_latest_trend_data()
        if not latest:
            raise HTTPException(status_code=404, detail="Veri yok.")

        text = f"Bu trendi analiz et: {latest['content']}"
        analysis = await model.chat_with_ai(text)

        return {
            "status": "success",
            "analysis": analysis,
            "latest_trend": latest
        }
    except Exception as e:
        print(f"❌ Analyze-trends hata: {e}")
        raise HTTPException(status_code=500, detail="AI analiz hatası.")


@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    """
    JSON Body: { "message": "Merhaba" }
    """
    try:
        if not request.message:
            raise HTTPException(status_code=400, detail="message alanı gerekli")

        response = await model.process_user_input(request.message)
        
        return {"reply": response} 
    except Exception as e:
        print(f"❌ Chat endpoint hatası: {e}")
        raise HTTPException(status_code=500, detail="AI sohbet hatası.")
    
    
    from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from dotenv import load_dotenv

# Doğru import (Yanındaki model.py dosyasını çağırır)
import model  

load_dotenv()

app = FastAPI(title="Trend Takip AI Analiz Servisi")

# --- MODEL TANIMLARI ---
class ChatRequest(BaseModel):
    message: str

class AnalyzeRequest(BaseModel):
    message: str
    categories: Optional[List[str]] = []

class TrendSaveRequest(BaseModel):
    content: str

# --- CORS AYARLARI ---
origins = ["*"] # Tüm kaynaklara izin ver (Test için)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- ENDPOINTLER ---

@app.get("/")
def read_root():
    return {"message": "Trend Takip AI Analiz Servisi Aktif 🚀"}

# 1. Dashboard İstatistikleri (DÜZELTİLDİ)
@app.get("/api/stats")
async def dashboard_stats_endpoint(time_range: str = "24h"):
    try:
        # model.py içindeki fonksiyonu çağırıyoruz
        stats = await model.get_dashboard_stats(time_range)
        
        if stats:
            return stats
            
        # Hata durumunda boş şablon dön
        return {
            "period_count": 0, "total_archive": 0,
            "sources": {"google": 0, "ecommerce": 0, "social": 0, "news": 0},
            "chart_data": [], "recent_activities": [],
            "ai_insight": "Veri yok.", "system_status": "Veri Bekleniyor"
        }
    except Exception as e:
        print(f"❌ İstatistik hatası: {e}")
        raise HTTPException(status_code=500, detail="İstatistikler alınamadı.")

# 2. Chat
@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    try:
        response = await model.process_user_input(request.message)
        return {"reply": response} 
    except Exception as e:
        print(f"Chat error: {e}")
        return {"reply": "Hata oluştu."}

# 3. Ham Veri
@app.get("/api/raw-data")
async def get_raw_data_endpoint(limit: int = 40):
    items = await model.get_filtered_raw_data([], limit)
    return {"status": "success", "raw_data": items}