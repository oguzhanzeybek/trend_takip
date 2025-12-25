import random
from datetime import datetime, timedelta
from typing import List, Dict
from utils import supabase, ai_client, MODEL_NAME, safe_json_parse, extract_date_range_from_query, simple_turkish_stemmer

# --- DATA FETCHING ---

async def fetch_data_in_range(start_date: datetime, end_date: datetime) -> List[Dict]:
    if not supabase: return []
    try:
        start_str = start_date.replace(hour=0, minute=0, second=0).isoformat()
        end_str = end_date.replace(hour=23, minute=59, second=59).isoformat()
        
        response = (
            supabase.table("processed_data")
            .select("*")
            .in_("data_type", ["Filtered", "Analyzed"]) 
            .filter("created_at", "gte", start_str)
            .filter("created_at", "lte", end_str)
            .order("created_at", desc=True)
            .limit(1000) # Performans için limit
            .execute()
        )
        return response.data if response.data else []
    except Exception as e:
        print(f"❌ Veri Çekme Hatası: {e}")
        return []

async def get_top_trends(period: str = "daily"):
    """Trends sayfası için verileri çeker."""
    if not supabase: return []
    days = 1
    if period == "weekly": days = 7
    if period == "monthly": days = 30
    
    try:
        # SQL tarafındaki RPC fonksiyonunu çağırır
        response = supabase.rpc('get_top_trends', {'lookback_days': days}).execute()
        return response.data or []
    except Exception as e:
        print(f"Trends Error: {e}")
        return []

# --- DASHBOARD & STATS ---

async def get_dashboard_stats(time_range: str = "24h"):
    print(f"--- Dashboard İsteği: {time_range} ---")
    
    # Hata olursa dönecek boş şablon (Sitenin çökmemesi için)
    empty_stats = {
        "period_count": 0,
        "total_archive": 0,
        "sources": {"google": 0, "ecommerce": 0, "social": 0, "news": 0},
        "chart_data": [],
        "recent_activities": [],
        "ai_insight": "Veri yüklenemedi.",
        "system_status": "Hata"
    }

    if not supabase: return empty_stats

    # Saati ayarla
    hours = 24
    if time_range == "7d": hours = 168
    if time_range == "30d": hours = 720

    try:
        # 1. SQL FONKSİYONUNU ÇAĞIR (Senin kodun çalışacak)
        response = supabase.rpc('get_trend_dashboard_stats', {'lookback_hours': hours}).execute()
        data = response.data 
        
        if not data: return empty_stats

        # 2. AI İÇGÖRÜSÜ (Burası ekstra, verileri yorumlar)
        ai_insight = "Veriler analiz ediliyor..."
        if ai_client:
            try:
                # Sadece son 15 veriyi çekip yorumlatalım (Hızlı olsun diye)
                summary_query = supabase.table("processed_data")\
                    .select("content, source")\
                    .order("created_at", desc=True)\
                    .limit(15)\
                    .execute()
                
                if summary_query.data:
                    lines = [f"[{item['source']}] {str(item['content'])[:50]}" for item in summary_query.data]
                    txt = "\n".join(lines)
                    prompt = f"Bu son verilere bakarak yöneticiler için 1 cümlelik çok kısa özet yaz: \n{txt}"
                    
                    ai_resp = ai_client.chat.completions.create(
                        model=MODEL_NAME, 
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.7, max_tokens=100
                    )
                    ai_insight = ai_resp.choices[0].message.content
            except:
                pass

        # SQL'den gelen veriye AI yorumunu ve durumu ekle
        data['ai_insight'] = ai_insight
        data['system_status'] = "Stabil"
        
        return data

    except Exception as e:
        print(f"❌ Dashboard Hatası: {e}")
        return empty_stats







from datetime import datetime, timedelta
from utils import supabase
import json
import asyncio 

