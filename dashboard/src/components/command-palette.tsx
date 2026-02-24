"use client";

import React, { useState, useEffect, useRef, useCallback, useMemo } from "react";
import { useRouter } from "next/navigation";
import {
  LayoutDashboard, Database, FileText, FolderOpen, MessageSquare,
  BarChart3, Users, Key, ScrollText, Settings, Puzzle, Globe,
  Layout, Code2, Activity, FlaskConical, Search, Upload, Plus,
  ArrowRight, Command,
} from "lucide-react";

interface CommandItem {
  id: string;
  label: string;
  description?: string;
  icon: React.ReactNode;
  section: "navigation" | "actions" | "recent";
  action: () => void;
  keywords?: string[];
}

export function CommandPalette() {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLDivElement>(null);

  const allItems: CommandItem[] = useMemo(() => [
    // Navigation
    { id: "nav-dashboard", label: "Dashboard", description: "Vue d'ensemble", icon: <LayoutDashboard size={18} />, section: "navigation" as const, action: () => router.push("/overview"), keywords: ["home", "accueil"] },
    { id: "nav-sources", label: "Sources", description: "Connecteurs de donnees", icon: <Database size={18} />, section: "navigation" as const, action: () => router.push("/sources"), keywords: ["connectors", "data"] },
    { id: "nav-documents", label: "Documents", description: "Documents indexes", icon: <FileText size={18} />, section: "navigation" as const, action: () => router.push("/documents"), keywords: ["files", "fichiers"] },
    { id: "nav-collections", label: "Collections", description: "Groupes de documents", icon: <FolderOpen size={18} />, section: "navigation" as const, action: () => router.push("/collections"), keywords: ["groups", "folders"] },
    { id: "nav-playground", label: "Playground", description: "Tester les requetes RAG", icon: <MessageSquare size={18} />, section: "navigation" as const, action: () => router.push("/playground"), keywords: ["query", "test", "chat"] },
    { id: "nav-analytics", label: "Analytics", description: "Metriques et graphiques", icon: <BarChart3 size={18} />, section: "navigation" as const, action: () => router.push("/analytics"), keywords: ["metrics", "stats", "charts"] },
    { id: "nav-evaluation", label: "Evaluation", description: "Tests de qualite RAG", icon: <FlaskConical size={18} />, section: "navigation" as const, action: () => router.push("/evaluation"), keywords: ["test", "quality", "eval"] },
    { id: "nav-users", label: "Users", description: "Gestion des utilisateurs", icon: <Users size={18} />, section: "navigation" as const, action: () => router.push("/users"), keywords: ["team", "accounts"] },
    { id: "nav-apikeys", label: "API Keys", description: "Cles d'acces API", icon: <Key size={18} />, section: "navigation" as const, action: () => router.push("/api-keys"), keywords: ["keys", "tokens", "auth"] },
    { id: "nav-plugins", label: "Plugins", description: "Extensions et marketplace", icon: <Puzzle size={18} />, section: "navigation" as const, action: () => router.push("/plugins"), keywords: ["extensions", "marketplace", "addons"] },
    { id: "nav-widgets", label: "Widgets", description: "Widgets embarquables", icon: <Globe size={18} />, section: "navigation" as const, action: () => router.push("/widgets"), keywords: ["embed", "chatbot", "search bar"] },
    { id: "nav-templates", label: "Templates", description: "Applications standalone", icon: <Layout size={18} />, section: "navigation" as const, action: () => router.push("/templates"), keywords: ["apps", "deploy"] },
    { id: "nav-developers", label: "Developers", description: "SDKs, API docs, CLI", icon: <Code2 size={18} />, section: "navigation" as const, action: () => router.push("/developers"), keywords: ["api", "sdk", "docs"] },
    { id: "nav-logs", label: "Logs", description: "Journal des requetes", icon: <ScrollText size={18} />, section: "navigation" as const, action: () => router.push("/logs"), keywords: ["history", "journal"] },
    { id: "nav-health", label: "Sante", description: "Monitoring des services", icon: <Activity size={18} />, section: "navigation" as const, action: () => router.push("/health"), keywords: ["health", "monitoring", "status"] },
    { id: "nav-settings", label: "Settings", description: "Configuration plateforme", icon: <Settings size={18} />, section: "navigation" as const, action: () => router.push("/settings"), keywords: ["config", "preferences"] },
    // Actions
    { id: "act-upload", label: "Upload un document", description: "Ajouter un fichier", icon: <Upload size={18} />, section: "actions" as const, action: () => router.push("/documents"), keywords: ["upload", "import", "add file"] },
    { id: "act-new-collection", label: "Nouvelle collection", description: "Creer une collection", icon: <Plus size={18} />, section: "actions" as const, action: () => router.push("/collections"), keywords: ["create", "new", "add"] },
    { id: "act-new-widget", label: "Nouveau widget", description: "Creer un widget", icon: <Globe size={18} />, section: "actions" as const, action: () => router.push("/widgets"), keywords: ["create", "embed"] },
    { id: "act-query", label: "Nouvelle requete", description: "Ouvrir le playground", icon: <MessageSquare size={18} />, section: "actions" as const, action: () => router.push("/playground"), keywords: ["ask", "question", "search"] },
  ], [router]);

  const filtered = useMemo(() => {
    if (!query.trim()) return allItems;
    const q = query.toLowerCase();
    return allItems.filter(item => {
      const searchText = `${item.label} ${item.description || ""} ${(item.keywords || []).join(" ")}`.toLowerCase();
      return searchText.includes(q);
    });
  }, [query, allItems]);

  const sections = useMemo(() => {
    const grouped: Record<string, CommandItem[]> = {};
    for (const item of filtered) {
      if (!grouped[item.section]) grouped[item.section] = [];
      grouped[item.section].push(item);
    }
    return grouped;
  }, [filtered]);

  const flatItems = useMemo(() => filtered, [filtered]);

  // Keyboard shortcut to open
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setOpen(prev => !prev);
      }
      if (e.key === "Escape") {
        setOpen(false);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  // Focus input when opened
  useEffect(() => {
    if (open) {
      setQuery("");
      setSelectedIndex(0);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [open]);

  // Keyboard navigation
  const handleInputKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setSelectedIndex(prev => Math.min(prev + 1, flatItems.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setSelectedIndex(prev => Math.max(prev - 1, 0));
    } else if (e.key === "Enter") {
      e.preventDefault();
      if (flatItems[selectedIndex]) {
        flatItems[selectedIndex].action();
        setOpen(false);
      }
    }
  }, [flatItems, selectedIndex]);

  // Scroll selected item into view
  useEffect(() => {
    const el = listRef.current?.querySelector(`[data-index="${selectedIndex}"]`);
    el?.scrollIntoView({ block: "nearest" });
  }, [selectedIndex]);

  if (!open) return null;

  const sectionLabels: Record<string, string> = {
    navigation: "Navigation",
    actions: "Actions rapides",
    recent: "Recent",
  };

  let globalIndex = 0;

  return (
    <div className="fixed inset-0 z-[100] flex items-start justify-center pt-[20vh]">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm animate-fade-in"
        onClick={() => setOpen(false)}
      />

      {/* Modal */}
      <div className="relative w-full max-w-xl mx-4 bg-surface-0 rounded-2xl shadow-2xl border border-border overflow-hidden animate-slide-in">
        {/* Search Input */}
        <div className="flex items-center gap-3 px-4 border-b border-border">
          <Search size={18} className="text-text-muted shrink-0" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => { setQuery(e.target.value); setSelectedIndex(0); }}
            onKeyDown={handleInputKeyDown}
            placeholder="Rechercher une page, action..."
            className="flex-1 py-4 bg-transparent text-text-primary text-sm outline-none placeholder:text-text-muted"
          />
          <kbd className="hidden sm:flex items-center gap-0.5 px-1.5 py-0.5 rounded bg-surface-2 text-[10px] text-text-muted font-mono">
            ESC
          </kbd>
        </div>

        {/* Results */}
        <div ref={listRef} className="max-h-[360px] overflow-y-auto scrollbar-thin p-2">
          {flatItems.length === 0 ? (
            <div className="py-8 text-center text-text-muted text-sm">
              Aucun resultat pour &quot;{query}&quot;
            </div>
          ) : (
            Object.entries(sections).map(([sectionKey, items]) => (
              <div key={sectionKey}>
                <div className="px-2 py-1.5 text-[10px] font-semibold text-text-muted uppercase tracking-wider">
                  {sectionLabels[sectionKey] || sectionKey}
                </div>
                {items.map((item) => {
                  const idx = globalIndex++;
                  return (
                    <button
                      key={item.id}
                      data-index={idx}
                      onClick={() => { item.action(); setOpen(false); }}
                      onMouseEnter={() => setSelectedIndex(idx)}
                      className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-left transition-colors ${
                        selectedIndex === idx
                          ? "bg-brand-50 dark:bg-brand-950 text-brand-700 dark:text-brand-300"
                          : "text-text-primary hover:bg-surface-2"
                      }`}
                    >
                      <span className={`shrink-0 ${selectedIndex === idx ? "text-brand-600" : "text-text-muted"}`}>
                        {item.icon}
                      </span>
                      <div className="flex-1 min-w-0">
                        <span className="text-sm font-medium">{item.label}</span>
                        {item.description && (
                          <span className="text-xs text-text-muted ml-2">{item.description}</span>
                        )}
                      </div>
                      {selectedIndex === idx && (
                        <ArrowRight size={14} className="shrink-0 text-brand-500" />
                      )}
                    </button>
                  );
                })}
              </div>
            ))
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-4 py-2.5 border-t border-border bg-surface-1 text-[10px] text-text-muted">
          <div className="flex items-center gap-3">
            <span className="flex items-center gap-1"><kbd className="px-1 py-0.5 rounded bg-surface-2 font-mono">↑↓</kbd> Naviguer</span>
            <span className="flex items-center gap-1"><kbd className="px-1 py-0.5 rounded bg-surface-2 font-mono">↵</kbd> Ouvrir</span>
            <span className="flex items-center gap-1"><kbd className="px-1 py-0.5 rounded bg-surface-2 font-mono">esc</kbd> Fermer</span>
          </div>
          <span className="flex items-center gap-1">
            <Command size={10} />K pour ouvrir
          </span>
        </div>
      </div>
    </div>
  );
}
