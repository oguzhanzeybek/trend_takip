"use client";

import { useState, useMemo } from "react";
import { 
  ShoppingBag, 
  Tag, 
  ExternalLink, 
  Activity, // Trend aktivitesi için
  Flame,    // Çok talep görenler için
  Filter, 
  X,
  Store,
  Clock,
  ShoppingCart,
  Globe,
  Zap,
  Eye,      // Görüntülenme sayısı için
  ArrowUpRight
} from "lucide-react";

// --- OTOMATİK TREND ÜRÜN VERİSİ ---
// İndirim yok, sadece popülerlik ve talep var.
const generateMockProducts = (count: number) => {
  const platforms = ["Trendyol", "Amazon", "N11", "Alibaba", "A101", "CarrefourSA"];
  const categories = ["Teknoloji", "Moda", "Ev", "Kozmetik", "Otomotiv"];
  
  const productNames = [
    "Dyson Airwrap", "Stanley Quencher Termos", "iPhone 15 Pro Max", "Adidas Samba", 
    "Sony PlayStation 5", "Fujifilm Instax Mini", "Nespresso Kahve Makinesi", "Crocs Terlik",
    "JBL Flip 6 Hoparlör", "Kindle Paperwhite", "Lululemon Tayt", "The North Face Mont",
    "Xiaomi Air Fryer", "Apple Watch Ultra 2", "Nike Dunk Low", "Sol De Janeiro Parfüm"
  ];

  return Array.from({ length: count }).map((_, i) => {
    const platform = platforms[Math.floor(Math.random() * platforms.length)];
    const category = categories[Math.floor(Math.random() * categories.length)];
    const name = productNames[Math.floor(Math.random() * productNames.length)];
    
    // Trend Metrikleri
    const trendScore = Math.floor(Math.random() * (100 - 65 + 1)) + 65; // 65-100 arası yüksek puan
    const views = Math.floor(Math.random() * 5000) + 500; // Anlık görüntülenme
    const price = Math.floor(Math.random() * 45000) + 500;

    return {
      id: i + 1,
      title: `${name} #${i+1}`,
      category: category,
      price: price,
      platform: platform,
      lastUpdate: `${Math.floor(Math.random() * 20) + 1} dk önce`,
      trendScore: trendScore,
      views: views,
      // Trend Sebebi (Modalda görünecek)
      trendReason: [
        "Sosyal medyada viral oldu", 
        "Stokları hızla tükeniyor", 
        "Mevsimsel talep artışı", 
        "Influencer paylaşımları arttı"
      ][Math.floor(Math.random() * 4)]
    };
  });
};

const MOCK_PRODUCTS = generateMockProducts(120);

