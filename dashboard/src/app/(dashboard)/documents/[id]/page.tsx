"use client";

import React, { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft, FileText, Layers, Hash, Clock,
  ChevronDown, ChevronRight, Search, Copy, Check,
  BarChart3,
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import {
  getDocument,
  getDocumentChunks,
  type Document,
  type DocumentChunksResponse,
  type ChunkInfo,
} from "@/lib/api";

export default function DocumentDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;

  const [doc, setDoc] = useState<Document | null>(null);
  const [chunksData, setChunksData] = useState<DocumentChunksResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchChunks, setSearchChunks] = useState("");
  const [expandedChunks, setExpandedChunks] = useState<Set<number>>(new Set());
  const [copiedChunk, setCopiedChunk] = useState<number | null>(null);

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const [docResult, chunksResult] = await Promise.allSettled([
          getDocument(id),
          getDocumentChunks(id),
        ]);
        if (docResult.status === "fulfilled") setDoc(docResult.value);
        if (chunksResult.status === "fulfilled") setChunksData(chunksResult.value);
        if (docResult.status === "rejected" && chunksResult.status === "rejected") {
          setError("Document not found");
        }
      } catch {
        setError("Failed to load document");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [id]);

  const toggleChunk = (idx: number) => {
    setExpandedChunks(prev => {
      const next = new Set(prev);
      if (next.has(idx)) next.delete(idx);
      else next.add(idx);
      return next;
    });
  };

  const copyChunk = (content: string, idx: number) => {
    navigator.clipboard.writeText(content);
    setCopiedChunk(idx);
    setTimeout(() => setCopiedChunk(null), 2000);
  };

  const expandAll = () => {
    if (!chunksData) return;
    setExpandedChunks(new Set(chunksData.chunks.map((_, i) => i)));
  };

  const collapseAll = () => setExpandedChunks(new Set());

  const filteredChunks = chunksData?.chunks.filter(c => {
    if (!searchChunks.trim()) return true;
    return c.content.toLowerCase().includes(searchChunks.toLowerCase());
  }) || [];

  const totalWords = chunksData?.chunks.reduce((sum, c) => sum + c.word_count, 0) || 0;
  const avgWords = chunksData?.chunks.length ? Math.round(totalWords / chunksData.chunks.length) : 0;

  if (loading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-8 w-64 bg-surface-2 rounded" />
        <div className="grid grid-cols-4 gap-4">
          {[1,2,3,4].map(i => <div key={i} className="h-24 bg-surface-2 rounded-xl" />)}
        </div>
        <div className="h-96 bg-surface-2 rounded-xl" />
      </div>
    );
  }

  if (error || !doc) {
    return (
      <div className="text-center py-16">
        <FileText size={48} className="mx-auto text-text-muted opacity-50 mb-4" />
        <h3 className="text-lg font-medium text-text-primary">{error || "Document not found"}</h3>
        <Button variant="outline" className="mt-4" onClick={() => router.push("/documents")}>
          Back to Documents
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <button
          onClick={() => router.push("/documents")}
          className="p-2 rounded-lg hover:bg-surface-2 text-text-muted transition-colors"
        >
          <ArrowLeft size={20} />
        </button>
        <div className="flex-1 min-w-0">
          <h1 className="text-2xl font-bold text-text-primary truncate">{doc.title}</h1>
          <div className="flex items-center gap-3 mt-1">
            <Badge variant={doc.status === "indexed" ? "success" : doc.status === "error" ? "error" : "warning"} dot>
              {doc.status}
            </Badge>
            <span className="text-xs text-text-muted">{doc.source_connector}</span>
            {doc.collection_name && (
              <span className="text-xs text-text-muted">• {doc.collection_name}</span>
            )}
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4 text-center">
            <Layers size={24} className="mx-auto text-indigo-500 mb-2" />
            <div className="text-2xl font-bold text-text-primary">{chunksData?.chunks_count || doc.chunks_count}</div>
            <div className="text-xs text-text-muted">Chunks</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <Hash size={24} className="mx-auto text-purple-500 mb-2" />
            <div className="text-2xl font-bold text-text-primary">{totalWords.toLocaleString()}</div>
            <div className="text-xs text-text-muted">Total Words</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <BarChart3 size={24} className="mx-auto text-emerald-500 mb-2" />
            <div className="text-2xl font-bold text-text-primary">{avgWords}</div>
            <div className="text-xs text-text-muted">Avg Words/Chunk</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <Clock size={24} className="mx-auto text-amber-500 mb-2" />
            <div className="text-sm font-bold text-text-primary">
              {doc.indexed_at ? new Date(doc.indexed_at).toLocaleDateString() : "N/A"}
            </div>
            <div className="text-xs text-text-muted">Indexed At</div>
          </CardContent>
        </Card>
      </div>

      {/* Chunks Explorer */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Chunks Explorer</CardTitle>
              <CardDescription>
                Inspect every text chunk indexed by the RAG engine
              </CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <Button variant="ghost" size="sm" onClick={expandAll}>Expand All</Button>
              <Button variant="ghost" size="sm" onClick={collapseAll}>Collapse All</Button>
            </div>
          </div>
          <div className="mt-3">
            <Input
              placeholder="Search within chunks..."
              icon={<Search size={16} />}
              value={searchChunks}
              onChange={(e) => setSearchChunks(e.target.value)}
            />
          </div>
        </CardHeader>
        <CardContent>
          {filteredChunks.length === 0 ? (
            <div className="text-center py-12">
              <Layers size={48} className="mx-auto text-text-muted opacity-30 mb-4" />
              <p className="text-sm text-text-muted">
                {searchChunks ? "No chunks match your search" : "No chunks available. The document may still be processing."}
              </p>
            </div>
          ) : (
            <div className="space-y-2">
              {filteredChunks.map((chunk, idx) => (
                <div
                  key={chunk.chunk_id}
                  data-chunk={idx}
                  className="border border-border rounded-xl overflow-hidden hover:border-brand-200 dark:hover:border-brand-800 transition-colors"
                >
                  {/* Chunk header */}
                  <button
                    onClick={() => toggleChunk(idx)}
                    className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-surface-1 transition-colors"
                  >
                    <div className="w-8 h-8 rounded-lg bg-brand-50 dark:bg-brand-950 flex items-center justify-center shrink-0">
                      <span className="text-xs font-bold text-brand-600">#{chunk.index + 1}</span>
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-text-primary truncate">
                        {chunk.content.slice(0, 120)}{chunk.content.length > 120 ? "..." : ""}
                      </p>
                    </div>
                    <div className="flex items-center gap-3 shrink-0">
                      <span className="text-xs text-text-muted">{chunk.word_count} words</span>
                      {expandedChunks.has(idx) ? <ChevronDown size={16} className="text-text-muted" /> : <ChevronRight size={16} className="text-text-muted" />}
                    </div>
                  </button>

                  {/* Expanded content */}
                  {expandedChunks.has(idx) && (
                    <div className="px-4 pb-4 border-t border-border">
                      <div className="flex items-center justify-between py-2">
                        <span className="text-xs font-mono text-text-muted">{chunk.chunk_id}</span>
                        <button
                          onClick={() => copyChunk(chunk.content, idx)}
                          className="p-1.5 rounded-lg text-text-muted hover:text-text-primary hover:bg-surface-2 transition-colors"
                        >
                          {copiedChunk === idx ? <Check size={14} /> : <Copy size={14} />}
                        </button>
                      </div>
                      <div className="bg-surface-1 rounded-lg p-4 text-sm text-text-primary whitespace-pre-wrap leading-relaxed font-mono">
                        {chunk.content}
                      </div>
                      {Object.keys(chunk.metadata).length > 0 && (
                        <div className="mt-3">
                          <p className="text-xs font-semibold text-text-muted mb-2">Metadata</p>
                          <div className="flex flex-wrap gap-2">
                            {Object.entries(chunk.metadata).map(([k, v]) => (
                              <span key={k} className="px-2 py-1 rounded bg-surface-2 text-xs text-text-secondary">
                                <span className="font-medium">{k}:</span> {String(v).slice(0, 50)}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Chunk size distribution visualization */}
      {filteredChunks.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Chunk Size Distribution</CardTitle>
            <CardDescription>Word count per chunk</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-end gap-1 h-32">
              {filteredChunks.map((chunk, idx) => {
                const maxWords = Math.max(...filteredChunks.map(c => c.word_count));
                const height = maxWords > 0 ? (chunk.word_count / maxWords) * 100 : 0;
                return (
                  <div
                    key={idx}
                    className="flex-1 bg-brand-500/20 hover:bg-brand-500/40 rounded-t transition-colors cursor-pointer relative group"
                    style={{ height: `${height}%`, minHeight: "4px" }}
                    onClick={() => {
                      setExpandedChunks(new Set([idx]));
                      document.querySelector(`[data-chunk="${idx}"]`)?.scrollIntoView({ behavior: "smooth" });
                    }}
                  >
                    <div className="absolute -top-6 left-1/2 -translate-x-1/2 opacity-0 group-hover:opacity-100 transition-opacity bg-surface-0 border border-border rounded px-1.5 py-0.5 text-[10px] text-text-primary whitespace-nowrap shadow-sm">
                      #{idx + 1}: {chunk.word_count} words
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
