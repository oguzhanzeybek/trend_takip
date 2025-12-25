import random
import json
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict
from utils import supabase

# --- SABİTLER ---
MAJOR_PLATFORMS = [
    "youtube", "twitter", "instagram", "tiktok", "google_trends", 
    "trendyol", "amazon", "n11", "alibaba", "a101", "carrefour", "rival"
]

# ==========================================
# 1. DASHBOARD & İSTATİSTİK FONKSİYONLARI
# ==========================================

async def get_dashboard_stats(time_range: str = "24h"):
    """
    Frontend Dashboard için gerekli tüm istatistikleri çeker.
    ÖNCELİK: Supabase RPC fonksiyonunu (get_trend_dashboard_stats) kullanır.
    YEDEK: Eğer RPC çalışmazsa Python tarafında manuel hesaplama yapar.
    """
    print(f"--- Dashboard İsteği: {time_range} ---")
    
    # Saat dönüşümü
    hours = 24
    if time_range == "7d": hours = 168
    if time_range == "30d": hours = 720

    # ---------------------------------------------------------
    # YÖNTEM 1: SUPABASE RPC (SQL FONKSİYONU) - EN SAĞLIKLISI
    # ---------------------------------------------------------
    try:
        # Senin yazdığın SQL fonksiyonunu çağırıyoruz
        rpc_response = supabase.rpc('get_trend_dashboard_stats', {'lookback_hours': hours}).execute()
        
        if rpc_response.data:
            print("✅ Veriler SQL RPC üzerinden çekildi.")
            data = rpc_response.data
            
            # Sistem statüsünü ekle ve dön
            data['system_status'] = "Operational (SQL)"
            return data

    except Exception as e:
        print(f"⚠️ SQL RPC Hatası (Python Fallback Devreye Giriyor): {e}")

    # ---------------------------------------------------------
    # YÖNTEM 2: PYTHON FALLBACK (Eğer SQL çalışmazsa burası devreye girer)
    # ---------------------------------------------------------
    try:
        now = datetime.now()
        start_time = (now - timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")

        # A) Toplam Arşiv
        total_res = supabase.table("processed_data").select("id", count="exact").execute()
        total_archive = total_res.count if total_res.count else 0

        # B) Bu Dönemdeki Toplam Veri
        period_res = supabase.table("processed_data").select("id", count="exact").gte("created_at_custom", start_time).execute()
        period_count = period_res.count if period_res.count else 0

        # C) Kaynak Dağılımı (MANUEL HESAPLAMA - DÜZELTİLDİ)
        # Artık %80/%20 uydurmasyon yok, gerçek sorgu var.

        # 1. Google
        google_filter = "source.ilike.%google%,content->>KAYNAK.ilike.%google%"
        google_res = supabase.table("processed_data").select("id", count="exact").gte("created_at_custom", start_time).or_(google_filter).execute()
        google_count = google_res.count if google_res.count else 0

        # 2. E-Ticaret
        ecom_filter = "source.ilike.%trendyol%,source.ilike.%amazon%,source.ilike.%n11%,source.ilike.%alibaba%,source.ilike.%a101%,content->>KAYNAK.ilike.%trendyol%"
        ecom_res = supabase.table("processed_data").select("id", count="exact").gte("created_at_custom", start_time).or_(ecom_filter).execute()
        ecom_count = ecom_res.count if ecom_res.count else 0

        # 3. Sosyal Medya (Artık gerçekten sayıyoruz)
        social_filter = "source.ilike.%youtube%,source.ilike.%twitter%,source.ilike.%instagram%,source.ilike.%tiktok%,content->>KAYNAK.ilike.%youtube%"
        social_res = supabase.table("processed_data").select("id", count="exact").gte("created_at_custom", start_time).or_(social_filter).execute()
        social_count = social_res.count if social_res.count else 0

        # 4. Haberler / Diğer (Geriye kalanlar)
        calculated_total = google_count + ecom_count + social_count
        news_count = max(0, period_count - calculated_total)

        sources_data = {
            "google": google_count,
            "ecommerce": ecom_count,
            "social": social_count,
            "news": news_count
        }

        # D) Grafik Verisi (Simülasyon - SQL yoksa mecbur)
        chart_data = []
        avg_per_hour = int(period_count / 12) if period_count > 0 else 0
        for i in range(12): 
            hour_label = (now - timedelta(hours=i*2)).strftime("%H:00")
            val = max(0, avg_per_hour + random.randint(-2, 5)) if avg_per_hour > 0 else 0
            chart_data.insert(0, {"label": hour_label, "value": val})

        # E) Son Aktiviteler
        # Gerçek veriden son 5 tanesini çek
        recent_activities = []
        last_items = supabase.table("processed_data").select("source, created_at_custom").order("created_at_custom", desc=True).limit(5).execute()
        
        if last_items.data:
            for item in last_items.data:
                try:
                    dt = datetime.strptime(item.get("created_at_custom"), "%Y-%m-%d %H:%M:%S")
                    diff_hour = int((now - dt).total_seconds() / 3600)
                    time_disp = f"{diff_hour} Saat Önce" if diff_hour > 0 else "Az Önce"
                except:
                    time_disp = "Bugün"
                
                recent_activities.append({
                    "count": 1,
                    "time_display": time_disp,
                    "description": f"Kaynak: {item.get('source', 'Bilinmeyen')}"
                })

        return {
            "period_count": period_count,
            "total_archive": total_archive,
            "sources": sources_data,
            "chart_data": chart_data,
            "recent_activities": recent_activities,
            "system_status": "Operational (Python)"
        }

    except Exception as e:
        print(f"❌ Python Fallback Hatası: {e}")
        return {
            "period_count": 0, "total_archive": 0,
            "sources": {"google": 0, "ecommerce": 0, "social": 0, "news": 0},
            "chart_data": [], "recent_activities": [],
            "system_status": "Error"
        }

async def get_strategic_insights():
    """
    Dashboard'daki 'Strategic Insights' kartı için en son analizi özetler.
    """
    try:
        data = await get_latest_social_analysis()
        if data:
            summary = data.get("genel_değerlendirme", "Veri yok")
            trends = [t.get("konu") for t in data.get("baskin_gundemler", [])[:3]]
            
            formatted_insight = f"{summary}\n\n🚀 Yükselenler: {', '.join(trends)}"
            
            return {
                "summary": formatted_insight,
                "trends": trends,
                "raw_data": data
            }
        return None
    except Exception as e:
        print(f"Insight Hatası: {e}")
        return None

# ==========================================
# 2. VERİ ÇEKME & FİLTRELEME (TRENDS PAGE)
# ==========================================

async def fetch_platform_specific(platform_keyword: str, start_date_str: str, limit: int):
    try:
        query = supabase.table("processed_data").select("*")
        query = query.in_("data_type", ["Filtered", "Raw"])
        query = query.gte("created_at_custom", start_date_str)
        
        or_filter = (
            f"content->>KAYNAK.ilike.%{platform_keyword}%,"
            f"content->>kaynak_dosya.ilike.%{platform_keyword}%,"
            f"source.ilike.%{platform_keyword}%"
        )
        query = query.or_(or_filter)
        query = query.order("trend_rank", desc=False)
        query = query.limit(limit)
        
        response = query.execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"Hata ({platform_keyword}): {e}")
        return []

