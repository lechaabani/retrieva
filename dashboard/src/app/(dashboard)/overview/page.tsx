"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  FileText,
  FolderOpen,
  FolderPlus,
  Search,
  TrendingUp,
  Upload,
  Plus,
  MessageSquare,
  ArrowRight,
  Clock,
  Zap,
  Puzzle,
  Key,
  AlertTriangle,
  Activity,
  Lightbulb,
  X,
  Scissors,
  Maximize2,
  LayoutGrid,
  Bug,
  FileUp,
  ArrowUpDown,
  CheckCircle2,
  type LucideIcon,
} from "lucide-react";
import { StatsCard } from "@/components/stats-card";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  getAnalytics,
  getHealth,
  getDocuments,
  getCollections,
  getActivityFeed,
  getSuggestions,
  type AnalyticsData,
  type HealthStatus,
  type DocumentsResponse,
  type Collection,
  type ActivityEvent,
  type Suggestion,
} from "@/lib/api";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function relativeTime(dateStr: string): string {
  const now = Date.now();
  const then = new Date(dateStr).getTime();
  const diffSec = Math.floor((now - then) / 1000);

  if (diffSec < 60) return "il y a quelques secondes";
  const diffMin = Math.floor(diffSec / 60);
  if (diffMin < 60) return `il y a ${diffMin} min`;
  const diffH = Math.floor(diffMin / 60);
  if (diffH < 24) return `il y a ${diffH}h`;
  const diffD = Math.floor(diffH / 24);
  if (diffD < 30) return `il y a ${diffD}j`;
  const diffM = Math.floor(diffD / 30);
  return `il y a ${diffM} mois`;
}

const EVENT_CONFIG: Record<
  string,
  { icon: React.ReactNode; color: string; dotColor: string }
> = {
  document_ingested: {
    icon: <FileText size={16} />,
    color: "text-emerald-600 dark:text-emerald-400",
    dotColor: "bg-emerald-500",
  },
  query_made: {
    icon: <Search size={16} />,
    color: "text-blue-600 dark:text-blue-400",
    dotColor: "bg-blue-500",
  },
  collection_created: {
    icon: <FolderPlus size={16} />,
    color: "text-violet-600 dark:text-violet-400",
    dotColor: "bg-violet-500",
  },
  api_key_created: {
    icon: <Key size={16} />,
    color: "text-amber-600 dark:text-amber-400",
    dotColor: "bg-amber-500",
  },
  error: {
    icon: <AlertTriangle size={16} />,
    color: "text-red-600 dark:text-red-400",
    dotColor: "bg-red-500",
  },
};

function getEventConfig(type: string) {
  return (
    EVENT_CONFIG[type] ?? {
      icon: <Activity size={16} />,
      color: "text-text-muted",
      dotColor: "bg-gray-400",
    }
  );
}

// ---------------------------------------------------------------------------
// Suggestion icon map & helpers
// ---------------------------------------------------------------------------

const ICON_MAP: Record<string, LucideIcon> = {
  FolderPlus,
  FileUp,
  Scissors,
  Maximize2,
  LayoutGrid,
  Key,
  ArrowUpDown,
  MessageSquare,
  Bug,
  Lightbulb,
  FileText,
  Search,
  Zap,
};

const TYPE_BORDER_COLOR: Record<string, string> = {
  setup: "border-l-blue-500",
  optimization: "border-l-emerald-500",
  tip: "border-l-violet-500",
  warning: "border-l-orange-500",
};

const TYPE_ICON_BG: Record<string, string> = {
  setup: "bg-blue-50 text-blue-600 dark:bg-blue-950 dark:text-blue-400",
  optimization: "bg-emerald-50 text-emerald-600 dark:bg-emerald-950 dark:text-emerald-400",
  tip: "bg-violet-50 text-violet-600 dark:bg-violet-950 dark:text-violet-400",
  warning: "bg-orange-50 text-orange-600 dark:bg-orange-950 dark:text-orange-400",
};

const DISMISSED_KEY = "retrieva_dismissed_suggestions";

function getDismissedIds(): string[] {
  if (typeof window === "undefined") return [];
  try {
    return JSON.parse(localStorage.getItem(DISMISSED_KEY) || "[]");
  } catch {
    return [];
  }
}

function persistDismissedIds(ids: string[]): void {
  localStorage.setItem(DISMISSED_KEY, JSON.stringify(ids));
}

// ---------------------------------------------------------------------------
// Smart Suggestions component
// ---------------------------------------------------------------------------

