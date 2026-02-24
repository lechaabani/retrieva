"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import {
  ArrowLeft,
  GitCompareArrows,
  FileText,
  Layers,
  BookOpen,
  Ruler,
  Clock,
  MessageSquare,
  Zap,
  Shield,
  Loader2,
} from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Select } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  getCollections,
  compareCollections,
  type Collection,
  type CollectionStats,
  type CompareQueryResult,
  type CompareResponse,
} from "@/lib/api";
import { formatRelativeTime } from "@/lib/utils";

/* -------------------------------------------------------------------------- */
/*  Stat bar component                                                         */
/* -------------------------------------------------------------------------- */

function StatBar({
  label,
  icon,
  valueA,
  valueB,
  format,
  higherWins = true,
}: {
  label: string;
  icon: React.ReactNode;
  valueA: number;
  valueB: number;
  format?: (v: number) => string;
  higherWins?: boolean;
}) {
  const fmt = format || ((v: number) => v.toLocaleString("fr-FR"));
  const max = Math.max(valueA, valueB, 1);
  const pctA = (valueA / max) * 100;
  const pctB = (valueB / max) * 100;

  const aWins = higherWins ? valueA > valueB : valueA < valueB;
  const bWins = higherWins ? valueB > valueA : valueA > valueB;
  const tie = valueA === valueB;

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-sm">
        <span className="flex items-center gap-2 text-text-secondary font-medium">
          {icon}
          {label}
        </span>
      </div>
      <div className="flex items-center gap-3">
        {/* Value A */}
        <span
          className={`text-sm font-semibold min-w-[80px] text-right ${
            aWins && !tie
              ? "text-emerald-600 dark:text-emerald-400"
              : "text-text-primary"
          }`}
        >
          {fmt(valueA)}
          {aWins && !tie && " *"}
        </span>

        {/* Bar A */}
        <div className="flex-1 flex gap-1">
          <div className="flex-1 h-6 bg-surface-2 rounded-l-md overflow-hidden flex justify-end">
            <div
              className="h-full bg-blue-500 rounded-l-md transition-all duration-700 ease-out"
              style={{ width: `${pctA}%` }}
            />
          </div>
          <div className="flex-1 h-6 bg-surface-2 rounded-r-md overflow-hidden">
            <div
              className="h-full bg-violet-500 rounded-r-md transition-all duration-700 ease-out"
              style={{ width: `${pctB}%` }}
            />
          </div>
        </div>

        {/* Value B */}
        <span
          className={`text-sm font-semibold min-w-[80px] ${
            bWins && !tie
              ? "text-emerald-600 dark:text-emerald-400"
              : "text-text-primary"
          }`}
        >
          {fmt(valueB)}
          {bWins && !tie && " *"}
        </span>
      </div>
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/*  Query result card                                                          */
/* -------------------------------------------------------------------------- */

function QueryResultCard({
  result,
  label,
  color,
  isFaster,
  isMoreConfident,
}: {
  result: CompareQueryResult;
  label: string;
  color: string;
  isFaster: boolean;
  isMoreConfident: boolean;
}) {
  return (
    <div
      className={`flex-1 rounded-xl border border-border bg-surface-0 p-5 space-y-4 animate-in fade-in slide-in-from-bottom-2 duration-500`}
    >
      <div className="flex items-center justify-between">
        <h4 className="font-semibold text-text-primary flex items-center gap-2">
          <div className={`w-3 h-3 rounded-full ${color}`} />
          {label}
        </h4>
        <div className="flex gap-2">
          <Badge variant={isFaster ? "success" : "neutral"}>
            <Zap size={10} className="mr-1" />
            {result.latency_ms} ms
          </Badge>
          <Badge variant={isMoreConfident ? "success" : "neutral"}>
            <Shield size={10} className="mr-1" />
            {(result.confidence * 100).toFixed(0)}%
          </Badge>
        </div>
      </div>
      <p className="text-sm text-text-secondary leading-relaxed whitespace-pre-wrap">
        {result.answer}
      </p>
      <div className="flex items-center gap-4 text-xs text-text-muted pt-2 border-t border-border">
        <span>{result.sources_count} sources</span>
      </div>
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/*  Main page                                                                  */
/* -------------------------------------------------------------------------- */

export default function CompareCollectionsPage() {
  const [collections, setCollections] = useState<Collection[]>([]);
  const [loading, setLoading] = useState(true);
  const [comparing, setComparing] = useState(false);
  const [querying, setQuerying] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [collectionAId, setCollectionAId] = useState("");
  const [collectionBId, setCollectionBId] = useState("");
  const [question, setQuestion] = useState("");

  const [result, setResult] = useState<CompareResponse | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const data = await getCollections();
        setCollections(data);
      } catch {
        setError("Impossible de charger les collections");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const handleCompare = useCallback(async () => {
    if (!collectionAId || !collectionBId) return;
    setComparing(true);
    setError(null);
    setResult(null);
    try {
      const data = await compareCollections({
        collection_a_id: collectionAId,
        collection_b_id: collectionBId,
      });
      setResult(data);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Erreur lors de la comparaison"
      );
    } finally {
      setComparing(false);
    }
  }, [collectionAId, collectionBId]);

  const handleQuery = useCallback(async () => {
    if (!collectionAId || !collectionBId || !question.trim()) return;
    setQuerying(true);
    setError(null);
    try {
      const data = await compareCollections({
        collection_a_id: collectionAId,
        collection_b_id: collectionBId,
        question: question.trim(),
      });
      setResult(data);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Erreur lors de la requete"
      );
    } finally {
      setQuerying(false);
    }
  }, [collectionAId, collectionBId, question]);

  const collectionOptions = collections.map((c) => ({
    value: c.id,
    label: `${c.name} (${c.documents_count} docs)`,
  }));

  const a = result?.collection_a;
  const b = result?.collection_b;

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-64 bg-surface-2 rounded animate-pulse" />
        <div className="h-48 bg-surface-2 rounded-xl animate-pulse" />
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link
          href="/collections"
          className="p-2 rounded-lg text-text-muted hover:text-text-primary hover:bg-surface-2 transition-colors"
        >
          <ArrowLeft size={20} />
        </Link>
        <div>
          <h1 className="text-2xl font-bold text-text-primary">
            Comparaison de Collections
          </h1>
          <p className="text-sm text-text-secondary mt-1">
            Comparez les statistiques et performances de deux collections
          </p>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 dark:bg-amber-950 dark:border-amber-800 p-3 text-sm text-amber-700 dark:text-amber-300">
          {error}
        </div>
      )}

      {/* Selection */}
      <Card>
        <CardContent className="p-5">
          <div className="grid grid-cols-1 md:grid-cols-[1fr_auto_1fr] gap-4 items-end">
            <Select
              label="Collection A"
              options={collectionOptions}
              placeholder="Choisir une collection..."
              value={collectionAId}
              onChange={(e) => setCollectionAId(e.target.value)}
            />
            <div className="flex items-center justify-center pt-5">
              <div className="w-10 h-10 rounded-full bg-surface-2 flex items-center justify-center text-text-muted">
                <GitCompareArrows size={20} />
              </div>
            </div>
            <Select
              label="Collection B"
              options={collectionOptions}
              placeholder="Choisir une collection..."
              value={collectionBId}
              onChange={(e) => setCollectionBId(e.target.value)}
            />
          </div>
          <div className="flex justify-center mt-5">
            <Button
              onClick={handleCompare}
              disabled={
                !collectionAId ||
                !collectionBId ||
                collectionAId === collectionBId ||
                comparing
              }
              loading={comparing}
              icon={<GitCompareArrows size={16} />}
            >
              Comparer
            </Button>
          </div>
          {collectionAId &&
            collectionBId &&
            collectionAId === collectionBId && (
              <p className="text-xs text-amber-600 dark:text-amber-400 text-center mt-2">
                Veuillez choisir deux collections differentes
              </p>
            )}
        </CardContent>
      </Card>

      {/* Results */}
      {result && a && b && (
        <>
          {/* Legend */}
          <div className="flex items-center justify-center gap-6 text-sm text-text-secondary">
            <span className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-blue-500" />
              {a.name}
            </span>
            <span className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-violet-500" />
              {b.name}
            </span>
            <span className="flex items-center gap-1 text-xs text-emerald-600 dark:text-emerald-400">
              * meilleur
            </span>
          </div>

          {/* Side by side stat cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Collection A card */}
            <Card className="border-t-4 border-t-blue-500 animate-in fade-in slide-in-from-left-4 duration-500">
              <CardContent className="p-5 space-y-3">
                <h3 className="font-semibold text-text-primary text-lg flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-blue-500" />
                  {a.name}
                </h3>
                <div className="grid grid-cols-2 gap-3">
                  <StatCell
                    icon={<FileText size={14} />}
                    label="Documents"
                    value={a.doc_count}
                    highlight={a.doc_count > b.doc_count}
                  />
                  <StatCell
                    icon={<Layers size={14} />}
                    label="Chunks"
                    value={a.chunk_count}
                    highlight={a.chunk_count > b.chunk_count}
                  />
                  <StatCell
                    icon={<BookOpen size={14} />}
                    label="Mots totaux"
                    value={a.total_words}
                    highlight={a.total_words > b.total_words}
                  />
                  <StatCell
                    icon={<Ruler size={14} />}
                    label="Taille moy. des chunks"
                    value={a.avg_chunk_size}
                    decimal
                    highlight={a.avg_chunk_size > b.avg_chunk_size}
                  />
                </div>
                <div className="flex items-center gap-2 text-xs text-text-muted pt-2 border-t border-border">
                  <Clock size={12} />
                  Derniere mise a jour:{" "}
                  {a.last_updated
                    ? formatRelativeTime(a.last_updated)
                    : "Aucune"}
                </div>
              </CardContent>
            </Card>

            {/* Collection B card */}
            <Card className="border-t-4 border-t-violet-500 animate-in fade-in slide-in-from-right-4 duration-500">
              <CardContent className="p-5 space-y-3">
                <h3 className="font-semibold text-text-primary text-lg flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-violet-500" />
                  {b.name}
                </h3>
                <div className="grid grid-cols-2 gap-3">
                  <StatCell
                    icon={<FileText size={14} />}
                    label="Documents"
                    value={b.doc_count}
                    highlight={b.doc_count > a.doc_count}
                  />
                  <StatCell
                    icon={<Layers size={14} />}
                    label="Chunks"
                    value={b.chunk_count}
                    highlight={b.chunk_count > a.chunk_count}
                  />
                  <StatCell
                    icon={<BookOpen size={14} />}
                    label="Mots totaux"
                    value={b.total_words}
                    highlight={b.total_words > a.total_words}
                  />
                  <StatCell
                    icon={<Ruler size={14} />}
                    label="Taille moy. des chunks"
                    value={b.avg_chunk_size}
                    decimal
                    highlight={b.avg_chunk_size > a.avg_chunk_size}
                  />
                </div>
                <div className="flex items-center gap-2 text-xs text-text-muted pt-2 border-t border-border">
                  <Clock size={12} />
                  Derniere mise a jour:{" "}
                  {b.last_updated
                    ? formatRelativeTime(b.last_updated)
                    : "Aucune"}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Bar chart comparison */}
          <Card className="animate-in fade-in slide-in-from-bottom-4 duration-700">
            <CardContent className="p-5 space-y-5">
              <h3 className="font-semibold text-text-primary">
                Comparaison visuelle
              </h3>
              <StatBar
                label="Documents"
                icon={<FileText size={14} />}
                valueA={a.doc_count}
                valueB={b.doc_count}
              />
              <StatBar
                label="Chunks"
                icon={<Layers size={14} />}
                valueA={a.chunk_count}
                valueB={b.chunk_count}
              />
              <StatBar
                label="Mots totaux"
                icon={<BookOpen size={14} />}
                valueA={a.total_words}
                valueB={b.total_words}
              />
              <StatBar
                label="Taille moy. des chunks"
                icon={<Ruler size={14} />}
                valueA={a.avg_chunk_size}
                valueB={b.avg_chunk_size}
                format={(v) => v.toFixed(1)}
              />
            </CardContent>
          </Card>

          {/* Query testing */}
          <Card className="animate-in fade-in slide-in-from-bottom-4 duration-700 delay-200">
            <CardContent className="p-5 space-y-4">
              <h3 className="font-semibold text-text-primary flex items-center gap-2">
                <MessageSquare size={18} />
                Tester une question sur les deux collections
              </h3>
              <div className="flex gap-3">
                <div className="flex-1">
                  <Input
                    placeholder="Posez votre question ici..."
                    value={question}
                    onChange={(e) => setQuestion(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && question.trim()) handleQuery();
                    }}
                  />
                </div>
                <Button
                  onClick={handleQuery}
                  disabled={!question.trim() || querying}
                  loading={querying}
                >
                  Envoyer
                </Button>
              </div>

              {/* Query results */}
              {result.query_a && result.query_b && (
                <div className="flex flex-col md:flex-row gap-4 mt-4">
                  <QueryResultCard
                    result={result.query_a}
                    label={a.name}
                    color="bg-blue-500"
                    isFaster={
                      result.query_a.latency_ms < result.query_b.latency_ms
                    }
                    isMoreConfident={
                      result.query_a.confidence > result.query_b.confidence
                    }
                  />
                  <QueryResultCard
                    result={result.query_b}
                    label={b.name}
                    color="bg-violet-500"
                    isFaster={
                      result.query_b.latency_ms < result.query_a.latency_ms
                    }
                    isMoreConfident={
                      result.query_b.confidence > result.query_a.confidence
                    }
                  />
                </div>
              )}
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/*  Stat cell sub-component                                                    */
/* -------------------------------------------------------------------------- */

function StatCell({
  icon,
  label,
  value,
  decimal,
  highlight,
}: {
  icon: React.ReactNode;
  label: string;
  value: number;
  decimal?: boolean;
  highlight?: boolean;
}) {
  return (
    <div
      className={`rounded-lg p-3 transition-colors ${
        highlight
          ? "bg-emerald-50 dark:bg-emerald-950 border border-emerald-200 dark:border-emerald-800"
          : "bg-surface-2"
      }`}
    >
      <div className="flex items-center gap-1.5 text-text-muted text-xs mb-1">
        {icon}
        {label}
      </div>
      <p
        className={`text-lg font-bold ${
          highlight
            ? "text-emerald-700 dark:text-emerald-300"
            : "text-text-primary"
        }`}
      >
        {decimal
          ? value.toFixed(1)
          : value.toLocaleString("fr-FR")}
      </p>
    </div>
  );
}
