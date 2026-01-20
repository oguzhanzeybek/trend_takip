"use client";

import { useState, useEffect, useRef } from "react";
import { 
  Brain, Activity, TrendingUp, ShoppingCart, 
  Smile, Users, Zap, Loader2, 
  CalendarDays, RefreshCcw, Download, Cloud, CloudRain, Sun, Thermometer
} from "lucide-react";
import { 
  PieChart, Pie, Cell, ResponsiveContainer, 
  Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis 
} from 'recharts';

import { toPng } from 'html-to-image';
import jsPDF from 'jspdf';

const API_BASE_URL = "http://127.0.0.1:8000";
// Duygular için Mor, Mavi, Turuncu paleti
const COLORS = ['#a855f7', '#3b82f6', '#f97316']; 

// --- ANIMASYONLU SAYAÇ ---
const AnimatedNumber = ({ value }: { value: number }) => {
    const [count, setCount] = useState(0);
    useEffect(() => {
        let start = 0;
        const end = value || 0; 
        if (start === end) return;
        const duration = 1000;
        const incrementTime = (duration / (Math.abs(end) || 1)) * 5; 

        const timer = setInterval(() => {
            if (start < end) start += 1;
            else if (start > end) start -= 1;
            
            setCount(start);
            if (start === end) clearInterval(timer);
        }, incrementTime);
        
        return () => clearInterval(timer);
    }, [value]);
    return <span>{count}</span>;
};

