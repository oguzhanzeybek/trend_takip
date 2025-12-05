"use client";

import { useState } from "react";
import { 
  Brain, 
  Activity, 
  TrendingUp, 
  MessageCircle, 
  ShoppingCart, 
  Smile, 
  Frown, 
  Meh, 
  AlertTriangle, 
  CheckCircle2, 
  RefreshCcw,
  Users,
  Clock,
  Zap
} from "lucide-react";

// --- SAHTE ANALİZ VERİSİ OLUŞTURUCU ---
const generateAnalysis = () => {
  return {
    marketHealth: 78, // Pazar Sağlığı Puanı
    purchaseIntent: 64, // Satın Alma İştahı
    viralRisk: 42, // Viral Olma (Risk) Puanı
    sentiment: {
      positive: 45,
      neutral: 30,
      negative: 25,
      dominant: "Umutlu"
    },
    behavior: {
      peakHour: "20:00 - 23:00",
      platform: "Instagram & Twitter",
      contentType: "Kısa Video (Reels/Shorts)"
    },
    aiInsights: [
      "Kullanıcılar 'fiyat artışı' kelimesine karşı duyarlı, ancak 'kampanya' kelimesi negatif algıyı %40 kırıyor.",
      "Elektronik kategorisinde akşam saatlerinde ani bir satın alma isteği (impulse buying) gözlemlendi.",
      "Sosyal medyada 'boykot' etiketi yükselişte, marka iletişiminde dikkatli olunmalı."
    ],
    risks: [
      { id: 1, title: "Stok Yetersizliği", level: "Yüksek", type: "Operasyonel" },
      { id: 2, title: "Negatif Yorum Botları", level: "Orta", type: "İtibar" }
    ],
    opportunities: [
      { id: 1, title: "Haftasonu İndirimi", potential: 85, type: "Satış" },
      { id: 2, title: "Influencer İşbirliği", potential: 92, type: "Pazarlama" }
    ]
  };
};