# Tümü seçildiğinde taranacak ANA PLATFORMLAR LİSTESİ
# (Klasör yapına ve veri kaynaklarına göre genişletildi)
MAJOR_PLATFORMS = [
    "youtube", 
    "twitter", 
    "instagram", 
    "tiktok", 
    "google_trends", 
    "trendyol", 
    "amazon", 
    "n11", 
    "alibaba", 
    "a101", 
    "carrefour", 
    "rival"
]

async def fetch_platform_specific(platform_keyword: str, start_date_str: str, limit: int):
    """
    Belirli bir platform için veri çeken yardımcı fonksiyon.
    Veritabanında kaynak isminde (source) veya içerikte (JSON) platform adını arar.
    """
    try:
        query = supabase.table("processed_data").select("*")
        
        # --- DATA TYPE FİLTRESİ ---
        # Hem 'Filtered' (AI Analizli) hem 'Raw' (Ham) verileri çekiyoruz.
        # Böylece veri havuzu daha geniş olur.
        query = query.in_("data_type", ["Filtered", "Raw"])
        
        # --- TARİH FİLTRESİ (KRİTİK) ---
        # start_date_str tarihinden sonra eklenenleri getirir (Haftalık/Aylık kontrolü burada işler)
        query = query.gte("created_at_custom", start_date_str)
        
        # --- PLATFORM FİLTRESİ ---
        # 1. content->KAYNAK içinde ara (Örn: "trendyol.csv")
        # 2. content->kaynak_dosya içinde ara
        # 3. source sütununda ara (Dosya ismi)
        or_filter = (
            f"content->>KAYNAK.ilike.%{platform_keyword}%,"
            f"content->>kaynak_dosya.ilike.%{platform_keyword}%,"
            f"source.ilike.%{platform_keyword}%"
        )
        query = query.or_(or_filter)
        
        # Sıralama: Trend Rank'e göre (1 numara en üstte)
        # Eğer rank yoksa en sona atar.
        query = query.order("trend_rank", desc=False)
        
        # Limit
        query = query.limit(limit)
        
        response = query.execute()
        return response.data if response.data else []
    
    except Exception as e:
        print(f"Hata ({platform_keyword}): {e}")
        return []

async def get_filtered_trends(platform: str, period: str, limit: int = 50):
    """
    Eğer platform='all' ise, her ana platformdan eşit miktarda veri çeker ve birleştirir.
    Değilse sadece o platformu çeker.
    Period parametresine göre (daily, weekly, monthly) tarih aralığını belirler.
    """
    try:
        # --- 1. TARİH AYARI (GÜNCELLENDİ) ---
        now = datetime.now()
        
        # Varsayılan: Günlük (Son 24 saat)
        start_date = now - timedelta(hours=24) 
        period_label = "GÜNLÜK"
        
        if period == "weekly":
            start_date = now - timedelta(days=7) # Son 7 gün
            period_label = "HAFTALIK"
        elif period == "monthly":
            start_date = now - timedelta(days=30) # Son 30 gün
            period_label = "AYLIK"
            
        start_date_str = start_date.strftime("%Y-%m-%d %H:%M:%S")
        
        # Konsola Bilgi Bas (Debug için)
        print(f"\n📅 FİLTRE: {period_label} | Başlangıç: {start_date_str}")
        
        raw_data = []

        # --- 2. VERİ ÇEKME STRATEJİSİ ---
        
        if platform == "all":
            # STRATEJİ A: "Tümü" seçildiyse HER PLATFORMDAN EŞİT ÇEK.
            # Her birinden 100 tane çekiyoruz (Toplam ~1200 veri potansiyeli)
            per_platform_limit = 100 
            
            print(f"🔄 Dağıtık veri çekiliyor... (Her platformdan {per_platform_limit} adet)")
            
            # Tüm platformlar için paralel sorgu oluştur
            tasks = [
                fetch_platform_specific(p, start_date_str, per_platform_limit) 
                for p in MAJOR_PLATFORMS
            ]
            
            # Hepsini aynı anda çalıştır ve bekle
            results = await asyncio.gather(*tasks)
            
            # Sonuçları tek listede birleştir
            for res in results:
                raw_data.extend(res)
                
        else:
            # STRATEJİ B: Tek bir platform seçildiyse o platformdan bolca çek.
            print(f"🔍 Tek platform verisi çekiliyor: {platform}")
            # Tek platform modunda en az 100 veri garanti olsun
            search_limit = max(limit, 100)
            raw_data = await fetch_platform_specific(platform, start_date_str, search_limit)

        # --- 3. TEKİLLEŞTİRME (Deduplication) ---
        seen_items = set()
        unique_data = []
        
        for item in raw_data:
            content = item.get("content", {}) or {}
            
            # Benzersizlik Anahtarı (Link > Başlık)
            link = content.get("Link") or content.get("link") or content.get("url") or ""
            title = (
                content.get("Ürün Adı") or 
                content.get("urun_adi") or 
                content.get("title") or 
                content.get("Trend") or 
                ""
            )
            
            unique_key = None
            if link and len(link) > 5:
                unique_key = link.strip().lower()
            elif title and len(title) > 3:
                unique_key = title.strip().lower()
            
            # Eğer anahtar geçerliyse ve daha önce eklenmediyse ekle
            if unique_key:
                if unique_key not in seen_items:
                    seen_items.add(unique_key)
                    unique_data.append(item)
            else:
                # Anahtarsız verileri (nadir) yine de ekle
                unique_data.append(item)
        
        # --- 4. SON SIRALAMA ---
        # Karışık gelen verileri tekrar Rank sırasına göre dizelim.
        # Rank'i olmayanları (None) en sona atarız (9999).
        unique_data.sort(key=lambda x: (x.get('trend_rank') if x.get('trend_rank') is not None else 9999))

        print(f"✅ Toplam {len(unique_data)} adet veri hazırlandı (İstenen Limit: {limit})")
        
        # "Tümü" modunda çeşitlilik için limiti biraz esnetelim
        if platform == "all":
             final_limit = max(limit, 200) # En az 200 veri dönsün
             return unique_data[:final_limit]
        else:
             return unique_data[:limit]

    except Exception as e:
        print(f"Genel Veri Hatası: {e}")
        return []

