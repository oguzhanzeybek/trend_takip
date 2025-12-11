"use client";

import { useState, useEffect } from "react";
import { 
  LayoutDashboard, ShoppingBag, Brain, Zap, ArrowRight, Clock,
  MoreHorizontal, ArrowUpRight, ArrowDownRight, Activity,
  Search, Globe, RefreshCcw, BarChart2, Wifi, Calendar
} from "lucide-react";

const API_BASE_URL = "http://127.0.0.1:8000";

export default function DashboardPage() {
  const [timeRange, setTimeRange] = useState("24h");
  const [loading, setLoading] = useState(true);
  const [latency, setLatency] = useState(0); 
  
  const [stats, setStats] = useState<any>({
    period_count: 0,
    total_archive: 0,
    sources: { google: 0, ecommerce: 0, social: 0, news: 0 },
    chart_data: [],
    recent_activities: [],
    ai_insight: "Veriler toplanıyor...",
    system_status: "..."
  });

  const fetchStats = async () => {
    try {
        setLoading(true);
        const start = Date.now();
        const res = await fetch(`${API_BASE_URL}/api/stats?time_range=${timeRange}`);
        setLatency(Date.now() - start);

        if(res.ok) {
            const data = await res.json();
            setStats(data);
        }
    } catch (error) {
        console.error("Dashboard hatası:", error);
    } finally {
        setLoading(false);
    }
  };

  useEffect(() => { fetchStats(); }, [timeRange]);

  const totalSrc = Object.values(stats?.sources || {}).reduce((a:any, b:any) => a+b, 0) || 1;
  const getPercent = (val: number) => Math.round((val / Number(totalSrc)) * 100);

  // Grafik Maksimum Değerini Bul
  const chartValues = stats?.chart_data?.map((d: any) => d.value) || [];
  const maxChartValue = Math.max(...chartValues, 10); // En az 10 olsun

  return (
    <div className="p-8 h-full overflow-y-auto bg-zinc-950 text-white font-sans">
      
      {/* HEADER */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-end mb-8 gap-4">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-3">
            <LayoutDashboard className="text-blue-500" />
            Trend Komuta Merkezi
          </h1>
          <p className="text-gray-400 mt-1">Sistemin nabzını tutan canlı veri akışı.</p>
        </div>

        <div className="flex items-center gap-3">
          <div className="bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-1.5 flex items-center gap-2 text-xs text-gray-400 mr-2">
             <div className={`w-2 h-2 rounded-full ${latency < 300 ? 'bg-green-500' : 'bg-red-500'} animate-pulse`}></div>
             Ping: <span className="text-white font-mono">{latency}ms</span>
          </div>

          <div className="bg-zinc-900 p-1 rounded-lg border border-zinc-800 flex text-xs font-medium">
            {[ {id:"24h", l:"Bugün"}, {id:"7d", l:"Bu Hafta"}, {id:"30d", l:"Bu Ay"} ].map((btn) => (
              <button key={btn.id} onClick={() => setTimeRange(btn.id)}
                className={`px-4 py-1.5 rounded-md transition-all ${timeRange === btn.id ? "bg-zinc-800 text-white shadow-sm border border-zinc-700" : "text-gray-500 hover:text-gray-300"}`}>
                {btn.l}
              </button>
            ))}
          </div>
          
          <button onClick={fetchStats} className="p-2 bg-zinc-900 border border-zinc-800 rounded-lg text-gray-400 hover:text-white transition-colors">
            <RefreshCcw size={18} className={loading ? "animate-spin" : ""} />
          </button>
        </div>
      </div>

      {/* KPI KARTLARI */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatCard title="Toplam Arşiv" value={(stats?.total_archive || 0).toLocaleString()} change="Tüm Zamanlar" isPositive={true} icon={<Activity size={20} className="text-blue-500"/>} color="blue"/>
        <StatCard title="Seçili Dönem Akışı" value={(stats?.period_count || 0).toLocaleString()} change={timeRange === '24h' ? "Son 24 Saat" : "Seçili Dönem"} isPositive={true} icon={<ShoppingBag size={20} className="text-purple-500"/>} color="purple"/>
        <StatCard title="Risk Skoru" value="Normal" change="Stabil" isPositive={true} icon={<Zap size={20} className="text-yellow-500"/>} color="yellow"/>
        <StatCard title="Sistem Sağlığı" value="OK" change="Backend Aktif" isPositive={true} icon={<Wifi size={20} className="text-green-500"/>} color="green"/>
      </div>

      {/* GRAFİK VE AI */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        
        {/* --- DÜZELTİLMİŞ GRAFİK --- */}
        <div className="lg:col-span-2 bg-zinc-900 border border-zinc-800 rounded-2xl p-6 min-h-[350px] flex flex-col relative">
           <div className="flex justify-between items-center mb-6">
             <div>
               <h3 className="text-lg font-bold text-white flex items-center gap-2">
                 <BarChart2 size={18} className="text-blue-500"/>
                 Veri Giriş Grafiği
               </h3>
               <p className="text-xs text-gray-500">Maksimum Veri Anlık: <span className="text-white font-bold">{maxChartValue.toLocaleString()}</span></p>
             </div>
           </div>
           
           <div className="flex-1 flex gap-2 relative">
              {/* Y-EKSENİ (0 - 50% - 100%) */}
              <div className="absolute left-0 top-0 bottom-8 w-full flex flex-col justify-between pointer-events-none opacity-20 z-0">
                  <div className="border-t border-zinc-500 w-full"></div>
                  <div className="border-t border-zinc-500 w-full border-dashed"></div>
                  <div className="border-t border-zinc-500 w-full"></div>
              </div>

              {/* BARLAR */}
              <div className="flex-1 flex items-end justify-between z-10 gap-1 pb-6 overflow-x-auto">
                {(stats?.chart_data || []).map((item: any, i: number) => {
                    const heightPercent = Math.max((item.value / maxChartValue) * 100, 2); // En az %2 yükseklik
                    return (
                    <div key={i} className="min-w-[30px] w-full flex flex-col justify-end group relative h-full">
                        {/* Sayı (Barın Üstünde) */}
                        <div className="text-[10px] text-zinc-400 text-center mb-1 opacity-0 group-hover:opacity-100 transition-opacity font-bold">
                            {item.value > 0 ? item.value : ''}
                        </div>
                        
                        {/* Bar */}
                        <div 
                        className="w-full bg-zinc-800 rounded-t-sm transition-all duration-500 group-hover:bg-blue-500 relative overflow-hidden"
                        style={{ height: `${heightPercent}%` }}
                        >
                            <div className="absolute bottom-0 left-0 w-full h-1/2 bg-gradient-to-t from-blue-500/20 to-transparent"></div>
                        </div>
                        
                        {/* X-Ekseni Etiketi */}
                        <span className="absolute -bottom-6 left-1/2 -translate-x-1/2 text-[9px] text-gray-500 font-mono w-max">
                            {item.label.split(' ')[0]}
                        </span>
                    </div>
                    )
                })}
              </div>
           </div>
        </div>

        {/* AI İÇGÖRÜSÜ */}
        <div className="bg-gradient-to-br from-zinc-900 to-zinc-950 border border-zinc-800 rounded-2xl p-6 relative overflow-hidden flex flex-col">
           <div className="absolute top-0 right-0 w-40 h-40 bg-pink-600/10 rounded-full blur-3xl -mr-10 -mt-10"></div>
           <div className="flex items-center justify-between mb-4">
             <h3 className="text-lg font-bold text-white flex items-center gap-2">
               <Brain className="text-pink-500" size={20}/>
               Stratejik İçgörü
             </h3>
             <span className="text-[10px] bg-pink-500/10 text-pink-500 px-2 py-1 rounded-full border border-pink-500/20 font-bold animate-pulse">CANLI</span>
           </div>
           <div className="flex-1 bg-zinc-950/50 rounded-xl border border-zinc-800/50 p-5 relative overflow-y-auto max-h-[300px] scrollbar-thin scrollbar-thumb-zinc-700">
             <p className="text-sm text-gray-200 leading-relaxed font-medium whitespace-pre-wrap">{stats?.ai_insight}</p>
           </div>
        </div>
      </div>

      {/* ALT GRID */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* KAYNAK DAĞILIMI */}
        <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6">
           <h3 className="text-sm font-bold text-gray-400 uppercase tracking-wider mb-4">Kaynak Dağılımı ({timeRange})</h3>
           <div className="space-y-5">
              <SourceItem name="Google Trends" percent={getPercent(stats?.sources?.google || 0)} color="bg-blue-500" icon={<Search size={14}/>} />
              <SourceItem name="E-Ticaret" percent={getPercent(stats?.sources?.ecommerce || 0)} color="bg-orange-500" icon={<ShoppingBag size={14}/>} />
              <SourceItem name="Sosyal Medya" percent={getPercent(stats?.sources?.social || 0)} color="bg-pink-500" icon={<Globe size={14}/>} />
              <SourceItem name="Haberler / Diğer" percent={getPercent(stats?.sources?.news || 0)} color="bg-gray-500" icon={<Globe size={14}/>} />
           </div>
        </div>

        {/* SON AKTİVİTELER */}
        <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6 col-span-1 lg:col-span-2">
           <div className="flex justify-between items-center mb-4">
              <h3 className="text-sm font-bold text-gray-400 uppercase tracking-wider">Son Veri Girişleri (Dakikalık Gruplama)</h3>
              <MoreHorizontal size={16} className="text-gray-500 cursor-pointer"/>
           </div>
           <div className="space-y-0 relative">
              <div className="absolute left-[9px] top-2 bottom-2 w-[1px] bg-zinc-800"></div>
              {(stats?.recent_activities || []).map((act: any, i:number) => (
                <div key={i} className="relative pl-6 pb-6 last:pb-0 group">
                  <div className="absolute left-0 top-1.5 w-4 h-4 rounded-full border-[3px] border-zinc-900 bg-blue-500 z-10 group-hover:scale-125 transition-transform"></div>
                  <div>
                      <h4 className="text-sm font-bold text-white leading-none group-hover:text-blue-400 transition-colors mb-1.5">
                        {act.count} Adet Veri Girildi
                      </h4>
                      <span className="text-[10px] text-gray-500 flex items-center gap-1 font-medium bg-zinc-950 px-2 py-0.5 rounded w-fit border border-zinc-800">
                        <Calendar size={10} className="text-gray-500"/> {act.time_group}
                      </span>
                  </div>
                </div>
              ))}
           </div>
        </div>
      </div>
    </div>
  );
}

// YARDIMCI KOMPONENTLER (Aynı Kalsın)
function StatCard({ title, value, change, isPositive, icon, color }: any) {
  const colorClass = color === 'blue' ? 'text-blue-500' : color === 'purple' ? 'text-purple-500' : color === 'green' ? 'text-green-500' : 'text-yellow-500';
  return (
    <div className="bg-zinc-900 p-5 rounded-2xl border border-zinc-800 hover:border-zinc-700 transition-all group relative overflow-hidden">
      <div className="flex justify-between items-start mb-4 relative z-10">
        <div>
           <p className="text-gray-400 text-xs font-bold uppercase tracking-wider mb-1">{title}</p>
           <h3 className="text-2xl font-black text-white tracking-tight">{value}</h3>
        </div>
        <div className={`p-2.5 rounded-lg bg-zinc-950 border border-zinc-800 ${colorClass}`}>{icon}</div>
      </div>
      <div className="flex items-end justify-between relative z-10">
        <div className={`flex items-center gap-1 text-xs font-bold ${isPositive ? 'text-green-500' : 'text-gray-500'}`}>
          <Activity size={14}/> {change}
        </div>
      </div>
    </div>
  );
}

function SourceItem({ name, percent, color, icon }: any) {
  return (
    <div>
      <div className="flex justify-between text-xs mb-2 text-gray-300 font-medium">
        <span className="flex items-center gap-2">{icon} {name}</span>
        <span>{percent}%</span>
      </div>
      <div className="w-full bg-zinc-950 h-2.5 rounded-full overflow-hidden border border-zinc-800">
        <div className={`h-full ${color} transition-all duration-1000 ease-out`} style={{ width: `${percent}%` }}></div>
      </div>
    </div>
  );
}