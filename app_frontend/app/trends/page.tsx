"use client";

import { useState, useEffect } from "react";
import { 
  TrendingUp, Youtube, Search, X, Calendar, BarChart2, ExternalLink,
  ShoppingBag, ShoppingCart, Twitter, Instagram, Video, Store, Globe,
  Clock, CalendarDays, CalendarRange, Loader2
} from "lucide-react";

// API URL (Backend adresin)
const API_BASE_URL = "http://127.0.0.1:8000";

// --- RENK VE İKON BELİRLEYİCİ ---
const getSourceStyle = (sourceName: string) => {
    const s = (sourceName || "").toLowerCase();
    
    if (s.includes("youtube")) return { 
        name: "YouTube", color: "text-red-500", bg: "bg-red-500/10", border: "border-red-500/20 hover:border-red-500", 
        bar: "bg-red-500", icon: <Youtube size={14} />, modalIcon: <Youtube size={32} /> 
    };
    if (s.includes("instagram")) return { 
        name: "Instagram", color: "text-pink-500", bg: "bg-pink-500/10", border: "border-pink-500/20 hover:border-pink-500", 
        bar: "bg-pink-500", icon: <Instagram size={14} />, modalIcon: <Instagram size={32} /> 
    };
    if (s.includes("twitter")) return { 
        name: "Twitter", color: "text-sky-500", bg: "bg-sky-500/10", border: "border-sky-500/20 hover:border-sky-500", 
        bar: "bg-sky-500", icon: <Twitter size={14} />, modalIcon: <Twitter size={32} /> 
    };
    if (s.includes("tiktok")) return { 
        name: "TikTok", color: "text-rose-500", bg: "bg-rose-500/10", border: "border-rose-500/20 hover:border-rose-500", 
        bar: "bg-rose-500", icon: <Video size={14} />, modalIcon: <Video size={32} /> 
    };
    if (s.includes("trendyol")) return { 
        name: "Trendyol", color: "text-orange-500", bg: "bg-orange-500/10", border: "border-orange-500/20 hover:border-orange-500", 
        bar: "bg-orange-500", icon: <ShoppingBag size={14} />, modalIcon: <ShoppingBag size={32} /> 
    };
    if (s.includes("amazon")) return { 
        name: "Amazon", color: "text-yellow-500", bg: "bg-yellow-500/10", border: "border-yellow-500/20 hover:border-yellow-500", 
        bar: "bg-yellow-500", icon: <ShoppingCart size={14} />, modalIcon: <ShoppingCart size={32} /> 
    };
    if (s.includes("n11")) return { 
        name: "N11", color: "text-purple-500", bg: "bg-purple-500/10", border: "border-purple-500/20 hover:border-purple-500", 
        bar: "bg-purple-500", icon: <Store size={14} />, modalIcon: <Store size={32} /> 
    };
    if (s.includes("a101")) return { 
        name: "A101", color: "text-cyan-400", bg: "bg-cyan-400/10", border: "border-cyan-400/20 hover:border-cyan-400", 
        bar: "bg-cyan-400", icon: <Store size={14} />, modalIcon: <Store size={32} /> 
    };
    if (s.includes("carrefour")) return { 
        name: "CarrefourSA", color: "text-blue-600", bg: "bg-blue-600/10", border: "border-blue-600/20 hover:border-blue-600", 
        bar: "bg-blue-600", icon: <ShoppingBag size={14} />, modalIcon: <ShoppingBag size={32} /> 
    };
    if (s.includes("alibaba")) return { 
        name: "Alibaba", color: "text-orange-400", bg: "bg-orange-400/10", border: "border-orange-400/20 hover:border-orange-400", 
        bar: "bg-orange-400", icon: <Globe size={14} />, modalIcon: <Globe size={32} /> 
    };
    
    // Varsayılan Stil
    return { 
        name: sourceName || "Diğer", color: "text-blue-500", bg: "bg-blue-500/10", border: "border-blue-500/20 hover:border-blue-500", 
        bar: "bg-blue-500", icon: <Search size={14} />, modalIcon: <Search size={32} /> 
    };
};

