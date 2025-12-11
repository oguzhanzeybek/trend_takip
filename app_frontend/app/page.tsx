"use client";

import React, { useState, useEffect, useRef } from "react";
import ReactMarkdown from "react-markdown";
import { 
  Bot, 
  Trash2,
  ArrowUp,
  Activity,
  Sparkles,
  Zap,
  BarChart3,
  RefreshCcw,
  TrendingUp,
  ShoppingBag,
  MessageCircle,
  Tag
} from "lucide-react";

// API URL
const API_BASE_URL = "http://127.0.0.1:8000";

type ChatMessage = { 
  role: "user" | "bot" | "error"; 
  content: string;
};

const LOADING_TEXTS = [
  "Veri setleri taranıyor...",
  "Fiyat ve stok analizleri yapılıyor...",
  "Ticari içgörüler çıkarılıyor...",
  "Rapor hazırlanıyor..."
];

// --- GÜNCELLENMİŞ VE BACKEND İLE UYUMLU SORGU KARTLARI ---
const SUGGESTIONS = [
  { 
    icon: <TrendingUp size={20} className="text-cyan-400"/>, 
    title: "Yükselen Trendler", 
    prompt: "Son 1 haftada arama hacmi ve popülaritesi en çok artan ürünleri analiz et." 
  },
  { 
    icon: <ShoppingBag size={20} className="text-violet-400"/>, 
    title: "Platform Analizi", 
    prompt: "Trendyol ve Amazon üzerindeki en çok satan ürünleri ve kullanıcı yorumlarını karşılaştır." 
  },
  { 
    icon: <MessageCircle size={20} className="text-yellow-400"/>, 
    title: "Müşteri Duygusu", 
    prompt: "Kullanıcıların ürünler hakkında en çok şikayet ettiği veya övdüğü konuları özetle." 
  },
  { 
    icon: <Tag size={20} className="text-pink-400"/>, 
    title: "Fiyat Fırsatları", 
    prompt: "Fiyatı düşen, indirime giren veya fiyat/performans oranı yüksek ürünleri listele." 
  },
];

