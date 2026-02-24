"use client";

import React, { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  ArrowLeft,
  Save,
  Code,
  Trash2,
  Copy,
  Check,
  MessageSquare,
  Search,
  Eye,
} from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Modal } from "@/components/ui/modal";
import {
  getWidget,
  updateWidget,
  deleteWidget,
  getWidgetEmbed,
  getCollections,
  type WidgetConfig,
  type Collection,
} from "@/lib/api";

export default function WidgetEditPage() {
  const params = useParams();
  const router = useRouter();
  const widgetId = params.id as string;

  const [widget, setWidget] = useState<WidgetConfig | null>(null);
  const [collections, setCollections] = useState<Collection[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [showEmbed, setShowEmbed] = useState(false);
  const [embedCode, setEmbedCode] = useState("");
  const [copied, setCopied] = useState(false);
  const [showPreview, setShowPreview] = useState(false);

  // Form state
  const [name, setName] = useState("");
  const [collectionId, setCollectionId] = useState("");
  const [isActive, setIsActive] = useState(true);
  const [config, setConfig] = useState({
    title: "Chat with us",
    welcome_message: "",
    position: "bottom-right",
    primary_color: "#4F46E5",
    text_color: "#FFFFFF",
    placeholder: "Type a message...",
    show_sources: false,
    custom_css: "",
  });

  useEffect(() => {
    const load = async () => {
      try {
        const [w, cols] = await Promise.all([
          getWidget(widgetId),
          getCollections(),
        ]);
        setWidget(w);
        setCollections(cols);
        setName(w.name);
        setCollectionId(w.collection_id || "");
        setIsActive(w.is_active);
        setConfig({
          title: (w.config.title as string) || "Chat with us",
          welcome_message: (w.config.welcome_message as string) || "",
          position: (w.config.position as string) || "bottom-right",
          primary_color: (w.config.primary_color as string) || "#4F46E5",
          text_color: (w.config.text_color as string) || "#FFFFFF",
          placeholder: (w.config.placeholder as string) || "Type a message...",
          show_sources: (w.config.show_sources as boolean) || false,
          custom_css: (w.config.custom_css as string) || "",
        });
      } catch {
        setError("Failed to load widget");
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [widgetId]);

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    setSuccess(null);
    try {
      await updateWidget(widgetId, {
        name,
        collection_id: collectionId || undefined,
        config,
        is_active: isActive,
      });
      setSuccess("Widget updated successfully");
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update widget");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    try {
      await deleteWidget(widgetId);
      router.push("/widgets");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete widget");
    }
  };

  const handleShowEmbed = async () => {
    try {
      const embed = await getWidgetEmbed(widgetId);
      setEmbedCode(embed.embed_code);
      setShowEmbed(true);
    } catch {
      setError("Failed to get embed code");
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-64 bg-surface-2 rounded animate-pulse" />
        <div className="h-96 bg-surface-2 rounded-xl animate-pulse" />
      </div>
    );
  }

  if (!widget) {
    return (
      <div className="text-center py-16">
        <p className="text-text-muted">Widget not found</p>
        <Button className="mt-4" variant="outline" onClick={() => router.push("/widgets")}>
          Back to Widgets
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button
            onClick={() => router.push("/widgets")}
            className="p-2 rounded-lg hover:bg-surface-2 transition-colors text-text-muted hover:text-text-primary"
          >
            <ArrowLeft size={20} />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-text-primary">{widget.name}</h1>
            <p className="text-sm text-text-secondary mt-0.5">
              {widget.widget_type === "chatbot" ? "Chatbot Widget" : "Search Bar Widget"}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" icon={<Code size={16} />} onClick={handleShowEmbed}>
            Embed Code
          </Button>
          <Button icon={<Save size={16} />} onClick={handleSave} loading={saving}>
            Save
          </Button>
        </div>
      </div>

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 dark:bg-red-950 dark:border-red-800 p-3 text-sm text-red-700 dark:text-red-300">
          {error}
        </div>
      )}
      {success && (
        <div className="rounded-lg border border-green-200 bg-green-50 dark:bg-green-950 dark:border-green-800 p-3 text-sm text-green-700 dark:text-green-300">
          {success}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Config Form */}
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardContent className="p-6 space-y-4">
              <h2 className="text-lg font-semibold text-text-primary">General</h2>
              <Input
                label="Name"
                value={name}
                onChange={(e) => setName(e.target.value)}
              />
              <div>
                <label className="block text-sm font-medium text-text-primary mb-1.5">Collection</label>
                <select
                  value={collectionId}
                  onChange={(e) => setCollectionId(e.target.value)}
                  className="w-full rounded-lg border border-border bg-surface-0 px-3 py-2 text-sm text-text-primary focus:border-brand-600 focus:ring-1 focus:ring-brand-600 outline-none"
                >
                  <option value="">Select a collection...</option>
                  {collections.map((c) => (
                    <option key={c.id} value={c.id}>{c.name}</option>
                  ))}
                </select>
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-sm font-medium text-text-primary">Active</span>
                  <p className="text-xs text-text-muted">Widget is publicly accessible</p>
                </div>
                <button
                  onClick={() => setIsActive(!isActive)}
                  className={`relative w-11 h-6 rounded-full transition-colors ${
                    isActive ? "bg-brand-600" : "bg-gray-300 dark:bg-gray-600"
                  }`}
                >
                  <span
                    className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform ${
                      isActive ? "translate-x-5" : ""
                    }`}
                  />
                </button>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6 space-y-4">
              <h2 className="text-lg font-semibold text-text-primary">Appearance</h2>
              <Input
                label="Title"
                value={config.title}
                onChange={(e) => setConfig({ ...config, title: e.target.value })}
              />
              <Input
                label="Welcome Message"
                placeholder="Hi! How can I help you today?"
                value={config.welcome_message}
                onChange={(e) => setConfig({ ...config, welcome_message: e.target.value })}
              />
              <Input
                label="Placeholder"
                value={config.placeholder}
                onChange={(e) => setConfig({ ...config, placeholder: e.target.value })}
              />
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-text-primary mb-1.5">Primary Color</label>
                  <div className="flex items-center gap-2">
                    <input
                      type="color"
                      value={config.primary_color}
                      onChange={(e) => setConfig({ ...config, primary_color: e.target.value })}
                      className="w-10 h-10 rounded-lg border border-border cursor-pointer"
                    />
                    <Input
                      value={config.primary_color}
                      onChange={(e) => setConfig({ ...config, primary_color: e.target.value })}
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-text-primary mb-1.5">Text Color</label>
                  <div className="flex items-center gap-2">
                    <input
                      type="color"
                      value={config.text_color}
                      onChange={(e) => setConfig({ ...config, text_color: e.target.value })}
                      className="w-10 h-10 rounded-lg border border-border cursor-pointer"
                    />
                    <Input
                      value={config.text_color}
                      onChange={(e) => setConfig({ ...config, text_color: e.target.value })}
                    />
                  </div>
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-text-primary mb-1.5">Position</label>
                <div className="grid grid-cols-2 gap-3">
                  {(["bottom-right", "bottom-left"] as const).map((pos) => (
                    <button
                      key={pos}
                      onClick={() => setConfig({ ...config, position: pos })}
                      className={`px-4 py-2.5 rounded-lg border-2 text-sm font-medium transition-colors ${
                        config.position === pos
                          ? "border-brand-600 bg-brand-50 dark:bg-brand-950 text-brand-700"
                          : "border-border hover:border-brand-300 text-text-secondary"
                      }`}
                    >
                      {pos === "bottom-right" ? "Bottom Right" : "Bottom Left"}
                    </button>
                  ))}
                </div>
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-sm font-medium text-text-primary">Show Sources</span>
                  <p className="text-xs text-text-muted">Display source references in responses</p>
                </div>
                <button
                  onClick={() => setConfig({ ...config, show_sources: !config.show_sources })}
                  className={`relative w-11 h-6 rounded-full transition-colors ${
                    config.show_sources ? "bg-brand-600" : "bg-gray-300 dark:bg-gray-600"
                  }`}
                >
                  <span
                    className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform ${
                      config.show_sources ? "translate-x-5" : ""
                    }`}
                  />
                </button>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6 space-y-4">
              <h2 className="text-lg font-semibold text-text-primary">Custom CSS</h2>
              <Textarea
                placeholder=".retrieva-widget { /* your custom styles */ }"
                value={config.custom_css}
                onChange={(e) => setConfig({ ...config, custom_css: e.target.value })}
                rows={5}
                className="font-mono text-sm"
              />
            </CardContent>
          </Card>

          {/* Danger zone */}
          <Card className="border-red-200 dark:border-red-900">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-semibold text-red-600">Delete Widget</h2>
                  <p className="text-sm text-text-muted mt-1">
                    This will permanently delete the widget and its public API key.
                  </p>
                </div>
                <Button
                  variant="outline"
                  className="border-red-200 text-red-600 hover:bg-red-50 dark:border-red-800 dark:hover:bg-red-950"
                  icon={<Trash2 size={16} />}
                  onClick={handleDelete}
                >
                  Delete
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right: Preview */}
        <div className="space-y-4">
          <Card className="sticky top-4">
            <CardContent className="p-6">
              <h2 className="text-lg font-semibold text-text-primary mb-4">Preview</h2>
              <div
                className="relative bg-gray-100 dark:bg-gray-800 rounded-lg overflow-hidden"
                style={{ height: "500px" }}
              >
                {/* Mini website mockup */}
                <div className="p-4 space-y-3">
                  <div className="h-4 w-32 bg-gray-300 dark:bg-gray-600 rounded" />
                  <div className="h-3 w-full bg-gray-200 dark:bg-gray-700 rounded" />
                  <div className="h-3 w-3/4 bg-gray-200 dark:bg-gray-700 rounded" />
                  <div className="h-3 w-5/6 bg-gray-200 dark:bg-gray-700 rounded" />
                  <div className="h-20 w-full bg-gray-200 dark:bg-gray-700 rounded mt-4" />
                  <div className="h-3 w-2/3 bg-gray-200 dark:bg-gray-700 rounded" />
                </div>

                {/* Widget preview */}
                {widget.widget_type === "chatbot" ? (
                  <div
                    className="absolute"
                    style={{
                      [config.position === "bottom-right" ? "right" : "left"]: "12px",
                      bottom: "12px",
                    }}
                  >
                    {showPreview ? (
                      <div className="mb-2 w-64 rounded-xl shadow-xl overflow-hidden bg-white dark:bg-gray-900">
                        <div
                          className="px-3 py-2.5 text-xs font-semibold flex items-center justify-between"
                          style={{ backgroundColor: config.primary_color, color: config.text_color }}
                        >
                          <span>{config.title}</span>
                          <button
                            onClick={() => setShowPreview(false)}
                            className="opacity-80 hover:opacity-100"
                            style={{ color: config.text_color }}
                          >
                            &times;
                          </button>
                        </div>
                        <div className="p-3 space-y-2 h-40 overflow-y-auto">
                          {config.welcome_message && (
                            <div className="bg-gray-100 dark:bg-gray-800 rounded-lg px-2.5 py-1.5 text-xs text-text-primary max-w-[80%]">
                              {config.welcome_message}
                            </div>
                          )}
                          <div
                            className="rounded-lg px-2.5 py-1.5 text-xs ml-auto max-w-[80%]"
                            style={{ backgroundColor: config.primary_color, color: config.text_color }}
                          >
                            What is RAG?
                          </div>
                          <div className="bg-gray-100 dark:bg-gray-800 rounded-lg px-2.5 py-1.5 text-xs text-text-primary max-w-[80%]">
                            RAG stands for Retrieval-Augmented Generation...
                          </div>
                        </div>
                        <div className="border-t border-border p-2 flex gap-1.5">
                          <div className="flex-1 border border-border rounded-md px-2 py-1 text-xs text-text-muted">
                            {config.placeholder}
                          </div>
                          <div
                            className="px-2 py-1 rounded-md text-xs"
                            style={{ backgroundColor: config.primary_color, color: config.text_color }}
                          >
                            &#9654;
                          </div>
                        </div>
                      </div>
                    ) : null}
                    <button
                      onClick={() => setShowPreview(!showPreview)}
                      className="w-11 h-11 rounded-full flex items-center justify-center shadow-lg"
                      style={{ backgroundColor: config.primary_color, color: config.text_color }}
                    >
                      <MessageSquare size={18} />
                    </button>
                  </div>
                ) : (
                  <div className="absolute top-1/3 left-4 right-4">
                    <div className="bg-white dark:bg-gray-900 rounded-lg border border-border shadow-sm p-2 flex items-center gap-2">
                      <Search size={14} className="text-text-muted" />
                      <span className="text-xs text-text-muted">{config.placeholder}</span>
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Embed Code Modal */}
      <Modal
        open={showEmbed}
        onClose={() => setShowEmbed(false)}
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
            <Button variant="outline" onClick={() => setShowEmbed(false)}>
              Close
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
