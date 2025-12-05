"use client";

import { useState, useEffect } from "react";
import { 
  LayoutDashboard, 
  TrendingUp, 
  ShoppingBag, 
  Brain, 
  Zap, 
  ArrowRight,
  Clock,
  MoreHorizontal,
  Download,
  Share2,
  Calendar,
  ArrowUpRight,
  ArrowDownRight,
  Activity,
  Search,
  Globe,
  Server
} from "lucide-react";

export default function DashboardPage() {
  const [timeRange, setTimeRange] = useState("24h");
  // Rastgele trafik verilerini tutacak state
  const [trafficData, setTrafficData] = useState<number[]>([]);

  // useEffect ile veriyi sadece tarayıcıda yüklendikten sonra üretiyoruz
  // Bu sayede Sunucu ve Client uyuşmazlığı (Hydration Error) ortadan kalkıyor.
  useEffect(() => {
    const data = Array.from({ length: 24 }).map(() => Math.floor(Math.random() * 70) + 20);
    setTrafficData(data);
  }, []);

  return (
    <div className="p-8 h-full overflow-y-auto bg-zinc-950 text-white">
      
      {/* --- ÜST HEADER --- */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-end mb-8 gap-4">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-3">
            <LayoutDashboard className="text-blue-500" />
            Trend Komuta Merkezi
          </h1>
          <p className="text-gray-400 mt-1">Sistemin nabzını tutan canlı veri akışı ve analizler.</p>
        </div>

        <div className="flex items-center gap-3">
          {/* Zaman Filtresi */}
          <div className="bg-zinc-900 p-1 rounded-lg border border-zinc-800 flex text-xs font-medium">
            {["24h", "7d", "30d"].map((t) => (
              <button 
                key={t}
                onClick={() => setTimeRange(t)}
                className={`px-3 py-1.5 rounded-md transition-all ${
                  timeRange === t ? "bg-zinc-800 text-white shadow-sm" : "text-gray-500 hover:text-gray-300"
                }`}
              >
                {t === "24h" ? "Bugün" : t === "7d" ? "Bu Hafta" : "Bu Ay"}
              </button>
            ))}
          </div>
          
          <button className="p-2 bg-zinc-900 border border-zinc-800 rounded-lg text-gray-400 hover:text-white transition-colors">
            <Download size={18} />
          </button>
          <button className="p-2 bg-zinc-900 border border-zinc-800 rounded-lg text-gray-400 hover:text-white transition-colors">
            <Share2 size={18} />
          </button>
        </div>
      </div>

      {/* --- KPI KARTLARI (Sparkline Grafikli) --- */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatCard 
          title="Toplam Trend Verisi" 
          value="14,203" 
          change="+12.5%" 
          isPositive={true}
          icon={<Activity size={20} className="text-blue-500"/>}
          data={[40, 30, 45, 60, 55, 70, 65, 80]}
          color="blue"
        />
        <StatCard 
          title="Takip Edilen Ürün" 
          value="845" 
          change="+4 Adet" 
          isPositive={true}
          icon={<ShoppingBag size={20} className="text-purple-500"/>}
          data={[20, 25, 30, 28, 35, 40, 42, 45]}
          color="purple"
        />
        <StatCard 
          title="Viral Risk Skoru" 
          value="Yüksek" 
          change="%88 Risk" 
          isPositive={false}
          icon={<Zap size={20} className="text-yellow-500"/>}
          data={[10, 20, 40, 30, 60, 80, 90, 85]}
          color="yellow"
        />
        <StatCard 
          title="AI Kredi Durumu" 
          value="%64" 
          change="-2.1%" 
          isPositive={false}
          icon={<Brain size={20} className="text-pink-500"/>}
          data={[90, 88, 85, 80, 75, 70, 68, 64]}
          color="pink"
        />
      </div>

      {/* --- BENTO GRID LAYOUT --- */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        
        {/* 1. BÜYÜK TRAFİK GRAFİĞİ (Sol - 2 Birim) */}
        <div className="lg:col-span-2 bg-zinc-900 border border-zinc-800 rounded-2xl p-6 min-h-[300px] flex flex-col">
           <div className="flex justify-between items-center mb-6">
              <div>
                <h3 className="text-lg font-bold text-white">Canlı Veri Trafiği</h3>
                <p className="text-xs text-gray-500">Google, YouTube ve E-Ticaret sitelerinden gelen veri akışı.</p>
              </div>
              <div className="flex items-center gap-2 text-xs text-gray-400">
                <span className="flex items-center gap-1"><div className="w-2 h-2 rounded-full bg-blue-500"></div> Google</span>
                <span className="flex items-center gap-1"><div className="w-2 h-2 rounded-full bg-purple-500"></div> E-Ticaret</span>
              </div>
           </div>
           
           {/* CSS Bar Chart Simülasyonu (DÜZELTİLDİ) */}
           <div className="flex-1 flex items-end gap-3 justify-between px-2">
              {Array.from({ length: 24 }).map((_, i) => {
                // Veri henüz yüklenmediyse (SSR sırasında) varsayılan yükseklik 10 olsun
                const height = trafficData.length > 0 ? trafficData[i] : 10;
                const isPeak = height > 80;
                return (
                  <div key={i} className="w-full flex flex-col justify-end group relative">
                    {/* Tooltip */}
                    <div className="absolute -top-8 left-1/2 -translate-x-1/2 bg-white text-black text-[10px] font-bold px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-10">
                      Saat {i}:00 - {height * 10} Veri
                    </div>
                    {/* Bar */}
                    <div 
                      className={`w-full rounded-t-sm transition-all duration-500 group-hover:bg-blue-400 ${isPeak ? 'bg-blue-500' : 'bg-zinc-800'}`} 
                      style={{ height: `${height}%` }}
                    ></div>
                  </div>
                )
              })}
           </div>
           <div className="flex justify-between text-[10px] text-gray-600 mt-2 px-1 font-mono uppercase">
              <span>00:00</span>
              <span>06:00</span>
              <span>12:00</span>
              <span>18:00</span>
              <span>23:00</span>
           </div>
        </div>

        {/* 2. AI ASİSTAN KARTI (Sağ Üst) */}
        <div className="bg-gradient-to-br from-zinc-900 to-zinc-950 border border-zinc-800 rounded-2xl p-6 relative overflow-hidden">
           <div className="absolute top-0 right-0 w-32 h-32 bg-pink-600/10 rounded-full blur-3xl -mr-10 -mt-10"></div>
           
           <div className="flex items-center justify-between mb-4">
             <h3 className="text-lg font-bold text-white flex items-center gap-2">
               <Brain className="text-pink-500" size={20}/>
               AI İçgörüsü
             </h3>
             <span className="text-[10px] bg-pink-500/10 text-pink-500 px-2 py-1 rounded-full border border-pink-500/20 font-bold">CANLI</span>
           </div>

           <div className="space-y-4">
             <div className="p-3 bg-zinc-950/50 rounded-xl border border-zinc-800/50">
               <p className="text-sm text-gray-300 leading-relaxed">
                 <span className="text-pink-500 font-bold">Dikkat:</span> Elektronik kategorisinde "Dyson" aramaları son 1 saatte <span className="text-white font-bold">%340</span> arttı. Stok tükenme riski var.
               </p>
             </div>
             <div className="p-3 bg-zinc-950/50 rounded-xl border border-zinc-800/50">
               <p className="text-sm text-gray-300 leading-relaxed">
                 <span className="text-blue-500 font-bold">Trend:</span> "Asgari Ücret" konusu Twitter gündeminden düşüyor, yerini "Seçim Anketi" alıyor.
               </p>
             </div>
           </div>

           <button className="w-full mt-6 py-2.5 bg-pink-600 hover:bg-pink-700 text-white rounded-lg font-bold text-sm transition-colors flex items-center justify-center gap-2">
             Detaylı Rapor Oluştur <ArrowRight size={14}/>
           </button>
        </div>
      </div>

      {/* --- ALT GRID (3'lü Yapı) --- */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        
        {/* KAYNAK DAĞILIMI */}
        <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6">
           <h3 className="text-sm font-bold text-gray-400 uppercase tracking-wider mb-4">Veri Kaynakları</h3>
           <div className="space-y-4">
              <SourceItem name="Google Trends" percent={45} color="bg-blue-500" icon={<Search size={14}/>} />
              <SourceItem name="E-Ticaret (Pazaryeri)" percent={30} color="bg-orange-500" icon={<ShoppingBag size={14}/>} />
              <SourceItem name="Sosyal Medya" percent={15} color="bg-pink-500" icon={<Globe size={14}/>} />
              <SourceItem name="Haber Siteleri" percent={10} color="bg-gray-500" icon={<Globe size={14}/>} />
           </div>
        </div>

        {/* SON AKTİVİTELER */}
        <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6">
           <div className="flex justify-between items-center mb-4">
              <h3 className="text-sm font-bold text-gray-400 uppercase tracking-wider">Son Aktiviteler</h3>
              <MoreHorizontal size={16} className="text-gray-500 cursor-pointer"/>
           </div>
           
           <div className="space-y-0 relative">
              {/* Timeline Çizgisi */}
              <div className="absolute left-[9px] top-2 bottom-2 w-[1px] bg-zinc-800"></div>
              
              <TimelineItem time="2 dk önce" title="Yeni Ürün Eklendi" desc="iPhone 15 Pro Max - Amazon" icon={<ShoppingBag size={12}/>} color="bg-purple-500" />
              <TimelineItem time="14 dk önce" title="Trend Alarmı" desc="#Seçim2025 etiketi viral oldu" icon={<Zap size={12}/>} color="bg-yellow-500" />
              <TimelineItem time="1 saat önce" title="Veri Tabanı" desc="Günlük yedekleme tamamlandı" icon={<Server size={12}/>} color="bg-green-500" />
           </div>
        </div>

        {/* SİSTEM DURUMU */}
        <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6 flex flex-col justify-between">
           <div>
             <h3 className="text-sm font-bold text-gray-400 uppercase tracking-wider mb-4">Sistem Sağlığı</h3>
             <div className="flex items-center gap-4 mb-6">
                <div className="relative w-16 h-16 flex items-center justify-center">
                   <svg className="w-full h-full transform -rotate-90">
                      <circle cx="32" cy="32" r="28" stroke="currentColor" strokeWidth="4" fill="transparent" className="text-zinc-800" />
                      <circle cx="32" cy="32" r="28" stroke="currentColor" strokeWidth="4" fill="transparent" strokeDasharray="175.9" strokeDashoffset="17.59" className="text-green-500" />
                   </svg>
                   <span className="absolute text-sm font-bold text-white">%98</span>
                </div>
                <div>
                   <div className="text-white font-bold">Mükemmel</div>
                   <div className="text-xs text-gray-500">Tüm servisler aktif</div>
                </div>
             </div>
           </div>

           <div className="grid grid-cols-2 gap-3">
              <div className="bg-zinc-950 p-3 rounded-lg border border-zinc-800 text-center">
                 <div className="text-xs text-gray-500">API Latency</div>
                 <div className="text-green-500 font-bold">24ms</div>
              </div>
              <div className="bg-zinc-950 p-3 rounded-lg border border-zinc-800 text-center">
                 <div className="text-xs text-gray-500">Uptime</div>
                 <div className="text-blue-500 font-bold">24g 12s</div>
              </div>
           </div>
        </div>

      </div>
    </div>
  );
}

// --- YARDIMCI BİLEŞENLER ---

// 1. Gelişmiş İstatistik Kartı (Sparkline'lı)
function StatCard({ title, value, change, isPositive, icon, data, color }: any) {
  // Basit SVG Sparkline oluşturucu
  const max = Math.max(...data);
  const min = Math.min(...data);
  const points = data.map((d: number, i: number) => {
    const x = (i / (data.length - 1)) * 100;
    const y = 100 - ((d - min) / (max - min)) * 100;
    return `${x},${y}`;
  }).join(" ");

  const colorClass = color === 'blue' ? 'text-blue-500 stroke-blue-500' :
                     color === 'purple' ? 'text-purple-500 stroke-purple-500' :
                     color === 'pink' ? 'text-pink-500 stroke-pink-500' : 
                     'text-yellow-500 stroke-yellow-500';

  return (
    <div className="bg-zinc-900 p-5 rounded-2xl border border-zinc-800 hover:border-zinc-700 transition-all group relative overflow-hidden">
      <div className="flex justify-between items-start mb-4 relative z-10">
        <div>
           <p className="text-gray-400 text-xs font-bold uppercase tracking-wider mb-1">{title}</p>
           <h3 className="text-2xl font-black text-white">{value}</h3>
        </div>
        <div className={`p-2.5 rounded-lg bg-zinc-950 border border-zinc-800 ${colorClass}`}>
           {icon}
        </div>
      </div>
      
      <div className="flex items-end justify-between relative z-10">
        <div className={`flex items-center gap-1 text-xs font-bold ${isPositive ? 'text-green-500' : 'text-red-500'}`}>
          {isPositive ? <ArrowUpRight size={14}/> : <ArrowDownRight size={14}/>}
          {change}
        </div>
        
        {/* Sparkline SVG */}
        <div className="w-24 h-10 opacity-50 group-hover:opacity-100 transition-opacity">
           <svg viewBox="0 0 100 100" className="w-full h-full overflow-visible">
              <polyline 
                 points={points} 
                 fill="none" 
                 strokeWidth="3" 
                 className={`${colorClass}`}
                 strokeLinecap="round" 
                 strokeLinejoin="round"
              />
           </svg>
        </div>
      </div>
    </div>
  );
}

// 2. Kaynak Satırı
function SourceItem({ name, percent, color, icon }: any) {
  return (
    <div>
      <div className="flex justify-between text-xs mb-1.5 text-gray-300 font-medium">
        <span className="flex items-center gap-2">{icon} {name}</span>
        <span>{percent}%</span>
      </div>
      <div className="w-full bg-zinc-950 h-2 rounded-full overflow-hidden border border-zinc-800/50">
        <div className={`h-full ${color}`} style={{ width: `${percent}%` }}></div>
      </div>
    </div>
  );
}

// 3. Timeline Satırı
function TimelineItem({ time, title, desc, icon, color }: any) {
  return (
    <div className="relative pl-6 pb-6 last:pb-0">
      <div className={`absolute left-0 top-1 w-5 h-5 rounded-full border-4 border-zinc-900 ${color} flex items-center justify-center text-white z-10`}>
         {/* İkon çok küçük olduğu için göstermeyebiliriz veya sadece nokta yapabiliriz */}
      </div>
      <div>
         <h4 className="text-sm font-bold text-white leading-none mb-1">{title}</h4>
         <p className="text-xs text-gray-400 mb-1">{desc}</p>
         <span className="text-[10px] text-gray-500 flex items-center gap-1">
           <Clock size={10}/> {time}
         </span>
      </div>
    </div>
  );
}