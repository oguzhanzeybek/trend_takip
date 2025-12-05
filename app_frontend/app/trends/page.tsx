"use client";

import { useState, useMemo } from "react";
import { 
  TrendingUp, 
  Youtube, 
  Search, 
  X, 
  Calendar, 
  BarChart2, 
  ExternalLink,
  ShoppingBag, 
  ShoppingCart,
  Twitter,
  Instagram,
  Video,
  Store,
  Globe,
  Filter,
  Clock,
  CalendarDays,
  CalendarRange
} from "lucide-react";

// --- GELİŞMİŞ VERİ ÜRETİCİSİ ---
const generateMockTrends = (count: number) => {
  const sources = ["Google", "YouTube", "Twitter", "Instagram", "TikTok", "Trendyol", "Amazon", "N11", "Alibaba", "A101", "CarrefourSA"];
  const periods = ["daily", "weekly", "monthly"];
  
  const templates = [
    { t: "Fiyat İndirimi", d: "Bu ürün grubunda son 24 saatte ciddi bir fiyat düşüşü tespit edildi." },
    { t: "Viral Akım", d: "Sosyal medya etkileşimleri %300 artış gösterdi, paylaşım rekoru kırılıyor." },
    { t: "Stok Uyarısı", d: "Ürüne olan yoğun talep nedeniyle stoklar hızla tükeniyor, acele edilmeli." },
    { t: "Gündem Analizi", d: "Kullanıcıların arama hacmi bu konu üzerinde yoğunlaştı." },
    { t: "Yeni Sezon", d: "Koleksiyonun yayınlanmasıyla birlikte tıklama oranları zirve yaptı." },
    { t: "Yatırım Fırsatı", d: "Finansal veriler bu başlıkta yukarı yönlü bir ivme olduğunu gösteriyor." }
  ];

  const subjects = [
    "iPhone 15", "Altın Piyasası", "Dolar Kuru", "Seçim Anketi", "Robot Süpürge", 
    "Yaz Tatili", "Kış Lastiği", "Okul Çantası", "Protein Tozu", "Stanley Termos",
    "Airfryer", "PlayStation 5", "Şampiyonlar Ligi", "Survivor", "MasterChef"
  ];

  return Array.from({ length: count }).map((_, i) => {
    const randomSource = sources[Math.floor(Math.random() * sources.length)];
    const randomPeriod = periods[Math.floor(Math.random() * periods.length)];
    const template = templates[Math.floor(Math.random() * templates.length)];
    const subject = subjects[Math.floor(Math.random() * subjects.length)];
    const randomScore = Math.floor(Math.random() * (100 - 45 + 1)) + 45; 

    return {
      id: i + 1,
      title: `${subject} ${template.t} #${i + 100}`, 
      score: randomScore,
      source: randomSource,
      date: "05.12.2025",
      period: randomPeriod,
      description: template.d, // Daha mantıklı açıklamalar
      keywords: ["trend", "gündem", randomSource.toLowerCase(), subject.toLowerCase().split(' ')[0]]
    };
  });
};

const MOCK_TRENDS = generateMockTrends(150);

