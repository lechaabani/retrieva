"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Zap,
  Settings,
  Code2,
  Database,
  Terminal,
  Puzzle,
  Globe,
  Server,
  ArrowLeft,
  Menu,
  X,
  ChevronRight,
  FileText,
} from "lucide-react";

const sidebarSections = [
  { label: "Vue d\u2019ensemble", href: "/docs", icon: FileText },
  { label: "D\u00e9marrage Rapide", href: "/docs/quickstart", icon: Zap },
  { label: "Configuration", href: "/docs/configuration", icon: Settings },
  { label: "API Reference", href: "/docs/api", icon: Code2 },
  { label: "Connecteurs", href: "/docs/connectors", icon: Database },
  { label: "SDKs", href: "/docs/sdks", icon: Terminal },
  { label: "Plugins", href: "/docs/plugins", icon: Puzzle },
  { label: "Widgets", href: "/docs/widgets", icon: Globe },
  { label: "D\u00e9ploiement", href: "/docs/deployment", icon: Server },
];

export default function DocsLayout({ children }: { children: React.ReactNode }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const pathname = usePathname();

  return (
    <div className="min-h-screen bg-[#0A0A0F] text-white">
      {/* Mobile header */}
      <div className="lg:hidden fixed top-0 left-0 right-0 z-50 bg-gray-950/80 backdrop-blur-xl border-b border-white/5">
        <div className="flex items-center justify-between px-4 h-14">
          <Link href="/" className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center">
              <Zap className="w-3.5 h-3.5 text-white" strokeWidth={2.5} />
            </div>
            <span className="text-sm font-bold text-white">
              retrieva<span className="text-indigo-400">.ai</span>
            </span>
          </Link>
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-2 text-gray-400 hover:text-white"
          >
            {sidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {/* Sidebar overlay (mobile) */}
      {sidebarOpen && (
        <div
          className="lg:hidden fixed inset-0 z-40 bg-black/50 backdrop-blur-sm"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`
          fixed top-0 left-0 z-40 h-screen w-72 bg-[#08080C] border-r border-white/5 overflow-y-auto
          transition-transform duration-300
          lg:translate-x-0
          ${sidebarOpen ? "translate-x-0" : "-translate-x-full"}
        `}
      >
        <div className="p-6">
          {/* Logo */}
          <Link href="/" className="hidden lg:flex items-center gap-2.5 mb-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center">
              <Zap className="w-4 h-4 text-white" strokeWidth={2.5} />
            </div>
            <span className="text-lg font-bold text-white">
              retrieva<span className="text-indigo-400">.ai</span>
            </span>
          </Link>

          {/* Back link */}
          <Link
            href="/"
            className="inline-flex items-center gap-2 text-sm text-gray-500 hover:text-gray-300 transition-colors mt-4 mb-8"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            Retour au site
          </Link>

          {/* Title */}
          <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-4">
            Documentation
          </h2>

          {/* Nav items */}
          <nav className="space-y-1">
            {sidebarSections.map((item) => {
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setSidebarOpen(false)}
                  className={`
                    flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all
                    ${
                      isActive
                        ? "bg-indigo-600/10 text-indigo-400 border border-indigo-500/20"
                        : "text-gray-400 hover:text-white hover:bg-white/5"
                    }
                  `}
                >
                  <item.icon className="w-4 h-4 shrink-0" />
                  {item.label}
                  {isActive && <ChevronRight className="w-3.5 h-3.5 ml-auto" />}
                </Link>
              );
            })}
          </nav>
        </div>
      </aside>

      {/* Main content */}
      <main className="lg:ml-72 pt-14 lg:pt-0 min-h-screen">
        <div className="max-w-4xl mx-auto px-6 py-12 lg:py-16">
          {children}
        </div>
      </main>
    </div>
  );
}
