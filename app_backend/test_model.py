import asyncio
import os
import time

# Windows için
if os.name == 'nt':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from model import chat_with_ai

# ==============================================================================
# 💀 DÜNYANIN EN ZORLU TEST SENARYOLARI
# ==============================================================================
ULTIMATE_TESTS = [
    {
        "id": 1,
        "type": "SOHBET & GİRİŞ",
        "query": "Selamlar, nasılsın? Bana yardımcı olabilir misin?",
        "zorluk": "Veritabanı araması gerektirmeyen insani bir giriş. Sistemin 'Veri bulamadım' mı diyeceği yoksa sohbet mi edeceği test ediliyor."
    },
    {
        "id": 2,
        "type": "KOMBO FİLTRE (Tarih + Platform + Çoklu Kelime + Stemming)",
        "query": "Son 1 hafta içinde hem Trendyol hem de Twitter tarafında, özellikle termoslar ve fiyatları hakkında neler var?",
        "zorluk": "Aynı anda: 7 günlük tarih hesabı + 2 Platform (Trendyol, Twitter) + Stemming (Termoslar -> Termos) + İçerik araması."
    },
    {
        "id": 3,
        "type": "HAFIZA & BAĞLAM (Zorlayıcı)",
        "query": "Peki bahsettiğin bu ürünlerin içindeki en pahalı olanın özellikleri ne ve insanlar buna ne tepki vermiş?",
        "zorluk": "Ürün adı yok. Tarih yok. Sadece 'bu ürünlerin' var. Hafızadan önceki listeyi çekip, hem fiyat analizi hem de (varsa) duygu analizi yapması lazım."
    },
    {
        "id": 4,
        "type": "DUYGU ANALİZİ (Sentiment) & SPESİFİK TARİH",
        "query": "5 Aralık tarihinde halkın genel hisleri, kaygı durumu ve öfke seviyesi nasıldı?",
        "zorluk": "Geçmiş bir tarihe (5 Aralık) gidip, o günün 'Analyzed' verisini bulmalı ve sayısal skorları yorumlamalı."
    },
    {
        "id": 5,
        "type": "OLMAYAN VERİ & HALÜSİNASYON TESTİ",
        "query": "Mars kolonisi bilet fiyatları ve uzaylıların tepkisi ne?",
        "zorluk": "Veritabanında asla olmayan bir şey. Sistemin saçmalamadan 'Veri yok' demesi gerekiyor."
    },
    {
        "id": 6,
        "type": "ÇAPRAZ SORGULAMA (Cross-Check)",
        "query": "Dün ve bugün için Twitter'daki #ErkenTrend etiketli fırsatları listele.",
        "zorluk": "Tarih: Dün+Bugün. Platform: Twitter. Etiket: #ErkenTrend. Hepsini aynı anda filtreleyebilmeli."
    }
]

async def run_ultimate_test():
    print("\n" + "="*60)
    print("🥊 TRENDAI: ULTIMATE STRESS TEST BAŞLIYOR 🥊")
    print("="*60 + "\n")

    for test in ULTIMATE_TESTS:
        print(f"🔥 TEST #{test['id']} - [{test['type']}]")
        print(f"⚠️  Zorluk: {test['zorluk']}")
        print(f"🗣️  Kullanıcı: '{test['query']}'")
        print("-" * 60)
        
        start = time.time()
        
        try:
            response = await chat_with_ai(test['query'])
            duration = time.time() - start
            
            print(f"\n🤖 TrendAI ({duration:.2f}sn):\n")
            print(response)
            
        except Exception as e:
            print(f"❌ SİSTEM ÇÖKTÜ: {e}")
            
        print("\n" + "="*60 + "\n")
        await asyncio.sleep(2) # Okumak için bekleme

    print("🏁 TEST BİTTİ. SONUÇLARI KONTROL ET.")

if __name__ == "__main__":
    asyncio.run(run_ultimate_test())