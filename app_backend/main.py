from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from dotenv import load_dotenv
import requests
import json
from datetime import datetime, timedelta

# Kendi modüllerimiz
import model_data
import model_chat
from model_chat import analyze_with_ai  # Özel analiz fonksiyonu
from utils import supabase

# Ortam değişkenlerini yükle
load_dotenv()

app = FastAPI(title="Trend Takip AI Analiz Servisi")

# --- CORS AYARLARI ---
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- VERİ MODELLERİ (PYDANTIC) ---
class ChatRequest(BaseModel):
    message: str

class AnalyzeRequest(BaseModel):
    message: str
    categories: Optional[List[str]] = []

class AskAnalysisRequest(BaseModel):
    question: str

# --- ROOT ---
@app.get("/")
def read_root():
    return {"message": "Trend Takip AI Analiz Servisi (Modular) Aktif 🚀"}

# ==========================================
# 1. DASHBOARD VE İSTATİSTİK ENDPOINTLERİ
# ==========================================

@app.get("/api/stats")
async def get_stats_endpoint(time_range: str = "24h"):
    try:
        stats = await model_data.get_dashboard_stats(time_range)
        if stats:
            return stats
        # Veri yoksa varsayılan boş veri dön
        return {"total_analysis": 0, "active_sources": 0, "trend_score": 0, "system_status": "Idle"}
    except Exception as e:
        print(f"Stats Error: {e}")
        return {"error": str(e)}

@app.get("/api/strategic-insights")
async def get_strategic_insights(time_range: str = "24h"):
    """
    Dashboard için stratejik özet ve içgörü sağlar.
    """
    try:
        # model_data.py içindeki fonksiyonu kullanıyoruz (Daha stabil)
        insights = await model_data.get_strategic_insights()
        if insights:
            return {"status": "success", "data": insights, "insight": insights.get("summary")}
        return {"status": "error", "message": "Analiz bulunamadı", "insight": "Veri yok."}
    except Exception as e:
        return {"status": "error", "message": str(e), "insight": "Hata oluştu."}

# ==========================================
# 2. TREND VERİLERİ (Trendler Sayfası)
# ==========================================

@app.get("/api/trends")
async def get_trends_endpoint(
    platform: str = Query("all", description="Platform filtresi"),
    period: str = Query("daily", description="Zaman aralığı"),
    limit: int = Query(50, description="Limit")
):
    try:
        data = await model_data.get_filtered_trends(platform, period, limit)
        return {"status": "success", "data": data, "count": len(data)}
    except Exception as e:
        print(f"Trends Error: {e}")
        raise HTTPException(status_code=500, detail="Veri çekilemedi.")

@app.get("/api/top-trends")
async def get_top_trends_endpoint(period: str = "daily"):
    # model_data.py içinde bu fonksiyon varsa çalışır, yoksa get_filtered_trends kullanılır
    try:
        data = await model_data.get_filtered_trends("all", period, 10)
        return {"status": "success", "data": data}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/raw-data")
async def get_raw_data_endpoint(limit: int = 40):
    try:
        data = await model_data.fetch_data_in_range(datetime.now()-timedelta(days=1), datetime.now())
        return {"status": "success", "raw_data": data[:limit]}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ==========================================
# 3. DETAYLI AI ANALİZ RAPORU (Analiz Sayfası)
# ==========================================

@app.get("/api/analysis")
async def get_analysis_endpoint():
    """
    Veritabanındaki en son detaylı analiz JSON raporunu döner.
    """
    try:
        data = await model_data.get_latest_social_analysis()
        if data:
            return {"status": "success", "data": data}
        else:
            return {"status": "error", "message": "Henüz analiz verisi yok."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/ask-analysis")
async def ask_analysis_endpoint(request: AskAnalysisRequest):
    """
    Kullanıcının mevcut analiz raporuyla sohbet etmesini sağlar.
    """
    try:
        # 1. Mevcut analizi çek
        analysis_data = await model_data.get_latest_social_analysis()
        if not analysis_data:
            return {"reply": "Henüz analiz verisi oluşmadığı için cevap veremiyorum."}
            
        # 2. Context oluştur
        context_str = json.dumps(analysis_data, ensure_ascii=False)
        
        # 3. AI'ya sor
        prompt = f"""
        Sen bu analiz raporunun uzmanısın. Kullanıcının sorusunu verilere dayanarak cevapla.
        
        ANALİZ VERİLERİ:
        {context_str}
        
        KULLANICI SORUSU:
        {request.question}
        
        Cevabın kısa, net ve profesyonel olsun. Türkçe cevap ver.
        """
        
        reply = await analyze_with_ai(prompt)
        return {"reply": reply}
        
    except Exception as e:
        print(f"Ask Analysis Error: {e}")
        return {"reply": "Üzgünüm, şu an cevap veremiyorum."}

# ==========================================
# 4. GENEL CHAT VE ÖZEL ANALİZ
# ==========================================

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    try:
        if not request.message:
            raise HTTPException(status_code=400, detail="Mesaj boş olamaz")
            
        # model_chat modülünü kullanıyoruz
        response = await model_chat.process_user_input(request.message)
        return {"reply": response}
    except Exception as e:
        print(f"Chat Error: {e}")
        return {"reply": "Üzgünüm, bir hata oluştu."}

@app.post("/api/analyze")
async def analyze_custom_endpoint(request: AnalyzeRequest):
    try:
        response = await model_chat.process_user_input(request.message)
        return {"status": "success", "analysis": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# 5. HAVA DURUMU (Widget)
# ==========================================

@app.get("/api/weather")
async def get_weather_data():
    """
    İstanbul için anlık hava durumu (Open-Meteo).
    """
    try:
        url = "https://api.open-meteo.com/v1/forecast?latitude=41.0138&longitude=28.9497&current_weather=true&timezone=auto"
        response = requests.get(url)
        data = response.json()
        
        if "current_weather" in data:
            return {"status": "success", "data": data["current_weather"]}
        else:
            return {"status": "error", "message": "Veri alınamadı"}
    except Exception as e:
        print(f"Weather Error: {e}")
        return {"status": "error", "message": str(e)}

# ==========================================
# SERVER BAŞLATMA (Opsiyonel)
# ==========================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)