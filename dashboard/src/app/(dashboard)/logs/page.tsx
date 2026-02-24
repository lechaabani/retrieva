"use client";

import React, { useState, useEffect, useCallback } from "react";
import {
  ScrollText,
  ChevronDown,
  ChevronRight,
  ChevronLeft,
  Search,
  Filter,
  Clock,
  Zap,
  FileText,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from "@/components/ui/table";
import {
  getLogs,
  getCollections,
  type LogEntry,
  type Collection,
} from "@/lib/api";
import { formatDate, truncate } from "@/lib/utils";

export default function LogsPage() {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [collections, setCollections] = useState<Collection[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(25);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set());

  // Filters
  const [filterCollection, setFilterCollection] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [minConfidence, setMinConfidence] = useState("");
  const [maxConfidence, setMaxConfidence] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getLogs({
        page,
        page_size: pageSize,
        collection_id: filterCollection || undefined,
        start_date: startDate || undefined,
        end_date: endDate || undefined,
        min_confidence: minConfidence ? parseFloat(minConfidence) : undefined,
        max_confidence: maxConfidence ? parseFloat(maxConfidence) : undefined,
      });
      setLogs(data.logs);
      setTotal(data.total);
    } catch {
      setError("Failed to load logs");
      setLogs([]);
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, filterCollection, startDate, endDate, minConfidence, maxConfidence]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    getCollections().then(setCollections).catch(() => {});
  }, []);

  const totalPages = Math.ceil(total / pageSize);

  const toggleRow = (id: string) => {
    setExpandedRows((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const confidenceVariant = (c: number): "success" | "warning" | "error" => {
    if (c >= 0.8) return "success";
    if (c >= 0.5) return "warning";
    return "error";
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-text-primary">Query Logs</h1>
        <p className="text-sm text-text-secondary mt-1">
          Inspect individual query results and performance
        </p>
      </div>

      {error && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 dark:bg-amber-950 dark:border-amber-800 p-3 text-sm text-amber-700 dark:text-amber-300">
          {error}
        </div>
      )}

      <div className="flex flex-wrap gap-3">
        <Select
          value={filterCollection}
          onChange={(e) => {
            setFilterCollection(e.target.value);
            setPage(1);
          }}
          placeholder="All Collections"
          options={[
            { value: "", label: "All Collections" },
            ...collections.map((c) => ({ value: c.id, label: c.name })),
          ]}
          className="w-48"
        />
        <Input
          type="date"
          value={startDate}
          onChange={(e) => {
            setStartDate(e.target.value);
            setPage(1);
          }}
          className="w-40"
          placeholder="Start date"
        />
        <Input
          type="date"
          value={endDate}
          onChange={(e) => {
            setEndDate(e.target.value);
            setPage(1);
          }}
          className="w-40"
          placeholder="End date"
        />
        <Input
          type="number"
          placeholder="Min confidence"
          value={minConfidence}
          onChange={(e) => {
            setMinConfidence(e.target.value);
            setPage(1);
          }}
          className="w-36"
          min={0}
          max={1}
          step={0.1}
        />
        <Input
          type="number"
          placeholder="Max confidence"
          value={maxConfidence}
          onChange={(e) => {
            setMaxConfidence(e.target.value);
            setPage(1);
          }}
          className="w-36"
          min={0}
          max={1}
          step={0.1}
        />
      </div>

      <div className="rounded-xl border border-border bg-surface-0 shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-text-muted">
            <div className="animate-spin h-6 w-6 border-2 border-brand-600 border-t-transparent rounded-full mx-auto mb-3" />
            Loading logs...
          </div>
        ) : logs.length === 0 ? (
          <div className="p-12 text-center">
            <ScrollText size={48} className="mx-auto text-text-muted opacity-50 mb-4" />
            <h3 className="text-lg font-medium text-text-primary">No logs found</h3>
            <p className="text-sm text-text-muted mt-1">
              Query logs will appear here after users start querying
            </p>
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-8" />
                <TableHead>Timestamp</TableHead>
                <TableHead>Question</TableHead>
                <TableHead>Collection</TableHead>
                <TableHead>Confidence</TableHead>
                <TableHead>Latency</TableHead>
                <TableHead>Tokens</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {logs.map((log) => (
                <React.Fragment key={log.id}>
                  <TableRow
                    className="cursor-pointer"
                    onClick={() => toggleRow(log.id)}
                  >
                    <TableCell>
                      {expandedRows.has(log.id) ? (
                        <ChevronDown size={14} className="text-text-muted" />
                      ) : (
                        <ChevronRight size={14} className="text-text-muted" />
                      )}
                    </TableCell>
                    <TableCell className="text-xs text-text-secondary whitespace-nowrap">
                      {formatDate(log.created_at)}
                    </TableCell>
                    <TableCell className="max-w-xs">
                      <span className="text-sm">{truncate(log.question, 60)}</span>
                    </TableCell>
                    <TableCell className="text-sm text-text-secondary">
                      {log.collection_name || log.collection_id || "-"}
                    </TableCell>
                    <TableCell>
                      {log.confidence != null ? (
                        <Badge variant={confidenceVariant(log.confidence)}>
                          {(log.confidence * 100).toFixed(0)}%
                        </Badge>
                      ) : (
                        <span className="text-text-muted">--</span>
                      )}
                    </TableCell>
                    <TableCell className="text-sm text-text-secondary">
                      {log.latency_ms != null ? `${log.latency_ms}ms` : "--"}
                    </TableCell>
                    <TableCell className="text-sm text-text-secondary">
                      {log.tokens_used != null ? log.tokens_used : "--"}
                    </TableCell>
                  </TableRow>
                  {expandedRows.has(log.id) && (
                    <TableRow className="bg-surface-1 hover:bg-surface-1">
                      <TableCell colSpan={7} className="p-0">
                        <div className="p-5 space-y-4 border-l-4 border-brand-500">
                          <div>
                            <h4 className="text-xs font-semibold uppercase tracking-wider text-text-muted mb-1">
                              Full Question
                            </h4>
                            <p className="text-sm text-text-primary">
                              {log.question}
                            </p>
                          </div>
                          <div>
                            <h4 className="text-xs font-semibold uppercase tracking-wider text-text-muted mb-1">
                              Answer
                            </h4>
                            <p className="text-sm text-text-primary whitespace-pre-wrap">
                              {log.answer}
                            </p>
                          </div>
                          {log.sources?.length > 0 && (
                            <div>
                              <h4 className="text-xs font-semibold uppercase tracking-wider text-text-muted mb-2">
                                Sources ({log.sources.length})
                              </h4>
                              <div className="space-y-2">
                                {log.sources.map((src, idx) => (
                                  <div
                                    key={idx}
                                    className="rounded-lg border border-border p-3 bg-surface-0"
                                  >
                                    <div className="flex items-center justify-between mb-1">
                                      <span className="text-xs font-medium text-text-secondary">
                                        {src.document_id}
                                      </span>
                                      <Badge variant="info">
                                        {(src.score * 100).toFixed(0)}% match
                                      </Badge>
                                    </div>
                                    <p className="text-xs text-text-secondary mt-1 line-clamp-3">
                                      {src.content}
                                    </p>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                          {log.error && (
                            <div className="rounded-lg border border-red-200 bg-red-50 dark:bg-red-950 dark:border-red-800 p-3">
                              <p className="text-sm text-red-700 dark:text-red-300">
                                Error: {log.error}
                              </p>
                            </div>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                  )}
                </React.Fragment>
              ))}
            </TableBody>
          </Table>
        )}
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-text-muted">
            Page {page} of {totalPages} ({total} entries)
          </p>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              icon={<ChevronLeft size={14} />}
              disabled={page <= 1}
              onClick={() => setPage((p) => p - 1)}
            >
              Previous
            </Button>
            <Button
              variant="outline"
              size="sm"
              disabled={page >= totalPages}
              onClick={() => setPage((p) => p + 1)}
            >
              Next
              <ChevronRight size={14} />
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