async def get_filtered_trends(platform: str, period: str, limit: int = 50):
    try:
        now = datetime.now()
        start_date = now - timedelta(hours=24) 
        if period == "weekly": start_date = now - timedelta(days=7)
        elif period == "monthly": start_date = now - timedelta(days=30)
        
        start_date_str = start_date.strftime("%Y-%m-%d %H:%M:%S")
        
        raw_data = []
        if platform == "all":
            per_platform_limit = 100 
            tasks = [fetch_platform_specific(p, start_date_str, per_platform_limit) for p in MAJOR_PLATFORMS]
            results = await asyncio.gather(*tasks)
            for res in results: raw_data.extend(res)
        else:
            search_limit = max(limit, 100)
            raw_data = await fetch_platform_specific(platform, start_date_str, search_limit)

        seen_items = set()
        unique_data = []
        
        for item in raw_data:
            content = item.get("content", {}) or {}
            link = content.get("Link") or content.get("link") or content.get("url") or ""
            title = (content.get("Ürün Adı") or content.get("urun_adi") or content.get("title") or content.get("Trend") or "")
            
            unique_key = None
            if link and len(link) > 5: unique_key = link.strip().lower()
            elif title and len(title) > 3: unique_key = title.strip().lower()
            
            if unique_key:
                if unique_key not in seen_items:
                    seen_items.add(unique_key)
                    unique_data.append(item)
            else:
                unique_data.append(item)
        
        unique_data.sort(key=lambda x: (x.get('trend_rank') if x.get('trend_rank') is not None else 9999))
        return unique_data[:limit]

    except Exception as e:
        print(f"Genel Veri Hatası: {e}")
        return []

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

# ==========================================
# 3. ANALİZ & CHAT YARDIMCILARI
# ==========================================

async def get_latest_social_analysis():
    try:
        response = supabase.table("processed_data") \
            .select("*") \
            .eq("data_type", "Analyzed") \
            .order("created_at_custom", desc=True) \
            .limit(1) \
            .execute()
            
        if response.data and len(response.data) > 0:
            return response.data[0]['content']
        return None
    except Exception as e:
        print(f"Analiz Verisi Çekme Hatası: {e}")
        return None

async def chat_with_ai_general(user_message: str):
    try:
        from openai import OpenAI
        import os
        
        api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENROUTER_KEY")
        if not api_key: return "API Key eksik."

        client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)
        
        completion = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Sen TrendAI asistanısın. Türkçe cevap ver."},
                {"role": "user", "content": user_message}
            ]
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"Chat Hatası: {e}")
        return "Üzgünüm, şu an bağlantı kuramıyorum."