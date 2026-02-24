"use client";

import React, { useState, useEffect } from "react";
import {
  Globe,
  Plus,
  MessageSquare,
  Search,
  Trash2,
  Code,
  Pencil,
  Copy,
  Check,
  ToggleLeft,
  ToggleRight,
} from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Modal } from "@/components/ui/modal";
import { Input } from "@/components/ui/input";
import {
  getWidgets,
  createWidget,
  deleteWidget,
  getWidgetEmbed,
  getCollections,
  type WidgetConfig,
  type Collection,
} from "@/lib/api";
import { formatRelativeTime } from "@/lib/utils";
import { useRouter } from "next/navigation";

export default function WidgetsPage() {
  const router = useRouter();
  const [widgets, setWidgets] = useState<WidgetConfig[]>([]);
  const [collections, setCollections] = useState<Collection[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [showEmbed, setShowEmbed] = useState<string | null>(null);
  const [embedCode, setEmbedCode] = useState("");
  const [rawKey, setRawKey] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [saving, setSaving] = useState(false);
  const [formData, setFormData] = useState({
    name: "",
    widget_type: "chatbot" as "chatbot" | "search",
    collection_id: "",
  });

  const load = async () => {
    setLoading(true);
    try {
      const [w, c] = await Promise.all([getWidgets(), getCollections()]);
      setWidgets(w);
      setCollections(c);
    } catch {
      setError("Failed to load widgets");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleCreate = async () => {
    if (!formData.name.trim()) return;
    setSaving(true);
    try {
      const result = await createWidget({
        name: formData.name,
        widget_type: formData.widget_type,
        collection_id: formData.collection_id || undefined,
        config: {
          title: formData.widget_type === "chatbot" ? "Chat with us" : "Search",
          primary_color: "#4F46E5",
          position: "bottom-right",
        },
      });
      setShowCreate(false);
      setFormData({ name: "", widget_type: "chatbot", collection_id: "" });
      // Show the raw public key
      if (result.raw_public_key) {
        setRawKey(result.raw_public_key);
      }
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create widget");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await deleteWidget(id);
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete widget");
    }
  };

  const handleShowEmbed = async (id: string) => {
    try {
      const embed = await getWidgetEmbed(id);
      setEmbedCode(embed.embed_code);
      setShowEmbed(id);
    } catch {
      setError("Failed to get embed code");
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const getCollectionName = (id: string | null) => {
    if (!id) return "All collections";
    const col = collections.find((c) => c.id === id);
    return col?.name || "Unknown";
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-48 bg-surface-2 rounded animate-pulse" />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-48 bg-surface-2 rounded-xl animate-pulse" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">Widgets</h1>
          <p className="text-sm text-text-secondary mt-1">
            Embeddable chatbots and search bars for your websites
          </p>
        </div>
        <Button
          icon={<Plus size={16} />}
          onClick={() => {
            setFormData({ name: "", widget_type: "chatbot", collection_id: "" });
            setShowCreate(true);
          }}
        >
          New Widget
        </Button>
      </div>

      {error && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 dark:bg-amber-950 dark:border-amber-800 p-3 text-sm text-amber-700 dark:text-amber-300">
          {error}
        </div>
      )}

      {rawKey && (
        <div className="rounded-lg border border-green-200 bg-green-50 dark:bg-green-950 dark:border-green-800 p-4">
          <h3 className="text-sm font-semibold text-green-800 dark:text-green-300 mb-2">
            Public API Key (shown once)
          </h3>
          <div className="flex items-center gap-2">
            <code className="flex-1 text-xs bg-white dark:bg-gray-900 border border-green-300 dark:border-green-700 rounded px-3 py-2 font-mono break-all">
              {rawKey}
            </code>
            <button
              onClick={() => copyToClipboard(rawKey)}
              className="p-2 rounded-lg hover:bg-green-100 dark:hover:bg-green-900 transition-colors"
            >
              {copied ? <Check size={16} className="text-green-600" /> : <Copy size={16} className="text-green-600" />}
            </button>
          </div>
          <p className="text-xs text-green-700 dark:text-green-400 mt-2">
            Save this key — you will need it for the embed snippet. It cannot be shown again.
          </p>
          <button
            onClick={() => setRawKey(null)}
            className="mt-2 text-xs text-green-600 hover:underline"
          >
            Dismiss
          </button>
        </div>
      )}

      {widgets.length === 0 ? (
        <div className="text-center py-16">
          <Globe size={48} className="mx-auto text-text-muted opacity-50 mb-4" />
          <h3 className="text-lg font-medium text-text-primary">No widgets yet</h3>
          <p className="text-sm text-text-muted mt-1">
            Create a widget to embed a chatbot or search bar on your website
          </p>
          <Button
            className="mt-4"
            icon={<Plus size={16} />}
            onClick={() => setShowCreate(true)}
          >
            Create First Widget
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {widgets.map((w) => (
            <Card key={w.id} className="hover:shadow-md transition-shadow group">
              <CardContent className="p-5">
                <div className="flex items-start justify-between">
                  <div className="w-10 h-10 rounded-lg bg-brand-50 dark:bg-brand-950 flex items-center justify-center text-brand-600 dark:text-brand-400">
                    {w.widget_type === "chatbot" ? (
                      <MessageSquare size={20} />
                    ) : (
                      <Search size={20} />
                    )}
                  </div>
                  <div className="flex items-center gap-1">
                    <span
                      className={`inline-flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded-full ${
                        w.is_active
                          ? "bg-green-100 text-green-700 dark:bg-green-950 dark:text-green-400"
                          : "bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-400"
                      }`}
                    >
                      {w.is_active ? "Active" : "Inactive"}
                    </span>
                  </div>
                </div>

                <h3 className="mt-3 font-semibold text-text-primary">{w.name}</h3>
                <p className="mt-1 text-sm text-text-secondary">
                  {w.widget_type === "chatbot" ? "Chatbot" : "Search Bar"} · {getCollectionName(w.collection_id)}
                </p>

                <div className="flex items-center gap-2 mt-4 pt-3 border-t border-border">
                  <button
                    onClick={() => router.push(`/widgets/${w.id}`)}
                    className="flex items-center gap-1.5 text-xs text-text-muted hover:text-text-primary transition-colors px-2 py-1.5 rounded-lg hover:bg-surface-2"
                  >
                    <Pencil size={13} /> Edit
                  </button>
                  <button
                    onClick={() => handleShowEmbed(w.id)}
                    className="flex items-center gap-1.5 text-xs text-text-muted hover:text-brand-600 transition-colors px-2 py-1.5 rounded-lg hover:bg-brand-50 dark:hover:bg-brand-950"
                  >
                    <Code size={13} /> Embed
                  </button>
                  <button
                    onClick={() => handleDelete(w.id)}
                    className="flex items-center gap-1.5 text-xs text-text-muted hover:text-red-600 transition-colors px-2 py-1.5 rounded-lg hover:bg-red-50 dark:hover:bg-red-950 ml-auto"
                  >
                    <Trash2 size={13} />
                  </button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Create Widget Modal */}
      <Modal
        open={showCreate}
        onClose={() => setShowCreate(false)}
        title="New Widget"
        description="Create an embeddable widget for your website"
      >
        <div className="space-y-4">
          <Input
            label="Name"
            placeholder="e.g., Support Chatbot"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
          />
          <div>
            <label className="block text-sm font-medium text-text-primary mb-2">Type</label>
            <div className="grid grid-cols-2 gap-3">
              <button
                onClick={() => setFormData({ ...formData, widget_type: "chatbot" })}
                className={`flex flex-col items-center gap-2 p-4 rounded-lg border-2 transition-colors ${
                  formData.widget_type === "chatbot"
                    ? "border-brand-600 bg-brand-50 dark:bg-brand-950"
                    : "border-border hover:border-brand-300"
                }`}
              >
                <MessageSquare size={24} className="text-brand-600" />
                <span className="text-sm font-medium">Chatbot</span>
                <span className="text-xs text-text-muted">Q&A conversationnel</span>
              </button>
              <button
                onClick={() => setFormData({ ...formData, widget_type: "search" })}
                className={`flex flex-col items-center gap-2 p-4 rounded-lg border-2 transition-colors ${
                  formData.widget_type === "search"
                    ? "border-brand-600 bg-brand-50 dark:bg-brand-950"
                    : "border-border hover:border-brand-300"
                }`}
              >
                <Search size={24} className="text-brand-600" />
                <span className="text-sm font-medium">Search Bar</span>
                <span className="text-xs text-text-muted">Recherche semantique</span>
              </button>
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-text-primary mb-1.5">Collection</label>
            <select
              value={formData.collection_id}
              onChange={(e) => setFormData({ ...formData, collection_id: e.target.value })}
              className="w-full rounded-lg border border-border bg-surface-0 px-3 py-2 text-sm text-text-primary focus:border-brand-600 focus:ring-1 focus:ring-brand-600 outline-none"
            >
              <option value="">Select a collection...</option>
              {collections.map((c) => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <Button variant="outline" onClick={() => setShowCreate(false)}>
              Cancel
            </Button>
            <Button onClick={handleCreate} disabled={!formData.name.trim()} loading={saving}>
              Create Widget
            </Button>
          </div>
        </div>
      </Modal>

      {/* Embed Code Modal */}
      <Modal
        open={showEmbed !== null}
        onClose={() => setShowEmbed(null)}
        title="Embed Code"
        description="Copy this snippet and paste it into your website HTML"
      >
        <div className="space-y-4">
          <div className="relative">
            <pre className="bg-gray-900 text-green-400 rounded-lg p-4 text-sm overflow-x-auto font-mono whitespace-pre-wrap">
              {embedCode}
            </pre>
            <button
              onClick={() => copyToClipboard(embedCode)}
              className="absolute top-2 right-2 p-2 rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-400 hover:text-white transition-colors"
            >
              {copied ? <Check size={14} /> : <Copy size={14} />}
            </button>
          </div>
          <p className="text-xs text-text-muted">
            Add the <code className="text-brand-600">data-key</code> attribute with your public API key to authenticate requests.
          </p>
          <div className="flex justify-end">
            <Button variant="outline" onClick={() => setShowEmbed(null)}>
              Close
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
