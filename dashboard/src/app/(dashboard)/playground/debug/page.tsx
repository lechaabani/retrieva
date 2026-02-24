"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  Bug,
  ArrowRight,
  Cpu,
  Database,
  ArrowUpDown,
  Sparkles,
  Clock,
  ChevronDown,
  ChevronRight,
  ArrowLeft,
  Zap,
  Search,
  Hash,
  Check,
  ArrowUp,
  ArrowDown,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import {
  queryDebug,
  getCollections,
  type DebugQueryResponse,
  type DebugStep,
  type DebugChunk,
  type Collection,
  type Source,
} from "@/lib/api";

/* -------------------------------------------------------------------------- */
/*  Helpers                                                                    */
/* -------------------------------------------------------------------------- */

const STEP_ICONS: Record<string, React.ReactNode> = {
  embedding: <Cpu size={18} />,
  retrieval: <Database size={18} />,
  reranking: <ArrowUpDown size={18} />,
  generation: <Sparkles size={18} />,
};

const STEP_COLORS: Record<string, string> = {
  embedding: "text-violet-500",
  retrieval: "text-blue-500",
  reranking: "text-amber-500",
  generation: "text-emerald-500",
};

const STEP_BG: Record<string, string> = {
  embedding: "bg-violet-500/10 border-violet-500/30",
  retrieval: "bg-blue-500/10 border-blue-500/30",
  reranking: "bg-amber-500/10 border-amber-500/30",
  generation: "bg-emerald-500/10 border-emerald-500/30",
};

const STEP_BAR_BG: Record<string, string> = {
  embedding: "bg-violet-500",
  retrieval: "bg-blue-500",
  reranking: "bg-amber-500",
  generation: "bg-emerald-500",
};

function durationVariant(ms: number): "success" | "warning" | "error" {
  if (ms < 200) return "success";
  if (ms < 500) return "warning";
  return "error";
}

function durationBarColor(ms: number): string {
  if (ms < 200) return "bg-emerald-500";
  if (ms < 500) return "bg-amber-500";
  return "bg-red-500";
}

/* -------------------------------------------------------------------------- */
/*  Pipeline Step Card                                                         */
/* -------------------------------------------------------------------------- */

function PipelineStepCard({
  step,
  isActive,
  isComplete,
  onClick,
}: {
  step: DebugStep;
  isActive: boolean;
  isComplete: boolean;
  onClick: () => void;
}) {
  const icon = STEP_ICONS[step.name] || <Zap size={18} />;
  const color = STEP_COLORS[step.name] || "text-text-primary";
  const bg = STEP_BG[step.name] || "bg-surface-1 border-border";
  const maxDuration = 1000;
  const barWidth = Math.min((step.duration_ms / maxDuration) * 100, 100);

  return (
    <button
      onClick={onClick}
      className={`relative flex flex-col items-center gap-2 p-4 rounded-xl border transition-all duration-200 min-w-[140px] cursor-pointer
        ${bg}
        ${isActive ? "ring-2 ring-brand-600 shadow-lg scale-105" : "hover:scale-[1.02] hover:shadow-md"}
      `}
    >
      {/* Icon */}
      <div className={`${color} transition-colors`}>{icon}</div>

      {/* Label */}
      <span className="text-xs font-semibold text-text-primary uppercase tracking-wide">
        {step.label}
      </span>

      {/* Duration */}
      <Badge variant={durationVariant(step.duration_ms)} className="text-[10px]">
        <Clock size={10} className="mr-0.5" />
        {step.duration_ms}ms
      </Badge>

      {/* Duration bar */}
      <div className="w-full h-1.5 rounded-full bg-surface-3 overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ${durationBarColor(step.duration_ms)}`}
          style={{ width: `${barWidth}%` }}
        />
      </div>

      {/* Status indicator */}
      <div className="absolute -top-1.5 -right-1.5">
        {isComplete ? (
          <div className="h-5 w-5 rounded-full bg-emerald-500 flex items-center justify-center shadow-sm">
            <Check size={12} className="text-white" />
          </div>
        ) : (
          <div className="h-5 w-5 rounded-full bg-surface-3 border-2 border-border animate-pulse" />
        )}
      </div>
    </button>
  );
}

