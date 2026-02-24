"use client";

import React, { useState, useEffect, useCallback } from "react";
import {
  Search,
  Clock,
  ShieldCheck,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  RefreshCw,
  MessageSquareText,
  Database,
  BarChart3,
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  getAnalyticsDashboard,
  type AnalyticsDashboardData,
  type AnalyticsDashboardLatencyTrend,
} from "@/lib/api";

/* ───────────────────────── helpers ───────────────────────── */

function clamp(v: number, min: number, max: number) {
  return Math.max(min, Math.min(max, v));
}

/** Build an SVG polyline path from data points. */
function buildLinePath(
  points: { x: number; y: number }[],
): string {
  if (points.length === 0) return "";
  return points.map((p, i) => `${i === 0 ? "M" : "L"} ${p.x} ${p.y}`).join(" ");
}

/* ───────────────────────── colour helpers ────────────────── */

const COLLECTION_COLORS = [
  "#6366f1",
  "#f59e0b",
  "#10b981",
  "#ef4444",
  "#8b5cf6",
];

const CONFIDENCE_COLORS = [
  "#ef4444",
  "#f97316",
  "#eab308",
  "#22c55e",
  "#16a34a",
];

/* ───────────────────────── page ──────────────────────────── */

export default function AnalyticsPage() {
  const [data, setData] = useState<AnalyticsDashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const d = await getAnalyticsDashboard();
      setData(d);
    } catch {
      setError("Impossible de charger les analytiques. Le backend est peut-être indisponible.");
      setData(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  /* ── loading skeleton ── */
  if (loading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-8 w-56 bg-surface-2 rounded" />
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-32 bg-surface-2 rounded-xl" />
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-80 bg-surface-2 rounded-xl" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* ── Header ── */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">Analytiques</h1>
          <p className="text-sm text-text-secondary mt-1">
            Performance et utilisation de la plateforme
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={load} className="flex items-center gap-2">
          <RefreshCw size={14} />
          Actualiser
        </Button>
      </div>

      {/* ── Error banner ── */}
      {error && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 dark:bg-amber-950 dark:border-amber-800 p-3 text-sm text-amber-700 dark:text-amber-300">
          {error}
        </div>
      )}

      {/* ── Empty state ── */}
      {!data && !error && (
        <div className="text-center py-16">
          <BarChart3 size={48} className="mx-auto text-text-muted opacity-50 mb-4" />
          <h3 className="text-lg font-medium text-text-primary">Aucune donnée</h3>
          <p className="text-sm text-text-muted mt-1">
            Les analytiques apparaîtront ici dès que des requêtes seront effectuées.
          </p>
        </div>
      )}

      {data && (
        <>
          {/* ═══════════════ 1. Top Stats Row ═══════════════ */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard
              label="Requêtes Totales"
              value={data.total_queries.toLocaleString()}
              sub={`${data.queries_today} aujourd'hui · ${data.queries_this_week} cette semaine`}
              icon={<Search size={20} />}
              color="blue"
            />
            <StatCard
              label="Latence Moyenne"
              value={`${Math.round(data.avg_latency_ms)} ms`}
              icon={<Clock size={20} />}
              color="amber"
            />
            <StatCard
              label="Confiance Moyenne"
              value={`${(data.avg_confidence * 100).toFixed(1)}%`}
              icon={<ShieldCheck size={20} />}
              color="green"
            />
            <StatCard
              label="Taux d'Erreur"
              value={`${data.error_rate.toFixed(1)}%`}
              icon={<AlertTriangle size={20} />}
              color="red"
              invertTrend
            />
          </div>

          {/* ═══════════════ 2. Latency Trend Chart ═══════════════ */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Clock size={18} className="text-amber-500" />
                Tendance de Latence
              </CardTitle>
            </CardHeader>
            <CardContent>
              <LatencyTrendChart data={data.latency_trend} />
            </CardContent>
          </Card>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* ═══════════════ 3. Confidence Distribution ═══════════════ */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <ShieldCheck size={18} className="text-emerald-500" />
                  Distribution de Confiance
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ConfidenceDistribution buckets={data.confidence_distribution} />
              </CardContent>
            </Card>

            {/* ═══════════════ 5. Collection Usage ═══════════════ */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Database size={18} className="text-indigo-500" />
                  Utilisation par Collection
                </CardTitle>
              </CardHeader>
              <CardContent>
                <CollectionUsageChart collections={data.collection_usage} />
              </CardContent>
            </Card>
          </div>

          {/* ═══════════════ 4. Top Questions ═══════════════ */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <MessageSquareText size={18} className="text-violet-500" />
                Questions Fréquentes
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <TopQuestionsTable questions={data.top_questions} />
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════
   Sub-components
   ═══════════════════════════════════════════════════════════════ */

/* ── StatCard ── */

const COLOR_MAP: Record<string, { bg: string; text: string; icon: string }> = {
  blue: {
    bg: "bg-blue-50 dark:bg-blue-950",
    text: "text-blue-700 dark:text-blue-300",
    icon: "text-blue-600 dark:text-blue-400",
  },
  amber: {
    bg: "bg-amber-50 dark:bg-amber-950",
    text: "text-amber-700 dark:text-amber-300",
    icon: "text-amber-600 dark:text-amber-400",
  },
  green: {
    bg: "bg-emerald-50 dark:bg-emerald-950",
    text: "text-emerald-700 dark:text-emerald-300",
    icon: "text-emerald-600 dark:text-emerald-400",
  },
  red: {
    bg: "bg-red-50 dark:bg-red-950",
    text: "text-red-700 dark:text-red-300",
    icon: "text-red-600 dark:text-red-400",
  },
};

function StatCard({
  label,
  value,
  sub,
  icon,
  color,
  invertTrend,
}: {
  label: string;
  value: string;
  sub?: string;
  icon: React.ReactNode;
  color: string;
  invertTrend?: boolean;
}) {
  const c = COLOR_MAP[color] ?? COLOR_MAP.blue;
  return (
    <div className="rounded-xl border border-border bg-surface-0 p-5 shadow-sm">
      <div className="flex items-start justify-between">
        <div className="space-y-1 min-w-0">
          <p className="text-sm text-text-muted">{label}</p>
          <p className="text-2xl font-bold text-text-primary">{value}</p>
          {sub && <p className="text-xs text-text-muted truncate">{sub}</p>}
        </div>
        <div className={`rounded-lg p-2.5 ${c.bg} ${c.icon} shrink-0`}>{icon}</div>
      </div>
    </div>
  );
}

/* ── Latency Trend (SVG line chart + bar backdrop) ── */

function LatencyTrendChart({ data }: { data: AnalyticsDashboardLatencyTrend[] }) {
  const [hoveredIdx, setHoveredIdx] = useState<number | null>(null);

  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-text-muted text-sm">
        Aucune donnée sur les 30 derniers jours
      </div>
    );
  }

  const W = 800;
  const H = 260;
  const PAD_L = 55;
  const PAD_R = 15;
  const PAD_T = 20;
  const PAD_B = 40;

  const chartW = W - PAD_L - PAD_R;
  const chartH = H - PAD_T - PAD_B;

  const maxLatency = Math.max(...data.map((d) => d.avg_latency), 1);
  const maxCount = Math.max(...data.map((d) => d.count), 1);

  const xStep = data.length > 1 ? chartW / (data.length - 1) : chartW / 2;
  const barW = Math.max(4, Math.min(20, chartW / data.length - 2));

  const linePoints = data.map((d, i) => ({
    x: PAD_L + i * xStep,
    y: PAD_T + chartH - (d.avg_latency / maxLatency) * chartH,
  }));

  // Y-axis ticks for latency
  const yTicks = 5;
  const yLabels = Array.from({ length: yTicks + 1 }, (_, i) =>
    Math.round((maxLatency / yTicks) * i)
  );

  return (
    <div className="w-full overflow-x-auto">
      <svg
        viewBox={`0 0 ${W} ${H}`}
        className="w-full min-w-[600px]"
        style={{ height: "260px" }}
        onMouseLeave={() => setHoveredIdx(null)}
      >
        {/* grid lines */}
        {yLabels.map((v, i) => {
          const y = PAD_T + chartH - (v / maxLatency) * chartH;
          return (
            <g key={i}>
              <line
                x1={PAD_L}
                y1={y}
                x2={W - PAD_R}
                y2={y}
                stroke="currentColor"
                className="text-border"
                strokeDasharray="3 3"
                strokeWidth={0.5}
              />
              <text
                x={PAD_L - 6}
                y={y + 4}
                textAnchor="end"
                className="text-text-muted"
                fontSize={10}
                fill="currentColor"
              >
                {v}ms
              </text>
            </g>
          );
        })}

        {/* bars (query count) */}
        {data.map((d, i) => {
          const bx = PAD_L + i * xStep - barW / 2;
          const bh = (d.count / maxCount) * chartH * 0.6;
          const by = PAD_T + chartH - bh;
          return (
            <rect
              key={`bar-${i}`}
              x={bx}
              y={by}
              width={barW}
              height={bh}
              rx={2}
              className="fill-indigo-100 dark:fill-indigo-900/40"
            />
          );
        })}

        {/* line */}
        <path
          d={buildLinePath(linePoints)}
          fill="none"
          stroke="#f59e0b"
          strokeWidth={2.5}
          strokeLinejoin="round"
          strokeLinecap="round"
        />

        {/* dots */}
        {linePoints.map((p, i) => (
          <circle
            key={i}
            cx={p.x}
            cy={p.y}
            r={hoveredIdx === i ? 5 : 3}
            fill={hoveredIdx === i ? "#f59e0b" : "#fbbf24"}
            stroke="#fff"
            strokeWidth={1.5}
            className="cursor-pointer transition-all"
            onMouseEnter={() => setHoveredIdx(i)}
          />
        ))}

        {/* X-axis labels */}
        {data.map((d, i) => {
          // show every Nth label to avoid crowding
          const showEvery = Math.max(1, Math.floor(data.length / 8));
          if (i % showEvery !== 0 && i !== data.length - 1) return null;
          return (
            <text
              key={`xl-${i}`}
              x={PAD_L + i * xStep}
              y={H - 8}
              textAnchor="middle"
              className="text-text-muted"
              fontSize={10}
              fill="currentColor"
            >
              {d.date.slice(5)}
            </text>
          );
        })}

        {/* Tooltip */}
        {hoveredIdx !== null && data[hoveredIdx] && (() => {
          const d = data[hoveredIdx];
          const p = linePoints[hoveredIdx];
          const tooltipW = 140;
          const tooltipH = 52;
          let tx = p.x - tooltipW / 2;
          if (tx < PAD_L) tx = PAD_L;
          if (tx + tooltipW > W - PAD_R) tx = W - PAD_R - tooltipW;
          const ty = p.y - tooltipH - 12;
          return (
            <g>
              <rect
                x={tx}
                y={ty}
                width={tooltipW}
                height={tooltipH}
                rx={6}
                className="fill-surface-0 stroke-border"
                strokeWidth={1}
              />
              <text x={tx + 10} y={ty + 18} fontSize={11} className="fill-text-primary" fontWeight={600}>
                {d.date}
              </text>
              <text x={tx + 10} y={ty + 32} fontSize={10} className="fill-text-muted">
                Latence: {d.avg_latency.toFixed(1)} ms
              </text>
              <text x={tx + 10} y={ty + 44} fontSize={10} className="fill-text-muted">
                Requêtes: {d.count}
              </text>
            </g>
          );
        })()}
      </svg>
    </div>
  );
}

/* ── Confidence Distribution (horizontal bars) ── */

function ConfidenceDistribution({
  buckets,
}: {
  buckets: { bucket: string; count: number }[];
}) {
  const max = Math.max(...buckets.map((b) => b.count), 1);
  const total = buckets.reduce((s, b) => s + b.count, 0) || 1;

  const LABELS: Record<string, string> = {
    "0-0.2": "0 – 20%",
    "0.2-0.4": "20 – 40%",
    "0.4-0.6": "40 – 60%",
    "0.6-0.8": "60 – 80%",
    "0.8-1.0": "80 – 100%",
  };

  return (
    <div className="space-y-3">
      {buckets.map((b, i) => {
        const pct = (b.count / total) * 100;
        const barPct = (b.count / max) * 100;
        return (
          <div key={b.bucket} className="flex items-center gap-3">
            <span className="text-xs text-text-muted w-20 shrink-0 text-right">
              {LABELS[b.bucket] ?? b.bucket}
            </span>
            <div className="flex-1 h-7 bg-surface-2 rounded-md overflow-hidden relative">
              <div
                className="h-full rounded-md transition-all duration-500"
                style={{
                  width: `${barPct}%`,
                  backgroundColor: CONFIDENCE_COLORS[i] ?? "#6366f1",
                }}
              />
              <span className="absolute inset-y-0 right-2 flex items-center text-xs font-medium text-text-primary">
                {b.count} ({pct.toFixed(0)}%)
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
}

/* ── Collection Usage (horizontal bars with colour) ── */

function CollectionUsageChart({
  collections,
}: {
  collections: { collection_name: string; query_count: number }[];
}) {
  if (collections.length === 0) {
    return (
      <div className="flex items-center justify-center h-48 text-text-muted text-sm">
        Aucune donnée de collection
      </div>
    );
  }

  const max = Math.max(...collections.map((c) => c.query_count), 1);
  const total = collections.reduce((s, c) => s + c.query_count, 0) || 1;

  return (
    <div className="space-y-4">
      {/* Legend dots */}
      <div className="flex flex-wrap gap-3 mb-2">
        {collections.map((c, i) => (
          <div key={c.collection_name} className="flex items-center gap-1.5 text-xs text-text-muted">
            <span
              className="inline-block w-2.5 h-2.5 rounded-full"
              style={{ backgroundColor: COLLECTION_COLORS[i % COLLECTION_COLORS.length] }}
            />
            {c.collection_name}
          </div>
        ))}
      </div>

      {/* Stacked bar representation */}
      <div className="h-8 rounded-lg overflow-hidden flex bg-surface-2">
        {collections.map((c, i) => {
          const pct = (c.query_count / total) * 100;
          return (
            <div
              key={c.collection_name}
              className="h-full relative group"
              style={{
                width: `${pct}%`,
                backgroundColor: COLLECTION_COLORS[i % COLLECTION_COLORS.length],
                minWidth: pct > 0 ? "4px" : "0px",
              }}
            >
              {/* tooltip on hover */}
              <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 hidden group-hover:block z-10">
                <div className="bg-surface-0 border border-border rounded-md px-2 py-1 text-xs shadow whitespace-nowrap">
                  <span className="font-medium text-text-primary">{c.collection_name}</span>
                  <br />
                  {c.query_count} requêtes ({pct.toFixed(1)}%)
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Detail list */}
      <div className="space-y-2">
        {collections.map((c, i) => {
          const pct = (c.query_count / total) * 100;
          const barPct = (c.query_count / max) * 100;
          return (
            <div key={c.collection_name} className="flex items-center gap-3">
              <span
                className="w-3 h-3 rounded-full shrink-0"
                style={{ backgroundColor: COLLECTION_COLORS[i % COLLECTION_COLORS.length] }}
              />
              <span className="text-sm text-text-primary min-w-0 truncate flex-1">
                {c.collection_name}
              </span>
              <span className="text-xs font-medium text-text-muted shrink-0">
                {c.query_count.toLocaleString()} ({pct.toFixed(0)}%)
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

/* ── Top Questions Table ── */

function TopQuestionsTable({
  questions,
}: {
  questions: { question: string; count: number; avg_confidence: number }[];
}) {
  if (questions.length === 0) {
    return (
      <div className="flex items-center justify-center h-32 text-text-muted text-sm">
        Aucune question enregistrée
      </div>
    );
  }

  function confidenceBadge(c: number) {
    if (c >= 0.8) return "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300";
    if (c >= 0.6) return "bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300";
    if (c >= 0.4) return "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/40 dark:text-yellow-300";
    if (c >= 0.2) return "bg-orange-100 text-orange-700 dark:bg-orange-900/40 dark:text-orange-300";
    return "bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300";
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-border text-left">
            <th className="px-5 py-3 text-xs font-medium text-text-muted uppercase tracking-wider">
              Question
            </th>
            <th className="px-5 py-3 text-xs font-medium text-text-muted uppercase tracking-wider text-right w-24">
              Nombre
            </th>
            <th className="px-5 py-3 text-xs font-medium text-text-muted uppercase tracking-wider text-right w-32">
              Confiance
            </th>
          </tr>
        </thead>
        <tbody>
          {questions.map((q, i) => (
            <tr
              key={i}
              className={`border-b border-border last:border-b-0 ${
                i % 2 === 0 ? "bg-surface-0" : "bg-surface-1"
              }`}
            >
              <td className="px-5 py-3 text-text-primary max-w-md truncate" title={q.question}>
                {q.question}
              </td>
              <td className="px-5 py-3 text-right text-text-secondary font-medium tabular-nums">
                {q.count}
              </td>
              <td className="px-5 py-3 text-right">
                <span
                  className={`inline-block px-2 py-0.5 text-xs font-medium rounded-full ${confidenceBadge(
                    q.avg_confidence
                  )}`}
                >
                  {(q.avg_confidence * 100).toFixed(0)}%
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
