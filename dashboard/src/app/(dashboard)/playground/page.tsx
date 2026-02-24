"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import {
  Send,
  Search,
  MessageSquare,
  ChevronDown,
  ChevronRight,
  Clock,
  Zap,
  FileText,
  Trash2,
  Settings,
  Bot,
  User,
  X,
  Globe,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Slider } from "@/components/ui/slider";
import { Toggle } from "@/components/ui/toggle";
import { Badge } from "@/components/ui/badge";
import {
  query as apiQuery,
  search as apiSearch,
  getCollections,
  type QueryResponse,
  type SearchResponse,
  type Collection,
  type Source,
} from "@/lib/api";

type Mode = "rag" | "search";

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  metadata?: {
    confidence?: number;
    latency_ms?: number;
    tokens_used?: number;
  };
  sources?: Source[];
  mode: Mode;
  timestamp: string;
  error?: string;
}

// ---------------------------------------------------------------------------
// Typing animation hook
// ---------------------------------------------------------------------------
function useTypingAnimation(
  fullText: string,
  active: boolean,
  charsPerFrame = 30
) {
  const [displayed, setDisplayed] = useState("");
  const [done, setDone] = useState(false);
  const indexRef = useRef(0);
  const rafRef = useRef<number | null>(null);

  useEffect(() => {
    if (!active) {
      setDisplayed(fullText);
      setDone(true);
      return;
    }

    indexRef.current = 0;
    setDisplayed("");
    setDone(false);

    const step = () => {
      indexRef.current = Math.min(
        indexRef.current + charsPerFrame,
        fullText.length
      );
      setDisplayed(fullText.slice(0, indexRef.current));
      if (indexRef.current < fullText.length) {
        rafRef.current = requestAnimationFrame(step);
      } else {
        setDone(true);
      }
    };

    rafRef.current = requestAnimationFrame(step);
    return () => {
      if (rafRef.current !== null) cancelAnimationFrame(rafRef.current);
    };
  }, [fullText, active, charsPerFrame]);

  return { displayed, done };
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function BouncingDots() {
  return (
    <div className="flex items-center gap-1 py-2 px-1">
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          className="h-2 w-2 rounded-full bg-text-muted"
          style={{
            animation: "bounce-dot 1.2s ease-in-out infinite",
            animationDelay: `${i * 0.15}s`,
          }}
        />
      ))}
      <style jsx>{`
        @keyframes bounce-dot {
          0%,
          80%,
          100% {
            transform: translateY(0);
            opacity: 0.4;
          }
          40% {
            transform: translateY(-6px);
            opacity: 1;
          }
        }
      `}</style>
    </div>
  );
}