/* -------------------------------------------------------------------------- */
/*  Pipeline Arrow                                                             */
/* -------------------------------------------------------------------------- */

function PipelineArrow() {
  return (
    <div className="flex items-center px-1">
      <div className="w-8 border-t-2 border-dashed border-text-muted relative">
        <div
          className="absolute top-0 left-0 w-full border-t-2 border-dashed border-brand-600 animate-flow"
          style={{ animationDuration: "1.5s" }}
        />
      </div>
      <ArrowRight size={14} className="text-text-muted -ml-1 shrink-0" />
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/*  Step Detail Panels                                                         */
/* -------------------------------------------------------------------------- */

function EmbeddingDetails({ step }: { step: DebugStep }) {
  const provider = (step.details.provider as string) || "openai";
  const model = (step.details.model as string) || "text-embedding-3-small";
  const dimensions = (step.details.dimensions as number) || 1536;

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      <div className="space-y-1">
        <span className="text-xs text-text-muted uppercase tracking-wider">Provider</span>
        <p className="text-sm font-medium text-text-primary">{provider}</p>
      </div>
      <div className="space-y-1">
        <span className="text-xs text-text-muted uppercase tracking-wider">Model</span>
        <p className="text-sm font-medium text-text-primary">{model}</p>
      </div>
      <div className="space-y-1">
        <span className="text-xs text-text-muted uppercase tracking-wider">Dimensions</span>
        <div className="flex items-center gap-1.5">
          <Hash size={14} className="text-violet-500" />
          <p className="text-sm font-medium text-text-primary">{dimensions}</p>
        </div>
      </div>
      <div className="col-span-full">
        <span className="text-xs text-text-muted uppercase tracking-wider">Latence</span>
        <div className="mt-1.5 w-full h-3 rounded-full bg-surface-3 overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-700 ${durationBarColor(step.duration_ms)}`}
            style={{ width: `${Math.min((step.duration_ms / 500) * 100, 100)}%` }}
          />
        </div>
        <p className="text-xs text-text-muted mt-1">{step.duration_ms}ms</p>
      </div>
    </div>
  );
}

function RetrievalDetails({ step }: { step: DebugStep }) {
  const strategy = (step.details.strategy as string) || "vector";
  const resultCount = step.chunks?.length || (step.details.result_count as number) || 0;
  const chunks = step.chunks || [];

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-6">
        <div className="space-y-1">
          <span className="text-xs text-text-muted uppercase tracking-wider">Strategie</span>
          <div className="flex items-center gap-1.5">
            <Badge variant={strategy === "hybrid" ? "warning" : "info"}>
              {strategy}
            </Badge>
          </div>
        </div>
        <div className="space-y-1">
          <span className="text-xs text-text-muted uppercase tracking-wider">Resultats</span>
          <p className="text-sm font-medium text-text-primary">{resultCount} chunks</p>
        </div>
      </div>

      {chunks.length > 0 && (
        <div className="space-y-2">
          <span className="text-xs text-text-muted uppercase tracking-wider">Chunks retrouves</span>
          {chunks.map((chunk, i) => (
            <ChunkCard key={i} chunk={chunk} index={i} />
          ))}
        </div>
      )}
    </div>
  );
}