function SmartSuggestions({ suggestions }: { suggestions: Suggestion[] }) {
  const [dismissedIds, setDismissedIds] = React.useState<string[]>(() =>
    getDismissedIds()
  );

  const visible = suggestions.filter((s) => !dismissedIds.includes(s.id));

  const dismiss = (id: string) => {
    const next = [...dismissedIds, id];
    setDismissedIds(next);
    persistDismissedIds(next);
  };

  if (visible.length === 0) {
    return (
      <Card>
        <CardContent className="flex flex-col items-center justify-center py-10 text-center">
          <div className="w-14 h-14 rounded-full bg-emerald-50 dark:bg-emerald-950 flex items-center justify-center mb-3">
            <CheckCircle2 size={28} className="text-emerald-500" />
          </div>
          <p className="text-sm font-semibold text-text-primary">
            Tout est en ordre !
          </p>
          <p className="text-xs text-text-muted mt-1">
            Votre configuration RAG est optimale.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-3">
      {visible.map((suggestion, index) => {
        const IconComp = ICON_MAP[suggestion.icon] || Lightbulb;
        const borderColor = TYPE_BORDER_COLOR[suggestion.type] || "border-l-gray-400";
        const iconBg = TYPE_ICON_BG[suggestion.type] || "bg-gray-50 text-gray-600";

        return (
          <div
            key={suggestion.id}
            className={`relative flex items-center gap-4 rounded-xl border border-border bg-surface-0 p-4 border-l-4 ${borderColor} transition-all hover:shadow-sm`}
            style={{
              animation: `fadeSlideIn 0.3s ease-out ${index * 0.07}s both`,
            }}
          >
            {/* Icon */}
            <div
              className={`flex-shrink-0 w-10 h-10 rounded-lg flex items-center justify-center ${iconBg}`}
            >
              <IconComp size={20} />
            </div>

            {/* Content */}
            <div className="flex-1 min-w-0">
              <p className="text-sm font-semibold text-text-primary">
                {suggestion.title}
              </p>
              <p className="text-xs text-text-muted mt-0.5 line-clamp-2">
                {suggestion.description}
              </p>
            </div>

            {/* Action button */}
            <Link href={suggestion.action_href} className="flex-shrink-0">
              <Button variant="outline" className="text-xs whitespace-nowrap gap-1">
                {suggestion.action_label}
                <ArrowRight size={14} />
              </Button>
            </Link>

            {/* Dismiss */}
            <button
              onClick={() => dismiss(suggestion.id)}
              className="absolute top-2 right-2 p-1 rounded-md text-text-muted hover:text-text-primary hover:bg-surface-2 transition-colors"
              aria-label="Masquer cette suggestion"
            >
              <X size={14} />
            </button>
          </div>
        );
      })}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Activity Feed component
// ---------------------------------------------------------------------------

function ActivityFeed({ events }: { events: ActivityEvent[] }) {
  if (events.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <div className="w-16 h-16 rounded-full bg-surface-2 flex items-center justify-center mb-4">
          <Activity size={28} className="text-text-muted opacity-50" />
        </div>
        <p className="text-sm font-medium text-text-secondary">
          Aucune activite recente
        </p>
        <p className="text-xs text-text-muted mt-1 max-w-xs">
          Les evenements apparaitront ici au fur et a mesure que vous utilisez la plateforme :
          ingestion de documents, requetes, creation de collections...
        </p>
      </div>
    );
  }

  return (
    <div className="relative">
      {/* Vertical timeline line */}
      <div className="absolute left-[19px] top-2 bottom-2 w-px bg-border" />

      <div className="space-y-1">
        {events.map((event, index) => {
          const config = getEventConfig(event.type);
          return (
            <div
              key={event.id}
              className="relative flex items-start gap-4 py-3 px-1 rounded-lg transition-colors hover:bg-surface-1"
              style={{
                animation: `fadeSlideIn 0.3s ease-out ${index * 0.05}s both`,
              }}
            >
              {/* Timeline dot */}
              <div className="relative z-10 flex-shrink-0 mt-0.5">
                <div
                  className={`w-[10px] h-[10px] rounded-full ring-[3px] ring-surface-0 ${config.dotColor}`}
                  style={{ marginLeft: "15px" }}
                />
              </div>

              {/* Icon */}
              <div
                className={`flex-shrink-0 w-8 h-8 rounded-lg bg-surface-2 flex items-center justify-center ${config.color}`}
              >
                {config.icon}
              </div>

              {/* Content */}
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-text-primary truncate">
                  {event.title}
                </p>
                {event.description && (
                  <p className="text-xs text-text-muted mt-0.5 truncate">
                    {event.description}
                  </p>
                )}
              </div>

              {/* Timestamp */}
              <span className="flex-shrink-0 text-[11px] text-text-muted whitespace-nowrap mt-0.5">
                {relativeTime(event.timestamp)}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

export default function DashboardPage() {
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [docStats, setDocStats] = useState<{ total: number } | null>(null);
  const [collections, setCollections] = useState<Collection[] | null>(null);
  const [activityEvents, setActivityEvents] = useState<ActivityEvent[]>([]);
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const [analyticsResult, healthResult, docsResult, collectionsResult, activityResult, suggestionsResult] =
          await Promise.allSettled([
            getAnalytics({ days: 30 }),
            getHealth(),
            getDocuments({ page: 1, page_size: 1 }),
            getCollections(),
            getActivityFeed(20),
            getSuggestions(),
          ]);
        if (analyticsResult.status === "fulfilled") setAnalytics(analyticsResult.value);
        if (healthResult.status === "fulfilled") setHealth(healthResult.value);
        if (docsResult.status === "fulfilled") setDocStats({ total: docsResult.value.total });
        if (collectionsResult.status === "fulfilled") setCollections(collectionsResult.value);
        if (activityResult.status === "fulfilled")
          setActivityEvents(activityResult.value.events);
        if (suggestionsResult.status === "fulfilled")
          setSuggestions(suggestionsResult.value.suggestions);

        // If all failed, show error
        if (
          analyticsResult.status === "rejected" &&
          healthResult.status === "rejected" &&
          docsResult.status === "rejected" &&
          collectionsResult.status === "rejected"
        ) {
          setError("Failed to connect to the backend API.");
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load dashboard data");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-8 w-48 bg-surface-2 rounded" />
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-32 bg-surface-2 rounded-xl" />
          ))}
        </div>
        <div className="h-64 bg-surface-2 rounded-xl" />
      </div>
    );
  }

  const healthStatus = health?.status === "ok" ? "healthy" : health?.status || null;

  return (
    <div className="space-y-6">
      {/* Keyframe animation for stagger fade-in */}
      <style jsx global>{`
        @keyframes fadeSlideIn {
          from {
            opacity: 0;
            transform: translateY(8px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
      `}</style>

      {/* Hero Banner */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-brand-600 via-brand-700 to-indigo-800 dark:from-brand-700 dark:via-brand-800 dark:to-indigo-950 p-8 text-white">
        <div className="absolute inset-0 opacity-10">
          <div className="absolute -top-24 -right-24 w-96 h-96 rounded-full bg-white/20 blur-3xl" />
          <div className="absolute -bottom-16 -left-16 w-64 h-64 rounded-full bg-white/10 blur-2xl" />
          <svg className="absolute bottom-0 right-0 w-80 h-80 opacity-5" viewBox="0 0 200 200">
            <path d="M20,60 Q60,20 100,60 T180,60 T180,140 T100,140 T20,140 Z" fill="currentColor" />
            <circle cx="50" cy="100" r="8" fill="currentColor" />
            <circle cx="100" cy="60" r="8" fill="currentColor" />
            <circle cx="150" cy="100" r="8" fill="currentColor" />
            <circle cx="100" cy="140" r="8" fill="currentColor" />
            <line x1="50" y1="100" x2="100" y2="60" stroke="currentColor" strokeWidth="2" />
            <line x1="100" y1="60" x2="150" y2="100" stroke="currentColor" strokeWidth="2" />
            <line x1="150" y1="100" x2="100" y2="140" stroke="currentColor" strokeWidth="2" />
            <line x1="100" y1="140" x2="50" y2="100" stroke="currentColor" strokeWidth="2" />
          </svg>
        </div>
        <div className="relative z-10 flex items-center justify-between">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-white/20 backdrop-blur-sm">
                <Zap size={22} className="text-yellow-300" />
              </div>
              <span className="text-xs font-semibold uppercase tracking-widest text-white/70">
                Retrieva Platform
              </span>
            </div>
            <h1 className="text-3xl font-extrabold tracking-tight">
              Le WordPress du RAG
            </h1>
            <p className="mt-2 text-base text-white/80 max-w-lg">
              Plateforme RAG modulaire et extensible. Ingestion, recherche semantique,
              generation augmentee — le tout pilote par un systeme de plugins.
            </p>
            <div className="flex items-center gap-4 mt-4">
              <Link href="/playground">
                <Button
                  variant="outline"
                  className="bg-white/10 border-white/20 text-white hover:bg-white/20 backdrop-blur-sm"
                  icon={<MessageSquare size={16} />}
                >
                  Playground
                </Button>
              </Link>
              <Link href="/plugins">
                <Button
                  variant="outline"
                  className="bg-white/10 border-white/20 text-white hover:bg-white/20 backdrop-blur-sm"
                  icon={<Puzzle size={16} />}
                >
                  Plugins
                </Button>
              </Link>
            </div>
          </div>
          <div className="hidden lg:flex flex-col items-end gap-2">
            {health && (
              <Badge variant={healthStatus === "healthy" ? "success" : "error"} dot>
                System {healthStatus}
              </Badge>
            )}
            <span className="text-xs text-white/50 font-mono">v0.1.0</span>
          </div>
        </div>
      </div>

      {error && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 dark:bg-amber-950 dark:border-amber-800 p-4 text-sm text-amber-700 dark:text-amber-300">
          {error} -- Connect the backend API to see live metrics.
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatsCard
          title="Total Documents"
          value={docStats != null ? docStats.total.toLocaleString() : "--"}
          icon={<FileText size={20} />}
        />
        <StatsCard
          title="Collections"
          value={collections != null ? String(collections.length) : "--"}
          icon={<FolderOpen size={20} />}
          subtitle="Active collections"
        />
        <StatsCard
          title="Total Queries"
          value={analytics?.total_queries != null ? analytics.total_queries.toLocaleString() : "--"}
          icon={<Search size={20} />}
          subtitle="Last 30 days"
        />
        <StatsCard
          title="Avg Confidence"
          value={
            analytics?.avg_confidence != null
              ? `${(analytics.avg_confidence * 100).toFixed(1)}%`
              : "--"
          }
          icon={<TrendingUp size={20} />}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Query Activity (Last 30 Days)</CardTitle>
          </CardHeader>
          <CardContent>
            {analytics?.buckets && analytics.buckets.length > 0 ? (
              <div className="space-y-3">
                {analytics.buckets.slice(-7).map((item, i) => (
                  <div
                    key={i}
                    className="flex items-center justify-between py-2 border-b border-border last:border-0"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-full bg-brand-50 dark:bg-brand-950 flex items-center justify-center text-brand-600">
                        <Search size={14} />
                      </div>
                      <div>
                        <p className="text-sm font-medium text-text-primary">
                          {item.date}
                        </p>
                        <p className="text-xs text-text-muted">
                          {item.query_count} queries &middot; {Math.round(item.avg_latency_ms)}ms avg
                        </p>
                      </div>
                    </div>
                    <Badge variant="info">{item.query_count}</Badge>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-text-muted">
                <Clock size={32} className="mx-auto mb-2 opacity-50" />
                <p className="text-sm">No recent queries</p>
                <p className="text-xs mt-1">
                  Start querying your documents in the Playground
                </p>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <Link href="/documents" className="block">
              <Button variant="outline" className="w-full justify-start" icon={<Upload size={16} />}>
                Upload Document
              </Button>
            </Link>
            <Link href="/collections" className="block">
              <Button variant="outline" className="w-full justify-start" icon={<Plus size={16} />}>
                New Collection
              </Button>
            </Link>
            <Link href="/playground" className="block">
              <Button variant="outline" className="w-full justify-start" icon={<MessageSquare size={16} />}>
                Open Playground
              </Button>
            </Link>

            {health && (
              <div className="mt-6 pt-4 border-t border-border">
                <p className="text-xs font-medium text-text-muted uppercase tracking-wider mb-3">
                  System Health
                </p>
                {health.database && (
                  <div className="flex items-center justify-between py-1.5">
                    <span className="text-sm text-text-secondary">Database</span>
                    <Badge
                      variant={health.database === "healthy" ? "success" : "error"}
                      dot
                    >
                      {health.database}
                    </Badge>
                  </div>
                )}
                {health.components && Object.entries(health.components).map(([name, comp]) => (
                  <div
                    key={name}
                    className="flex items-center justify-between py-1.5"
                  >
                    <span className="text-sm text-text-secondary capitalize">
                      {name}
                    </span>
                    <Badge
                      variant={comp.status === "healthy" ? "success" : "error"}
                      dot
                    >
                      {comp.status}
                    </Badge>
                  </div>
                ))}
                {health.version && (
                  <div className="flex items-center justify-between py-1.5 mt-2 pt-2 border-t border-border">
                    <span className="text-sm text-text-secondary">Version</span>
                    <span className="text-xs text-text-muted font-mono">{health.version}</span>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Smart Suggestions */}
      <div>
        <div className="flex items-center gap-2 mb-3">
          <Lightbulb size={18} className="text-amber-500" />
          <h2 className="text-base font-semibold text-text-primary">
            Suggestions Intelligentes
          </h2>
        </div>
        <SmartSuggestions suggestions={suggestions} />
      </div>

      {/* Activity Feed */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Activity size={18} className="text-brand-600" />
              <CardTitle>Activite Recente</CardTitle>
            </div>
            {activityEvents.length > 0 && (
              <Link href="/logs">
                <Button variant="ghost" className="text-xs gap-1 text-text-muted hover:text-text-primary">
                  Voir tout
                  <ArrowRight size={14} />
                </Button>
              </Link>
            )}
          </div>
        </CardHeader>
        <CardContent>
          <ActivityFeed events={activityEvents} />
        </CardContent>
      </Card>
    </div>
  );
}