export default function TrendsPage() {
  const [selectedTrend, setSelectedTrend] = useState<any>(null);
  const [timeRange, setTimeRange] = useState("daily"); 

  const displayedTrends = useMemo(() => {
    const filtered = MOCK_TRENDS.filter(trend => trend.period === timeRange);
    return filtered.sort((a, b) => b.score - a.score);
  }, [timeRange]);

  // --- RENK DÜZELTMESİ ---
  // Tailwind'in renkleri algılaması için "barColor" olarak tam sınıf ismini yazdık.
  const getSourceStyle = (source: string) => {
    switch (source) {
      case "YouTube": return { 
        color: "text-red-500", bg: "bg-red-500/10", border: "hover:border-red-500", 
        barColor: "bg-red-500", // <-- ARTIK ÇALIŞACAK
        icon: <Youtube size={14} />, modalIcon: <Youtube size={32} /> 
      };
      case "Instagram": return { 
        color: "text-pink-500", bg: "bg-pink-500/10", border: "hover:border-pink-500", 
        barColor: "bg-pink-500", 
        icon: <Instagram size={14} />, modalIcon: <Instagram size={32} /> 
      };
      case "Twitter": return { 
        color: "text-sky-500", bg: "bg-sky-500/10", border: "hover:border-sky-500", 
        barColor: "bg-sky-500", 
        icon: <Twitter size={14} />, modalIcon: <Twitter size={32} /> 
      };
      case "TikTok": return { 
        color: "text-rose-500", bg: "bg-rose-500/10", border: "hover:border-rose-500", 
        barColor: "bg-rose-500", 
        icon: <Video size={14} />, modalIcon: <Video size={32} /> 
      };
      case "Trendyol": return { 
        color: "text-orange-500", bg: "bg-orange-500/10", border: "hover:border-orange-500", 
        barColor: "bg-orange-500", 
        icon: <ShoppingBag size={14} />, modalIcon: <ShoppingBag size={32} /> 
      };
      case "Amazon": return { 
        color: "text-yellow-500", bg: "bg-yellow-500/10", border: "hover:border-yellow-500", 
        barColor: "bg-yellow-500", 
        icon: <ShoppingCart size={14} />, modalIcon: <ShoppingCart size={32} /> 
      };
      case "N11": return { 
        color: "text-purple-500", bg: "bg-purple-500/10", border: "hover:border-purple-500", 
        barColor: "bg-purple-500", 
        icon: <Store size={14} />, modalIcon: <Store size={32} /> 
      };
      case "Alibaba": return { 
        color: "text-orange-400", bg: "bg-orange-400/10", border: "hover:border-orange-400", 
        barColor: "bg-orange-400", 
        icon: <Globe size={14} />, modalIcon: <Globe size={32} /> 
      };
      case "A101": return { 
        color: "text-cyan-400", bg: "bg-cyan-400/10", border: "hover:border-cyan-400", 
        barColor: "bg-cyan-400", 
        icon: <Store size={14} />, modalIcon: <Store size={32} /> 
      };
      case "CarrefourSA": return { 
        color: "text-blue-600", bg: "bg-blue-600/10", border: "hover:border-blue-600", 
        barColor: "bg-blue-600", 
        icon: <ShoppingBag size={14} />, modalIcon: <ShoppingBag size={32} /> 
      };
      default: return { 
        color: "text-blue-500", bg: "bg-blue-500/10", border: "hover:border-blue-500", 
        barColor: "bg-blue-500", 
        icon: <Search size={14} />, modalIcon: <Search size={32} /> 
      };
    }
  };

  return (
    <div className="p-8 h-full overflow-y-auto">
      
      {/* BAŞLIK */}
      <div className="flex flex-col xl:flex-row justify-between items-start xl:items-center gap-4 mb-8">
        <div>
            <h1 className="text-3xl font-bold text-white flex items-center gap-3">
            <TrendingUp className="text-green-500" />
            Trend Havuzu
            </h1>
            <p className="text-gray-400 mt-2 flex items-center gap-2">
               Şu an analiz edilen 
               <span className="bg-zinc-800 text-white px-2 py-0.5 rounded text-xs border border-zinc-700 font-mono">
                 {MOCK_TRENDS.length}
               </span> 
               veri arasından gösteriliyor.
            </p>
        </div>

        {/* FİLTRE */}
        <div className="bg-zinc-900 p-1 rounded-xl border border-zinc-800 flex items-center shadow-lg shadow-black/50">
            <button 
                onClick={() => setTimeRange("daily")}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${timeRange === 'daily' ? 'bg-zinc-800 text-white shadow-sm ring-1 ring-zinc-700' : 'text-gray-500 hover:text-gray-300'}`}
            >
                <Clock size={14} />
                Günlük
            </button>
            <div className="w-px h-4 bg-zinc-800 mx-1"></div>
            <button 
                onClick={() => setTimeRange("weekly")}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${timeRange === 'weekly' ? 'bg-zinc-800 text-white shadow-sm ring-1 ring-zinc-700' : 'text-gray-500 hover:text-gray-300'}`}
            >
                <CalendarDays size={14} />
                Haftalık
            </button>
            <div className="w-px h-4 bg-zinc-800 mx-1"></div>
            <button 
                onClick={() => setTimeRange("monthly")}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${timeRange === 'monthly' ? 'bg-zinc-800 text-white shadow-sm ring-1 ring-zinc-700' : 'text-gray-500 hover:text-gray-300'}`}
            >
                <CalendarRange size={14} />
                Aylık
            </button>
        </div>
      </div>

      {/* LİSTE */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 pb-20">
        {displayedTrends.length > 0 ? (
            displayedTrends.map((trend) => {
            const style = getSourceStyle(trend.source);
            
            return (
                <div 
                key={trend.id}
                onClick={() => setSelectedTrend(trend)}
                className={`group bg-zinc-900 border border-zinc-800 rounded-xl p-6 cursor-pointer ${style.border} hover:bg-zinc-800/80 transition-all duration-300 relative overflow-hidden shadow-sm hover:shadow-md`}
                >
                <div className={`absolute top-0 right-0 w-24 h-24 rounded-full blur-3xl -mr-10 -mt-10 transition-all opacity-10 group-hover:opacity-30 ${style.bg.replace('/10', '/30')}`}></div>

                <div className="flex justify-between items-start mb-4">
                    <span className={`px-3 py-1.5 rounded-full text-xs font-bold flex items-center gap-1.5 ${style.bg} ${style.color}`}>
                    {style.icon}
                    {trend.source}
                    </span>
                    <span className="text-gray-500 text-xs flex items-center gap-1 bg-zinc-950 px-2 py-1 rounded border border-zinc-800/50">
                    <Calendar size={12} /> {trend.date}
                    </span>
                </div>

                <h3 className={`text-xl font-bold text-white mb-3 line-clamp-2 leading-tight group-hover:${style.color} transition-colors`}>
                    {trend.title}
                </h3>
                
                <p className="text-gray-400 text-sm line-clamp-3 mb-6 leading-relaxed">
                    {trend.description}
                </p>

                {/* DÜZELTİLEN SKOR BARI */}
                <div className="flex items-center gap-3 mt-auto pt-4 border-t border-zinc-800/50">
                    <div className="flex-1 bg-zinc-950 h-2.5 rounded-full overflow-hidden border border-zinc-800">
                    <div 
                        // Burada style.barColor doğrudan kullanılıyor, replace yapılmıyor
                        className={`h-full transition-all duration-500 ${trend.score > 90 ? 'bg-green-500 shadow-[0_0_10px_rgba(34,197,94,0.5)]' : style.barColor}`} 
                        style={{ width: `${trend.score}%` }}
                    ></div>
                    </div>
                    <span className={`text-sm font-bold ${trend.score > 90 ? 'text-green-500' : 'text-white'}`}>
                        %{trend.score}
                    </span>
                </div>
                </div>
            );
            })
        ) : (
            <div className="col-span-full flex flex-col items-center justify-center py-20 text-gray-500">
                <Search size={48} className="mb-4 opacity-20"/>
                <p>Bu filtreye uygun trend bulunamadı.</p>
            </div>
        )}
      </div>

      {/* MODAL */}
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
                      <div className="flex items-center gap-4 mb-6">
                        <div className={`p-4 rounded-xl ${modalStyle.bg} ${modalStyle.color}`}>
                            {modalStyle.modalIcon}
                        </div>
                        <div>
                            <h2 className="text-2xl font-bold text-white leading-tight">{selectedTrend.title}</h2>
                            <span className="text-gray-400 text-sm mt-1 block">Tespit Tarihi: {selectedTrend.date}</span>
                        </div>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                        <div className="bg-zinc-950 p-5 rounded-xl border border-zinc-800">
                          <h4 className="text-gray-400 text-xs uppercase mb-2 font-bold tracking-wider">Trend Skoru</h4>
                          <div className="flex items-end gap-2">
                            <span className="text-5xl font-black text-green-500 tracking-tighter">{selectedTrend.score}</span>
                            <span className="text-gray-500 mb-2 font-medium">/ 100</span>
                          </div>
                        </div>
                        <div className="bg-zinc-950 p-5 rounded-xl border border-zinc-800">
                          <h4 className="text-gray-400 text-xs uppercase mb-2 font-bold tracking-wider">Platform</h4>
                          <div className="flex items-center gap-2 mt-2">
                            <span className="text-xl font-medium text-white">{selectedTrend.source}</span>
                            <span className="text-xs px-2 py-1 bg-zinc-800 rounded text-gray-400">TR</span>
                          </div>
                        </div>
                      </div>

                      <div className="mb-8 bg-zinc-950/50 p-6 rounded-xl border border-zinc-800/50">
                        <h3 className={`text-lg font-bold mb-3 flex items-center gap-2 ${modalStyle.color}`}>
                          <BarChart2 size={20} />
                          Analiz Raporu
                        </h3>
                        <p className="text-gray-300 leading-relaxed text-lg">
                          {selectedTrend.description}
                        </p>
                      </div>

                      <div className="flex flex-wrap gap-2 mb-8">
                        {selectedTrend.keywords.map((kw: string, index: number) => (
                          <span key={index} className="px-4 py-1.5 bg-zinc-800 hover:bg-zinc-700 text-gray-300 text-sm rounded-full border border-zinc-700 transition-colors cursor-default">
                            #{kw}
                          </span>
                        ))}
                      </div>

                      <div className="flex justify-end gap-3 pt-4 border-t border-zinc-800">
                        <button 
                          onClick={() => setSelectedTrend(null)}
                          className="px-6 py-2.5 rounded-lg text-gray-400 hover:text-white hover:bg-zinc-800 transition-colors font-medium"
                        >
                          Kapat
                        </button>
                        <button className={`px-8 py-2.5 text-white rounded-lg font-bold flex items-center gap-2 transition-transform active:scale-95 shadow-lg ${modalStyle.color.replace('text-', 'bg-')} hover:brightness-110`}>
                          <ExternalLink size={18} />
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