function ChunkCard({ chunk, index }: { chunk: DebugChunk; index: number }) {
  const [expanded, setExpanded] = useState(false);
  const scorePercent = Math.round(chunk.score * 100);

  return (
    <div className="rounded-lg border border-border bg-surface-1 overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center gap-3 p-3 text-left hover:bg-surface-2 transition-colors"
      >
        <span className="text-xs font-mono text-text-muted w-6 shrink-0">#{index + 1}</span>
        <div className="flex-1 min-w-0">
          <p className="text-sm text-text-primary truncate">
            {chunk.content.slice(0, 100)}...
          </p>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <div className="w-20 h-2 rounded-full bg-surface-3 overflow-hidden">
            <div
              className="h-full rounded-full bg-blue-500 transition-all duration-500"
              style={{ width: `${scorePercent}%` }}
            />
          </div>
          <span className="text-xs font-medium text-text-primary w-10 text-right">{scorePercent}%</span>
          {expanded ? <ChevronDown size={14} className="text-text-muted" /> : <ChevronRight size={14} className="text-text-muted" />}
        </div>
      </button>
      {expanded && (
        <div className="px-3 pb-3 border-t border-border">
          <p className="text-sm text-text-secondary whitespace-pre-wrap mt-2 leading-relaxed">
            {chunk.content}
          </p>
          <p className="text-xs text-text-muted mt-2">
            Doc: <span className="font-mono">{chunk.doc_id}</span>
          </p>
        </div>
      )}
    </div>
  );
}