export default function AnalyzePage() {
  const [data, setData] = useState(generateAnalysis());
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // Verileri yenileme simülasyonu
  const handleRefresh = () => {
    setIsAnalyzing(true);
    setTimeout(() => {
      setData(generateAnalysis()); // Yeni rastgele veri
      setIsAnalyzing(false);
    }, 1500);
  };

  return (
    <div className="p-8 h-full overflow-y-auto">
      
      {/* --- BAŞLIK ALANI --- */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
        <div>
          <h1 className="text-3xl font-bold text-white flex items-center gap-3">
            <Brain className="text-pink-500" />
            AI Detaylı Analiz
          </h1>
          <p className="text-gray-400 mt-1">
            Milyonlarca veri noktasının yapay zeka ile işlenmiş davranış ve duygu raporu.
          </p>
        </div>
        
        <button 
          onClick={handleRefresh}
          disabled={isAnalyzing}
          className={`flex items-center gap-2 px-6 py-3 rounded-xl font-bold transition-all
            ${isAnalyzing 
              ? "bg-zinc-800 text-gray-500 cursor-not-allowed" 
              : "bg-pink-600 hover:bg-pink-700 text-white shadow-lg shadow-pink-900/40 hover:scale-105"}
          `}
        >
          <RefreshCcw size={18} className={isAnalyzing ? "animate-spin" : ""} />
          {isAnalyzing ? "Yapay Zeka Düşünüyor..." : "Analizi Güncelle"}
        </button>
      </div>

      {/* --- ÜST KPI KARTLARI --- */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        
        {/* Pazar Sağlığı */}
        <div className="bg-zinc-900 p-6 rounded-2xl border border-zinc-800 relative overflow-hidden group">
           <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
              <Activity size={80} className="text-green-500" />
           </div>
           <h3 className="text-gray-400 font-medium mb-2">Genel Pazar Sağlığı</h3>
           <div className="flex items-end gap-3">
              <span className="text-4xl font-black text-white">{data.marketHealth}/100</span>
              <span className="text-sm text-green-500 font-bold mb-1 flex items-center">
                <TrendingUp size={14} className="mr-1"/> Pozitif
              </span>
           </div>
           <div className="w-full bg-zinc-800 h-2 rounded-full mt-4 overflow-hidden">
              <div className="h-full bg-green-500 transition-all duration-1000" style={{ width: `${data.marketHealth}%` }}></div>
           </div>
        </div>

        {/* Satın Alma İştahı */}
        <div className="bg-zinc-900 p-6 rounded-2xl border border-zinc-800 relative overflow-hidden group">
           <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
              <ShoppingCart size={80} className="text-blue-500" />
           </div>
           <h3 className="text-gray-400 font-medium mb-2">Satın Alma Eğilimi</h3>
           <div className="flex items-end gap-3">
              <span className="text-4xl font-black text-white">%{data.purchaseIntent}</span>
              <span className="text-sm text-blue-400 font-bold mb-1">Orta Seviye</span>
           </div>
           <p className="text-xs text-gray-500 mt-2">Kullanıcılar sepete ekliyor ancak ödemede bekliyor.</p>
        </div>

        {/* Viral Risk */}
        <div className="bg-zinc-900 p-6 rounded-2xl border border-zinc-800 relative overflow-hidden group">
           <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
              <MessageCircle size={80} className="text-orange-500" />
           </div>
           <h3 className="text-gray-400 font-medium mb-2">Gündem Viral Skoru</h3>
           <div className="flex items-end gap-3">
              <span className="text-4xl font-black text-white">{data.viralRisk}</span>
              <span className="text-sm text-orange-500 font-bold mb-1">Yüksek Etkileşim</span>
           </div>
           <p className="text-xs text-gray-500 mt-2">Şu an trend olan konular hızlı yayılıyor.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* --- SOL KOLON (Duygu & Davranış) --- */}
        <div className="lg:col-span-2 space-y-8">
          
          {/* 1. DUYGU ANALİZİ */}
          <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6">
            <h3 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
              <Smile className="text-yellow-500" />
              Duygu Durum Analizi (Sentiment Analysis)
            </h3>
            
            {/* Duygu Barları */}
            <div className="space-y-6">
               {/* Pozitif */}
               <div>
                 <div className="flex justify-between text-sm mb-2">
                    <span className="text-white flex items-center gap-2"><Smile size={16} className="text-green-500"/> Pozitif Yorumlar</span>
                    <span className="font-bold text-green-500">%{data.sentiment.positive}</span>
                 </div>
                 <div className="w-full bg-zinc-800 h-3 rounded-full overflow-hidden">
                    <div className="h-full bg-green-500" style={{ width: `${data.sentiment.positive}%` }}></div>
                 </div>
               </div>

               {/* Nötr */}
               <div>
                 <div className="flex justify-between text-sm mb-2">
                    <span className="text-white flex items-center gap-2"><Meh size={16} className="text-gray-400"/> Nötr / Soru Soranlar</span>
                    <span className="font-bold text-gray-400">%{data.sentiment.neutral}</span>
                 </div>
                 <div className="w-full bg-zinc-800 h-3 rounded-full overflow-hidden">
                    <div className="h-full bg-gray-500" style={{ width: `${data.sentiment.neutral}%` }}></div>
                 </div>
               </div>

               {/* Negatif */}
               <div>
                 <div className="flex justify-between text-sm mb-2">
                    <span className="text-white flex items-center gap-2"><Frown size={16} className="text-red-500"/> Negatif / Şikayet</span>
                    <span className="font-bold text-red-500">%{data.sentiment.negative}</span>
                 </div>
                 <div className="w-full bg-zinc-800 h-3 rounded-full overflow-hidden">
                    <div className="h-full bg-red-500" style={{ width: `${data.sentiment.negative}%` }}></div>
                 </div>
               </div>
            </div>

            <div className="mt-6 p-4 bg-zinc-950 rounded-xl border border-zinc-800 flex items-center gap-4">
               <div className="p-3 bg-pink-500/10 rounded-full text-pink-500">
                  <Brain size={24} />
               </div>
               <div>
                  <h4 className="text-sm font-bold text-gray-300">Yapay Zeka Tespiti</h4>
                  <p className="text-sm text-gray-400">
                    Kitle şu an ağırlıklı olarak <strong className="text-white">{data.sentiment.dominant}</strong> bir ruh hali içinde. 
                    Satış kampanyaları için uygun bir zaman dilimi.
                  </p>
               </div>
            </div>
          </div>

          {/* 2. DAVRANIŞ ANALİZİ */}
          <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6">
            <h3 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
              <Users className="text-purple-500" />
              Kullanıcı Davranış Analizi
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
               {/* Kutu 1 */}
               <div className="bg-zinc-950 p-4 rounded-xl border border-zinc-800 text-center">
                  <Clock className="mx-auto text-purple-500 mb-2" size={24}/>
                  <div className="text-xs text-gray-500 uppercase font-bold">En Aktif Saatler</div>
                  <div className="text-lg font-bold text-white mt-1">{data.behavior.peakHour}</div>
               </div>
               {/* Kutu 2 */}
               <div className="bg-zinc-950 p-4 rounded-xl border border-zinc-800 text-center">
                  <Activity className="mx-auto text-blue-500 mb-2" size={24}/>
                  <div className="text-xs text-gray-500 uppercase font-bold">Platform Tercihi</div>
                  <div className="text-lg font-bold text-white mt-1">{data.behavior.platform}</div>
               </div>
               {/* Kutu 3 */}
               <div className="bg-zinc-950 p-4 rounded-xl border border-zinc-800 text-center">
                  <Zap className="mx-auto text-yellow-500 mb-2" size={24}/>
                  <div className="text-xs text-gray-500 uppercase font-bold">Tüketilen İçerik</div>
                  <div className="text-lg font-bold text-white mt-1">{data.behavior.contentType}</div>
               </div>
            </div>
          </div>

        </div>

        {/* --- SAĞ KOLON (Gündem & Fırsatlar) --- */}
        <div className="space-y-8">
          
          {/* AI ÖZET KARTI */}
          <div className="bg-gradient-to-b from-pink-900/20 to-zinc-900 border border-pink-500/30 rounded-2xl p-6">
            <h3 className="text-lg font-bold text-pink-400 mb-4 flex items-center gap-2">
              <Brain size={20} />
              TrendAI Asistan Özeti
            </h3>
            <ul className="space-y-4">
              {data.aiInsights.map((insight, idx) => (
                <li key={idx} className="flex gap-3 text-sm text-gray-300">
                  <span className="mt-1 min-w-[6px] h-[6px] rounded-full bg-pink-500"></span>
                  {insight}
                </li>
              ))}
            </ul>
          </div>

          {/* FIRSATLAR LİSTESİ */}
          <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6">
            <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
              <CheckCircle2 size={20} className="text-green-500" />
              Tespit Edilen Fırsatlar
            </h3>
            <div className="space-y-3">
              {data.opportunities.map((opp) => (
                <div key={opp.id} className="flex items-center justify-between p-3 bg-zinc-950 rounded-lg border border-zinc-800 hover:border-green-500/50 transition-colors">
                   <div>
                      <div className="font-bold text-white text-sm">{opp.title}</div>
                      <div className="text-xs text-gray-500">{opp.type}</div>
                   </div>
                   <div className="px-2 py-1 bg-green-900/30 text-green-400 text-xs font-bold rounded">
                      Skor: {opp.potential}
                   </div>
                </div>
              ))}
            </div>
          </div>

          {/* RİSKLER LİSTESİ */}
          <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6">
            <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
              <AlertTriangle size={20} className="text-red-500" />
              Dikkat Gerektiren Riskler
            </h3>
            <div className="space-y-3">
              {data.risks.map((risk) => (
                <div key={risk.id} className="flex items-center justify-between p-3 bg-zinc-950 rounded-lg border border-zinc-800 hover:border-red-500/50 transition-colors">
                   <div>
                      <div className="font-bold text-white text-sm">{risk.title}</div>
                      <div className="text-xs text-gray-500">{risk.type}</div>
                   </div>
                   <div className="px-2 py-1 bg-red-900/30 text-red-400 text-xs font-bold rounded uppercase">
                      {risk.level}
                   </div>
                </div>
              ))}
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}