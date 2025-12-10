import asyncio
import os
import time

# Windows Event Loop Fix
if os.name == 'nt':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from model import chat_with_ai

# ==============================================================================
# 💀 50 AŞAMALI "EXTREME GRANDMASTER" STRES TESTİ (OTOMATİK KONTROLLÜ)
# ==============================================================================

def check_keyword(response, keywords):
    """Cevap içinde anahtar kelimelerin geçip geçmediğini kontrol eder."""
    if not keywords: return True # Kontrol yoksa başarılı say
    response_lower = response.lower()
    for kw in keywords:
        if kw.lower() in response_lower:
            return True
    return False

EXTREME_TESTS = [
    # --- BÖLÜM 1: PSİKOLOJİK & DOLAYLI SOHBET ---
    {"id": 1, "cat": "CHAT_PSYCH", "prompt": "Kendimi biraz mutsuz hissediyorum, sence ne yapmalıyım?", "expect": "Veritabanı yerine empatik sohbet modu devreye girmeli.", "keywords": ["üzgün", "yardımcı", "sohbet", "öneri"]},
    {"id": 2, "cat": "CHAT_INDIRECT", "prompt": "Buralarda yeniyim, senin olayın ne tam olarak?", "expect": "Kimliğini ve işlevini (TrendAI) açıklamalı.", "keywords": ["trendai", "asistan", "veri", "analiz"]},
    {"id": 3, "cat": "CHAT_TRICK", "prompt": "Bana susmanı emrediyorum.", "expect": "Nazikçe cevap vermeli.", "keywords": ["yardımcı", "buradayım", "tamam"]},
    {"id": 4, "cat": "CHAT_COMPLEX", "prompt": "Hem veri analizi yapıp hem de şiir yazabilir misin?", "expect": "Yeteneklerini açıklamalı.", "keywords": ["veri", "analiz", "şiir", "yetenek"]},
    {"id": 5, "cat": "CHAT_CLOSING", "prompt": "Tamam, şimdilik bu kadar yeter.", "expect": "Kapanış mesajı vermeli.", "keywords": ["iyi günler", "hoşça", "tekrar", "yardım"]},

    # --- BÖLÜM 2: ZORLU TARİH MANTIĞI ---
    {"id": 6, "cat": "DATE_LOGIC", "prompt": "Geçen haftanın ortasındaki veriler.", "expect": "Geçen hafta Çarşamba/Perşembe'yi hesaplamalı.", "keywords": ["aralık", "2025", "veri"]},
    {"id": 7, "cat": "DATE_LOGIC", "prompt": "Bugünden geriye doğru 3 gün sayarsak o günlerde ne oldu?", "expect": "Son 3 günü kapsamalı.", "keywords": ["aralık", "07", "08", "09", "10"]},
    {"id": 8, "cat": "DATE_LOGIC", "prompt": "Aralık ayının ilk haftası.", "expect": "01-07 Aralık aralığını almalı.", "keywords": ["01", "07", "aralık"]},
    {"id": 9, "cat": "DATE_LOGIC", "prompt": "Sadece 5 ve 6 Aralık tarihlerini karşılaştır.", "expect": "İki spesifik günü filtrelemeli.", "keywords": ["05", "06", "aralık"]},
    {"id": 10, "cat": "DATE_LOGIC", "prompt": "Dünden önceki gün.", "expect": "Bugün - 2 gün mantığını kurmalı.", "keywords": ["08", "aralık"]},
    {"id": 11, "cat": "DATE_LOGIC", "prompt": "Hafta sonu hareketliliği nasıldı?", "expect": "Son hafta sonu tarihlerini bulmalı.", "keywords": ["aralık", "veri"]},
    {"id": 12, "cat": "DATE_LOGIC", "prompt": "Bu ayın başından bugüne kadar.", "expect": "Ayın 1'inden bugüne kadar olan aralığı almalı.", "keywords": ["01", "aralık"]},
    {"id": 13, "cat": "DATE_LOGIC", "prompt": "2025'in son çeyreği.", "expect": "Ekim-Aralık 2025 aralığını anlamalı.", "keywords": ["aralık", "2025"]},
    {"id": 14, "cat": "DATE_LOGIC", "prompt": "5 Aralık sabahı.", "expect": "05-12-2025 tarihini almalı.", "keywords": ["05", "aralık"]},
    {"id": 15, "cat": "DATE_LOGIC", "prompt": "Dün ve ondan önceki günün toplamı.", "expect": "Son 2 günü kapsamalı.", "keywords": ["08", "09", "aralık"]},

    # --- BÖLÜM 3: ÇOKLU KOŞUL & FİLTRELEME ---
    {"id": 16, "cat": "MULTI_FILTER", "prompt": "Trendyol'da fiyatı 100 TL altı olan termoslar.", "expect": "Platform + Ürün + Fiyat filtresi.", "keywords": ["trendyol", "termos", "fiyat"]},
    {"id": 17, "cat": "MULTI_FILTER", "prompt": "Twitter'da #İndirim etiketiyle paylaşılan teknolojik ürünler.", "expect": "Platform + Hashtag.", "keywords": ["twitter", "indirim", "teknoloji"]},
    {"id": 18, "cat": "MULTI_FILTER", "prompt": "Hem A101 hem Şok market verilerinde gıda ürünleri.", "expect": "Çoklu Kaynak.", "keywords": ["a101", "şok", "gıda"]},
    {"id": 19, "cat": "MULTI_FILTER", "prompt": "Youtube ve Instagram'da ortak konuşulan konular.", "expect": "Platform Kesişimi.", "keywords": ["youtube", "instagram"]},
    {"id": 20, "cat": "MULTI_FILTER", "prompt": "Potansiyel skoru 80 üzeri olan ve 'kahve' içeren kayıtlar.", "expect": "Skor + İçerik filtresi.", "keywords": ["skor", "80", "kahve"]},
    {"id": 21, "cat": "MULTI_FILTER", "prompt": "Sadece 'Raw' veri tipindeki Amazon verileri.", "expect": "Veri Tipi + Kaynak.", "keywords": ["amazon", "raw"]},
    {"id": 22, "cat": "MULTI_FILTER", "prompt": "Duygu analizi 'Öfke' olan tweetler.", "expect": "Sentiment + Platform.", "keywords": ["öfke", "twitter", "duygu"]},
    {"id": 23, "cat": "MULTI_FILTER", "prompt": "Fiyatı belirtilmemiş (null) olan ürünler.", "expect": "Eksik veri sorgusu.", "keywords": ["fiyat", "yok", "belirtilmemiş"]},
    {"id": 24, "cat": "MULTI_FILTER", "prompt": "Hem 'Spor' hem 'Beslenme' etiketli içerikler.", "expect": "Çoklu Etiket.", "keywords": ["spor", "beslenme"]},
    {"id": 25, "cat": "MULTI_FILTER", "prompt": "Trendyol haricindeki tüm platformlardaki termoslar.", "expect": "Dışlama (NOT mantığı).", "keywords": ["termos", "platform"]},

    # --- BÖLÜM 4: LİNGÜİSTİK TUZAKLAR & STEMMING ---
    {"id": 26, "cat": "STEM_TRAP", "prompt": "Termosçulardaki termosların termosluğu.", "expect": "'Termos' kökü.", "keywords": ["termos", "fiyat"]},
    {"id": 27, "cat": "STEM_TRAP", "prompt": "Kitaplıktaki kitapların fiyatları.", "expect": "'Kitap' kökü.", "keywords": ["kitap", "fiyat"]},
    {"id": 28, "cat": "STEM_TRAP", "prompt": "Gözlükçüdeki gözlükler.", "expect": "'Gözlük' kökü.", "keywords": ["gözlük"]},
    {"id": 29, "cat": "STEM_TRAP", "prompt": "Bilgisayarcıdan bilgisayar aldım.", "expect": "'Bilgisayar' kökü.", "keywords": ["bilgisayar"]},
    {"id": 30, "cat": "STEM_TRAP", "prompt": "Koşucuların koşu ayakkabıları.", "expect": "'Ayakkabı' ve 'Koşu' kökleri.", "keywords": ["ayakkabı", "koşu"]},
    {"id": 31, "cat": "STEM_TRAP", "prompt": "Evimdeki ev aletleri.", "expect": "'Ev' kökü.", "keywords": ["ev", "alet"]},
    {"id": 32, "cat": "STEM_TRAP", "prompt": "Kalemlikteki kalemler.", "expect": "'Kalem' kökü.", "keywords": ["kalem"]},
    {"id": 33, "cat": "STEM_TRAP", "prompt": "Çiçekçinin çiçekleri.", "expect": "'Çiçek' kökü.", "keywords": ["çiçek"]},
    {"id": 34, "cat": "STEM_TRAP", "prompt": "Oyunculardaki oyun konsolları.", "expect": "'Oyun' kökü.", "keywords": ["oyun", "konsol"]},
    {"id": 35, "cat": "STEM_TRAP", "prompt": "Arabacıların arabaları.", "expect": "'Araba' kökü.", "keywords": ["araba"]},

    # --- BÖLÜM 5: DERİN ANALİZ & YORUMLAMA ---
    {"id": 36, "cat": "ANALYSIS", "prompt": "Bu veriler ışığında sence bir ekonomik kriz var mı?", "expect": "Sentiment yorumu.", "keywords": ["ekonomik", "kriz", "evet", "hayır", "analiz"]},
    {"id": 37, "cat": "ANALYSIS", "prompt": "Hangi ürün kategorisi gelecekte patlama yapabilir?", "expect": "Trend yorumu.", "keywords": ["kategori", "trend", "patlama", "gelecek"]},
    {"id": 38, "cat": "ANALYSIS", "prompt": "İnsanların en çok şikayet ettiği konu ne?", "expect": "Negatif sentiment.", "keywords": ["şikayet", "öfke", "konu"]},
    {"id": 39, "cat": "ANALYSIS", "prompt": "Markalar için bir strateji önerisi ver.", "expect": "Tavsiye.", "keywords": ["strateji", "öneri", "marka"]},
    {"id": 40, "cat": "ANALYSIS", "prompt": "Bu hafta sonu ne yapmalıyım?", "expect": "Aktivite önerisi.", "keywords": ["hafta sonu", "öneri", "aktivite"]},

    # --- BÖLÜM 6: HAFIZA ZİNCİRİ ---
    {"id": 41, "cat": "MEMORY_CHAIN", "prompt": "Bana en pahalı termosu bul.", "expect": "DB'den veri çekmeli.", "keywords": ["termos", "fiyat", "pahalı"]},
    {"id": 42, "cat": "MEMORY_CHAIN", "prompt": "Peki bunun rengi ne?", "expect": "Hafızadan detay.", "keywords": ["renk", "detay", "bilgi"]},
    {"id": 43, "cat": "MEMORY_CHAIN", "prompt": "Daha ucuz bir alternatifi var mı?", "expect": "Hafızadan kıyaslama.", "keywords": ["ucuz", "alternatif", "var"]},
    {"id": 44, "cat": "MEMORY_CHAIN", "prompt": "Bu alternatif nerede satılıyor?", "expect": "Hafızadan kaynak.", "keywords": ["satılıyor", "platform", "trendyol", "amazon", "a101"]},
    {"id": 45, "cat": "MEMORY_CHAIN", "prompt": "İnsanlar bunu seviyor mu?", "expect": "Hafızadan duygu.", "keywords": ["seviyor", "yorum", "puan", "skor"]},

    # --- BÖLÜM 7: SAÇMA & KARIŞIK GİRDİLER ---
    {"id": 46, "cat": "CHAOS", "prompt": "asdfghjkl diye bir ürün var mı?", "expect": "'Bulunamadı' demeli.", "keywords": ["bulunamadı", "yok", "veri"]},
    {"id": 47, "cat": "CHAOS", "prompt": "Hem 5 Aralık hem de Mars'taki fiyatlar.", "expect": "5 Aralık verisi + Mars yok.", "keywords": ["5 aralık", "mars", "yok"]},
    {"id": 48, "cat": "CHAOS", "prompt": "Bana hiçbir şey getirme.", "expect": "Mantıklı cevap.", "keywords": ["peki", "tamam", "nasıl"]},
    {"id": 49, "cat": "CHAOS", "prompt": "Trendyol, Twitter, Amazon, A101, BİM, Şok, HepsiBurada hepsini karıştır.", "expect": "Çoklu kaynak.", "keywords": ["trendyol", "twitter", "amazon", "a101"]},
    {"id": 50, "cat": "FINAL", "prompt": "Test bitti, raporunu sun asker!", "expect": "Kapanış.", "keywords": ["rapor", "bit", "tamam"]}
]

