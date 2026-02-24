"use client";

import React, { useState, useEffect } from "react";
import {
  FlaskConical,
  Play,
  Plus,
  Trash2,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Clock,
  Target,
  BarChart3,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import {
  getCollections,
  runEvalSuite,
  type Collection,
  type EvalTestCase,
  type EvalSuiteResult,
  type EvalTestCaseResult,
} from "@/lib/api";

interface TestRow {
  id: string;
  question: string;
  expected_answer: string;
  expected_sources: string;
}

function ScoreBar({ value, label }: { value: number; label: string }) {
  const pct = Math.min(value * 100, 100);
  const color =
    pct >= 70 ? "bg-green-500" : pct >= 40 ? "bg-amber-500" : "bg-red-500";
  return (
    <div className="space-y-1 mt-2">
      <div className="flex items-center justify-between">
        <span className="text-xs text-text-muted">{label}</span>
        <span className="text-xs font-mono font-bold text-text-primary">
          {pct.toFixed(1)}%
        </span>
      </div>
      <div className="h-2 bg-surface-2 rounded-full overflow-hidden">
        <div
          className={`h-full ${color} rounded-full transition-all`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

export default function EvaluationPage() {
  const [collections, setCollections] = useState<Collection[]>([]);
  const [selectedCollection, setSelectedCollection] = useState("");
  const [suiteName, setSuiteName] = useState("Test Suite");
  const [topK, setTopK] = useState(5);
  const [testRows, setTestRows] = useState<TestRow[]>([
    { id: "1", question: "", expected_answer: "", expected_sources: "" },
  ]);
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<EvalSuiteResult | null>(null);
  const [expandedResults, setExpandedResults] = useState<Set<number>>(
    new Set()
  );
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getCollections()
      .then(setCollections)
      .catch(() => {});
  }, []);

  const addRow = () => {
    setTestRows([
      ...testRows,
      {
        id: String(Date.now()),
        question: "",
        expected_answer: "",
        expected_sources: "",
      },
    ]);
  };

  const removeRow = (id: string) => {
    if (testRows.length <= 1) return;
    setTestRows(testRows.filter((r) => r.id !== id));
  };

  const updateRow = (id: string, field: keyof TestRow, value: string) => {
    setTestRows(
      testRows.map((r) => (r.id === id ? { ...r, [field]: value } : r))
    );
  };

  const handleRun = async () => {
    if (!selectedCollection) {
      setError("Selectionnez une collection avant de lancer l'evaluation");
      return;
    }

    const cases: EvalTestCase[] = testRows
      .filter((r) => r.question.trim())
      .map((r) => ({
        question: r.question,
        expected_answer: r.expected_answer || undefined,
        expected_sources: r.expected_sources
          ? r.expected_sources.split(",").map((s) => s.trim())
          : undefined,
      }));

    if (cases.length === 0) {
      setError("Ajoutez au moins une question a tester");
      return;
    }

    setRunning(true);
    setError(null);
    setResult(null);

    try {
      // Find collection name from selected id
      const col = collections.find((c) => c.id === selectedCollection);
      const collectionName = col ? col.name : selectedCollection;

      const res = await runEvalSuite({
        name: suiteName,
        collection: collectionName,
        top_k: topK,
        test_cases: cases,
      });
      setResult(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Evaluation failed");
    } finally {
      setRunning(false);
    }
  };

  const toggleExpand = (idx: number) => {
    const next = new Set(expandedResults);
    if (next.has(idx)) next.delete(idx);
    else next.add(idx);
    setExpandedResults(next);
  };

  // Pre-built test templates
  const loadTemplate = (template: string) => {
    if (template === "rag_basics") {
      setTestRows([
        {
          id: "t1",
          question: "Qu'est-ce que le RAG ?",
          expected_answer: "Retrieval-Augmented Generation",
          expected_sources: "",
        },
        {
          id: "t2",
          question: "Comment fonctionne la recherche semantique ?",
          expected_answer: "embeddings vecteurs similarite",
          expected_sources: "",
        },
        {
          id: "t3",
          question: "Quels sont les avantages du RAG ?",
          expected_answer: "pertinence sources donnees",
          expected_sources: "",
        },
      ]);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-text-primary">
          Evaluation RAG
        </h1>
        <p className="text-sm text-text-secondary mt-1">
          Testez la qualite de vos reponses avec des suites de tests
          automatisees
        </p>
      </div>

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 dark:bg-red-950 dark:border-red-800 p-3 text-sm text-red-700 dark:text-red-300">
          {error}
        </div>
      )}

      {/* Config */}
      <Card>
        <CardHeader>
          <CardTitle>Configuration</CardTitle>
          <CardDescription>Parametrez votre suite de tests</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <Input
              label="Nom de la suite"
              value={suiteName}
              onChange={(e) => setSuiteName(e.target.value)}
            />
            <Select
              label="Collection"
              value={selectedCollection}
              onChange={(e) => setSelectedCollection(e.target.value)}
              options={[
                { value: "", label: "-- Selectionnez une collection --" },
                ...collections.map((c) => ({ value: c.id, label: c.name })),
              ]}
            />
            <Input
              label="Top K"
              type="number"
              value={String(topK)}
              onChange={(e) => setTopK(Number(e.target.value))}
            />
          </div>
          <div className="mt-3">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => loadTemplate("rag_basics")}
            >
              Charger template: RAG Basics
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Test Cases */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Cas de test</CardTitle>
              <CardDescription>
                Definissez les questions et reponses attendues
              </CardDescription>
            </div>
            <Button
              size="sm"
              variant="outline"
              icon={<Plus size={14} />}
              onClick={addRow}
            >
              Ajouter
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {testRows.map((row, idx) => (
            <div
              key={row.id}
              className="grid grid-cols-12 gap-3 items-start border-b border-border pb-4 last:border-0"
            >
              <div className="col-span-1 flex items-center justify-center h-10">
                <span className="text-xs font-bold text-text-muted">
                  #{idx + 1}
                </span>
              </div>
              <div className="col-span-4">
                <Input
                  placeholder="Question..."
                  value={row.question}
                  onChange={(e) => updateRow(row.id, "question", e.target.value)}
                />
              </div>
              <div className="col-span-4">
                <Input
                  placeholder="Reponse attendue (mots cles)..."
                  value={row.expected_answer}
                  onChange={(e) =>
                    updateRow(row.id, "expected_answer", e.target.value)
                  }
                />
              </div>
              <div className="col-span-2">
                <Input
                  placeholder="Sources..."
                  value={row.expected_sources}
                  onChange={(e) =>
                    updateRow(row.id, "expected_sources", e.target.value)
                  }
                />
              </div>
              <div className="col-span-1">
                <button
                  onClick={() => removeRow(row.id)}
                  className="p-2 rounded-lg text-text-muted hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-950"
                >
                  <Trash2 size={16} />
                </button>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>

      {/* Run Button */}
      <div className="flex justify-center">
        <Button
          icon={<Play size={18} />}
          onClick={handleRun}
          loading={running}
          className="px-8 py-3"
        >
          {running ? "Evaluation en cours..." : "Lancer l'evaluation"}
        </Button>
      </div>

      {/* Results */}
      {result && (
        <>
          {/* Summary */}
          <Card>
            <CardHeader>
              <CardTitle>Resultats: {result.name}</CardTitle>
              <CardDescription>
                {result.total_cases} cas testes
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 sm:grid-cols-4 gap-6">
                <div className="text-center">
                  <div className="text-3xl font-bold text-text-primary">
                    {result.total_cases}
                  </div>
                  <div className="text-xs text-text-muted mt-1">
                    Tests executes
                  </div>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-brand-600">
                    {(result.avg_confidence * 100).toFixed(1)}%
                  </div>
                  <div className="text-xs text-text-muted mt-1">
                    Confiance moyenne
                  </div>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-text-primary">
                    {Math.round(result.avg_latency_ms)}ms
                  </div>
                  <div className="text-xs text-text-muted mt-1">
                    Latence moyenne
                  </div>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-text-primary">
                    {result.source_hit_rate != null
                      ? `${(result.source_hit_rate * 100).toFixed(0)}%`
                      : "N/A"}
                  </div>
                  <div className="text-xs text-text-muted mt-1">
                    Taux de source hit
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Detailed Results */}
          <div className="space-y-3">
            {result.results.map((r, idx) => (
              <Card key={idx}>
                <CardContent className="p-4">
                  <div
                    className="flex items-center justify-between cursor-pointer"
                    onClick={() => toggleExpand(idx)}
                  >
                    <div className="flex items-center gap-3 flex-1 min-w-0">
                      <div
                        className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${
                          r.confidence >= 0.7
                            ? "bg-green-100 dark:bg-green-900 text-green-600"
                            : r.confidence >= 0.4
                            ? "bg-amber-100 dark:bg-amber-900 text-amber-600"
                            : "bg-red-100 dark:bg-red-900 text-red-600"
                        }`}
                      >
                        {r.confidence >= 0.7 ? (
                          <CheckCircle2 size={16} />
                        ) : r.confidence >= 0.4 ? (
                          <AlertTriangle size={16} />
                        ) : (
                          <XCircle size={16} />
                        )}
                      </div>
                      <div className="min-w-0">
                        <p className="text-sm font-medium text-text-primary truncate">
                          {r.question}
                        </p>
                        <p className="text-xs text-text-muted truncate">
                          {r.answer.slice(0, 120)}
                          {r.answer.length > 120 ? "..." : ""}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4 shrink-0 ml-4">
                      <Badge
                        variant={
                          r.confidence >= 0.7
                            ? "success"
                            : r.confidence >= 0.4
                            ? "warning"
                            : "error"
                        }
                      >
                        {(r.confidence * 100).toFixed(0)}%
                      </Badge>
                      <span className="text-xs text-text-muted">
                        {Math.round(r.latency_ms)}ms
                      </span>
                      {expandedResults.has(idx) ? (
                        <ChevronUp size={16} className="text-text-muted" />
                      ) : (
                        <ChevronDown size={16} className="text-text-muted" />
                      )}
                    </div>
                  </div>

                  {expandedResults.has(idx) && (
                    <div className="mt-4 pt-4 border-t border-border space-y-4">
                      <div>
                        <h4 className="text-xs font-semibold text-text-muted mb-1">
                          Reponse generee
                        </h4>
                        <p className="text-sm text-text-primary bg-surface-1 rounded-lg p-3">
                          {r.answer}
                        </p>
                      </div>
                      {r.expected_answer && (
                        <div>
                          <h4 className="text-xs font-semibold text-text-muted mb-1">
                            Reponse attendue
                          </h4>
                          <p className="text-sm text-text-secondary bg-surface-1 rounded-lg p-3">
                            {r.expected_answer}
                          </p>
                          {r.answer_similarity != null && (
                            <ScoreBar
                              value={r.answer_similarity}
                              label="Similarite des mots"
                            />
                          )}
                        </div>
                      )}
                      {r.relevance_score != null && (
                        <ScoreBar
                          value={r.relevance_score}
                          label="Score de pertinence (top chunk)"
                        />
                      )}
                      <div>
                        <h4 className="text-xs font-semibold text-text-muted mb-1">
                          Sources ({r.sources.length})
                        </h4>
                        {r.sources.length === 0 ? (
                          <p className="text-xs text-text-muted">
                            Aucune source trouvee
                          </p>
                        ) : (
                          <div className="space-y-2">
                            {r.sources.map((s, si) => (
                              <div
                                key={si}
                                className="text-xs bg-surface-1 rounded p-2"
                              >
                                <span className="font-medium text-text-primary">
                                  {s.title || "Sans titre"}
                                </span>
                                <span className="text-text-muted ml-2">
                                  score: {s.score?.toFixed(3)}
                                </span>
                                <p className="text-text-secondary mt-1">
                                  {s.content}
                                </p>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                      {r.source_hit !== null && r.source_hit !== undefined && (
                        <div className="flex items-center gap-2">
                          <span className="text-xs text-text-muted">
                            Source trouvee:
                          </span>
                          {r.source_hit ? (
                            <Badge variant="success" dot>
                              Oui
                            </Badge>
                          ) : (
                            <Badge variant="error" dot>
                              Non
                            </Badge>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
