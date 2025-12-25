from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from dotenv import load_dotenv
from utils import supabase

# main.py dosyasının en tepesi:
from fastapi import FastAPI # vb...
# ... diğer importlar ...

# ÖNEMLİ OLAN SATIR BU:
from model_chat import analyze_with_ai

# Yeni modülleri import ediyoruz
import model_data
import model_chat

load_dotenv()

app = FastAPI(title="Trend Takip AI Analiz Servisi")

# --- MODEL TANIMLARI ---
class ChatRequest(BaseModel):
    message: str

class AnalyzeRequest(BaseModel):
    message: str
    categories: Optional[List[str]] = []

# --- CORS AYARLARI ---
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
    return {"message": "Trend Takip AI Analiz Servisi (Modular) Aktif 🚀"}

# --- DATA ENDPOINTLERİ (model_data.py) ---

@app.get("/api/stats")
async def get_stats_endpoint(time_range: str = "24h"):
    try:
        stats = await model_data.get_dashboard_stats(time_range)
        if stats: return stats
        raise HTTPException(status_code=500, detail="İstatistik alınamadı")
    except Exception as e:
        print(f"Stats Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/top-trends")
async def get_top_trends_endpoint(period: str = "daily"):
    data = await model_data.get_top_trends(period)
    return {"status": "success", "data": data}

@app.get("/api/raw-data")
async def get_raw_data_endpoint(limit: int = 40):
    # Basit bir raw data çekimi (şimdilik son 24 saati baz alalım örnek olarak)
    from datetime import datetime, timedelta
    data = await model_data.fetch_data_in_range(datetime.now()-timedelta(days=1), datetime.now())
    return {"status": "success", "raw_data": data[:limit]}

# --- AI CHAT ENDPOINTLERİ (model_chat.py) ---

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    try:
        if not request.message:
            raise HTTPException(status_code=400, detail="Mesaj boş olamaz")
            
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
    
    
    
# --- STRATEJİK İÇGÖRÜ ENDPOINT'İ (TEMİZ METİN MODU) ---

@app.get("/api/strategic-insights")
async def get_strategic_insights(time_range: str = "24h"):
    try:
        # 1. Süre Ayarı
        hours = 24
        if time_range == "7d": hours = 168
        if time_range == "30d": hours = 720

        # 2. Veriyi Çek
        response = supabase.rpc("get_ai_insight_data", {"lookback_hours": hours}).execute()
        
        if not response.data or not response.data.get('raw_dump'):
            return {"insight": "Analiz için yeterli veri akışı yok.", "raw_data": {}}
            
        raw_list = response.data.get('raw_dump', [])
        
        # Veriyi metne dök
        data_text = "\n".join([f"Kaynak: {item['source']} | İçerik: {item['snippet']}" for item in raw_list])
        
        # 3. PROMPT (ÇOK ÖNEMLİ DEĞİŞİKLİK BURADA)
        # Markdown yasaklıyoruz, sadece temiz metin istiyoruz.
        prompt = f"""
        Sen "TrendAI", kıdemli bir Pazar Analistisin.
        Aşağıda son {time_range} verileri var.
        
        VERİLER:
        {data_text}
        
        ---
        GÖREVİN:
        Pazarın genel durumunu ve gidişatını anlatan profesyonel bir "Yönetici Özeti" yaz.
        
        ÇOK ÖNEMLİ BİÇİM KURALLARI:
        1. ASLA yıldız (*), kare (#), tire (-) veya madde işareti KULLANMA.
        2. ASLA "1.", "2." gibi numaralandırma yapma.
        3. Başlıkları sadece BÜYÜK HARFLERLE yaz ve hemen altına paragrafı yaz.
        4. Paragraflar arasında bir satır boşluk bırak.
        
        ŞU BAŞLIKLARI KULLAN:
        
        🌍 GENEL PAZAR ATMOSFERİ
        (Buraya genel durumu anlatan akıcı bir paragraf yaz)

        🌊 YÜKSELEN ANA AKIMLAR
        (Buraya trendleri anlatan akıcı bir paragraf yaz)

        🧠 TÜKETİCİ PSİKOLOJİSİ
        (Buraya insan davranışlarını anlatan akıcı bir paragraf yaz)

        🧭 STRATEJİK YÖN TAVSİYESİ
        (Buraya ne yapılması gerektiğini anlatan akıcı bir paragraf yaz)

        Çıktın Türkçe ve okuması çok kolay, akıcı bir metin olsun.
        """

        # 4. AI'ya Gönder
        ai_response = await analyze_with_ai(prompt)

        return {
            "insight": ai_response,
            "raw_data": raw_list[:50] 
        }

    except Exception as e:
        print(f"Hata: {str(e)}")
        return {"insight": "Analiz oluşturulamadı.", "error": str(e)}
    
    
    
    
