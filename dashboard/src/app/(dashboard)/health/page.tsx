"use client";

import React, { useState, useEffect, useCallback } from "react";
import {
  Activity,
  Database,
  Server,
  Cpu,
  HardDrive,
  RefreshCw,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Clock,
  Zap,
  Brain,
  Search as SearchIcon,
} from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { getHealth, type HealthStatus } from "@/lib/api";

function StatusIcon({ status }: { status: string }) {
  if (status === "healthy" || status === "ok" || status === "configured") {
    return <CheckCircle2 size={20} className="text-green-500" />;
  }
  if (status === "unhealthy" || status === "error") {
    return <XCircle size={20} className="text-red-500" />;
  }
  return <AlertCircle size={20} className="text-amber-500" />;
}

function StatusBadge({ status }: { status: string }) {
  const variant =
    status === "healthy" || status === "ok" || status === "configured"
      ? "success"
      : status === "unhealthy" || status === "error"
      ? "error"
      : "warning";
  return (
    <Badge variant={variant} dot>
      {status}
    </Badge>
  );
}

const SERVICE_META: Record<
  string,
  { label: string; icon: React.ReactNode; description: string }
> = {
  database: {
    label: "PostgreSQL",
    icon: <Database size={24} />,
    description: "Base de donnees principale",
  },
  qdrant: {
    label: "Qdrant",
    icon: <SearchIcon size={24} />,
    description: "Moteur de recherche vectorielle",
  },
  redis: {
    label: "Redis",
    icon: <Zap size={24} />,
    description: "Cache et file de messages",
  },
  llm_provider: {
    label: "LLM Provider",
    icon: <Brain size={24} />,
    description: "Fournisseur de generation IA",
  },
  embedding_provider: {
    label: "Embedding Provider",
    icon: <Cpu size={24} />,
    description: "Fournisseur d'embeddings",
  },
  celery_worker: {
    label: "Workers",
    icon: <Server size={24} />,
    description: "Workers de traitement asynchrone",
  },
  data: {
    label: "Donnees",
    icon: <HardDrive size={24} />,
    description: "Statistiques du contenu indexe",
  },
};