function SourcesAccordion({ sources }: { sources: Source[] }) {
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
    <div className="mt-2 space-y-1">
      <p className="text-xs font-medium text-text-muted mb-1">
        Sources ({sources.length})
      </p>
      {sources.map((source, idx) => (
        <div
          key={idx}
          className="border border-border rounded-lg overflow-hidden bg-surface-0"
        >
          <button
            onClick={() => toggle(idx)}
            className="w-full flex items-center justify-between p-2 text-left hover:bg-surface-1 transition-colors"
          >
            <div className="flex items-center gap-1.5 min-w-0">
              {expanded.has(idx) ? (
                <ChevronDown size={12} className="shrink-0 text-text-muted" />
              ) : (
                <ChevronRight size={12} className="shrink-0 text-text-muted" />
              )}
              <span className="text-xs font-medium text-text-primary truncate">
                {source.document_id}
              </span>
            </div>
            <Badge variant="info" className="text-[10px] px-1.5 py-0">
              {(source.score * 100).toFixed(0)}%
            </Badge>
          </button>
          {expanded.has(idx) && (
            <div className="px-3 pb-2 pt-0 border-t border-border">
              <p className="text-xs text-text-secondary whitespace-pre-wrap mt-1.5 leading-relaxed">
                {source.content}
              </p>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

function AssistantMessage({
  message,
  isLatest,
}: {
  message: ChatMessage;
  isLatest: boolean;
}) {
  const shouldAnimate = isLatest && !message.error;
  const { displayed, done } = useTypingAnimation(
    message.content,
    shouldAnimate
  );

  const text = shouldAnimate ? displayed : message.content;

  return (
    <div className="flex gap-3 items-start animate-msg-in">
      <div className="shrink-0 h-8 w-8 rounded-full bg-surface-2 flex items-center justify-center">
        <Bot size={16} className="text-text-muted" />
      </div>
      <div className="flex-1 min-w-0 max-w-[85%]">
        <div className="rounded-2xl rounded-tl-sm bg-surface-1 border border-border px-4 py-3">
          {message.error ? (
            <p className="text-sm text-red-500">{message.error}</p>
          ) : (
            <p className="text-sm text-text-primary leading-relaxed whitespace-pre-wrap">
              {text}
              {shouldAnimate && !done && (
                <span className="inline-block w-[2px] h-[1em] bg-text-primary ml-0.5 align-text-bottom animate-blink" />
              )}
            </p>
          )}
        </div>

        {/* Metadata bar */}
        {!message.error && message.metadata && done && (
          <div className="flex items-center gap-3 mt-1.5 px-1 flex-wrap">
            {message.metadata.confidence != null && (
              <div className="flex items-center gap-1 text-[11px] text-text-muted">
                <Zap size={10} className="text-amber-500" />
                <span>{(message.metadata.confidence * 100).toFixed(1)}%</span>
              </div>
            )}
            {message.metadata.latency_ms != null && (
              <div className="flex items-center gap-1 text-[11px] text-text-muted">
                <Clock size={10} className="text-blue-500" />
                <span>{message.metadata.latency_ms}ms</span>
              </div>
            )}
            {message.metadata.tokens_used != null && (
              <div className="flex items-center gap-1 text-[11px] text-text-muted">
                <FileText size={10} className="text-green-500" />
                <span>{message.metadata.tokens_used} tokens</span>
              </div>
            )}
            <Badge
              variant={message.mode === "rag" ? "info" : "neutral"}
              className="text-[10px] px-1.5 py-0"
            >
              {message.mode.toUpperCase()}
            </Badge>
          </div>
        )}

        {/* Sources */}
        {!message.error && message.sources && message.sources.length > 0 && done && (
          <SourcesAccordion sources={message.sources} />
        )}
      </div>
    </div>
  );
}

function UserMessage({ message }: { message: ChatMessage }) {
  return (
    <div className="flex justify-end animate-msg-in">
      <div className="max-w-[85%]">
        <div className="rounded-2xl rounded-tr-sm bg-brand-600 text-white px-4 py-3">
          <p className="text-sm leading-relaxed whitespace-pre-wrap">
            {message.content}
          </p>
        </div>
        <div className="flex justify-end mt-1 px-1">
          <span className="text-[10px] text-text-muted">
            {new Date(message.timestamp).toLocaleTimeString([], {
              hour: "2-digit",
              minute: "2-digit",
            })}
          </span>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main page component
// ---------------------------------------------------------------------------
export default function PlaygroundPage() {
  const [questionInput, setQuestionInput] = useState("");
  const [mode, setMode] = useState<Mode>("rag");
  const [collectionId, setCollectionId] = useState("");
  const [topK, setTopK] = useState(5);
  const [includeSources, setIncludeSources] = useState(true);
  const [language, setLanguage] = useState("fr");
  const [collections, setCollections] = useState<Collection[]>([]);
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [latestId, setLatestId] = useState<string | null>(null);

  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    getCollections().then(setCollections).catch(() => {});
  }, []);

  // Auto-scroll on new messages or loading change
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTo({
        top: scrollRef.current.scrollHeight,
        behavior: "smooth",
      });
    }
  }, [messages, loading]);

  const isQueryResponse = (
    r: QueryResponse | SearchResponse
  ): r is QueryResponse => "answer" in r;

  const handleSubmit = useCallback(async () => {
    const question = questionInput.trim();
    if (!question || loading) return;

    const userMsg: ChatMessage = {
      id: `u-${Date.now()}`,
      role: "user",
      content: question,
      mode,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setQuestionInput("");
    setLoading(true);

    try {
      const params = {
        question,
        collection_id: collectionId || undefined,
        top_k: topK,
        include_sources: includeSources,
        language,
      };

      let response: QueryResponse | SearchResponse;
      if (mode === "rag") {
        response = await apiQuery(params);
      } else {
        response = await apiSearch(params);
      }

      const assistantContent = isQueryResponse(response)
        ? response.answer
        : response.results.map((r) => r.content).join("\n\n---\n\n");

      const sources: Source[] = isQueryResponse(response)
        ? response.sources
        : response.results;

      const assistantMsg: ChatMessage = {
        id: `a-${Date.now()}`,
        role: "assistant",
        content: assistantContent,
        metadata: {
          confidence: isQueryResponse(response)
            ? response.confidence
            : undefined,
          latency_ms: response.latency_ms,
          tokens_used: isQueryResponse(response)
            ? response.tokens_used
            : undefined,
        },
        sources,
        mode,
        timestamp: new Date().toISOString(),
      };

      setLatestId(assistantMsg.id);
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Query failed";
      const errMsg: ChatMessage = {
        id: `a-${Date.now()}`,
        role: "assistant",
        content: "",
        error: errorMessage,
        mode,
        timestamp: new Date().toISOString(),
      };
      setLatestId(errMsg.id);
      setMessages((prev) => [...prev, errMsg]);
    } finally {
      setLoading(false);
    }
  }, [
    questionInput,
    loading,
    mode,
    collectionId,
    topK,
    includeSources,
    language,
  ]);

  const clearConversation = () => {
    setMessages([]);
    setLatestId(null);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-7rem)]">
      {/* Inline styles for custom animations */}
      <style jsx global>{`
        @keyframes msg-in {
          from {
            opacity: 0;
            transform: translateY(12px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        .animate-msg-in {
          animation: msg-in 0.3s ease-out;
        }
        @keyframes blink {
          0%,
          100% {
            opacity: 1;
          }
          50% {
            opacity: 0;
          }
        }
        .animate-blink {
          animation: blink 0.8s step-end infinite;
        }
      `}</style>

      {/* Header */}
      <div className="flex items-center justify-between pb-4">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">Playground</h1>
          <p className="text-sm text-text-secondary mt-0.5">
            Testez vos requêtes RAG et recherche de manière interactive
          </p>
        </div>
        {messages.length > 0 && (
          <Button
            variant="ghost"
            size="sm"
            icon={<Trash2 size={14} />}
            onClick={clearConversation}
          >
            Effacer
          </Button>
        )}
      </div>

      {/* Chat area */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto rounded-xl border border-border bg-surface-0 px-4 py-6 space-y-6 scroll-smooth scrollbar-thin"
      >
        {messages.length === 0 && !loading ? (
          /* Empty state */
          <div className="flex flex-col items-center justify-center h-full text-text-muted">
            <div className="h-16 w-16 rounded-full bg-surface-2 flex items-center justify-center mb-4">
              <MessageSquare size={28} className="opacity-40" />
            </div>
            <p className="text-sm font-medium text-text-secondary">
              Commencez une conversation avec vos documents
            </p>
            <p className="text-xs text-text-muted mt-1">
              Posez une question ci-dessous pour démarrer
            </p>
          </div>
        ) : (
          <>
            {messages.map((msg) =>
              msg.role === "user" ? (
                <UserMessage key={msg.id} message={msg} />
              ) : (
                <AssistantMessage
                  key={msg.id}
                  message={msg}
                  isLatest={msg.id === latestId}
                />
              )
            )}

            {/* Loading indicator */}
            {loading && (
              <div className="flex gap-3 items-start animate-msg-in">
                <div className="shrink-0 h-8 w-8 rounded-full bg-surface-2 flex items-center justify-center">
                  <Bot size={16} className="text-text-muted" />
                </div>
                <div className="rounded-2xl rounded-tl-sm bg-surface-1 border border-border px-4 py-2">
                  <BouncingDots />
                </div>
              </div>
            )}
          </>
        )}
      </div>

      {/* Settings panel (slide-open) */}
      {settingsOpen && (
        <div className="border border-border border-b-0 rounded-t-xl bg-surface-0 px-4 py-3 animate-msg-in">
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm font-semibold text-text-primary">
              Paramètres
            </span>
            <button
              onClick={() => setSettingsOpen(false)}
              className="p-1 rounded-lg text-text-muted hover:text-text-primary hover:bg-surface-2 transition-colors"
            >
              <X size={14} />
            </button>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <Slider
              label="Top K"
              value={topK}
              onChange={setTopK}
              min={1}
              max={20}
              step={1}
            />

            <div>
              <span className="block text-sm font-medium text-text-primary mb-1.5">
                Mode
              </span>
              <div className="flex gap-1">
                <button
                  onClick={() => setMode("rag")}
                  className={`flex-1 flex items-center justify-center gap-1.5 py-1.5 px-2 rounded-lg text-xs font-medium transition-colors ${
                    mode === "rag"
                      ? "bg-brand-600 text-white"
                      : "bg-surface-2 text-text-secondary hover:text-text-primary"
                  }`}
                >
                  <MessageSquare size={12} />
                  RAG
                </button>
                <button
                  onClick={() => setMode("search")}
                  className={`flex-1 flex items-center justify-center gap-1.5 py-1.5 px-2 rounded-lg text-xs font-medium transition-colors ${
                    mode === "search"
                      ? "bg-brand-600 text-white"
                      : "bg-surface-2 text-text-secondary hover:text-text-primary"
                  }`}
                >
                  <Search size={12} />
                  Search
                </button>
              </div>
            </div>

            <Toggle
              label="Inclure les sources"
              checked={includeSources}
              onChange={setIncludeSources}
            />

            <Select
              label="Langue"
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              options={[
                { value: "fr", label: "Français" },
                { value: "en", label: "English" },
                { value: "de", label: "Deutsch" },
                { value: "es", label: "Español" },
                { value: "ar", label: "العربية" },
              ]}
            />
          </div>
        </div>
      )}

      {/* Input bar */}
      <div className="border border-border rounded-xl bg-surface-0 px-3 py-2 mt-2 flex items-center gap-2">
        {/* Collection selector - compact */}
        <div className="shrink-0 w-40">
          <Select
            value={collectionId}
            onChange={(e) => setCollectionId(e.target.value)}
            placeholder="Collection"
            options={[
              { value: "", label: "Toutes" },
              ...collections.map((c) => ({ value: c.id, label: c.name })),
            ]}
            className="h-8 text-xs"
          />
        </div>

        {/* Text input */}
        <input
          ref={inputRef}
          type="text"
          value={questionInput}
          onChange={(e) => setQuestionInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Posez votre question..."
          className="flex-1 h-9 bg-transparent text-sm text-text-primary placeholder:text-text-muted outline-none"
          disabled={loading}
        />

        {/* Settings gear */}
        <button
          onClick={() => setSettingsOpen((v) => !v)}
          className={`shrink-0 p-2 rounded-lg transition-colors ${
            settingsOpen
              ? "bg-brand-100 text-brand-600 dark:bg-brand-950 dark:text-brand-400"
              : "text-text-muted hover:text-text-primary hover:bg-surface-2"
          }`}
          title="Paramètres"
        >
          <Settings size={16} />
        </button>

        {/* Send button */}
        <Button
          size="sm"
          icon={<Send size={14} />}
          onClick={handleSubmit}
          loading={loading}
          disabled={!questionInput.trim()}
          className="shrink-0"
        >
          Envoyer
        </Button>
      </div>
    </div>
  );
}
