"use client";

import React, { useState, useEffect, useRef } from "react";
import { Send, Bot, User, MoreVertical, AlertCircle, RefreshCw } from "lucide-react";
import ReactMarkdown from "react-markdown"; // AI cevaplarını güzel göstermek için

// API URL Ayarı
// Eğer Backend'i Render'a yüklediysen buraya Render URL'ini yaz.
// Local test için: "http://127.0.0.1:8000"
const API_BASE_URL = "http://127.0.0.1:8000";

type ChatMessage = { 
  role: "user" | "bot" | "error"; 
  content: string 
};

export default function ChatPage() {
  const [chatInput, setChatInput] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // Otomatik kaydırma
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const handleSendMessage = async () => {
    if (!chatInput.trim() || loading) return;

    const userMessageText = chatInput;
    setChatInput(""); // Inputu hemen temizle

    // 1. Kullanıcı mesajını ekrana bas
    setMessages((prev) => [...prev, { role: "user", content: userMessageText }]);
    setLoading(true);

    try {
      // 2. Backend'e İstek At (POST /api/chat)
      const response = await fetch(`${API_BASE_URL}/api/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        // Backend'deki Pydantic modeli: class ChatRequest(BaseModel): message: str
        body: JSON.stringify({ message: userMessageText }),
      });

      if (!response.ok) {
        throw new Error(`Sunucu Hatası: ${response.status}`);
      }

      const data = await response.json();

      // 3. Backend'den gelen cevabı ekle ({ "reply": "..." })
      if (data.reply) {
        setMessages((prev) => [...prev, { role: "bot", content: data.reply }]);
      } else {
        throw new Error("Boş cevap döndü.");
      }

    } catch (err) {
      console.error("Chat Hatası:", err);
      setMessages((prev) => [
        ...prev,
        { role: "error", content: "Sunucuya ulaşılamadı. Lütfen internet bağlantınızı veya Backend servisini kontrol edin." }
      ]);
    } finally {
      setLoading(false);
    }
  };

  // Enter tuşu kontrolü (Shift+Enter alt satıra geçer)
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="flex flex-col h-screen max-h-screen bg-zinc-950 text-white font-sans">
      
      {/* HEADER */}
      <header className="h-16 border-b border-zinc-900 flex items-center justify-between px-6 bg-zinc-950/80 backdrop-blur-md sticky top-0 z-20">
        <div className="flex items-center gap-3">
            <div className="relative">
              <div className={`w-2.5 h-2.5 rounded-full ${loading ? 'bg-yellow-500 animate-pulse' : 'bg-green-500'} shadow-[0_0_10px_currentColor]`}></div>
              {loading && <div className="absolute inset-0 w-2.5 h-2.5 bg-yellow-500 rounded-full animate-ping opacity-75"></div>}
            </div>
            <div>
                <h2 className="font-semibold text-sm tracking-wide">TrendAI Asistan</h2>
                <p className="text-[10px] text-zinc-500 font-medium">
                  {loading ? "Yazıyor..." : "Çevrimiçi • v1.0"}
                </p>
            </div>
        </div>
        <button className="text-zinc-500 hover:text-white transition-colors" title="Ayarlar">
          <MoreVertical className="w-5 h-5"/>
        </button>
      </header>

      {/* MESAJ ALANI */}
      <div className="flex-1 overflow-y-auto p-4 md:p-8 space-y-6 scrollbar-thin scrollbar-thumb-zinc-800 scrollbar-track-transparent">
        
        {messages.length === 0 && (
            <div className="h-full flex flex-col items-center justify-center text-center opacity-60 select-none animate-in fade-in zoom-in duration-500">
                <div className="w-24 h-24 bg-zinc-900 rounded-full flex items-center justify-center mb-6 shadow-2xl shadow-blue-900/20 border border-zinc-800">
                  <Bot className="w-10 h-10 text-blue-500" />
                </div>
                <h3 className="text-2xl font-bold mb-3 bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
                  Nasıl yardımcı olabilirim?
                </h3>
                <p className="text-sm text-zinc-400 max-w-xs mx-auto leading-relaxed">
                  "TikTok trendlerini analiz et", "Altın fiyatları ne durumda?" veya "Son dakika haberleri" diyebilirsiniz.
                </p>
            </div>
        )}

        {messages.map((msg, i) => (
            <div key={i} className={`flex w-full ${msg.role === "user" ? "justify-end" : "justify-start"} animate-in slide-in-from-bottom-2 duration-300`}>
              <div className={`flex max-w-[90%] md:max-w-[75%] gap-3 ${msg.role === "user" ? "flex-row-reverse" : "flex-row"}`}>
                
                {/* Avatar */}
                <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 mt-1 shadow-lg ${
                  msg.role === "user" ? "bg-zinc-800 border border-zinc-700" : 
                  msg.role === "error" ? "bg-red-900/20 border border-red-500/30" : "bg-gradient-to-br from-blue-600 to-indigo-600 border border-blue-500/30"
                }`}>
                  {msg.role === "user" ? <User className="w-4 h-4 text-zinc-400"/> : 
                   msg.role === "error" ? <AlertCircle className="w-4 h-4 text-red-500"/> : <Bot className="w-4 h-4 text-white"/>}
                </div>

                {/* Balon */}
                <div className={`px-5 py-3.5 rounded-2xl text-[15px] leading-relaxed shadow-md ${
                  msg.role === "user" 
                    ? "bg-zinc-800 text-white rounded-tr-sm border border-zinc-700" 
                    : msg.role === "error" 
                    ? "bg-red-950/30 border border-red-900 text-red-400 rounded-tl-sm"
                    : "bg-zinc-900/80 border border-zinc-800/80 text-gray-200 rounded-tl-sm backdrop-blur-sm"
                }`}>
                  {msg.role === "bot" ? (
                    // Markdown Render Edici (Bold, Liste vb. için)
                    <div className="prose prose-invert prose-sm max-w-none">
                      <ReactMarkdown>{msg.content}</ReactMarkdown>
                    </div>
                  ) : (
                    msg.content
                  )}
                </div>
              </div>
            </div>
        ))}

        {loading && (
             <div className="flex w-full justify-start animate-fade-in pl-11">
                <div className="bg-zinc-900 border border-zinc-800 px-4 py-3 rounded-2xl rounded-tl-sm flex items-center gap-1.5 shadow-sm">
                   <span className="w-2 h-2 bg-blue-500 rounded-full animate-bounce"></span>
                   <span className="w-2 h-2 bg-blue-500 rounded-full animate-bounce delay-75"></span>
                   <span className="w-2 h-2 bg-blue-500 rounded-full animate-bounce delay-150"></span>
                </div>
             </div>
        )}
        <div ref={chatEndRef} className="h-4" />
      </div>

      {/* INPUT ALANI */}
      <div className="p-4 md:p-6 bg-zinc-950 border-t border-zinc-900/80">
        <div className="relative flex items-center max-w-4xl mx-auto w-full group">
            <input 
              type="text" 
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Merak ettiğin bir trendi sor..."
              disabled={loading}
              className="w-full bg-zinc-900/50 border border-zinc-800 rounded-2xl pl-6 pr-14 py-4 text-white focus:outline-none focus:border-blue-600/50 focus:ring-1 focus:ring-blue-600/50 transition-all placeholder:text-zinc-600 shadow-xl disabled:opacity-50 disabled:cursor-not-allowed"
            />
            <button 
              onClick={handleSendMessage}
              disabled={!chatInput.trim() || loading}
              className="absolute right-3 p-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-xl disabled:opacity-50 disabled:bg-zinc-800 disabled:text-zinc-500 transition-all duration-200 shadow-lg hover:shadow-blue-600/20 active:scale-95"
            >
              {loading ? <RefreshCw className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
            </button>
        </div>
        <div className="text-center mt-3">
          <p className="text-[11px] text-zinc-600">AI yanıtları hatalı olabilir. Önemli kararlar için verileri doğrulayın.</p>
        </div>
      </div>
    </div>
  );
}