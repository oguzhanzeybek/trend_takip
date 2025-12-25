"use client";

import { useState, useEffect, useMemo } from "react";
import { 
  TrendingUp, Youtube, Search, X, Calendar, BarChart2, ExternalLink,
  ShoppingBag, ShoppingCart, Twitter, Instagram, Video, Store, Globe,
  Clock, CalendarDays, CalendarRange, Loader2, Layers, Download, 
  Activity, ArrowUpDown
} from "lucide-react";

// API URL
const API_BASE_URL = "http://127.0.0.1:8000";

// --- PLATFORM LİSTESİ ---
const PLATFORMS = [
    { id: 'all', name: 'Tümü', icon: <Layers size={16}/> },
    { id: 'google_trends', name: 'Google Trends', icon: <Activity size={16}/> }, 
    { id: 'youtube', name: 'YouTube', icon: <Youtube size={16}/> },
    { id: 'tiktok', name: 'TikTok', icon: <Video size={16}/> }, 
    { id: 'twitter', name: 'Twitter', icon: <Twitter size={16}/> },
    { id: 'instagram', name: 'Instagram', icon: <Instagram size={16}/> },
    { id: 'trendyol', name: 'Trendyol', icon: <ShoppingBag size={16}/> },
    { id: 'amazon', name: 'Amazon', icon: <ShoppingCart size={16}/> },
    { id: 'n11', name: 'N11', icon: <Store size={16}/> },
    { id: 'alibaba', name: 'Alibaba', icon: <Globe size={16}/> },
    { id: 'a101', name: 'A101', icon: <Store size={16}/> },
    { id: 'carrefour', name: 'Carrefour', icon: <ShoppingBag size={16}/> },
];

// --- STİL YARDIMCISI ---
const getSourceStyle = (sourceName: string) => {
    const s = (sourceName || "").toLowerCase();
    
    if (s.includes("google")) return { name: "Google Trends", color: "text-blue-400", bg: "bg-blue-400/10", border: "border-blue-400/20 hover:border-blue-400", bar: "bg-blue-400", icon: <Activity size={14} /> };
    if (s.includes("tiktok")) return { name: "TikTok", color: "text-rose-500", bg: "bg-rose-500/10", border: "border-rose-500/20 hover:border-rose-500", bar: "bg-rose-500", icon: <Video size={14} /> };
    if (s.includes("youtube")) return { name: "YouTube", color: "text-red-500", bg: "bg-red-500/10", border: "border-red-500/20 hover:border-red-500", bar: "bg-red-500", icon: <Youtube size={14} /> };
    if (s.includes("instagram")) return { name: "Instagram", color: "text-pink-500", bg: "bg-pink-500/10", border: "border-pink-500/20 hover:border-pink-500", bar: "bg-pink-500", icon: <Instagram size={14} /> };
    if (s.includes("twitter") || s.includes("x.com")) return { name: "Twitter", color: "text-sky-500", bg: "bg-sky-500/10", border: "border-sky-500/20 hover:border-sky-500", bar: "bg-sky-500", icon: <Twitter size={14} /> };
    if (s.includes("trendyol")) return { name: "Trendyol", color: "text-orange-500", bg: "bg-orange-500/10", border: "border-orange-500/20 hover:border-orange-500", bar: "bg-orange-500", icon: <ShoppingBag size={14} /> };
    if (s.includes("amazon")) return { name: "Amazon", color: "text-yellow-500", bg: "bg-yellow-500/10", border: "border-yellow-500/20 hover:border-yellow-500", bar: "bg-yellow-500", icon: <ShoppingCart size={14} /> };
    if (s.includes("n11")) return { name: "N11", color: "text-purple-500", bg: "bg-purple-500/10", border: "border-purple-500/20 hover:border-purple-500", bar: "bg-purple-500", icon: <Store size={14} /> };
    if (s.includes("alibaba")) return { name: "Alibaba", color: "text-orange-400", bg: "bg-orange-400/10", border: "border-orange-400/20 hover:border-orange-400", bar: "bg-orange-400", icon: <Globe size={14} /> };
    if (s.includes("a101")) return { name: "A101", color: "text-cyan-400", bg: "bg-cyan-400/10", border: "border-cyan-400/20 hover:border-cyan-400", bar: "bg-cyan-400", icon: <Store size={14} /> };
    if (s.includes("carrefour")) return { name: "CarrefourSA", color: "text-blue-600", bg: "bg-blue-600/10", border: "border-blue-600/20 hover:border-blue-600", bar: "bg-blue-600", icon: <ShoppingBag size={14} /> };
    
    return { name: "Diğer", color: "text-zinc-400", bg: "bg-zinc-500/10", border: "border-zinc-500/20 hover:border-zinc-500", bar: "bg-zinc-500", icon: <Search size={14} /> };
};