export default function AnalyzePage() {
  const [analysisData, setAnalysisData] = useState<any>(null);
  const [weatherData, setWeatherData] = useState<any>(null); 
  const [loading, setLoading] = useState(true);
  const [pdfGenerating, setPdfGenerating] = useState(false);
  
  const printRef = useRef<HTMLDivElement>(null);

  // --- VERİ ÇEKME ---
  const fetchData = async () => {
    try {
      setLoading(true);
      
      const resAnalysis = await fetch(`${API_BASE_URL}/api/analysis`);
      const resultAnalysis = await resAnalysis.json();
      if (resultAnalysis.status === "success" && resultAnalysis.data) {
        setAnalysisData(resultAnalysis.data);
      }

      const resWeather = await fetch(`${API_BASE_URL}/api/weather`);
      const resultWeather = await resWeather.json();
      if (resultWeather.status === "success" && resultWeather.data) {
        setWeatherData(resultWeather.data);
      }

    } catch (error) {
      console.error("Veri hatası:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, []);

  // --- PDF İNDİRME ---
  const handleDownloadPDF = async () => {
      if (!printRef.current) return;
      setPdfGenerating(true);
      try {
          const element = printRef.current;
          const imgData = await toPng(element, {
              quality: 0.95,
              backgroundColor: '#000000',
              height: element.scrollHeight, 
              style: { overflow: 'visible', maxHeight: 'none', height: 'auto' }
          });
          const pdf = new jsPDF({ orientation: 'p', unit: 'mm', format: 'a4' });
          const imgWidth = 210; 
          const imgProps = pdf.getImageProperties(imgData);
          const imgHeight = (imgProps.height * imgWidth) / imgProps.width;
          let heightLeft = imgHeight;
          let position = 0;
          const pageHeight = 297;

          pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight);
          heightLeft -= pageHeight;

          while (heightLeft >= 0) {
            position = heightLeft - imgHeight;
            pdf.addPage();
            pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight);
            heightLeft -= pageHeight;
          }
          pdf.save(`TrendAI_Rapor_${new Date().toISOString().slice(0,10)}.pdf`);
      } catch (error) {
          console.error("PDF Hatası:", error);
          alert("PDF hatası oluştu.");
      } finally {
          setPdfGenerating(false);
      }
  };

  if (loading) return (
    <div className="flex flex-col items-center justify-center h-full gap-4">
        <Loader2 size={64} className="animate-spin text-pink-500" />
        <p className="text-xl text-gray-400 animate-pulse">Yapay zeka verileri işliyor...</p>
    </div>
  );

  if (!analysisData) return <div className="p-8 text-white text-2xl">Veri bulunamadı.</div>;

  // --- HESAPLAMALAR ---

  const avgEmotionScore = analysisData.ana_duygular 
    ? analysisData.ana_duygular.reduce((acc:any, curr:any) => acc + curr.skor, 0) / analysisData.ana_duygular.length
    : 50;
  
  const risks = analysisData.gelecek_tahminleri || [];
  const riskScoreTotal = risks.reduce((acc:number, curr:any) => {
      if (curr.risk_seviyesi === "Yüksek") return acc + 100;
      if (curr.risk_seviyesi === "Orta") return acc + 50;
      return acc + 10;
  }, 0);
  const avgRiskScore = riskScoreTotal / (risks.length || 1);

  const aiScores = analysisData.stratejik_skorlar || {};

  // Yardımcı Fonksiyonlar
  const getSmartScore = (key: string, fallbackVal: number) => {
      const val = aiScores[key];
      if (typeof val === 'number') return val; 
      if (typeof val === 'object' && val?.skor !== undefined) return val.skor; 
      return fallbackVal; 
  };

  const getSmartDesc = (key: string, defaultDesc: string) => {
      const val = aiScores[key];
      if (typeof val === 'object' && val?.aciklama) return val.aciklama; 
      return defaultDesc; 
  };

  // --- METRİKLER VE BASİT DİL AÇIKLAMALARI ---
  const marketHealth = getSmartScore("pazar_sagligi", Math.round(Math.max(10, 100 - (avgRiskScore * 0.8))));
  const marketHealthDesc = getSmartDesc("pazar_sagligi", "Piyasanın nabzı nasıl? İnsanlar genel olarak huzurlu mu yoksa gidişattan endişeli mi? Bu puan bunu gösterir.");

  const purchaseIntent = getSmartScore("satin_alma_istahi", Math.round((marketHealth * 0.7) + (30 - (avgRiskScore / 5))));
  const purchaseIntentDesc = getSmartDesc("satin_alma_istahi", "Cüzdanlar açılıyor mu? Tüketiciler para harcamaya hevesli mi yoksa kemer mi sıkıyorlar?");

  const viralScore = getSmartScore("viral_etki", Math.min(100, Math.round(avgEmotionScore * 1.2)));
  const viralDesc = getSmartDesc("viral_etki", "Herkes bunu mu konuşuyor? Gündemdeki olaylar ne kadar hızlı yayılıyor ve etkileşim alıyor?");

  const opportunityScore = getSmartScore("firsat_skoru", Math.round(100 - avgRiskScore));

  // --- DİNAMİK RENK FONKSİYONU ---
  const getScoreColorInfo = (score: number) => {
    if (score >= 70) return { 
        text: "text-green-500", 
        bg: "bg-green-500", 
        border: "border-green-500/30", 
        glow: "bg-green-500/10", 
        from: "from-green-600", 
        to: "to-green-400" 
    };
    if (score >= 40) return { 
        text: "text-yellow-500", 
        bg: "bg-yellow-500", 
        border: "border-yellow-500/30", 
        glow: "bg-yellow-500/10", 
        from: "from-yellow-600", 
        to: "to-yellow-400" 
    };
    return { 
        text: "text-red-500", 
        bg: "bg-red-500", 
        border: "border-red-500/30", 
        glow: "bg-red-500/10", 
        from: "from-red-600", 
        to: "to-red-400" 
    };
  };

  const marketColor = getScoreColorInfo(marketHealth);
  const purchaseColor = getScoreColorInfo(purchaseIntent);
  const viralColor = getScoreColorInfo(viralScore);
  
  // Grafik Verileri
  const sentimentData = (analysisData.ana_duygular || []).map((e:any) => ({ name: e.duygu, value: e.skor }));

  const radarData = [
    { subject: 'Sağlık', A: marketHealth, fullMark: 100 },
    { subject: 'Satış', A: purchaseIntent, fullMark: 100 },
    { subject: 'Viral', A: viralScore, fullMark: 100 },
    { subject: 'Risk', A: Math.round(avgRiskScore), fullMark: 100 },
    { subject: 'Fırsat', A: opportunityScore, fullMark: 100 },
  ];

  const getRiskColor = (level: string) => {
    if (level === "Yüksek") return "text-red-400 bg-red-500/10 border-red-500/20";
    if (level === "Orta") return "text-orange-400 bg-orange-500/10 border-orange-500/20";
    return "text-green-400 bg-green-500/10 border-green-500/20";
  };
  
  // --- HAVA DURUMU ---
  const getWeatherImpact = () => {
      const temp = weatherData?.temperature || 15;
      const code = weatherData?.weathercode || 0;
      
      let condition = "Parçalı Bulutlu";
      let icon = <Cloud size={40} className="text-gray-400"/>;
      let impactTitle = "Normal Seyir";
      let insight = "Hava koşulları alışveriş alışkanlıklarını nötr etkiliyor.";

      if ([51, 53, 55, 61, 63, 65, 80, 81, 82].includes(code)) {
          condition = "Yağmurlu";
          icon = <CloudRain size={40} className="text-blue-400"/>;
          impactTitle = "Online Sipariş Artışı";
          insight = "Yağışlı hava fiziksel mağaza trafiğini düşürüp online siparişleri artırabilir.";
      } 
      else if ([0, 1].includes(code)) {
          condition = "Güneşli";
          icon = <Sun size={40} className="text-yellow-400 animate-spin-slow"/>;
          impactTitle = "Fiziksel Trafik Artışı";
          insight = "Güzel hava insanları dışarı çıkmaya ve AVM/cadde mağazalarını gezmeye teşvik ediyor.";
      }

      return { temp, condition, icon, impactTitle, insight };
  };

  const weatherImpact = getWeatherImpact();

  return (
    <div className="h-full overflow-y-auto bg-black text-white font-sans selection:bg-pink-500/30">
      
      <div ref={printRef} className="p-6 md:p-10 min-h-screen bg-black">
      
          {/* --- HEADER --- */}
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 pb-6 border-b border-zinc-800">
            <div>
              <h1 className="text-4xl font-black text-white flex items-center gap-4 tracking-tight">
                <div className="p-3 bg-pink-600 rounded-xl shadow-[0_0_30px_rgba(236,72,153,0.5)]">
                    <Brain className="text-white" size={32} />
                </div>
                AI Stratejik Raporu
              </h1>
              <div className="flex items-center gap-4 mt-3">
                  <span className="px-4 py-2 rounded-full bg-zinc-900 border border-zinc-800 text-sm text-gray-400 flex items-center gap-2">
                    <CalendarDays size={16}/> 
                    {new Date(analysisData.analiz_tarihi || Date.now()).toLocaleDateString("tr-TR", {
                        day: 'numeric', month: 'long', year: 'numeric', hour: '2-digit', minute: '2-digit'
                    })}
                  </span>
                  <span className="px-4 py-2 rounded-full bg-green-900/20 border border-green-900/30 text-sm text-green-500 flex items-center gap-2">
                    <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div> Sistem Aktif
                  </span>
              </div>
            </div>
            
            <div className="flex gap-3 mt-4 md:mt-0" data-html2canvas-ignore="true">
                <button 
                    onClick={handleDownloadPDF} 
                    disabled={pdfGenerating}
                    className={`flex items-center gap-2 px-5 py-3 rounded-xl font-bold border border-zinc-800 transition-all text-base ${
                        pdfGenerating ? "bg-zinc-800 text-gray-500 cursor-wait" : "bg-zinc-900 hover:bg-zinc-800 hover:text-white text-gray-400"
                    }`}
                >
                    {pdfGenerating ? <Loader2 size={20} className="animate-spin"/> : <Download size={20} />} 
                    <span className="hidden md:inline">{pdfGenerating ? "Oluşturuluyor..." : "PDF İndir"}</span>
                </button>
                
                <button onClick={fetchData} className="flex items-center gap-2 px-6 py-3 rounded-xl font-bold bg-white text-black hover:bg-gray-200 shadow-[0_0_30px_rgba(255,255,255,0.2)] transition-all text-base">
                    <RefreshCcw size={20} /> <span className="hidden md:inline">Canlı Analiz</span>
                </button>
            </div>
          </div>

          {/* --- KPI KARTLARI (GÜNCELLENDİ: Daha Kompakt ama Net) --- */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
            
            {/* 1. Pazar Sağlığı */}
            <div className={`bg-zinc-900/50 backdrop-blur-xl p-6 rounded-3xl border border-zinc-800 relative overflow-hidden group hover:${marketColor.border} transition-all`}>
               <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity duration-500">
                  <Activity size={100} className={marketColor.text} />
               </div>
               <div className={`absolute -bottom-10 -left-10 w-32 h-32 ${marketColor.glow} blur-[80px] rounded-full transition-all`}></div>
               
               <h3 className="text-gray-400 font-bold text-sm uppercase tracking-widest mb-2">Pazar Sağlığı</h3>
               
               <div className="flex items-end gap-2 mb-4">
                  <span className="text-6xl font-black text-white tracking-tighter leading-none">
                      <AnimatedNumber value={marketHealth} />
                  </span>
                  <span className="text-3xl text-zinc-500 font-bold">/100</span>
               </div>
               
               <div className="w-full bg-zinc-800 h-2 rounded-full overflow-hidden mb-4">
                  <div className={`h-full bg-gradient-to-r ${marketColor.from} ${marketColor.to}`} style={{ width: `${marketHealth}%` }}></div>
               </div>
               
               {/* Açıklama Alanı */}
               <div className="bg-black/20 rounded-xl p-3 border border-white/5">
                   <p className="text-xs font-bold text-white mb-1 uppercase opacity-70">Bu Ne Demek?</p>
                   <p className="text-sm text-gray-300 leading-snug">
                     {marketHealthDesc}
                   </p>
               </div>
            </div>

            {/* 2. Satın Alma */}
            <div className={`bg-zinc-900/50 backdrop-blur-xl p-6 rounded-3xl border border-zinc-800 relative overflow-hidden group hover:${purchaseColor.border} transition-all`}>
               <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity duration-500">
                  <ShoppingCart size={100} className={purchaseColor.text} />
               </div>
               <div className={`absolute -bottom-10 -left-10 w-32 h-32 ${purchaseColor.glow} blur-[80px] rounded-full transition-all`}></div>

               <h3 className="text-gray-400 font-bold text-sm uppercase tracking-widest mb-2">Satın Alma İştahı</h3>
               <div className="flex items-start gap-1 mb-4">
                  <span className="text-3xl text-zinc-500 font-bold mt-2">%</span>
                  <span className="text-6xl font-black text-white tracking-tighter leading-none">
                      <AnimatedNumber value={purchaseIntent} />
                  </span>
               </div>
               <div className="w-full bg-zinc-800 h-2 rounded-full overflow-hidden mb-4">
                  <div className={`h-full bg-gradient-to-r ${purchaseColor.from} ${purchaseColor.to}`} style={{ width: `${purchaseIntent}%` }}></div>
               </div>
               {/* Açıklama Alanı */}
               <div className="bg-black/20 rounded-xl p-3 border border-white/5">
                   <p className="text-xs font-bold text-white mb-1 uppercase opacity-70">Bu Ne Demek?</p>
                   <p className="text-sm text-gray-300 leading-snug">
                     {purchaseIntentDesc}
                   </p>
               </div>
            </div>

            {/* 3. Viral Skor */}
            <div className={`bg-zinc-900/50 backdrop-blur-xl p-6 rounded-3xl border border-zinc-800 relative overflow-hidden group hover:${viralColor.border} transition-all`}>
               <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity duration-500">
                  <Zap size={100} className={viralColor.text} />
               </div>
               <div className={`absolute -bottom-10 -left-10 w-32 h-32 ${viralColor.glow} blur-[80px] rounded-full transition-all`}></div>

               <h3 className="text-gray-400 font-bold text-sm uppercase tracking-widest mb-2">Viral Etki</h3>
               <div className="flex items-start gap-1 mb-4">
                  <span className="text-3xl text-zinc-500 font-bold mt-2">%</span>
                  <span className="text-6xl font-black text-white tracking-tighter leading-none">
                      <AnimatedNumber value={viralScore} />
                  </span>
               </div>
               <div className="w-full bg-zinc-800 h-2 rounded-full overflow-hidden mb-4">
                  <div className={`h-full bg-gradient-to-r ${viralColor.from} ${viralColor.to}`} style={{ width: `${viralScore}%` }}></div>
               </div>
               {/* Açıklama Alanı */}
               <div className="bg-black/20 rounded-xl p-3 border border-white/5">
                   <p className="text-xs font-bold text-white mb-1 uppercase opacity-70">Bu Ne Demek?</p>
                   <p className="text-sm text-gray-300 leading-snug">
                     {viralDesc}
                   </p>
               </div>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            
            {/* --- SOL KOLON --- */}
            <div className="space-y-8">
                
                {/* RADAR CHART */}
                <div className="bg-zinc-900/50 border border-zinc-800 rounded-3xl p-6 relative overflow-hidden">
                    <h3 className="font-bold text-white mb-6 flex items-center gap-2 text-sm uppercase tracking-wider">
                        <Users size={18} className="text-pink-500"/> Pazar Dengesi
                    </h3>
                    <div className="h-[250px] w-full flex justify-center items-center -ml-2">
                        <ResponsiveContainer width="100%" height="100%">
                            <RadarChart cx="50%" cy="50%" outerRadius="75%" data={radarData}>
                                <PolarGrid stroke="#3f3f46" strokeOpacity={0.5} />
                                <PolarAngleAxis dataKey="subject" tick={{ fill: '#d4d4d8', fontSize: 11, fontWeight: 'bold' }} />
                                <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} axisLine={false}/>
                                <Radar name="Skor" dataKey="A" stroke="#db2777" strokeWidth={3} fill="#db2777" fillOpacity={0.4} />
                            </RadarChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* PASTA GRAFİĞİ */}
                <div className="bg-zinc-900/50 border border-zinc-800 rounded-3xl p-6">
                    <h3 className="font-bold text-white mb-6 flex items-center gap-2 text-sm uppercase tracking-wider">
                        <Smile size={18} className="text-yellow-500"/> Duygu Dağılımı
                    </h3>
                    <div className="flex items-center flex-col md:flex-row gap-4">
                        <div className="h-[180px] w-full md:w-1/2">
                            <ResponsiveContainer width="100%" height="100%">
                                <PieChart>
                                    <Pie data={sentimentData} innerRadius={50} outerRadius={75} paddingAngle={6} dataKey="value" stroke="none">
                                        {sentimentData.map((entry:any, index:number) => (
                                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                        ))}
                                    </Pie>
                                </PieChart>
                            </ResponsiveContainer>
                        </div>
                        <div className="w-full md:w-1/2 space-y-2">
                            {analysisData.ana_duygular?.map((d:any, i:number) => (
                                <div key={i} className="flex justify-between items-center text-sm p-2 bg-black/20 rounded-lg">
                                    <span className="text-gray-300 flex items-center gap-2 font-medium">
                                        <div className={`w-3 h-3 rounded-full shadow-[0_0_8px]`} style={{backgroundColor: COLORS[i%3], boxShadow: `0 0 10px ${COLORS[i%3]}`}}></div>
                                        {d.duygu}
                                    </span>
                                    <span className="font-bold text-white bg-zinc-800 px-3 py-0.5 rounded-md">%{d.skor}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                {/* HAVA DURUMU */}
                <div className="bg-gradient-to-br from-blue-900/20 to-zinc-900 border border-blue-500/20 rounded-3xl p-6 relative overflow-hidden">
                    <div className="absolute top-0 right-0 w-32 h-32 bg-blue-500/10 blur-[60px] rounded-full"></div>
                    <h3 className="font-bold text-white mb-4 flex items-center gap-2 text-sm uppercase tracking-wider">
                        <Cloud size={18} className="text-blue-400"/> Dış Faktörler
                    </h3>
                    <div className="flex items-center justify-between mb-6">
                        <div className="flex items-center gap-3">
                            <div className="p-3 bg-zinc-950 rounded-2xl border border-zinc-800">
                                {weatherImpact.icon}
                            </div>
                            <div>
                                <div className="text-4xl font-black text-white">{weatherImpact.temp}°C</div>
                                <div className="text-sm text-gray-400 font-bold">{weatherImpact.condition}</div>
                            </div>
                        </div>
                        <div className="text-right">
                            <div className="text-xs text-gray-500 uppercase font-bold">Rüzgar</div>
                            <div className="text-lg font-bold text-green-400">{weatherData?.windspeed || 0} km/s</div>
                        </div>
                    </div>
                    <div className="p-4 bg-black/30 rounded-xl border border-white/5">
                        <div className="flex items-center gap-2 mb-2">
                            <Thermometer size={16} className="text-gray-400"/>
                            <span className="text-sm font-bold text-white">{weatherImpact.impactTitle}</span>
                        </div>
                        <p className="text-sm text-gray-400 leading-relaxed">
                            {weatherImpact.insight}
                        </p>
                    </div>
                </div>
            </div>

            {/* --- ORTA KOLON --- */}
            <div className="lg:col-span-2 space-y-8">
                
                {/* AI SUMMARY */}
                <div className="bg-gradient-to-br from-zinc-900 via-zinc-900 to-black border border-zinc-800 rounded-3xl p-8 relative overflow-hidden">
                    <div className="absolute top-0 right-0 w-64 h-64 bg-pink-600/5 blur-[120px] rounded-full"></div>
                    
                    <div className="flex flex-col md:flex-row justify-between items-start gap-4 mb-6 relative z-10">
                        <h3 className="text-2xl font-bold text-white flex items-center gap-3">
                            <div className="p-2 bg-pink-500/10 rounded-lg">
                                <Brain className="text-pink-500" size={24}/>
                            </div>
                            Yapay Zeka Yönetici Özeti
                        </h3>
                        {/* GÜNCELLEME: En Baskın Gündem Burada Gösteriliyor */}
                        <div className="bg-pink-600/20 border border-pink-500/30 px-4 py-2 rounded-full">
                            <span className="text-xs text-pink-400 font-bold uppercase tracking-wider mr-2">En Sıcak Konu:</span>
                            <span className="text-white font-bold">{analysisData.baskin_gundemler?.[0]?.konu || "Analiz Ediliyor"}</span>
                        </div>
                    </div>

                    <p className="text-gray-300 leading-loose text-lg font-light relative z-10 border-l-4 border-pink-500/30 pl-6">
                        {analysisData.genel_değerlendirme}
                    </p>
                    
                    <div className="mt-8 pt-8 border-t border-zinc-800/50 grid grid-cols-1 md:grid-cols-2 gap-8 relative z-10">
                        <div className="group p-4 bg-black/20 rounded-2xl border border-white/5 hover:border-pink-500/30 transition-all">
                            <span className="text-xs text-gray-500 uppercase font-bold tracking-wider">Detaylı Gündem</span>
                            <div className="text-white font-bold mt-2 text-xl group-hover:text-pink-400 transition-colors">
                                {analysisData.baskin_gundemler?.[0]?.köken || "Veri bekleniyor..."}
                            </div>
                        </div>
                        <div className="group p-4 bg-black/20 rounded-2xl border border-white/5 hover:border-blue-500/30 transition-all">
                            <span className="text-xs text-gray-500 uppercase font-bold tracking-wider">Sektörel Etki</span>
                            <div className="text-white font-bold mt-2 text-xl group-hover:text-blue-400 transition-colors">
                                {analysisData.harcama_egilimi_analizi?.sektor_etkisi?.split('.')[0] || "Veri Bekleniyor"}
                            </div>
                        </div>
                    </div>
                </div>

                {/* RİSKLER */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="bg-zinc-900/50 border border-zinc-800 rounded-3xl p-6">
                        <h3 className="font-bold text-white mb-6 flex items-center gap-2 text-sm uppercase tracking-wider">
                            <TrendingUp size={18} className="text-blue-500"/> Gelecek Öngörüleri
                        </h3>
                        <div className="space-y-4">
                            {analysisData.gelecek_tahminleri?.map((t:any, i:number) => (
                                <div key={i} className="p-4 bg-black/40 rounded-2xl border border-white/5 hover:border-blue-500/30 transition-all group">
                                    <div className="flex justify-between items-start mb-2">
                                        <span className="text-lg font-bold text-gray-200 group-hover:text-white transition-colors">{t.tahmin}</span>
                                        <span className={`text-[10px] px-3 py-1 rounded-lg font-bold border uppercase tracking-wider ${getRiskColor(t.risk_seviyesi)}`}>
                                            {t.risk_seviyesi} RİSK
                                        </span>
                                    </div>
                                    <p className="text-sm text-gray-500 leading-relaxed">{t.neden}</p>
                                </div>
                            ))}
                        </div>
                    </div>
                    <div className="bg-zinc-900/50 border border-zinc-800 rounded-3xl p-6">
                        <h3 className="font-bold text-white mb-6 flex items-center gap-2 text-sm uppercase tracking-wider">
                            <Users size={18} className="text-purple-500"/> Toplumun Gündemi
                        </h3>
                        <div className="space-y-4">
                            {analysisData.baskin_gundemler?.map((g:any, i:number) => (
                                <div key={i} className="flex gap-4 items-start p-3 hover:bg-white/5 rounded-xl transition-colors border border-transparent hover:border-white/10">
                                    <div className="mt-1 min-w-[32px] h-[32px] rounded-full bg-zinc-800 text-gray-400 border border-zinc-700 flex items-center justify-center text-sm font-bold font-mono">
                                        {i+1}
                                    </div>
                                    <div>
                                        <div className="text-lg font-bold text-white">{g.konu}</div>
                                        <div className="text-sm text-gray-500 leading-snug mt-1">{g.köken}</div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>

          </div>
      </div>
    </div>
  );
}