# main.py

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from dotenv import load_dotenv

# Modüller
import model_data
import model_chat

load_dotenv()

app = FastAPI(title="Trend Takip AI Analiz Servisi")

# --- CORS AYARLARI ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- ANA TREND ENDPOINT'İ ---
@app.get("/api/trends")
async def get_trends_endpoint(
    platform: str = Query("all", description="Platform filtresi (youtube, twitter, all vb.)"),
    period: str = Query("daily", description="Zaman aralığı (daily, weekly, monthly)"),
    limit: int = Query(50, description="Çekilecek maksimum kayıt sayısı")
):
    """
    Frontend'den gelen parametrelere göre, JSON içindeki kaynağı filtreleyerek veri döner.
    """
    try:
        data = await model_data.get_filtered_trends(platform, period, limit)
        return {"status": "success", "data": data, "count": len(data)}
    except Exception as e:
        print(f"API Hatası (/api/trends): {e}")
        raise HTTPException(status_code=500, detail="Veri çekilemedi.")

# --- DİĞER CHAT VE DASHBOARD ENDPOINTLERİ ---
# (Eski kodundaki /api/chat, /api/stats vb. buraya aynen gelecek)
# Önceki main.py kodundaki diğer kısımları buraya yapıştırabilirsin.





# main.py içine ekle:

@app.get("/api/analysis")
async def get_analysis_endpoint():
    """
    En son yapılan detaylı AI analiz raporunu döner.
    """
    try:
        data = await model_data.get_latest_social_analysis()
        if data:
            return {"status": "success", "data": data}
        else:
            # Veri yoksa boş bir şablon dönelim ki frontend çökmesin
            return {"status": "error", "message": "Henüz analiz verisi yok."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    # main.py içine ekle:

class AskAnalysisRequest(BaseModel):
    question: str

@app.post("/api/ask-analysis")
async def ask_analysis_endpoint(request: AskAnalysisRequest):
    """
    Kullanıcının analiz raporu hakkındaki sorularını cevaplar.
    """
    try:
        # 1. Mevcut analiz verisini çek
        analysis_data = await model_data.get_latest_social_analysis()
        if not analysis_data:
            return {"reply": "Henüz analiz verisi oluşmadığı için cevap veremiyorum."}
            
        # 2. Context (Bağlam) oluştur
        context_str = json.dumps(analysis_data, ensure_ascii=False)
        
        # 3. AI'ya Sor
        prompt = f"""
        Sen bu analiz raporunun uzmanısın. Kullanıcının sorusunu aşağıdaki verilere dayanarak cevapla.
        
        ANALİZ VERİLERİ:
        {context_str}
        
        KULLANICI SORUSU:
        {request.question}
        
        Cevabın kısa, net ve profesyonel olsun. Veride olmayan bir şey uydurma.
        """
        
        reply = await analyze_with_ai(prompt)
        return {"reply": reply}
        
    except Exception as e:
        print(f"Chat Hatası: {e}")
        return {"reply": "Üzgünüm, şu an cevap veremiyorum."}