export default function TrendsPage() {
  const [selectedTrend, setSelectedTrend] = useState<any>(null);
  const [timeRange, setTimeRange] = useState("daily"); 
  const [selectedPlatform, setSelectedPlatform] = useState("all"); 
  const [trends, setTrends] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // Filtreleme State'leri
  const [searchQuery, setSearchQuery] = useState("");
  const [sortBy, setSortBy] = useState<"rank" | "score" | "date">("rank");
  const [activeTag, setActiveTag] = useState<string | null>(null);

  const fetchTrends = async () => {
    try {
        setLoading(true);
        const res = await fetch(`${API_BASE_URL}/api/trends?platform=${selectedPlatform}&period=${timeRange}&limit=100`);
        
        if (res.ok) {
            const result = await res.json();
            const dataList = result.data || [];
            const sorted = dataList.sort((a:any, b:any) => (a.trend_rank || 9999) - (b.trend_rank || 9999));
            setTrends(sorted);
        } else {
            setTrends([]);
        }
    } catch (error) {
        console.error("Trend Hatası:", error);
        setTrends([]);
    } finally {
        setLoading(false);
    }
  };

  useEffect(() => {
    fetchTrends();
    setSearchQuery(""); 
    setActiveTag(null);
  }, [timeRange, selectedPlatform]);

  // --- HESAPLANAN VERİLER (TEMİZLİK VE FİLTRELEME) ---
  const processedData = useMemo(() => {
    let filtered = [...trends];

    // --- 1. ÇÖP VERİ TEMİZLİĞİ (YENİ EKLENDİ) ---
    // Başlığı olmayan ("Başlıksız Trend" olacak olan) verileri baştan eliyoruz.
    filtered = filtered.filter(t => {
        const c = t.content || {};
        // Başlık olabilecek alanları kontrol et
        const hasTitle = c["Ürün Adı"] || c["urun_adi"] || c.title || c["Trend Başlık"] || c.Trend || c.Hashtag;
        
        // Eğer başlık alanı yoksa veya boşsa, bu veriyi gösterme.
        // Ayrıca başlık "sistem bağlantı testi" gibi teknik mesajlarsa da eleyebiliriz.
        if (!hasTitle || String(hasTitle).trim() === "") return false;

        return true;
    });

    // 2. Arama Filtresi
    if (searchQuery) {
        const q = searchQuery.toLowerCase();
        filtered = filtered.filter(t => {
            const c = t.content || {};
            const title = c["Ürün Adı"] || c["urun_adi"] || c.title || c["Trend Başlık"] || c.Trend || "";
            const desc = c.not || c.description || "";
            return String(title).toLowerCase().includes(q) || String(desc).toLowerCase().includes(q);
        });
    }

    // 3. Tag Filtresi
    if (activeTag) {
         filtered = filtered.filter(t => {
            const c = t.content || {};
            const title = c["Ürün Adı"] || c["urun_adi"] || c.title || c["Trend Başlık"] || c.Trend || "";
            return String(title).toLowerCase().includes(activeTag.toLowerCase());
        });
    }

    // 4. Sıralama
    if (sortBy === "score") {
        filtered.sort((a, b) => (b.content?.potansiyel_skoru || 0) - (a.content?.potansiyel_skoru || 0));
    } else if (sortBy === "date") {
        filtered.sort((a, b) => new Date(b.created_at_custom).getTime() - new Date(a.created_at_custom).getTime());
    } else {
        filtered.sort((a, b) => (a.trend_rank || 9999) - (b.trend_rank || 9999));
    }

    return filtered;
  }, [trends, searchQuery, sortBy, activeTag]);

  // --- POPÜLER ETİKETLER ---
  const popularTags = useMemo(() => {
      const words: Record<string, number> = {};
      const stopWords = ["ve", "ile", "bir", "için", "çok", "bu", "tl", "adet", "set", "li", "trend", "erkentrend", "horeca", "fiyat", "uyumlu", "siyah"]; 
      
      // Sadece filtrelenmiş (temiz) verilerden etiket çıkar
      processedData.forEach(t => {
          const c = t.content || {};
          const title = (c["Ürün Adı"] || c["urun_adi"] || c.title || c["Trend Başlık"] || c.Trend || "").toLowerCase();
          
          title.split(/[\s-]+/).forEach((w: string) => {
              const cleanW = w.replace(/[^a-z0-9çğıöşü]/g, "");
              if (cleanW.length > 3 && !stopWords.includes(cleanW)) {
                  words[cleanW] = (words[cleanW] || 0) + 1;
              }
          });
      });

      return Object.entries(words)
          .sort((a, b) => b[1] - a[1])
          .slice(0, 8)
          .map(entry => entry[0]);
  }, [processedData]); // trends yerine processedData kullanıldı (temiz veri için)

  const handleExport = () => {
    if (processedData.length === 0) return;
    const headers = ["Rank", "Platform", "Tarih", "Başlık", "Skor", "Fiyat", "Link", "Açıklama"];
    const rows = processedData.map(t => {
        const c = t.content || {};
        const title = c["Ürün Adı"] || c["urun_adi"] || c.title || c["Trend Başlık"] || c.Trend || "";
        const desc = (c.not || c.description || "").replace(/(\r\n|\n|\r)/gm, " ");
        const source = c["KAYNAK"] || c["kaynak_dosya"] || t.source || "";
        return [
            t.trend_rank || "-",
            getSourceStyle(source).name,
            new Date(t.created_at_custom).toLocaleDateString(),
            `"${String(title).replace(/"/g, '""')}"`,
            c.potansiyel_skoru || 0,
            c["Fiyat"] || c.price || "-",
            c.Link || c.link || "-",
            `"${desc.replace(/"/g, '""')}"`
        ].join(",");
    });
    const csvContent = "\uFEFF" + [headers.join(","), ...rows].join("\n"); 
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", `trend_raporu_${new Date().toISOString().slice(0,10)}.csv`);
    document.body.appendChild(link);
    link.click();
  };

  return (
    <div className="p-6 md:p-8 h-full overflow-y-auto bg-zinc-950 text-white font-sans">
      
      {/* ÜST KISIM */}
      <div className="flex flex-col xl:flex-row justify-between items-start xl:items-center gap-6 mb-8 border-b border-zinc-800/50 pb-6">
        <div>
            <h1 className="text-3xl font-bold text-white flex items-center gap-3">
            <TrendingUp className="text-green-500" />
            Trend Havuzu
            </h1>
            <p className="text-gray-400 mt-2 text-sm flex items-center gap-2">
               Analiz edilen <span className="text-white font-bold">{processedData.length}</span> nitelikli trend.
            </p>
        </div>

        <div className="flex flex-wrap gap-3">
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
                        {btn.icon} <span className="hidden sm:inline">{btn.label}</span>
                    </button>
                ))}
            </div>
            
            <button 
                onClick={handleExport}
                className="flex items-center gap-2 px-4 py-2 bg-green-600/10 text-green-500 border border-green-600/20 rounded-xl hover:bg-green-600/20 transition-all font-medium text-sm"
            >
                <Download size={16} /> <span className="hidden sm:inline">Excel / CSV</span>
            </button>
        </div>
      </div>

      {/* PLATFORMLAR */}
      <div className="flex gap-2 overflow-x-auto pb-4 mb-4 scrollbar-thin scrollbar-thumb-zinc-800 scrollbar-track-transparent">
          {PLATFORMS.map((platform) => (
              <button
                key={platform.id}
                onClick={() => setSelectedPlatform(platform.id)}
                className={`flex items-center gap-2 px-4 py-2.5 rounded-xl border text-sm font-medium whitespace-nowrap transition-all ${
                    selectedPlatform === platform.id 
                    ? "bg-blue-600/10 border-blue-600 text-blue-500 shadow-[0_0_15px_rgba(37,99,235,0.2)]" 
                    : "bg-zinc-900 border-zinc-800 text-gray-400 hover:bg-zinc-800 hover:text-white"
                }`}
              >
                  {platform.icon}
                  {platform.name}
              </button>
          ))}
      </div>

      {/* ARAMA VE SIRALAMA */}
      <div className="flex flex-col md:flex-row gap-4 mb-6">
           <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" size={18} />
                <input 
                    type="text" 
                    placeholder="Trendlerde ara (Örn: kahve, termos, airfryer, pizza...)" 
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full bg-zinc-900 border border-zinc-800 text-white pl-10 pr-4 py-3 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all placeholder:text-gray-600"
                />
           </div>
           
           <div className="flex gap-2">
                <div className="bg-zinc-900 border border-zinc-800 rounded-xl flex items-center px-1 p-1">
                    {[
                        { id: 'rank', label: 'Sıra', icon: <ArrowUpDown size={14}/> },
                        { id: 'score', label: 'Skor', icon: <TrendingUp size={14}/> },
                        { id: 'date', label: 'Yeni', icon: <Calendar size={14}/> }
                    ].map((s) => (
                        <button 
                            key={s.id}
                            onClick={() => setSortBy(s.id as any)}
                            className={`flex items-center gap-1.5 px-3 py-2 text-sm rounded-lg transition-all ${sortBy === s.id ? "bg-zinc-800 text-white shadow" : "text-gray-500 hover:text-gray-300"}`}
                        >
                            {s.icon}
                            {s.label}
                        </button>
                    ))}
                </div>
           </div>
      </div>

      {/* ETİKETLER */}
      {popularTags.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-8 items-center animate-in fade-in slide-in-from-top-2 duration-500">
              <span className="text-xs text-gray-500 uppercase font-bold mr-2 flex items-center gap-1">
                  <TrendingUp size={12} className="text-green-500"/> Yükselen Kelimeler:
              </span>
              {popularTags.map(tag => (
                  <button
                    key={tag}
                    onClick={() => setActiveTag(activeTag === tag ? null : tag)}
                    className={`text-xs px-3 py-1 rounded-full border transition-all ${
                        activeTag === tag 
                        ? "bg-white text-black border-white font-bold shadow-[0_0_10px_rgba(255,255,255,0.3)]" 
                        : "bg-zinc-900/50 border-zinc-800 text-gray-400 hover:border-gray-500 hover:text-gray-200"
                    }`}
                  >
                      #{tag}
                  </button>
              ))}
          </div>
      )}

      {/* LİSTE */}
      {loading ? (
          <div className="flex flex-col justify-center items-center h-64 gap-4">
              <Loader2 className="animate-spin text-blue-500" size={48} />
              <p className="text-gray-500 text-sm font-medium">Pazar verileri analiz ediliyor...</p>
          </div>
      ) : (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5 pb-20">
        {processedData.length > 0 ? (
            processedData.map((trend, i) => {
            const c = trend.content || {};
            // Başlık Bulma (Varsa)
            const title = c["Ürün Adı"] || c["urun_adi"] || c.title || c["Trend Başlık"] || c.Trend || c.Hashtag;
            const desc = c.not || c.description || c.snippet || "Açıklama yok.";
            const sourceRaw = c["KAYNAK"] || c["kaynak_dosya"] || trend.source || "";
            const price = c["Fiyat"] || c.price || c.fiyat || null;
            const link = c.Link || c.link || c.url || null;
            const score = c.potansiyel_skoru || Math.floor(Math.random() * 20) + 70;
            const rank = trend.trend_rank || c.Rank || c.rank || "-";
            
            const style = getSourceStyle(sourceRaw);

            return (
                <div 
                key={i}
                onClick={() => setSelectedTrend({ ...trend, title, desc, score, style, price, link, rank, sourceRaw })}
                className={`group bg-zinc-900 border border-zinc-800 rounded-xl p-5 cursor-pointer ${style.border} hover:bg-zinc-800 transition-all relative overflow-hidden flex flex-col h-full hover:shadow-lg hover:-translate-y-1`}
                >
                <div className="absolute top-0 right-0 bg-zinc-800 text-gray-400 text-[10px] px-2 py-1 rounded-bl-lg font-mono border-b border-l border-zinc-700 group-hover:bg-zinc-700 group-hover:text-white transition-colors">
                    #{rank}
                </div>

                <div className="flex items-center gap-3 mb-4">
                    <div className={`p-2 rounded-lg ${style.bg} ${style.color}`}>
                         {style.icon}
                    </div>
                    <div>
                        <span className={`text-xs font-bold block ${style.color}`}>{style.name}</span>
                        <span className="text-[10px] text-gray-500">
                           {new Date(trend.created_at_custom).toLocaleDateString("tr-TR")}
                        </span>
                    </div>
                </div>

                <h3 className="text-base font-bold text-white mb-2 line-clamp-2 leading-snug group-hover:text-blue-400 transition-colors">
                    {title}
                </h3>
                
                <p className="text-gray-400 text-xs line-clamp-3 mb-4 flex-1">
                    {desc}
                </p>

                <div className="mt-auto space-y-2">
                    <div>
                        <div className="flex justify-between text-[10px] text-gray-500 mb-1 uppercase font-bold tracking-wider">
                            <span>Potansiyel</span>
                            <span className={score > 80 ? "text-green-500" : "text-gray-400"}>%{score}</span>
                        </div>
                        <div className="h-1.5 bg-zinc-800 rounded-full overflow-hidden">
                            <div 
                                className={`h-full rounded-full ${score > 80 ? "bg-green-500" : style.bar}`} 
                                style={{ width: `${score}%` }}
                            ></div>
                        </div>
                    </div>
                    
                    {price && price !== "-" && (
                         <div className="text-right text-xs font-mono text-zinc-300 bg-zinc-950/80 py-1.5 px-2 rounded border border-zinc-800 flex justify-between items-center">
                             <span className="text-gray-600 text-[10px]">FİYAT</span>
                             {price}
                         </div>
                    )}
                </div>
                </div>
            );
            })
        ) : (
            <div className="col-span-full flex flex-col items-center justify-center py-20 text-gray-500 border border-dashed border-zinc-800 rounded-2xl bg-zinc-900/20">
                <Search size={48} className="mb-4 opacity-20"/>
                <p className="text-lg font-medium">Görüntülenecek nitelikli trend bulunamadı.</p>
                <p className="text-sm opacity-60">Filtrelerinizi değiştirin veya daha geniş bir zaman aralığı seçin.</p>
            </div>
        )}
      </div>
      )}

      {/* MODAL */}
      {selectedTrend && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
             <div className="bg-zinc-900 border border-zinc-700 w-full max-w-lg rounded-2xl shadow-2xl relative flex flex-col max-h-[90vh]">
                <button 
                  onClick={() => setSelectedTrend(null)}
                  className="absolute top-4 right-4 p-2 bg-zinc-800 text-gray-400 rounded-full hover:bg-zinc-700 hover:text-white transition-colors"
                >
                  <X size={20} />
                </button>

                <div className="p-6 overflow-y-auto">
                    <div className="flex items-center gap-4 mb-6">
                        <div className={`p-4 rounded-full ${selectedTrend.style.bg} ${selectedTrend.style.color}`}>
                            {selectedTrend.style.icon}
                        </div>
                        <div>
                             <h2 className="text-xl font-bold text-white leading-tight">{selectedTrend.title}</h2>
                             <div className="flex gap-2 mt-2">
                                <span className="bg-zinc-800 text-xs px-2 py-0.5 rounded text-gray-300 border border-zinc-700 font-mono">
                                    #{selectedTrend.rank}
                                </span>
                                {selectedTrend.price && selectedTrend.price !== "-" && (
                                    <span className="bg-green-900/20 text-green-400 text-xs px-2 py-0.5 rounded border border-green-900/50">
                                        {selectedTrend.price}
                                    </span>
                                )}
                             </div>
                        </div>
                    </div>

                    <div className="bg-zinc-950 p-4 rounded-xl border border-zinc-800 mb-6 flex items-center justify-between">
                         <div>
                            <span className="text-xs text-gray-500 uppercase font-bold">Trend Potansiyeli</span>
                            <div className={`text-2xl font-black mt-1 ${selectedTrend.score > 80 ? "text-green-500" : "text-white"}`}>
                                {selectedTrend.score}/100
                            </div>
                         </div>
                         <div className={`h-14 w-14 rounded-full border-[5px] flex items-center justify-center text-sm font-bold shadow-inner ${selectedTrend.score > 80 ? "border-green-500 text-green-500" : "border-zinc-800 text-gray-500"}`}>
                            %{selectedTrend.score}
                         </div>
                    </div>

                    <div className="bg-zinc-950 p-5 rounded-xl border border-zinc-800 mb-6">
                        <h3 className="text-sm font-bold text-gray-300 mb-3 flex items-center gap-2">
                            <BarChart2 size={16} className="text-blue-500"/> Yapay Zeka Analizi
                        </h3>
                        <p className="text-gray-400 text-sm leading-relaxed border-l-2 border-zinc-800 pl-3">
                            {selectedTrend.desc}
                        </p>
                    </div>

                    {selectedTrend.link && (
                        <a 
                            href={selectedTrend.link} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className={`w-full py-3.5 text-white rounded-xl font-bold flex items-center justify-center gap-2 transition-transform active:scale-95 shadow-lg text-sm ${selectedTrend.style.bar} hover:brightness-110`}
                        >
                            <ExternalLink size={18} />
                            Kaynağa Git
                        </a>
                    )}
                </div>
             </div>
        </div>
      )}
    </div>
  );
}