# --- DİĞER FONKSİYONLAR (Aynen Kalıyor) ---

async def get_dashboard_stats(time_range: str = "24h"):
    try:
        hours = 24
        if time_range == "7d": hours = 168
        if time_range == "30d": hours = 720
            
        start_time = (datetime.now() - timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")

        count_res = supabase.table("processed_data") \
            .select("id", count="exact") \
            .gte("created_at_custom", start_time) \
            .execute()
            
        total_count = count_res.count if count_res.count else 0
        
        return {
            "total_analysis": total_count,
            "active_sources": len(MAJOR_PLATFORMS), 
            "trend_score": 85,
            "system_status": "Operational"
        }
    except Exception as e:
        print(f"Stats Error: {e}")
        return None

async def fetch_data_in_range(start, end):
    try:
        response = supabase.table("processed_data") \
            .select("*") \
            .gte("created_at_custom", start.strftime("%Y-%m-%d %H:%M:%S")) \
            .lte("created_at_custom", end.strftime("%Y-%m-%d %H:%M:%S")) \
            .order("created_at_custom", desc=True) \
            .limit(100) \
            .execute()
        return response.data
    except Exception as e:
        print(f"Fetch Range Error: {e}")
        return []
    
    
    
    
    # model_data.py içine ekle:

async def get_latest_social_analysis():
    """
    Veritabanından en son yüklenen 'Analyzed' tipindeki sosyal medya analiz JSON'unu çeker.
    """
    try:
        # data_type = 'Analyzed' olan ve category='social_media_sentiment' olan en son kaydı getir.
        response = supabase.table("processed_data") \
            .select("*") \
            .eq("data_type", "Analyzed") \
            .order("created_at_custom", desc=True) \
            .limit(1) \
            .execute()
            
        if response.data and len(response.data) > 0:
            # content sütunu zaten JSON formatındadır
            return response.data[0]['content']
        else:
            return None
    except Exception as e:
        print(f"Analiz Verisi Çekme Hatası: {e}")
        return None