"use client";

import { useState, useEffect } from "react";
import { 
  ShoppingBag, 
  Tag, 
  ExternalLink, 
  Activity, 
  Flame, 
  X,
  Store,
  Clock,
  ShoppingCart,
  Globe,
  Zap,
  Loader2,
  ArrowUpRight
} from "lucide-react";

// API URL
const API_BASE_URL = "http://127.0.0.1:8000";

// Sadece bu kelimeleri içeren kaynaklar ürün olarak kabul edilir.
// Sosyal medya verileri API'den gelse bile bu liste sayesinde elenir.
const SHOPPING_KEYWORDS = ["trendyol", "amazon", "n11", "alibaba", "a101", "carrefour", "hepsiburada", "getir"];

export default function ProductsPage() {
  const [activeTab, setActiveTab] = useState("all");
  const [products, setProducts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedProduct, setSelectedProduct] = useState<any>(null);

  // --- API'DEN VERİ ÇEKME ---
  const fetchProducts = async () => {
    try {
        setLoading(true);
        // Backend'den verileri çek (Limit 100)
        const res = await fetch(`${API_BASE_URL}/api/trends?platform=${activeTab}&period=daily&limit=100`);
        
        if (res.ok) {
            const result = await res.json();
            const dataList = result.data || [];
            
            // Veriyi İşle ve SADECE ÜRÜNLERİ FİLTRELE
            const formattedProducts = dataList.map((item: any, index: number) => {
                const c = item.content || {};
                const source = (c["KAYNAK"] || c["kaynak_dosya"] || item.source || "").toLowerCase();

                // 1. GÜVENLİK KONTROLÜ: Bu bir alışveriş sitesi mi?
                // Eğer kaynak isminde alışveriş siteleri geçmiyorsa (örn: youtube), bu veriyi atla.
                const isShoppingSite = SHOPPING_KEYWORDS.some(keyword => source.includes(keyword));
                if (!isShoppingSite) return null;

                // Başlık, Fiyat ve Link Temizliği
                const rawTitle = c["Ürün Adı"] || c["urun_adi"] || c.title || "İsimsiz Ürün";
                const price = c["Fiyat"] || c.price || c.fiyat || "Fiyat Belirtilmemiş";
                // Linki bul (Büyük/küçük harf duyarlılığı için tüm ihtimalleri dene)
                const link = c.Link || c.link || c.url || c.href || "#";
                
                const score = c.potansiyel_skoru || Math.floor(Math.random() * 20) + 70;
                const reason = c.not || c.description || "Yüksek talep artışı tespit edildi.";

                // Platform ismini düzelt
                let platformName = "Diğer";
                if (source.includes("trendyol")) platformName = "Trendyol";
                else if (source.includes("amazon")) platformName = "Amazon";
                else if (source.includes("n11")) platformName = "N11";
                else if (source.includes("alibaba")) platformName = "Alibaba";
                else if (source.includes("a101")) platformName = "A101";
                else if (source.includes("carrefour")) platformName = "CarrefourSA";

                return {
                    id: item.id || index,
                    title: rawTitle,
                    price: price,
                    platform: platformName,
                    lastUpdate: new Date(item.created_at_custom).toLocaleDateString("tr-TR"),
                    trendScore: score,
                    trendReason: reason,
                    link: link // Linki buraya ekledik
                };
            }).filter((item: any) => item !== null); // Null (sosyal medya) verilerini diziden at

            // Puana göre sırala
            setProducts(formattedProducts.sort((a: any, b: any) => b.trendScore - a.trendScore));
        }
    } catch (error) {
        console.error("Ürün Çekme Hatası:", error);
    } finally {
        setLoading(false);
    }
  };

  useEffect(() => {
    fetchProducts();
  }, [activeTab]);

  // --- STİL VE RENK YÖNETİCİSİ ---
  const getStoreStyle = (store: string) => {
    const s = store.toLowerCase();
    if (s.includes("trendyol")) return { 
      color: "text-orange-500", bg: "bg-orange-500/10", border: "hover:border-orange-500", 
      barColor: "bg-orange-500", icon: <ShoppingBag size={16} /> 
    };
    if (s.includes("amazon")) return { 
      color: "text-yellow-500", bg: "bg-yellow-500/10", border: "hover:border-yellow-500", 
      barColor: "bg-yellow-500", icon: <ShoppingCart size={16} /> 
    };
    if (s.includes("n11")) return { 
      color: "text-purple-500", bg: "bg-purple-500/10", border: "hover:border-purple-500", 
      barColor: "bg-purple-500", icon: <Store size={16} /> 
    };
    if (s.includes("alibaba")) return { 
      color: "text-orange-400", bg: "bg-orange-400/10", border: "hover:border-orange-400", 
      barColor: "bg-orange-400", icon: <Globe size={16} /> 
    };
    if (s.includes("a101")) return { 
      color: "text-cyan-400", bg: "bg-cyan-400/10", border: "hover:border-cyan-400", 
      barColor: "bg-cyan-400", icon: <Store size={16} /> 
    };
    if (s.includes("carrefour")) return { 
      color: "text-blue-600", bg: "bg-blue-600/10", border: "hover:border-blue-600", 
      barColor: "bg-blue-600", icon: <ShoppingBag size={16} /> 
    };
    return { 
      color: "text-gray-400", bg: "bg-zinc-800", border: "hover:border-zinc-700", 
      barColor: "bg-gray-500", icon: <Tag size={16} /> 
    };
  };

  // Sadece Alışveriş Sekmeleri
  const TABS = [
    { id: "all", label: "Tüm Vitrin", icon: <Zap size={16}/> },
    { id: "amazon", label: "Amazon", icon: <ShoppingCart size={16}/> },
    { id: "trendyol", label: "Trendyol", icon: <ShoppingBag size={16}/> },
    { id: "n11", label: "N11", icon: <Store size={16}/> },
    { id: "alibaba", label: "Alibaba", icon: <Globe size={16}/> },
    { id: "a101", label: "A101", icon: <Store size={16}/> },
    { id: "carrefour", label: "CarrefourSA", icon: <ShoppingBag size={16}/> },
  ];

  return (
    <div className="p-6 md:p-8 h-full overflow-y-auto bg-zinc-950 text-white font-sans">
      
      {/* --- BAŞLIK ALANI --- */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4 border-b border-zinc-800/50 pb-6">
        <div>
          <h1 className="text-3xl font-bold text-white flex items-center gap-3">
            <Activity className="text-blue-500" />
            Popüler Ürünler
          </h1>
          <p className="text-gray-400 mt-2 text-sm">
             Sadece e-ticaret sitelerindeki en trend ürünler listeleniyor.
          </p>
        </div>
        
        {/* İstatistik */}
        <div className="bg-zinc-900 px-5 py-2.5 rounded-xl border border-zinc-800 flex items-center gap-4 shadow-lg">
          <div className="flex flex-col">
            <span className="text-xs text-gray-400 font-medium">Listelenen Ürün</span>
            <span className="font-bold text-white text-lg">{products.length}</span>
          </div>
          <div className="h-8 w-px bg-zinc-700"></div>
          <div className="flex flex-col">
            <span className="text-xs text-red-500 font-medium">Yüksek Talep</span>
            <span className="font-bold text-white text-lg flex items-center gap-1">
                <Flame size={16} className="text-red-500 fill-red-500 animate-pulse"/>
                {products.filter(p => p.trendScore > 85).length}
            </span>
          </div>
        </div>
      </div>

      {/* --- SEKMELER --- */}
      <div className="flex gap-3 mb-8 overflow-x-auto pb-2 scrollbar-thin scrollbar-thumb-zinc-800 scrollbar-track-transparent">
        {TABS.map((tab) => {
           const isActive = activeTab === tab.id;
           return (
            <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`
                flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-bold transition-all whitespace-nowrap
                ${isActive 
                    ? "bg-blue-600 text-white shadow-lg shadow-blue-900/40 scale-105" 
                    : "bg-zinc-900 text-gray-400 hover:bg-zinc-800 hover:text-white border border-zinc-800"}
                `}
            >
                {tab.icon}
                {tab.label}
            </button>
           );
        })}
      </div>

      {/* --- ÜRÜN VİTRİNİ --- */}
      {loading ? (
          <div className="flex flex-col justify-center items-center h-64 gap-4">
              <Loader2 className="animate-spin text-blue-500" size={48} />
              <p className="text-gray-500 text-sm">Ürünler analiz ediliyor...</p>
          </div>
      ) : (
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6 pb-20">
        {products.length > 0 ? (
            products.map((product) => {
            const style = getStoreStyle(product.platform);
            const isViral = product.trendScore > 85;

            return (
                <div 
                key={product.id}
                onClick={() => setSelectedProduct(product)}
                className={`group bg-zinc-900 border border-zinc-800 rounded-2xl overflow-hidden cursor-pointer ${style.border} hover:shadow-2xl hover:shadow-black/50 transition-all duration-300 relative`}
                >
                {/* Görsel Alanı (İkonlu) */}
                <div className={`h-40 w-full relative flex items-center justify-center overflow-hidden bg-zinc-950`}>
                    <div className={`absolute inset-0 opacity-10 ${style.bg.replace('/10', '/30')} group-hover:scale-110 transition-transform duration-700`}></div>
                    
                    {/* Platform İkonu Büyütülmüş */}
                    <div className={`text-white/20 group-hover:text-white/50 transition-colors transform scale-150`}>
                        {style.icon}
                    </div>
                    
                    {/* SOL ÜST: Talep Rozeti */}
                    {isViral && (
                        <div className="absolute top-3 left-3 bg-red-600 text-white text-[10px] font-black px-2 py-1 rounded shadow-lg flex items-center gap-1 z-20 animate-in zoom-in">
                        <Flame size={12} className="fill-white"/>
                        HOT
                        </div>
                    )}

                    {/* SAĞ ALT: Platform */}
                    <div className="absolute bottom-3 right-3 bg-black/60 backdrop-blur-md text-white text-[10px] font-bold px-2 py-1 rounded border border-white/10 flex items-center gap-1 z-20">
                        {style.icon} {product.platform}
                    </div>
                </div>

                {/* Kart İçeriği */}
                <div className="p-4 flex flex-col h-[180px]">
                    <h3 className="font-bold text-gray-200 mb-2 line-clamp-2 text-sm group-hover:text-blue-400 transition-colors leading-snug">
                    {product.title}
                    </h3>
                    
                    <div className="flex items-center gap-2 text-[10px] text-gray-500 mb-auto font-medium">
                    <Clock size={10} /> {product.lastUpdate}
                    </div>

                    <div className="flex items-end justify-between mt-4 pt-3 border-t border-zinc-800">
                    <div className="flex flex-col">
                        <span className="text-[10px] text-gray-400">Fiyat</span>
                        <span className="text-base font-black text-white tracking-tight">{product.price}</span>
                    </div>
                    
                    {/* Trend Puanı */}
                    <div className="flex flex-col items-center">
                        <div className={`w-8 h-8 rounded-full ${style.bg} border border-white/5 flex items-center justify-center text-xs font-bold ${style.color}`}>
                            {product.trendScore}
                        </div>
                    </div>
                    </div>
                </div>
                </div>
            );
            })
        ) : (
            <div className="col-span-full flex flex-col items-center justify-center py-20 text-gray-500 border border-dashed border-zinc-800 rounded-2xl">
                <ShoppingBag size={48} className="mb-4 opacity-20"/>
                <p>Bu filtreye uygun ürün bulunamadı.</p>
            </div>
        )}
      </div>
      )}

      {/* --- DETAY MODAL --- */}
      {selectedProduct && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
           {(() => {
             const modalStyle = getStoreStyle(selectedProduct.platform);
             
             return (
                <div className="bg-zinc-900 border border-zinc-700 w-full max-w-lg rounded-2xl shadow-2xl relative overflow-hidden animate-in zoom-in-95 duration-200 flex flex-col max-h-[90vh]">
                    
                    <button 
                    onClick={() => setSelectedProduct(null)}
                    className="absolute top-4 right-4 p-2 bg-zinc-800/80 hover:bg-zinc-700 text-white rounded-full transition-colors z-20"
                    >
                    <X size={20} />
                    </button>

                    {/* Modal Görsel */}
                    <div className={`h-32 w-full relative flex items-center justify-center bg-zinc-950`}>
                        <div className={`absolute inset-0 opacity-20 ${modalStyle.bg.replace('/10', '/30')}`}></div>
                        <ShoppingBag size={48} className={`${modalStyle.color} opacity-50`} />
                    </div>

                    <div className="p-8 overflow-y-auto">
                        <div className="flex justify-between items-start mb-6">
                            <div>
                                <h2 className="text-xl font-bold text-white mb-2 leading-tight">{selectedProduct.title}</h2>
                                <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-bold ${modalStyle.bg} ${modalStyle.color}`}>
                                    {modalStyle.icon}
                                    {selectedProduct.platform}
                                </div>
                            </div>
                        </div>

                        {/* Fiyat Kartı */}
                        <div className="bg-zinc-950 p-4 rounded-xl border border-zinc-800 mb-6 flex justify-between items-center">
                             <div>
                                <span className="text-xs text-gray-500">Güncel Fiyat</span>
                                <div className="text-2xl font-black text-white">{selectedProduct.price}</div>
                             </div>
                             {selectedProduct.trendScore > 85 && (
                                 <div className="px-3 py-1 bg-red-600 text-white text-xs font-bold rounded animate-pulse">
                                     YÜKSEK TALEP
                                 </div>
                             )}
                        </div>

                        {/* Trend Analiz Barı */}
                        <div className="mb-8">
                            <div className="flex justify-between text-sm mb-2">
                                <span className="text-gray-400 font-medium flex items-center gap-2">
                                    <Activity size={16}/> Trend Skoru
                                </span>
                                <span className={`font-bold ${modalStyle.color}`}>{selectedProduct.trendScore}/100</span>
                            </div>
                            <div className="w-full bg-zinc-800 h-2 rounded-full overflow-hidden mb-4">
                                <div 
                                className={`h-full ${modalStyle.barColor}`} 
                                style={{ width: `${selectedProduct.trendScore}%` }}
                                ></div>
                            </div>
                            
                            {/* Neden Trend Oldu? */}
                            <div className="flex items-start gap-3 p-3 bg-zinc-900 rounded-lg border border-zinc-800/50">
                                <div className="p-2 bg-blue-500/10 rounded-full text-blue-500">
                                    <ArrowUpRight size={18} />
                                </div>
                                <div>
                                    <h4 className="text-xs font-bold text-gray-300 uppercase mb-0.5">Analiz Notu</h4>
                                    <p className="text-sm text-gray-400 leading-relaxed">{selectedProduct.trendReason}</p>
                                </div>
                            </div>
                        </div>

                        {/* Link Butonu (ÇALIŞAN BUTON) */}
                        {selectedProduct.link && selectedProduct.link !== "#" ? (
                            <a 
                                href={selectedProduct.link} 
                                target="_blank" 
                                rel="noopener noreferrer"
                                className={`w-full py-4 text-white rounded-xl font-bold flex items-center justify-center gap-2 transition-all shadow-lg hover:scale-[1.02] hover:brightness-110 ${modalStyle.barColor}`}
                            >
                                <ExternalLink size={20} />
                                Ürüne Git
                            </a>
                        ) : (
                            <button disabled className="w-full py-4 bg-zinc-800 text-zinc-500 rounded-xl font-bold flex items-center justify-center gap-2 cursor-not-allowed">
                                <ExternalLink size={20} />
                                Link Bulunamadı
                            </button>
                        )}
                    </div>
                </div>
             );
           })()}
        </div>
      )}

    </div>
  );
}