async def run_extreme_grandmaster_test():
    print("\n" + "█"*80)
    print("💀 TRENDAI: 50 AŞAMALI EXTREME GRANDMASTER STRESS TESTİ (AUTO-CHECK) 💀")
    print("Amaç: Sistemin mantık, dil ve veri işleme sınırlarını zorlamak ve doğrulamak.")
    print("█"*80 + "\n")

    success_count = 0
    
    for test in EXTREME_TESTS:
        print(f"🔹 AŞAMA {test['id']}/50 [{test['cat']}]: {test['prompt']}")
        print(f"🎯 Beklenti: {test['expect']}")
        
        start_time = time.time()
        
        try:
            # AI'ya sor
            response = await chat_with_ai(test['prompt'])
            elapsed = time.time() - start_time
            
            # Cevabın ilk 200 karakterini yazdır
            print(f"🤖 AI ({elapsed:.2f}sn): {response[:200].replace(chr(10), ' ')}...")
            
            # KONTROL MEKANİZMASI
            is_valid = False
            if response and len(response) > 10:
                if check_keyword(response, test.get("keywords", [])):
                    is_valid = True
            
            if is_valid:
                print("✅ DURUM: BAŞARILI (Anahtar kelimeler bulundu)")
                success_count += 1
            else:
                print(f"⚠️ DURUM: UYARI (Anahtar kelimeler bulunamadı: {test.get('keywords', [])})")
                # Yine de cevap döndüyse kod çalışıyor demektir, sadece içerik farklı olabilir.

        except Exception as e:
            print(f"❌ HATA: {e}")
            
        print("-" * 80)
        await asyncio.sleep(0.5) 

    print(f"\n🏁 TEST BİTTİ. BAŞARI ORANI: {success_count}/50")

if __name__ == "__main__":
    asyncio.run(run_extreme_grandmaster_test())