"use client";

import "./globals.css";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { 
  LayoutDashboard, 
  LineChart, 
  ShoppingBag, 
  Search, 
  MessageSquare, 
  Bot 
} from "lucide-react";

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();

  return (
    <html lang="tr" className="dark">
      <body className="bg-zinc-950 text-white flex h-screen overflow-hidden font-sans">
        
        {/* --- SABİT SOL MENÜ --- */}
        <aside className="w-64 bg-black border-r border-gray-900 flex flex-col py-6 fixed h-full z-20">
          <div className="mb-8 px-6">
            <h1 className="text-2xl font-bold text-blue-600 tracking-tight">TrendAI</h1>
          </div>

          <nav className="flex-1 w-full space-y-2 px-3">
            <SidebarLink href="/" icon={<MessageSquare />} label="AI Chat Asistanı" active={pathname === "/"} />
            <SidebarLink href="/dashboard" icon={<LayoutDashboard />} label="Dashboard" active={pathname === "/dashboard"} />
            <SidebarLink href="/trends" icon={<LineChart />} label="Trendler" active={pathname.includes("/trends")} />
            <SidebarLink href="/products" icon={<ShoppingBag />} label="Ürünler" active={pathname.includes("/products")} />
            <SidebarLink href="/analyze" icon={<Search />} label="Analiz" active={pathname.includes("/analyze")} />
          </nav>

          <div className="px-6 mt-auto pb-4">
             <div className="flex items-center gap-2 text-xs text-gray-600">
               <Bot className="w-4 h-4"/> v1.0 Beta
             </div>
          </div>
        </aside>

        {/* --- SAĞ TARAF (MAIN) --- */}
        {/* GÜNCELLEME: 'p-8' kaldırıldı, 'h-full' ve 'relative' eklendi */}
        <main className="flex-1 ml-64 h-full bg-zinc-950 relative">
          {children} 
        </main>

      </body>
    </html>
  );
}

// SidebarLink bileşeni aynı kalabilir
function SidebarLink({ href, icon, label, active }: { href: string; icon: any; label: string; active: boolean }) {
  return (
    <Link 
      href={href}
      className={`flex items-center gap-3 p-3 rounded-lg transition-all duration-200 ${
        active ? "text-blue-500 bg-blue-500/10 font-medium" : "text-gray-400 hover:text-white hover:bg-zinc-900"
      }`}
    >
      <div className={`w-5 h-5 ${active ? "text-blue-500" : "text-gray-400"}`}>{icon}</div>
      <span className="text-sm">{label}</span>
    </Link>
  );
}