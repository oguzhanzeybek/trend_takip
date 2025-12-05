"use client";

import "./globals.css";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react"; // State için ekledik
import { 
  LayoutDashboard, 
  LineChart, 
  ShoppingBag, 
  Search, 
  MessageSquare, 
  Bot,
  ChevronLeft,
  ChevronRight,
  Menu
} from "lucide-react";

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const [isCollapsed, setIsCollapsed] = useState(false); // Menü kapalı mı?

  return (
    <html lang="tr" className="dark">
      <body className="bg-zinc-950 text-white flex h-screen overflow-hidden font-sans">
        
        {/* --- DİNAMİK SOL MENÜ --- */}
        <aside 
          className={`
            fixed h-full z-20 bg-black border-r border-gray-900 flex flex-col py-6 transition-all duration-300
            ${isCollapsed ? "w-20" : "w-64"} 
          `}
        >
          {/* Logo ve Toggle Butonu */}
          <div className={`flex items-center mb-8 px-6 ${isCollapsed ? "justify-center" : "justify-between"}`}>
            {!isCollapsed && (
               <h1 className="text-2xl font-bold text-blue-600 tracking-tight whitespace-nowrap">TrendAI</h1>
            )}
            
            <button 
              onClick={() => setIsCollapsed(!isCollapsed)}
              className="p-1.5 rounded-md hover:bg-zinc-800 text-gray-400 transition-colors"
            >
              {isCollapsed ? <ChevronRight size={20} /> : <ChevronLeft size={20} />}
            </button>
          </div>

          <nav className="flex-1 w-full space-y-2 px-3">
            <SidebarLink 
              href="/" 
              icon={<MessageSquare size={22} />} 
              label="AI Chat" 
              active={pathname === "/"} 
              collapsed={isCollapsed}
            />
            <SidebarLink 
              href="/dashboard" 
              icon={<LayoutDashboard size={22} />} 
              label="Dashboard" 
              active={pathname === "/dashboard"} 
              collapsed={isCollapsed}
            />
            <SidebarLink 
              href="/trends" 
              icon={<LineChart size={22} />} 
              label="Trendler" 
              active={pathname.includes("/trends")} 
              collapsed={isCollapsed}
            />
            <SidebarLink 
              href="/products" 
              icon={<ShoppingBag size={22} />} 
              label="Ürünler" 
              active={pathname.includes("/products")} 
              collapsed={isCollapsed}
            />
            <SidebarLink 
              href="/analyze" 
              icon={<Search size={22} />} 
              label="Analiz" 
              active={pathname.includes("/analyze")} 
              collapsed={isCollapsed}
            />
          </nav>

          <div className="px-6 mt-auto pb-4 flex justify-center">
             <div className="flex items-center gap-2 text-xs text-gray-600 whitespace-nowrap overflow-hidden">
               <Bot className="w-4 h-4 min-w-[16px]"/> 
               {!isCollapsed && <span>v1.0 Beta</span>}
             </div>
          </div>
        </aside>

        {/* --- SAĞ TARAF (MAIN) --- */}
        {/* Margin soldan menünün genişliğine göre ayarlanıyor */}
        <main 
          className={`
            flex-1 h-full bg-zinc-950 relative transition-all duration-300
            ${isCollapsed ? "ml-20" : "ml-64"}
          `}
        >
          {children} 
        </main>

      </body>
    </html>
  );
}

// SidebarLink artık collapsed prop'u alıyor
function SidebarLink({ href, icon, label, active, collapsed }: { href: string; icon: any; label: string; active: boolean, collapsed: boolean }) {
  return (
    <Link 
      href={href}
      className={`
        flex items-center gap-3 p-3 rounded-lg transition-all duration-200 group
        ${active ? "text-blue-500 bg-blue-500/10 font-medium" : "text-gray-400 hover:text-white hover:bg-zinc-900"}
        ${collapsed ? "justify-center" : ""}
      `}
      title={collapsed ? label : ""} // Kapalıyken üzerine gelince tooltiip çıksın
    >
      <div className={`w-5 h-5 ${active ? "text-blue-500" : "text-gray-400 group-hover:text-white"}`}>
        {icon}
      </div>
      
      {/* Menü kapalıysa yazıyı gizle, açıksa göster */}
      {!collapsed && (
        <span className="text-sm animate-in fade-in duration-300 whitespace-nowrap">
          {label}
        </span>
      )}
    </Link>
  );
}