export default function TrendsPage() {
  const [selectedTrend, setSelectedTrend] = useState<any>(null);
  const [timeRange, setTimeRange] = useState("daily"); 
  const [trends, setTrends] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // API'den Veri Çek
  const fetchTrends = async () => {
    try {
        setLoading(true);
        const res = await fetch(`${API_BASE_URL}/api/top-trends?period=${timeRange}`);
        if (res.ok) {
            const result = await res.json();
            // Backend'den gelen veri 'data' anahtarında olabilir
            const dataList = result.data || [];
            
            // Skora göre sırala (Yüksekten düşüğe)
            const sorted = dataList.sort((a:any, b:any) => b.score - a.score);
            setTrends(sorted);
        }
    } catch (error) {
        console.error("Trend Hatası:", error);
    } finally {
        setLoading(false);
    }
  };

  useEffect(() => {
    fetchTrends();
  }, [timeRange]);

  return (
    <div className="p-8 h-full overflow-y-auto bg-zinc-950 text-white font-sans">
      
      {/* --- BAŞLIK VE FİLTRE --- */}
      <div className="flex flex-col xl:flex-row justify-between items-start xl:items-center gap-4 mb-8">
        <div>
            <h1 className="text-3xl font-bold text-white flex items-center gap-3">
            <TrendingUp className="text-green-500" />
            Trend Havuzu
            </h1>
            <p className="text-gray-400 mt-2 flex items-center gap-2">
               Analiz edilen 
               <span className="bg-zinc-800 text-white px-2 py-0.5 rounded text-xs border border-zinc-700 font-mono">
                 {loading ? "..." : trends.length}
               </span> 
               veri arasından en popülerler listeleniyor.
            </p>
        </div>

        <div className="bg-zinc-900 p-1 rounded-xl border border-zinc-800 flex items-center shadow-lg">
            {[
                { id: 'daily', label: 'Günlük', icon: <Clock size={14} /> },
                { id: 'weekly', label: 'Haftalık', icon: <CalendarDays size={14} /> },
                { id: 'monthly', label: 'Aylık', icon: <CalendarRange size={14} /> }
            ].map((btn) => (
                <button 
                    key={btn.id}
                    onClick={() => setTimeRange(btn.id)}
                    className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${timeRange === btn.id ? 'bg-zinc-800 text-white shadow-sm ring-1 ring-zinc-700' : 'text-gray-500 hover:text-gray-300'}`}
                >
                    {btn.icon} {btn.label}
                </button>
            ))}
        </div>
      </div>

      {/* --- YÜKLENİYOR VEYA LİSTE --- */}
      {loading ? (
          <div className="flex flex-col justify-center items-center h-64 gap-4">
              <Loader2 className="animate-spin text-blue-500" size={48} />
              <p className="text-gray-500 text-sm">Trendler analiz ediliyor...</p>
          </div>
      ) : (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 pb-20">
        {trends.length > 0 ? (
            trends.map((trend, i) => {
            const style = getSourceStyle(trend.source);
            
            return (
                <div 
                key={i}
                onClick={() => setSelectedTrend(trend)}
                className={`group bg-zinc-900 border border-zinc-800 rounded-xl p-6 cursor-pointer ${style.border} hover:bg-zinc-800/80 transition-all duration-300 relative overflow-hidden shadow-sm hover:shadow-md h-full flex flex-col`}
                >
                {/* Arka Plan Efekti */}
                <div className={`absolute top-0 right-0 w-24 h-24 rounded-full blur-3xl -mr-10 -mt-10 transition-all opacity-10 group-hover:opacity-30 ${style.bg.replace('/10', '/30')}`}></div>

                {/* Üst Bilgi (Kaynak ve Tarih) */}
                <div className="flex justify-between items-start mb-4">
                    <span className={`px-3 py-1.5 rounded-full text-xs font-bold flex items-center gap-1.5 ${style.bg} ${style.color} border border-white/5`}>
                    {style.icon}
                    {style.name}
                    </span>
                    <span className="text-gray-500 text-[10px] flex items-center gap-1 bg-zinc-950 px-2 py-1 rounded border border-zinc-800/50">
                    <Calendar size={10} /> {trend.date || "Bugün"}
                    </span>
                </div>

                {/* Başlık */}
                <h3 className={`text-lg font-bold text-white mb-3 line-clamp-2 leading-tight group-hover:${style.color} transition-colors`}>
                    {trend.title}
                </h3>
                
                {/* Açıklama */}
                <p className="text-gray-400 text-xs line-clamp-3 mb-6 leading-relaxed">
                    {trend.description}
                </p>

                {/* Skor Barı */}
                <div className="flex items-center gap-3 mt-auto pt-4 border-t border-zinc-800/50">
                    <div className="flex-1 bg-zinc-950 h-2 rounded-full overflow-hidden border border-zinc-800">
                    <div 
                        className={`h-full transition-all duration-1000 ease-out ${trend.score > 90 ? 'bg-green-500 shadow-[0_0_10px_rgba(34,197,94,0.5)]' : style.bar}`} 
                        style={{ width: `${trend.score}%` }}
                    ></div>
                    </div>
                    <span className={`text-xs font-bold ${trend.score > 90 ? 'text-green-500' : 'text-white'}`}>
                        %{trend.score}
                    </span>
                </div>
                </div>
            );
            })
        ) : (
            <div className="col-span-full flex flex-col items-center justify-center py-20 text-gray-500 border border-dashed border-zinc-800 rounded-2xl">
                <Search size={48} className="mb-4 opacity-20"/>
                <p>Bu filtreye uygun trend bulunamadı.</p>
            </div>
        )}
      </div>
      )}

      {/* --- DETAY MODALI --- */}
      {selectedTrend && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-in fade-in duration-200">
            {(() => {
                const modalStyle = getSourceStyle(selectedTrend.source);
                return (
                  <div className="bg-zinc-900 border border-zinc-700 w-full max-w-2xl rounded-2xl shadow-2xl relative overflow-hidden animate-in zoom-in-95 duration-200 flex flex-col max-h-[90vh]">
                    
                    <button 
                      onClick={() => setSelectedTrend(null)}
                      className="absolute top-4 right-4 p-2 bg-zinc-800 text-gray-400 rounded-full hover:bg-zinc-700 hover:text-white transition-colors z-10"
                    >
                      <X size={20} />
                    </button>

                    <div className="p-8 overflow-y-auto">
                      {/* Modal Başlık */}
                      <div className="flex items-center gap-4 mb-6">
                        <div className={`p-4 rounded-xl ${modalStyle.bg} ${modalStyle.color}`}>
                            {modalStyle.modalIcon}
                        </div>
                        <div>
                            <h2 className="text-2xl font-bold text-white leading-tight">{selectedTrend.title}</h2>
                            <span className="text-gray-400 text-sm mt-1 block flex items-center gap-2">
                                <Calendar size={14}/> Tespit: {selectedTrend.date}
                            </span>
                        </div>
                      </div>

                      {/* Modal Skor ve Kaynak */}
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                         <div className="bg-zinc-950 p-4 rounded-xl border border-zinc-800">
                            <span className="text-xs text-gray-500 uppercase font-bold">Trend Skoru</span>
                            <div className="text-3xl font-black text-white mt-1">
                                {selectedTrend.score}<span className="text-sm text-gray-600 font-medium">/100</span>
                            </div>
                         </div>
                         <div className="bg-zinc-950 p-4 rounded-xl border border-zinc-800">
                            <span className="text-xs text-gray-500 uppercase font-bold">Platform</span>
                            <div className="text-xl font-bold text-white mt-1 flex items-center gap-2">
                                {modalStyle.name} <span className="px-2 py-0.5 rounded bg-zinc-800 text-[10px] text-gray-400 font-mono">TR</span>
                            </div>
                         </div>
                      </div>

                      {/* Modal İçerik */}
                      <div className="mb-8 bg-zinc-950/50 p-6 rounded-xl border border-zinc-800/50">
                        <h3 className={`text-lg font-bold mb-3 flex items-center gap-2 ${modalStyle.color}`}>
                          <BarChart2 size={20} />
                          Analiz Raporu
                        </h3>
                        <p className="text-gray-300 leading-relaxed text-sm">
                          {selectedTrend.description}
                        </p>
                      </div>

                      {/* Alt Butonlar */}
                      <div className="flex justify-end gap-3 pt-4 border-t border-zinc-800">
                        <button 
                            onClick={() => setSelectedTrend(null)}
                            className="px-6 py-2.5 rounded-lg text-gray-400 hover:text-white hover:bg-zinc-800 transition-colors font-medium text-sm"
                        >
                            Kapat
                        </button>
                        <button className={`px-6 py-2.5 text-white rounded-lg font-bold flex items-center gap-2 transition-transform active:scale-95 shadow-lg text-sm ${modalStyle.color.replace('text-', 'bg-')} hover:brightness-110`}>
                          <ExternalLink size={16} />
                          Kaynağa Git
                        </button>
                      </div>

                    </div>
                  </div>
                );
            })()}
        </div>
      )}
    </div>
  );
}