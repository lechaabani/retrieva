"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard,
  Database,
  FileText,
  FolderOpen,
  MessageSquare,
  BarChart3,
  Users,
  Key,
  ScrollText,
  Settings,
  Puzzle,
  Globe,
  Layout,
  Code2,
  Activity,
  FlaskConical,
  ChevronLeft,
  Menu,
  Zap,
  Sun,
  Moon,
  LogOut,
  Keyboard,
  Lock,
  Crown,
  Shield,
} from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import {
  useFeatureFlags,
  getRequiredTier,
  type FeatureName,
  type PlanTier,
} from "@/lib/feature-flags";

interface NavItem {
  label: string;
  href: string;
  icon: React.ReactNode;
  featureFlag?: FeatureName;
}

const navItems: NavItem[] = [
  { label: "Dashboard", href: "/overview", icon: <LayoutDashboard size={20} />, featureFlag: "dashboard" },
  { label: "Sources", href: "/sources", icon: <Database size={20} />, featureFlag: "sources" },
  { label: "Documents", href: "/documents", icon: <FileText size={20} />, featureFlag: "documents" },
  { label: "Collections", href: "/collections", icon: <FolderOpen size={20} />, featureFlag: "collections" },
  { label: "Playground", href: "/playground", icon: <MessageSquare size={20} />, featureFlag: "playground" },
  { label: "Analytics", href: "/analytics", icon: <BarChart3 size={20} />, featureFlag: "analytics" },
  { label: "Evaluation", href: "/evaluation", icon: <FlaskConical size={20} />, featureFlag: "evaluation" },
  { label: "Users", href: "/users", icon: <Users size={20} />, featureFlag: "users" },
  { label: "API Keys", href: "/api-keys", icon: <Key size={20} />, featureFlag: "apiKeys" },
  { label: "Plugins", href: "/plugins", icon: <Puzzle size={20} />, featureFlag: "plugins" },
  { label: "Widgets", href: "/widgets", icon: <Globe size={20} />, featureFlag: "widgets" },
  { label: "Templates", href: "/templates", icon: <Layout size={20} />, featureFlag: "templates" },
  { label: "Developers", href: "/developers", icon: <Code2 size={20} />, featureFlag: "developers" },
  { label: "Logs", href: "/logs", icon: <ScrollText size={20} />, featureFlag: "logs" },
  { label: "Sante", href: "/health", icon: <Activity size={20} />, featureFlag: "health" },
  { label: "Settings", href: "/settings", icon: <Settings size={20} />, featureFlag: "settings" },
];

interface SidebarProps {
  theme: "light" | "dark";
  onToggleTheme: () => void;
}

function TierBadge({ tier, collapsed }: { tier: PlanTier; collapsed: boolean }) {
  if (tier === "community") return null;
  const isEnterprise = tier === "enterprise";
  if (collapsed) {
    return (
      <Lock size={12} className="shrink-0 text-text-muted" />
    );
  }
  return (
    <span
      className={cn(
        "ml-auto inline-flex items-center gap-0.5 rounded px-1.5 py-0.5 text-[10px] font-semibold leading-none",
        isEnterprise
          ? "bg-violet-100 text-violet-700 dark:bg-violet-950 dark:text-violet-300"
          : "bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-300"
      )}
    >
      {isEnterprise ? <Shield size={10} /> : <Crown size={10} />}
      {isEnterprise ? "Enterprise" : "Pro"}
    </span>
  );
}