export default function ProductsPage() {
  const [activeTab, setActiveTab] = useState("all");
  const [selectedProduct, setSelectedProduct] = useState<any>(null);

  // --- STİL VE RENK YÖNETİCİSİ (Aynı kaldı) ---
  const getStoreStyle = (store: string) => {
    switch (store) {
      case "Trendyol": return { 
        color: "text-orange-500", bg: "bg-orange-500/10", border: "hover:border-orange-500", 
        barColor: "bg-orange-500", icon: <ShoppingBag size={16} /> 
      };
      case "Amazon": return { 
        color: "text-yellow-500", bg: "bg-yellow-500/10", border: "hover:border-yellow-500", 
        barColor: "bg-yellow-500", icon: <ShoppingCart size={16} /> 
      };
      case "N11": return { 
        color: "text-purple-500", bg: "bg-purple-500/10", border: "hover:border-purple-500", 
        barColor: "bg-purple-500", icon: <Store size={16} /> 
      };
      case "Alibaba": return { 
        color: "text-orange-400", bg: "bg-orange-400/10", border: "hover:border-orange-400", 
        barColor: "bg-orange-400", icon: <Globe size={16} /> 
      };
      case "A101": return { 
        color: "text-cyan-400", bg: "bg-cyan-400/10", border: "hover:border-cyan-400", 
        barColor: "bg-cyan-400", icon: <Store size={16} /> 
      };
      case "CarrefourSA": return { 
        color: "text-blue-600", bg: "bg-blue-600/10", border: "hover:border-blue-600", 
        barColor: "bg-blue-600", icon: <ShoppingBag size={16} /> 
      };
      default: return { 
        color: "text-gray-400", bg: "bg-zinc-800", border: "hover:border-zinc-700", 
        barColor: "bg-gray-500", icon: <Tag size={16} /> 
      };
    }
  };

  // --- FİLTRELEME VE SIRALAMA ---
  const displayedProducts = useMemo(() => {
    let products = MOCK_PRODUCTS;

    if (activeTab !== "all") {
      products = products.filter(p => p.platform.toLowerCase() === activeTab.toLowerCase());
    }

    // Trend Skoruna Göre Sırala (En popüler en üstte)
    return products.sort((a, b) => b.trendScore - a.trendScore);
  }, [activeTab]);

  const TABS = [
    { id: "all", label: "Tüm Trendler", icon: <Zap size={16}/> },
    { id: "Amazon", label: "Amazon", icon: <ShoppingCart size={16}/> },
    { id: "Trendyol", label: "Trendyol", icon: <ShoppingBag size={16}/> },
    { id: "N11", label: "N11", icon: <Store size={16}/> },
    { id: "Alibaba", label: "Alibaba", icon: <Globe size={16}/> },
    { id: "A101", label: "A101", icon: <Store size={16}/> },
    { id: "CarrefourSA", label: "CarrefourSA", icon: <ShoppingBag size={16}/> },
  ];

  return (
    <div className="p-8 h-full overflow-y-auto">
      
      {/* --- BAŞLIK ALANI --- */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
        <div>
          <h1 className="text-3xl font-bold text-white flex items-center gap-3">
            <Activity className="text-blue-500" />
            Popüler Ürünler
          </h1>
          <p className="text-gray-400 mt-1">
            Şu an internette en çok aranan ve talep gören ürünler.
          </p>
        </div>
        
        {/* İstatistik */}
        <div className="bg-zinc-900 px-5 py-2.5 rounded-xl border border-zinc-800 flex items-center gap-4 shadow-lg">
          <div className="flex flex-col">
            <span className="text-xs text-gray-400 font-medium">Analiz Edilen</span>
            <span className="font-bold text-white text-lg">{MOCK_PRODUCTS.length}</span>
          </div>
          <div className="h-8 w-px bg-zinc-700"></div>
          <div className="flex flex-col">
            <span className="text-xs text-red-500 font-medium">Viral Olanlar</span>
            <span className="font-bold text-white text-lg flex items-center gap-1">
                <Flame size={16} className="text-red-500 fill-red-500 animate-pulse"/>
                {MOCK_PRODUCTS.filter(p => p.trendScore > 90).length}
            </span>
          </div>
        </div>
      </div>

      {/* --- SEKMELER --- */}
      <div className="flex gap-3 mb-8 overflow-x-auto pb-2 scrollbar-hide">
        {TABS.map((tab) => {
           const isActive = activeTab.toLowerCase() === tab.id.toLowerCase();
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
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6 pb-20">
        {displayedProducts.map((product) => {
          const style = getStoreStyle(product.platform);
          // 90 üzeri puan alanlara 'Alev' efekti verelim
          const isViral = product.trendScore > 90;

          return (
            <div 
              key={product.id}
              onClick={() => setSelectedProduct(product)}
              className={`group bg-zinc-900 border border-zinc-800 rounded-2xl overflow-hidden cursor-pointer ${style.border} hover:shadow-2xl hover:shadow-black/50 transition-all duration-300 relative`}
            >
              {/* Resim Alanı */}
              <div className={`h-48 w-full relative flex items-center justify-center overflow-hidden bg-zinc-950`}>
                <div className={`absolute inset-0 opacity-10 ${style.bg.replace('/10', '/30')} group-hover:scale-110 transition-transform duration-700`}></div>
                
                <ShoppingBag size={48} className={`text-white/20 group-hover:text-white/40 transition-colors z-10`} />
                
                {/* SOL ÜST: Talep Rozeti */}
                {isViral && (
                    <div className="absolute top-3 left-3 bg-red-600 text-white text-[10px] font-black px-2 py-1 rounded shadow-lg flex items-center gap-1 z-20 animate-in zoom-in">
                    <Flame size={12} className="fill-white"/>
                    ÇOK YÜKSEK TALEP
                    </div>
                )}

                {/* SAĞ ALT: Platform */}
                <div className="absolute bottom-3 right-3 bg-black/60 backdrop-blur-md text-white text-[10px] font-bold px-2 py-1 rounded border border-white/10 flex items-center gap-1 z-20">
                   {style.icon} {product.platform}
                </div>
              </div>

              {/* Kart İçeriği */}
              <div className="p-4">
                <h3 className="font-bold text-gray-200 mb-2 line-clamp-1 text-sm group-hover:text-white transition-colors">
                  {product.title}
                </h3>
                
                <div className="flex items-center gap-2 text-[10px] text-gray-500 mb-4 font-medium">
                  <Clock size={10} /> {product.lastUpdate} • <Eye size={10} /> {product.views} görüntülenme
                </div>

                <div className="flex items-end justify-between mt-auto pt-2 border-t border-zinc-800">
                  <div className="flex flex-col">
                    <span className="text-[10px] text-gray-400">Piyasa Fiyatı</span>
                    <span className="text-lg font-black text-white tracking-tight">₺{product.price.toLocaleString()}</span>
                  </div>
                  
                  {/* Trend Puanı */}
                  <div className="flex flex-col items-center">
                    <div className={`w-9 h-9 rounded-full ${style.bg} border border-white/5 flex items-center justify-center text-xs font-bold ${style.color}`}>
                        {product.trendScore}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* --- DETAY MODAL --- */}
      {selectedProduct && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
           {(() => {
             const modalStyle = getStoreStyle(selectedProduct.platform);
             
             return (
                <div className="bg-zinc-900 border border-zinc-700 w-full max-w-lg rounded-2xl shadow-2xl relative overflow-hidden animate-in zoom-in-95 duration-200 flex flex-col">
                    
                    <button 
                    onClick={() => setSelectedProduct(null)}
                    className="absolute top-4 right-4 p-2 bg-zinc-800/80 hover:bg-zinc-700 text-white rounded-full transition-colors z-20"
                    >
                    <X size={20} />
                    </button>

                    {/* Modal Görsel */}
                    <div className={`h-40 w-full relative flex items-center justify-center bg-zinc-950`}>
                        <div className={`absolute inset-0 opacity-20 ${modalStyle.bg.replace('/10', '/30')}`}></div>
                        <ShoppingBag size={64} className={`${modalStyle.color} opacity-50`} />
                    </div>

                    <div className="p-8">
                        <div className="flex justify-between items-start mb-6">
                            <div>
                                <h2 className="text-2xl font-bold text-white mb-2 leading-tight">{selectedProduct.title}</h2>
                                <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-bold ${modalStyle.bg} ${modalStyle.color}`}>
                                    {modalStyle.icon}
                                    Kaynak: {selectedProduct.platform}
                                </div>
                            </div>
                            <div className="text-right">
                                <span className="block text-xs text-gray-400">Ortalama Fiyat</span>
                                <span className="text-3xl font-black text-white">₺{selectedProduct.price.toLocaleString()}</span>
                            </div>
                        </div>

                        {/* Trend Analiz Barı */}
                        <div className="mb-8 bg-zinc-950 p-5 rounded-xl border border-zinc-800">
                            <div className="flex justify-between text-sm mb-3">
                                <span className="text-gray-400 font-medium flex items-center gap-2">
                                    <Activity size={16}/> Trend İvmesi
                                </span>
                                <span className={`font-bold ${modalStyle.color}`}>{selectedProduct.trendScore}/100</span>
                            </div>
                            <div className="w-full bg-zinc-800 h-3 rounded-full overflow-hidden">
                                <div 
                                className={`h-full ${modalStyle.barColor}`} 
                                style={{ width: `${selectedProduct.trendScore}%` }}
                                ></div>
                            </div>
                            
                            {/* Neden Trend Oldu? */}
                            <div className="mt-4 flex items-start gap-3 p-3 bg-zinc-900 rounded-lg border border-zinc-800/50">
                                <div className="p-2 bg-blue-500/10 rounded-full text-blue-500">
                                    <ArrowUpRight size={18} />
                                </div>
                                <div>
                                    <h4 className="text-xs font-bold text-gray-300 uppercase mb-0.5">Yükseliş Nedeni</h4>
                                    <p className="text-sm text-white">{selectedProduct.trendReason}</p>
                                </div>
                            </div>
                        </div>

                        <button className={`w-full py-4 text-white rounded-xl font-bold flex items-center justify-center gap-2 transition-all shadow-lg hover:scale-[1.02] ${modalStyle.barColor.replace('bg-', 'hover:bg-').replace('500', '600')} ${modalStyle.barColor}`}>
                            <ExternalLink size={20} />
                            Ürüne Git ({selectedProduct.platform})
                        </button>
                    </div>
                </div>
             );
           })()}
        </div>
      )}

    </div>
  );
}