"use client";

import { useState, useEffect } from "react";
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
  Users, 
  Zap, 
  Loader2, 
  CalendarDays,
  RefreshCcw
} from "lucide-react";
import { 
  PieChart, Pie, Cell, ResponsiveContainer, Tooltip as RechartsTooltip, 
  Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis 
} from 'recharts';

const API_BASE_URL = "http://127.0.0.1:8000";
const COLORS = ['#22c55e', '#eab308', '#ef4444']; // Yeşil, Sarı, Kırmızı

export default function AnalyzePage() {
  const [analysisData, setAnalysisData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  // --- ANALİZ VERİSİNİ ÇEK ---
  const fetchAnalysis = async () => {
    try {
      setLoading(true);
      const res = await fetch(`${API_BASE_URL}/api/analysis`);
      const result = await res.json();
      
      if (result.status === "success" && result.data) {
        setAnalysisData(result.data);
      }
    } catch (error) {
      console.error("Analiz verisi alınamadı:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalysis();
  }, []);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-gray-500 gap-4">
        <Loader2 size={48} className="animate-spin text-pink-500" />
        <p>Yapay zeka veritabanından güncel analizi çekiyor...</p>
      </div>
    );
  }

  if (!analysisData) {
    return <div className="p-8 text-white">Analiz verisi bulunamadı. Lütfen önce analiz scriptini çalıştırın.</div>;
  }

  // --- %100 DİNAMİK HESAPLAMALAR ---
  // Artık hiçbir sayı elle yazılmıyor, hepsi JSON'dan türetiliyor.

  // 1. Duygu Ortalaması ve Toplamı
  const emotions = analysisData.ana_duygular || [];
  const totalEmotionScore = emotions.reduce((acc:number, curr:any) => acc + (curr.skor || 0), 0);
  const avgEmotionScore = totalEmotionScore / (emotions.length || 1);

  // 2. Risk Ortalaması (Yüksek Risk = 100, Orta = 50, Düşük = 0 kabul edip ortalama alıyoruz)
  const risks = analysisData.gelecek_tahminleri || [];
  const riskScoreTotal = risks.reduce((acc:number, curr:any) => {
      if (curr.risk_seviyesi === "Yüksek") return acc + 100;
      if (curr.risk_seviyesi === "Orta") return acc + 50;
      return acc + 10; // Düşük
  }, 0);
  const avgRiskScore = riskScoreTotal / (risks.length || 1);

  // --- KPI FORMÜLLERİ ---
  
  // A) Pazar Sağlığı: (100 - Risk Skoru) ve (Pozitif Duygu Varlığı) ortalaması
  // Eğer risk yüksekse sağlık düşer.
  const marketHealth = Math.round(Math.max(10, 100 - (avgRiskScore * 0.8)));

  // B) Viral Skor: Duyguların toplam yoğunluğu (İnsanlar ne kadar yoğun hissediyorsa viralite o kadar artar)
  // Duygu skorlarının ortalaması ne kadar yüksekse viralite o kadar yüksek.
  const viralScore = Math.min(100, Math.round(avgEmotionScore * 1.2)); 

  // C) Satın Alma İştahı (Purchase Intent): 
  // Pazar sağlığı yüksekse ve risk düşükse satın alma artar.
  // Formül: (Sağlık Skoru * 0.7) + (30 puan bonus - Risk/3)
  const purchaseIntent = Math.round((marketHealth * 0.7) + (30 - (avgRiskScore / 5)));

  // D) Fırsat Skoru:
  // Risk ne kadar düşükse, fırsat o kadar yüksektir.
  const opportunityScore = Math.round(100 - avgRiskScore);

  // --- GRAFİK VERİLERİ ---
  
  // Pasta Grafiği (Duygular)
  const sentimentData = emotions.map((e:any) => ({
      name: e.duygu,
      value: e.skor
  }));

  // Radar Grafiği (Tüm Metrikler)
  const radarData = [
    { subject: 'Pazar Sağlığı', A: marketHealth, fullMark: 100 },
    { subject: 'Satın Alma', A: purchaseIntent, fullMark: 100 },
    { subject: 'Viralite', A: viralScore, fullMark: 100 },
    { subject: 'Risk Seviyesi', A: Math.round(avgRiskScore), fullMark: 100 },
    { subject: 'Fırsat', A: opportunityScore, fullMark: 100 },
  ];

  // Renk Yardımcısı
  const getRiskColor = (level: string) => {
    if (level === "Yüksek") return "text-red-500 bg-red-900/30";
    if (level === "Orta") return "text-orange-500 bg-orange-900/30";
    return "text-green-500 bg-green-900/30";
  };

  return (
    <div className="p-6 md:p-8 h-full overflow-y-auto bg-zinc-950 text-white font-sans relative">
      
      {/* HEADER */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4 border-b border-zinc-800/50 pb-6">
        <div>
          <h1 className="text-3xl font-bold text-white flex items-center gap-3">
            <Brain className="text-pink-500" />
            AI Detaylı Pazar Analizi
          </h1>
          <p className="text-gray-400 mt-2 text-sm flex items-center gap-2">
            <CalendarDays size={14}/> Rapor Tarihi: <span className="text-white font-mono">{analysisData.analiz_tarihi}</span>
          </p>
        </div>
        
        <button 
          onClick={fetchAnalysis}
          className="flex items-center gap-2 px-6 py-3 rounded-xl font-bold bg-pink-600 hover:bg-pink-700 text-white shadow-lg shadow-pink-900/20 hover:scale-105 transition-all"
        >
          <RefreshCcw size={18} />
          Raporu Yenile
        </button>
      </div>

      {/* --- KPI KARTLARI (Tamamen Dinamik) --- */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        
        {/* Pazar Sağlığı */}
        <div className="bg-zinc-900 p-6 rounded-2xl border border-zinc-800 relative overflow-hidden group">
           <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
              <Activity size={80} className={marketHealth > 50 ? "text-green-500" : "text-red-500"} />
           </div>
           <h3 className="text-gray-400 font-medium mb-2 text-sm uppercase tracking-wider">Toplum Ruh Hali Endeksi</h3>
           <div className="flex items-end gap-3">
              <span className="text-4xl font-black text-white">{marketHealth}/100</span>
              <span className={`text-sm font-bold mb-1 flex items-center ${marketHealth > 50 ? "text-green-500" : "text-red-500"}`}>
                {marketHealth > 50 ? "Pozitif / Dengeli" : "Negatif / Gergin"}
              </span>
           </div>
           <div className="w-full bg-zinc-800 h-1.5 rounded-full mt-4 overflow-hidden">
              <div className={`h-full transition-all duration-1000 ${marketHealth > 50 ? "bg-green-500" : "bg-red-500"}`} style={{ width: `${marketHealth}%` }}></div>
           </div>
        </div>

        {/* Harcama Eğilimi */}
        <div className="bg-zinc-900 p-6 rounded-2xl border border-zinc-800 relative overflow-hidden group">
           <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
              <ShoppingCart size={80} className="text-blue-500" />
           </div>
           <h3 className="text-gray-400 font-medium mb-2 text-sm uppercase tracking-wider">Satın Alma İştahı</h3>
           <div className="flex items-end gap-3">
              <span className="text-4xl font-black text-white">
                %{purchaseIntent}
              </span>
              <span className="text-sm text-blue-400 font-bold mb-1">
                  {purchaseIntent > 60 ? "Yüksek" : purchaseIntent > 40 ? "Orta" : "Düşük"}
              </span>
           </div>
           <p className="text-xs text-gray-500 mt-3 line-clamp-1">
             {analysisData.harcama_egilimi_analizi?.egilim}
           </p>
        </div>

        {/* Viral Skor */}
        <div className="bg-zinc-900 p-6 rounded-2xl border border-zinc-800 relative overflow-hidden group">
           <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
              <MessageCircle size={80} className="text-orange-500" />
           </div>
           <h3 className="text-gray-400 font-medium mb-2 text-sm uppercase tracking-wider">Gündem Yoğunluğu</h3>
           <div className="flex items-end gap-3">
              <span className="text-4xl font-black text-white">%{viralScore}</span>
              <span className="text-sm text-orange-500 font-bold mb-1">Etkileşim Gücü</span>
           </div>
           <p className="text-xs text-gray-500 mt-2">Duygusal yoğunluk sosyal medyada viraliteyi belirliyor.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* --- SOL KOLON (Grafikler) --- */}
        <div className="space-y-8">
            
            {/* RADAR CHART (Tamamen Dinamik Data ile) */}
            <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6 relative overflow-hidden">
                <h3 className="font-bold text-gray-300 mb-4 flex items-center gap-2">
                    <Activity size={18} className="text-blue-500"/> Pazar Dengesi
                </h3>
                <div className="h-[250px] w-full flex justify-center items-center -ml-4">
                    <ResponsiveContainer width="100%" height="100%">
                        <RadarChart cx="50%" cy="50%" outerRadius="80%" data={radarData}>
                            <PolarGrid stroke="#3f3f46" />
                            <PolarAngleAxis dataKey="subject" tick={{ fill: '#a1a1aa', fontSize: 10 }} />
                            <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} axisLine={false}/>
                            <Radar name="Skor" dataKey="A" stroke="#ec4899" fill="#ec4899" fillOpacity={0.3} />
                            <RechartsTooltip contentStyle={{ backgroundColor: '#18181b', borderColor: '#27272a', color: '#fff' }}/>
                        </RadarChart>
                    </ResponsiveContainer>
                </div>
            </div>

            {/* PASTA GRAFİĞİ (JSON Duygularından) */}
            <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6">
                <h3 className="font-bold text-gray-300 mb-2 flex items-center gap-2">
                    <Smile size={18} className="text-yellow-500"/> Duygu Dağılımı
                </h3>
                <div className="flex items-center">
                    <div className="h-[180px] w-1/2">
                        <ResponsiveContainer width="100%" height="100%">
                            <PieChart>
                                <Pie data={sentimentData} innerRadius={40} outerRadius={60} paddingAngle={5} dataKey="value">
                                    {sentimentData.map((entry:any, index:number) => (
                                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                    ))}
                                </Pie>
                                <RechartsTooltip contentStyle={{ backgroundColor: '#18181b', borderColor: '#27272a', borderRadius: '8px' }}/>
                            </PieChart>
                        </ResponsiveContainer>
                    </div>
                    <div className="w-1/2 space-y-2">
                        {emotions.map((d:any, i:number) => (
                            <div key={i} className="flex justify-between text-xs">
                                <span className="text-gray-400 flex items-center gap-1">
                                    <div className={`w-2 h-2 rounded-full`} style={{backgroundColor: COLORS[i%3]}}></div>
                                    {d.duygu}
                                </span>
                                <span className="font-bold text-white">%{d.skor}</span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

        </div>

        {/* --- ORTA KOLON (Yazılı Analizler - Direkt JSON'dan) --- */}
        <div className="lg:col-span-2 space-y-6">
            
            {/* EXECUTIVE SUMMARY */}
            <div className="bg-gradient-to-br from-zinc-900 to-zinc-950 border border-zinc-800 rounded-2xl p-8 relative">
                <div className="absolute top-0 right-0 p-4 opacity-5">
                    <Brain size={120} />
                </div>
                <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                    <Zap className="text-yellow-500 fill-yellow-500"/> Yapay Zeka Özeti
                </h3>
                <p className="text-gray-300 leading-relaxed text-lg font-light">
                    {analysisData.genel_değerlendirme}
                </p>
                <div className="mt-6 pt-6 border-t border-zinc-800 grid grid-cols-2 gap-6">
                    <div>
                        <span className="text-xs text-gray-500 uppercase font-bold">Baskın Gündem</span>
                        <div className="text-white font-bold mt-1 text-lg">
                            {analysisData.baskin_gundemler?.[0]?.konu || "Tespit Edilemedi"}
                        </div>
                    </div>
                    <div>
                        <span className="text-xs text-gray-500 uppercase font-bold">Sektörel Etki</span>
                        <div className="text-white font-bold mt-1 text-lg">
                            {analysisData.harcama_egilimi_analizi?.sektor_etkisi?.split('.')[0] || "Veri Bekleniyor"}
                        </div>
                    </div>
                </div>
            </div>

            {/* FIRSATLAR & RİSKLER GRID */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                
                {/* GELECEK TAHMİNLERİ */}
                <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6">
                    <h3 className="font-bold text-white mb-4 flex items-center gap-2">
                        <TrendingUp size={18} className="text-blue-500"/> Gelecek Öngörüleri
                    </h3>
                    <div className="space-y-4">
                        {analysisData.gelecek_tahminleri?.map((t:any, i:number) => (
                            <div key={i} className="p-3 bg-black/20 rounded-lg border border-white/5 hover:border-blue-500/30 transition-colors">
                                <div className="flex justify-between items-start mb-1">
                                    <span className="text-sm font-bold text-gray-200">{t.tahmin}</span>
                                    <span className={`text-[10px] px-2 py-0.5 rounded font-bold ${getRiskColor(t.risk_seviyesi)}`}>
                                        {t.risk_seviyesi.toUpperCase()} RİSK
                                    </span>
                                </div>
                                <p className="text-xs text-gray-500">{t.neden}</p>
                            </div>
                        ))}
                    </div>
                </div>

                {/* GÜNDEM MADDELERİ */}
                <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6">
                    <h3 className="font-bold text-white mb-4 flex items-center gap-2">
                        <Users size={18} className="text-purple-500"/> Toplumun Gündemi
                    </h3>
                    <div className="space-y-4">
                        {analysisData.baskin_gundemler?.map((g:any, i:number) => (
                            <div key={i} className="flex gap-3 items-start">
                                <div className="mt-1 min-w-[24px] h-[24px] rounded-full bg-purple-500/10 text-purple-500 flex items-center justify-center text-xs font-bold">
                                    {i+1}
                                </div>
                                <div>
                                    <div className="text-sm font-bold text-white">{g.konu}</div>
                                    <div className="text-xs text-gray-500 leading-snug mt-0.5">{g.köken}</div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

            </div>
        </div>

      </div>
    </div>
  );
}