export function Sidebar({ theme, onToggleTheme }: SidebarProps) {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const flags = useFeatureFlags();

  const isActive = (href: string) => {
    if (href === "/overview") return pathname === "/overview";
    return pathname.startsWith(href);
  };

  const isLocked = (item: NavItem): boolean => {
    if (!item.featureFlag) return false;
    return !flags[item.featureFlag];
  };

  const getItemRequiredTier = (item: NavItem): PlanTier => {
    if (!item.featureFlag) return "community";
    return getRequiredTier(item.featureFlag);
  };

  const sidebarContent = (
    <div className="flex h-full flex-col">
      <div
        className={cn(
          "flex items-center gap-3 border-b border-border px-4 h-16 shrink-0",
          collapsed && "justify-center px-2"
        )}
      >
        <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-brand-600 text-white">
          <Zap size={18} />
        </div>
        {!collapsed && (
          <div className="flex flex-col">
            <span className="text-lg font-bold text-text-primary leading-tight">Retrieva</span>
            <span className="text-[10px] font-medium text-text-muted leading-tight tracking-wide">Le WordPress du RAG</span>
          </div>
        )}
      </div>

      <nav className="flex-1 overflow-y-auto scrollbar-thin py-3 px-2 space-y-0.5">
        {navItems.map((item) => {
          const locked = isLocked(item);
          const requiredTier = getItemRequiredTier(item);
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={() => setMobileOpen(false)}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors duration-150",
                collapsed && "justify-center px-2",
                locked && "opacity-50",
                isActive(item.href) && !locked
                  ? "bg-brand-50 text-brand-700 dark:bg-brand-950 dark:text-brand-300"
                  : "text-text-secondary hover:text-text-primary hover:bg-surface-2"
              )}
              title={
                collapsed
                  ? locked
                    ? `${item.label} (${requiredTier})`
                    : item.label
                  : undefined
              }
            >
              <span className="shrink-0">{item.icon}</span>
              {!collapsed && <span>{item.label}</span>}
              {locked && <TierBadge tier={requiredTier} collapsed={collapsed} />}
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-border p-2 space-y-1 shrink-0">
        {user && (
          <>
            <div className={cn(
              "flex items-center gap-3 px-3 py-2 text-sm text-text-secondary",
              collapsed && "justify-center px-2"
            )}>
              <div className="w-7 h-7 rounded-full bg-brand-100 dark:bg-brand-900 flex items-center justify-center text-brand-600 text-xs font-bold shrink-0">
                {user.email[0].toUpperCase()}
              </div>
              {!collapsed && (
                <span className="truncate text-xs">{user.email}</span>
              )}
            </div>
            <button
              onClick={logout}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-text-secondary hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-950 transition-colors w-full",
                collapsed && "justify-center px-2"
              )}
              title={collapsed ? "Deconnexion" : undefined}
            >
              <LogOut size={20} />
              {!collapsed && "Deconnexion"}
            </button>
          </>
        )}
        <button
          onClick={onToggleTheme}
          className={cn(
            "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-text-secondary hover:text-text-primary hover:bg-surface-2 transition-colors w-full",
            collapsed && "justify-center px-2"
          )}
          title={collapsed ? (theme === "light" ? "Dark mode" : "Light mode") : undefined}
        >
          {theme === "light" ? <Moon size={20} /> : <Sun size={20} />}
          {!collapsed && (theme === "light" ? "Dark mode" : "Light mode")}
        </button>
        <button
          onClick={() => window.dispatchEvent(new CustomEvent("open-shortcuts-help"))}
          className={cn(
            "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-text-secondary hover:text-text-primary hover:bg-surface-2 transition-colors w-full",
            collapsed && "justify-center px-2"
          )}
          title={collapsed ? "Raccourcis clavier" : undefined}
        >
          <Keyboard size={20} />
          {!collapsed && "Raccourcis"}
        </button>
        <button
          onClick={() => setCollapsed(!collapsed)}
          className={cn(
            "hidden lg:flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-text-secondary hover:text-text-primary hover:bg-surface-2 transition-colors w-full",
            collapsed && "justify-center px-2"
          )}
        >
          <ChevronLeft
            size={20}
            className={cn("transition-transform", collapsed && "rotate-180")}
          />
          {!collapsed && "Collapse"}
        </button>
      </div>
    </div>
  );

  return (
    <>
      {/* Mobile trigger */}
      <button
        onClick={() => setMobileOpen(true)}
        className="fixed top-4 left-4 z-40 lg:hidden rounded-lg p-2 bg-surface-0 border border-border shadow-sm text-text-primary hover:bg-surface-2 transition-colors"
      >
        <Menu size={20} />
      </button>

      {/* Mobile overlay */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 lg:hidden animate-fade-in"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Mobile sidebar */}
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-50 w-64 bg-surface-0 border-r border-border transform transition-transform duration-200 lg:hidden",
          mobileOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        {sidebarContent}
      </aside>

      {/* Desktop sidebar */}
      <aside
        className={cn(
          "hidden lg:flex flex-col h-screen bg-surface-0 border-r border-border transition-all duration-200 shrink-0 sticky top-0",
          collapsed ? "w-16" : "w-60"
        )}
      >
        {sidebarContent}
      </aside>
    </>
  );
}