export default function ChatPage() {
  const [chatInput, setChatInput] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState(0); 
  const [isFocused, setIsFocused] = useState(false);
  
  const chatEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // --- AUTO-FOCUS ---
  useEffect(() => {
    if (!loading && textareaRef.current) {
      setTimeout(() => textareaRef.current?.focus(), 10);
    }
  }, [loading]);

  // Otomatik kaydırma
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  // Loading Text Döngüsü
  useEffect(() => {
    if (!loading) {
      setLoadingStep(0);
      return;
    }
    const interval = setInterval(() => {
      setLoadingStep((prev) => (prev + 1) % LOADING_TEXTS.length);
    }, 2000);
    return () => clearInterval(interval);
  }, [loading]);

  // Textarea Yükseklik
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  }, [chatInput]);

  const handleSendMessage = async (textOverride?: string) => {
    const textToSend = textOverride || chatInput;
    if (!textToSend.trim() || loading) return;

    setChatInput(""); 
    if (textareaRef.current) textareaRef.current.style.height = "auto"; 

    setMessages((prev) => [...prev, { role: "user", content: textToSend }]);
    setLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: textToSend }),
      });

      if (!response.ok) throw new Error(`Hata: ${response.status}`);
      const data = await response.json();

      if (data.reply) {
        setMessages((prev) => [...prev, { role: "bot", content: data.reply }]);
      } else {
        throw new Error("Boş cevap.");
      }

    } catch (err) {
      setMessages((prev) => [...prev, { role: "error", content: "Sunucu ile bağlantı kurulamadı. Backend çalışıyor mu?" }]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    // --- GÜNCELLEME: Arka plan rengi #030304 -> #0a0a0c yapıldı ---
    <div className="flex flex-col h-full bg-[#0a0a0c] text-white font-sans relative overflow-hidden selection:bg-cyan-500/30">
      
      {/* --- AMBİYANS IŞIKLARI (Biraz daha soft) --- */}
      <div className="fixed top-[-20%] left-1/4 w-[600px] h-[600px] bg-indigo-900/15 rounded-full blur-[120px] pointer-events-none z-0"></div>
      <div className="fixed bottom-[-20%] right-1/4 w-[600px] h-[600px] bg-cyan-900/10 rounded-full blur-[120px] pointer-events-none z-0"></div>

      {/* --- HEADER --- */}
      <header className="h-16 flex items-center justify-between px-6 sticky top-0 z-20 bg-[#0a0a0c]/80 backdrop-blur-xl border-b border-white/5">
        <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-600 to-violet-700 flex items-center justify-center shadow-[0_0_15px_-3px_rgba(99,102,241,0.4)] border border-white/10">
              <Bot size={18} className="text-white" />
            </div>
            <div>
              <h2 className="font-bold text-lg tracking-tight text-white">
                TrendAI
              </h2>
              <div className="flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                  <span className="text-[10px] text-zinc-400 font-medium tracking-wide">PAZAR ANALİSTİ</span>
              </div>
            </div>
        </div>
        <div>
            {messages.length > 0 && (
                <button 
                    onClick={() => setMessages([])} 
                    className="p-2 text-zinc-500 hover:text-red-400 hover:bg-white/5 rounded-lg transition-all"
                    title="Sohbeti Temizle"
                >
                    <Trash2 size={18}/>
                </button>
            )}
        </div>
      </header>

      {/* --- SOHBET ALANI --- */}
      <div className="flex-1 overflow-y-auto relative z-10 scrollbar-thin scrollbar-thumb-zinc-800 scrollbar-track-transparent">
        <div className="max-w-3xl mx-auto px-4 py-8 min-h-full flex flex-col justify-end">
            
            {/* HOŞGELDİN EKRANI */}
            {messages.length === 0 && (
                <div className="flex flex-col items-center justify-center h-full pb-20 animate-in fade-in zoom-in duration-700">
                    
                    {/* İkon & Başlık */}
                    <div className="mb-6 relative">
                        <div className="absolute inset-0 bg-cyan-500/20 blur-2xl rounded-full"></div>
                        <div className="relative bg-zinc-900/80 p-5 rounded-2xl border border-white/10 shadow-2xl">
                            <TrendingUp size={40} className="text-cyan-400" />
                        </div>
                    </div>

                    <h1 className="text-4xl font-bold mb-3 text-center tracking-tight">
                        <span className="bg-gradient-to-r from-white via-cyan-100 to-zinc-400 bg-clip-text text-transparent">
                            Pazarı Analiz Etmeye Hazırım
                        </span>
                    </h1>
                    <p className="text-zinc-500 text-center mb-10 max-w-md text-sm leading-relaxed">
                        Milyonlarca veriyi tarayarak ticari fırsatları, fiyat değişimlerini ve tüketici eğilimlerini senin için raporlayabilirim.
                    </p>
                    
                    {/* Modern Kartlar */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 w-full max-w-2xl">
                        {SUGGESTIONS.map((s, i) => (
                            <button 
                                key={i}
                                onClick={() => handleSendMessage(s.prompt)}
                                className="group relative p-4 bg-zinc-900/40 hover:bg-zinc-800/80 border border-white/5 hover:border-cyan-500/20 rounded-2xl text-left transition-all duration-300 hover:shadow-lg hover:-translate-y-1 overflow-hidden"
                            >
                                {/* Hover Gradient Efekti */}
                                <div className="absolute inset-0 bg-gradient-to-br from-cyan-500/0 via-transparent to-transparent group-hover:from-cyan-500/5 transition-all duration-500"></div>
                                
                                <div className="relative z-10 flex items-start gap-4">
                                    <div className="p-2.5 rounded-xl bg-zinc-900 border border-white/5 group-hover:bg-zinc-800 group-hover:scale-110 transition-all duration-300">
                                        {s.icon}
                                    </div>
                                    <div className="flex-1">
                                        <h3 className="font-semibold text-zinc-200 text-sm mb-1 group-hover:text-white transition-colors">
                                            {s.title}
                                        </h3>
                                        <p className="text-xs text-zinc-500 leading-relaxed group-hover:text-zinc-400">
                                            {s.prompt}
                                        </p>
                                    </div>
                                </div>
                            </button>
                        ))}
                    </div>
                </div>
            )}

            {/* MESAJ AKIŞI */}
            <div className="space-y-8">
                {messages.map((msg, i) => (
                    <div key={i} className={`flex gap-4 animate-in fade-in slide-in-from-bottom-2 duration-300 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                        
                        {/* Bot Avatar */}
                        {msg.role !== 'user' && (
                            <div className="w-8 h-8 mt-1 rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-600 flex items-center justify-center flex-shrink-0 shadow-lg shadow-indigo-500/20">
                                {msg.role === 'error' ? <Zap size={16} className="text-white"/> : <Sparkles size={16} className="text-white"/>}
                            </div>
                        )}

                        {/* --- SOHBET YAPISI --- */}
                        <div className={`
                          relative max-w-[85%]
                          ${msg.role === 'user' 
                            // USER: Daha modern bir gri/mavi ton
                            ? 'bg-[#27272a] border border-white/5 text-white px-5 py-3 rounded-2xl rounded-tr-sm shadow-md' 
                            
                            // BOT: SADECE METİN
                            : 'bg-transparent text-zinc-300 px-0 py-1'
                          }
                        `}>
                             {/* Bot İsmi */}
                             {msg.role === 'bot' && (
                                <div className="text-[10px] font-bold text-cyan-500 mb-1 opacity-80 uppercase tracking-widest">TrendAI</div>
                             )}

                             {msg.role === 'bot' ? (
                                <div className="prose prose-invert prose-p:text-zinc-300 prose-headings:text-cyan-100 prose-strong:text-white max-w-none text-[15px] leading-relaxed">
                                    <ReactMarkdown>{msg.content}</ReactMarkdown>
                                </div>
                             ) : (
                                <p className="whitespace-pre-wrap leading-relaxed text-[15px] font-normal">{msg.content}</p>
                             )}
                        </div>
                    </div>
                ))}

                {/* --- YÜKLENİYOR İNDİKATÖRÜ --- */}
                {loading && (
                    <div className="flex gap-4 animate-in fade-in duration-300 justify-start pl-1">
                         <div className="w-8 h-8 rounded-xl bg-zinc-900 border border-white/10 flex items-center justify-center flex-shrink-0">
                            <Activity size={16} className="text-cyan-500 animate-pulse"/>
                        </div>
                        <div className="flex flex-col justify-center gap-1.5 min-w-[200px]">
                            <span className="text-xs font-mono text-cyan-400 font-medium tracking-wide animate-pulse">
                                {LOADING_TEXTS[loadingStep]}
                            </span>
                            <div className="h-1 w-full bg-zinc-800 rounded-full overflow-hidden">
                                <div className="h-full bg-gradient-to-r from-cyan-500 to-indigo-500 w-1/3 rounded-full animate-[shimmer_1s_infinite]"></div>
                            </div>
                        </div>
                    </div>
                )}
                
                <div ref={chatEndRef} className="h-4" />
            </div>
        </div>
      </div>

      {/* --- INPUT ALANI --- */}
      <div className="p-4 relative z-30">
        <div className="max-w-2xl mx-auto">
            <div 
              className={`
                relative rounded-[26px] transition-all duration-300 ease-out flex items-end
                ${isFocused 
                  ? "bg-[#18181b] border border-white/90 shadow-[0_0_30px_0px_rgba(255,255,255,0.15)]" 
                  : "bg-[#18181b] border border-white/10 shadow-lg" 
                }
              `}
            >
                <textarea
                    ref={textareaRef}
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    onFocus={() => setIsFocused(true)}
                    onBlur={() => setIsFocused(false)}
                    autoFocus
                    placeholder="Merak ettiğin bir ürün veya trend var mı?"
                    rows={1}
                    className="w-full bg-transparent text-white pl-6 py-4 rounded-[26px] focus:outline-none resize-none max-h-[150px] overflow-y-auto scrollbar-hide placeholder:text-zinc-500 font-normal text-[15px] z-10"
                />
                
                <button 
                    onClick={() => handleSendMessage()}
                    disabled={!chatInput.trim() || loading}
                    className={`
                        m-2 p-2.5 rounded-full transition-all duration-300 flex items-center justify-center flex-shrink-0 z-10
                        ${chatInput.trim() && !loading
                            ? "bg-white text-black hover:bg-zinc-200 hover:scale-105 shadow-md" 
                            : "bg-zinc-800 text-zinc-600 cursor-not-allowed"}
                    `}
                >
                    {loading ? <RefreshCcw size={18} className="animate-spin"/> : <ArrowUp size={20} strokeWidth={2.5} />}
                </button>
            </div>
            
            <p className="text-center mt-3 text-[10px] text-zinc-600 font-medium">
                TrendAI, e-ticaret ve sosyal medya verilerini anlık analiz eder.
            </p>
        </div>
      </div>
      
      <style jsx global>{`
        @keyframes shimmer {
          0% { transform: translateX(-100%); }
          100% { transform: translateX(300%); }
        }
      `}</style>

    </div>
  );
}