function RerankingDetails({ step }: { step: DebugStep }) {
  const before = (step.details.before as DebugChunk[]) || step.chunks || [];
  const after = (step.details.after as DebugChunk[]) || [];

  if (before.length === 0 && after.length === 0) {
    return (
      <p className="text-sm text-text-muted">Aucune donnee de reranking disponible.</p>
    );
  }

  return (
    <div className="space-y-3">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Before */}
        <div>
          <span className="text-xs text-text-muted uppercase tracking-wider mb-2 block">
            Avant reranking ({before.length})
          </span>
          <div className="space-y-1.5">
            {before.map((chunk, i) => {
              const scorePercent = Math.round(chunk.score * 100);
              return (
                <div key={i} className="flex items-center gap-2 p-2 rounded-lg bg-surface-1 border border-border">
                  <span className="text-xs font-mono text-text-muted w-5">#{i + 1}</span>
                  <p className="text-xs text-text-primary flex-1 truncate">{chunk.content.slice(0, 60)}</p>
                  <span className="text-xs font-medium text-text-secondary">{scorePercent}%</span>
                </div>
              );
            })}
          </div>
        </div>
        {/* After */}
        <div>
          <span className="text-xs text-text-muted uppercase tracking-wider mb-2 block">
            Apres reranking ({after.length})
          </span>
          <div className="space-y-1.5">
            {after.map((chunk, i) => {
              const scorePercent = Math.round(chunk.score * 100);
              const beforeIndex = before.findIndex((b) => b.doc_id === chunk.doc_id);
              const moved = beforeIndex >= 0 ? beforeIndex - i : 0;
              return (
                <div key={i} className="flex items-center gap-2 p-2 rounded-lg bg-surface-1 border border-border">
                  <span className="text-xs font-mono text-text-muted w-5">#{i + 1}</span>
                  <p className="text-xs text-text-primary flex-1 truncate">{chunk.content.slice(0, 60)}</p>
                  {moved > 0 && (
                    <span className="flex items-center text-emerald-500">
                      <ArrowUp size={10} />
                      <span className="text-[10px] font-medium">{moved}</span>
                    </span>
                  )}
                  {moved < 0 && (
                    <span className="flex items-center text-red-500">
                      <ArrowDown size={10} />
                      <span className="text-[10px] font-medium">{Math.abs(moved)}</span>
                    </span>
                  )}
                  <span className="text-xs font-medium text-text-secondary">{scorePercent}%</span>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}

function GenerationDetails({ step }: { step: DebugStep }) {
  const provider = (step.details.provider as string) || "openai";
  const model = (step.details.model as string) || "gpt-4";
  const tokens = (step.details.tokens_used as number) || 0;
  const answer = (step.details.answer as string) || "";

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="space-y-1">
          <span className="text-xs text-text-muted uppercase tracking-wider">Provider</span>
          <p className="text-sm font-medium text-text-primary">{provider}</p>
        </div>
        <div className="space-y-1">
          <span className="text-xs text-text-muted uppercase tracking-wider">Model</span>
          <p className="text-sm font-medium text-text-primary">{model}</p>
        </div>
        <div className="space-y-1">
          <span className="text-xs text-text-muted uppercase tracking-wider">Tokens utilises</span>
          <p className="text-sm font-medium text-text-primary">{tokens}</p>
        </div>
      </div>
      {answer && (
        <div className="space-y-1">
          <span className="text-xs text-text-muted uppercase tracking-wider">Reponse generee</span>
          <div className="rounded-lg border border-border bg-surface-1 p-4">
            <p className="text-sm text-text-primary leading-relaxed whitespace-pre-wrap">{answer}</p>
          </div>
        </div>
      )}
    </div>
  );
}

function StepDetailPanel({ step }: { step: DebugStep }) {
  switch (step.name) {
    case "embedding":
      return <EmbeddingDetails step={step} />;
    case "retrieval":
      return <RetrievalDetails step={step} />;
    case "reranking":
      return <RerankingDetails step={step} />;
    case "generation":
      return <GenerationDetails step={step} />;
    default:
      return (
        <pre className="text-xs text-text-secondary bg-surface-1 rounded-lg p-3 overflow-auto">
          {JSON.stringify(step.details, null, 2)}
        </pre>
      );
  }
}

/* -------------------------------------------------------------------------- */
/*  Latency Breakdown Bar                                                      */
/* -------------------------------------------------------------------------- */

function LatencyBreakdown({ steps, total }: { steps: DebugStep[]; total: number }) {
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold text-text-primary uppercase tracking-wider">
          Repartition de la latence
        </span>
        <span className="text-xs text-text-muted">{total}ms total</span>
      </div>
      <div className="flex h-6 rounded-full overflow-hidden bg-surface-3">
        {steps.map((step) => {
          const pct = total > 0 ? (step.duration_ms / total) * 100 : 0;
          if (pct < 0.5) return null;
          const bg = STEP_BAR_BG[step.name] || "bg-gray-500";
          return (
            <div
              key={step.name}
              className={`${bg} relative group transition-all duration-500 flex items-center justify-center`}
              style={{ width: `${pct}%` }}
              title={`${step.label}: ${step.duration_ms}ms (${pct.toFixed(1)}%)`}
            >
              {pct > 12 && (
                <span className="text-[10px] font-medium text-white truncate px-1">
                  {step.label}
                </span>
              )}
              {/* Tooltip */}
              <div className="absolute bottom-full mb-1.5 left-1/2 -translate-x-1/2 pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity bg-surface-0 border border-border rounded-lg shadow-lg px-2.5 py-1.5 whitespace-nowrap z-10">
                <p className="text-xs font-medium text-text-primary">{step.label}</p>
                <p className="text-[10px] text-text-muted">{step.duration_ms}ms ({pct.toFixed(1)}%)</p>
              </div>
            </div>
          );
        })}
      </div>
      <div className="flex flex-wrap gap-3">
        {steps.map((step) => {
          const bg = STEP_BAR_BG[step.name] || "bg-gray-500";
          return (
            <div key={step.name} className="flex items-center gap-1.5">
              <div className={`h-2.5 w-2.5 rounded-sm ${bg}`} />
              <span className="text-xs text-text-muted">{step.label}</span>
              <span className="text-xs font-medium text-text-primary">{step.duration_ms}ms</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/*  Sources Panel                                                              */
/* -------------------------------------------------------------------------- */

function SourcesPanel({ sources }: { sources: Source[] }) {
  const [expanded, setExpanded] = useState<Set<number>>(new Set());

  const toggle = (idx: number) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(idx)) next.delete(idx);
      else next.add(idx);
      return next;
    });
  };

  if (!sources.length) return null;

  return (
    <div className="space-y-2">
      {sources.map((source, idx) => (
        <div key={idx} className="rounded-lg border border-border overflow-hidden bg-surface-0">
          <button
            onClick={() => toggle(idx)}
            className="w-full flex items-center justify-between p-3 text-left hover:bg-surface-1 transition-colors"
          >
            <div className="flex items-center gap-2 min-w-0">
              {expanded.has(idx) ? (
                <ChevronDown size={14} className="shrink-0 text-text-muted" />
              ) : (
                <ChevronRight size={14} className="shrink-0 text-text-muted" />
              )}
              <span className="text-sm font-medium text-text-primary truncate">
                {source.document_id}
              </span>
            </div>
            <Badge variant="info">{(source.score * 100).toFixed(0)}%</Badge>
          </button>
          {expanded.has(idx) && (
            <div className="px-3 pb-3 border-t border-border">
              <p className="text-sm text-text-secondary whitespace-pre-wrap mt-2 leading-relaxed">
                {source.content}
              </p>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/*  Main Page                                                                  */
/* -------------------------------------------------------------------------- */

export default function DebugPage() {
  const [question, setQuestion] = useState("");
  const [collectionId, setCollectionId] = useState("");
  const [collections, setCollections] = useState<Collection[]>([]);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<DebugQueryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeStep, setActiveStep] = useState<string | null>(null);

  useEffect(() => {
    getCollections().then(setCollections).catch(() => {});
  }, []);

  const handleDebug = async () => {
    if (!question.trim() || loading) return;
    setLoading(true);
    setResult(null);
    setError(null);
    setActiveStep(null);

    try {
      const res = await queryDebug({
        question,
        collection: collectionId || "",
        options: {
          include_sources: true,
        },
      });
      setResult(res);
      // Auto-select the first step
      if (res.steps.length > 0) {
        setActiveStep(res.steps[0].name);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Debug query failed");
    } finally {
      setLoading(false);
    }
  };

  const activeStepData = result?.steps.find((s) => s.name === activeStep) || null;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-text-primary flex items-center gap-2">
          <Bug size={24} className="text-brand-600" />
          RAG Pipeline Debugger
        </h1>
        <p className="text-sm text-text-secondary mt-1">
          Analysez chaque etape du pipeline RAG en detail
        </p>
      </div>

      {/* Query Input Bar */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col sm:flex-row gap-3">
            <div className="flex-1">
              <Input
                placeholder="Posez votre question..."
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                icon={<Search size={16} />}
                onKeyDown={(e) => {
                  if (e.key === "Enter") handleDebug();
                }}
              />
            </div>
            <div className="w-full sm:w-56">
              <Select
                value={collectionId}
                onChange={(e) => setCollectionId(e.target.value)}
                placeholder="Toutes les collections"
                options={[
                  { value: "", label: "Toutes les collections" },
                  ...collections.map((c) => ({ value: c.id, label: c.name })),
                ]}
              />
            </div>
            <Button
              icon={<Bug size={16} />}
              onClick={handleDebug}
              loading={loading}
              disabled={!question.trim()}
            >
              Debug Query
            </Button>
          </div>
          <div className="mt-2">
            <Link
              href="/playground"
              className="inline-flex items-center gap-1 text-xs text-text-muted hover:text-brand-600 transition-colors"
            >
              <ArrowLeft size={12} />
              Retour au Playground
            </Link>
          </div>
        </CardContent>
      </Card>

      {/* Error */}
      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 dark:bg-red-950 dark:border-red-800 p-4 text-sm text-red-700 dark:text-red-300">
          {error}
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="flex flex-col items-center justify-center py-16 text-text-muted">
          <div className="animate-spin h-10 w-10 border-3 border-brand-600 border-t-transparent rounded-full mb-4" />
          <p className="text-sm font-medium">Analyse du pipeline en cours...</p>
          <p className="text-xs mt-1">Inspection de chaque etape</p>
        </div>
      )}

      {/* Pipeline Visualization */}
      {result && !loading && (
        <div className="space-y-6">
          {/* Pipeline Steps */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Zap size={16} className="text-brand-600" />
                Pipeline
              </CardTitle>
              <CardDescription>
                Cliquez sur une etape pour voir les details
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-center flex-wrap gap-y-4 py-4 overflow-x-auto">
                {result.steps.map((step, idx) => (
                  <React.Fragment key={step.name}>
                    {idx > 0 && <PipelineArrow />}
                    <PipelineStepCard
                      step={step}
                      isActive={activeStep === step.name}
                      isComplete={true}
                      onClick={() =>
                        setActiveStep(activeStep === step.name ? null : step.name)
                      }
                    />
                  </React.Fragment>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Step Detail Panel */}
          {activeStepData && (
            <div
              className="transition-all duration-300 ease-in-out"
              style={{ animation: "fadeSlideIn 0.3s ease-out" }}
            >
              <Card className={`border-l-4 ${
                activeStep === "embedding" ? "border-l-violet-500" :
                activeStep === "retrieval" ? "border-l-blue-500" :
                activeStep === "reranking" ? "border-l-amber-500" :
                activeStep === "generation" ? "border-l-emerald-500" :
                "border-l-brand-600"
              }`}>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <span className={STEP_COLORS[activeStepData.name] || "text-text-primary"}>
                      {STEP_ICONS[activeStepData.name] || <Zap size={16} />}
                    </span>
                    {activeStepData.label}
                    <Badge variant={durationVariant(activeStepData.duration_ms)} className="ml-2">
                      {activeStepData.duration_ms}ms
                    </Badge>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <StepDetailPanel step={activeStepData} />
                </CardContent>
              </Card>
            </div>
          )}

          {/* Final Answer */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Sparkles size={16} className="text-emerald-500" />
                Reponse finale
              </CardTitle>
              <CardDescription className="flex items-center gap-3">
                <span className="flex items-center gap-1">
                  <Zap size={12} className="text-amber-500" />
                  Confiance: {(result.confidence * 100).toFixed(1)}%
                </span>
                <span className="flex items-center gap-1">
                  <Clock size={12} className="text-blue-500" />
                  Latence totale: {result.total_latency_ms}ms
                </span>
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="rounded-lg border border-border bg-surface-1 p-5">
                <p className="text-sm text-text-primary leading-relaxed whitespace-pre-wrap">
                  {result.answer}
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Sources */}
          {result.sources.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Database size={16} className="text-blue-500" />
                  Sources ({result.sources.length})
                </CardTitle>
              </CardHeader>
              <CardContent>
                <SourcesPanel sources={result.sources} />
              </CardContent>
            </Card>
          )}

          {/* Latency Breakdown */}
          <Card>
            <CardContent className="p-5">
              <LatencyBreakdown steps={result.steps} total={result.total_latency_ms} />
            </CardContent>
          </Card>
        </div>
      )}

      {/* Empty State */}
      {!result && !loading && !error && (
        <Card className="min-h-[300px]">
          <CardContent className="flex flex-col items-center justify-center py-16 text-text-muted">
            <Bug size={48} className="opacity-20 mb-4" />
            <p className="text-sm font-medium">Aucune analyse en cours</p>
            <p className="text-xs mt-1">
              Entrez une question et cliquez sur Debug Query pour commencer
            </p>
          </CardContent>
        </Card>
      )}

      {/* Animation keyframes */}
      <style jsx>{`
        @keyframes fadeSlideIn {
          from {
            opacity: 0;
            transform: translateY(-8px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        @keyframes flow {
          0% {
            clip-path: inset(0 100% 0 0);
          }
          100% {
            clip-path: inset(0 0 0 0);
          }
        }
        :global(.animate-flow) {
          animation: flow 1.5s ease-in-out infinite;
        }
      `}</style>
    </div>
  );
}