export default function HealthPage() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastChecked, setLastChecked] = useState<Date | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(false);

  const loadHealth = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getHealth();
      setHealth(data);
      setLastChecked(new Date());
    } catch {
      setError(
        "Impossible de contacter le backend. Verifiez que l'API est demarree."
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadHealth();
  }, [loadHealth]);

  useEffect(() => {
    if (!autoRefresh) return;
    const interval = setInterval(loadHealth, 15000);
    return () => clearInterval(interval);
  }, [autoRefresh, loadHealth]);

  const components = health?.components || {};

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">
            Sante du Systeme
          </h1>
          <p className="text-sm text-text-secondary mt-1">
            Monitoring en temps reel de tous les composants
          </p>
        </div>
        <div className="flex items-center gap-3">
          {lastChecked && (
            <span className="text-xs text-text-muted flex items-center gap-1">
              <Clock size={12} />
              {lastChecked.toLocaleTimeString()}
            </span>
          )}
          <Button
            variant="outline"
            size="sm"
            onClick={() => setAutoRefresh(!autoRefresh)}
          >
            {autoRefresh ? "Pause" : "Auto-refresh"}
          </Button>
          <Button
            icon={<RefreshCw size={16} />}
            onClick={loadHealth}
            loading={loading}
          >
            Rafraichir
          </Button>
        </div>
      </div>

      {/* Overall Status Banner */}
      {health && (
        <div
          className={`rounded-xl p-6 border ${
            health.status === "ok"
              ? "bg-green-50 dark:bg-green-950 border-green-200 dark:border-green-800"
              : "bg-red-50 dark:bg-red-950 border-red-200 dark:border-red-800"
          }`}
        >
          <div className="flex items-center gap-4">
            <div
              className={`w-12 h-12 rounded-full flex items-center justify-center ${
                health.status === "ok"
                  ? "bg-green-100 dark:bg-green-900"
                  : "bg-red-100 dark:bg-red-900"
              }`}
            >
              {health.status === "ok" ? (
                <CheckCircle2 size={28} className="text-green-600" />
              ) : (
                <XCircle size={28} className="text-red-600" />
              )}
            </div>
            <div>
              <h2
                className={`text-xl font-bold ${
                  health.status === "ok"
                    ? "text-green-800 dark:text-green-200"
                    : "text-red-800 dark:text-red-200"
                }`}
              >
                {health.status === "ok"
                  ? "Tous les systemes sont operationnels"
                  : "Certains services sont degrades"}
              </h2>
              <p
                className={`text-sm ${
                  health.status === "ok"
                    ? "text-green-600 dark:text-green-400"
                    : "text-red-600 dark:text-red-400"
                }`}
              >
                Version {health.version} &middot;{" "}
                {Object.keys(components).length} composants verifies
              </p>
            </div>
          </div>
        </div>
      )}

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 dark:bg-red-950 dark:border-red-800 p-4 text-sm text-red-700 dark:text-red-300">
          {error}
        </div>
      )}

      {/* Component Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {Object.entries(components).map(([key, value]) => {
          const meta = SERVICE_META[key] || {
            label: key,
            icon: <Server size={24} />,
            description: "",
          };
          const comp = value as Record<string, any>;

          return (
            <Card key={key} className="overflow-hidden">
              <CardContent className="p-5">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-surface-2 flex items-center justify-center text-text-secondary">
                      {meta.icon}
                    </div>
                    <div>
                      <h3 className="text-sm font-semibold text-text-primary">
                        {meta.label}
                      </h3>
                      <p className="text-xs text-text-muted">
                        {meta.description}
                      </p>
                    </div>
                  </div>
                  <StatusIcon status={comp.status} />
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-text-muted">Statut</span>
                    <StatusBadge status={comp.status} />
                  </div>

                  {comp.latency_ms !== undefined && (
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-text-muted">Latence</span>
                      <span
                        className={`text-xs font-mono ${
                          comp.latency_ms < 50
                            ? "text-green-600"
                            : comp.latency_ms < 200
                            ? "text-amber-600"
                            : "text-red-600"
                        }`}
                      >
                        {comp.latency_ms}ms
                      </span>
                    </div>
                  )}

                  {comp.collections !== undefined && (
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-text-muted">
                        Collections
                      </span>
                      <span className="text-xs font-medium text-text-primary">
                        {comp.collections}
                      </span>
                    </div>
                  )}

                  {comp.memory_used && (
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-text-muted">Memoire</span>
                      <span className="text-xs font-medium text-text-primary">
                        {comp.memory_used}
                      </span>
                    </div>
                  )}

                  {comp.provider && (
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-text-muted">Provider</span>
                      <span className="text-xs font-medium text-text-primary capitalize">
                        {comp.provider}
                      </span>
                    </div>
                  )}

                  {comp.has_api_key !== undefined && (
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-text-muted">Cle API</span>
                      <Badge
                        variant={comp.has_api_key ? "success" : "warning"}
                        dot
                      >
                        {comp.has_api_key ? "Configuree" : "Manquante"}
                      </Badge>
                    </div>
                  )}

                  {comp.documents !== undefined && (
                    <>
                      <div className="flex items-center justify-between">
                        <span className="text-xs text-text-muted">
                          Documents
                        </span>
                        <span className="text-xs font-medium text-text-primary">
                          {comp.documents}
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-xs text-text-muted">
                          Collections
                        </span>
                        <span className="text-xs font-medium text-text-primary">
                          {comp.collections}
                        </span>
                      </div>
                    </>
                  )}

                  {comp.task_results_count !== undefined && (
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-text-muted">
                        Resultats de taches
                      </span>
                      <span className="text-xs font-medium text-text-primary">
                        {comp.task_results_count}
                      </span>
                    </div>
                  )}

                  {comp.error && (
                    <div className="mt-2 p-2 rounded bg-red-50 dark:bg-red-950">
                      <p className="text-xs text-red-600 dark:text-red-400 font-mono break-all">
                        {comp.error}
                      </p>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
