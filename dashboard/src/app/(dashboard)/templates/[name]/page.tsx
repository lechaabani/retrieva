"use client";

import React, { useState, useEffect, useCallback, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  ArrowLeft,
  Download,
  Eye,
  Palette,
  Type,
  Settings2,
  Monitor,
  Tablet,
  Smartphone,
  RotateCcw,
  Copy,
  Check,
  ExternalLink,
  RefreshCw,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  getTemplate,
  getWidgets,
  downloadTemplate,
  type TemplateInfo,
  type WidgetConfig,
} from "@/lib/api";

type Viewport = "desktop" | "tablet" | "mobile";

interface EditorConfig {
  // Connection
  api_url: string;
  api_key: string;
  widget_id: string;
  // Visual
  primary_color: string;
  primary_hover: string;
  background_color: string;
  text_color: string;
  border_color: string;
  // Content
  title: string;
  subtitle: string;
  placeholder: string;
  welcome_message: string;
  // Layout
  border_radius: string;
  font_family: string;
}

const DEFAULT_CONFIG: EditorConfig = {
  api_url: typeof window !== "undefined" ? window.location.origin : "http://localhost:8000",
  api_key: "",
  widget_id: "",
  primary_color: "#4F46E5",
  primary_hover: "#4338CA",
  background_color: "#FFFFFF",
  text_color: "#1F2937",
  border_color: "#E5E7EB",
  title: "",
  subtitle: "",
  placeholder: "Posez votre question...",
  welcome_message: "Bonjour ! Comment puis-je vous aider ?",
  border_radius: "12",
  font_family: "Inter, system-ui, sans-serif",
};

const PRESET_THEMES = [
  { name: "Indigo", primary: "#4F46E5", hover: "#4338CA", bg: "#FFFFFF", text: "#1F2937", border: "#E5E7EB" },
  { name: "Emerald", primary: "#059669", hover: "#047857", bg: "#FFFFFF", text: "#1F2937", border: "#D1D5DB" },
  { name: "Rose", primary: "#E11D48", hover: "#BE123C", bg: "#FFFFFF", text: "#1F2937", border: "#E5E7EB" },
  { name: "Amber", primary: "#D97706", hover: "#B45309", bg: "#FFFFFF", text: "#1F2937", border: "#E5E7EB" },
  { name: "Violet", primary: "#7C3AED", hover: "#6D28D9", bg: "#FFFFFF", text: "#1F2937", border: "#E5E7EB" },
  { name: "Dark", primary: "#6366F1", hover: "#818CF8", bg: "#0F172A", text: "#F1F5F9", border: "#334155" },
  { name: "Slate", primary: "#3B82F6", hover: "#2563EB", bg: "#1E293B", text: "#E2E8F0", border: "#475569" },
  { name: "Warm", primary: "#EA580C", hover: "#C2410C", bg: "#FFFBEB", text: "#451A03", border: "#FDE68A" },
];

const FONT_OPTIONS = [
  "Inter, system-ui, sans-serif",
  "system-ui, sans-serif",
  "'Segoe UI', Tahoma, sans-serif",
  "Georgia, serif",
  "'Fira Code', monospace",
];

export default function TemplateEditorPage() {
  const params = useParams();
  const router = useRouter();
  const templateName = params.name as string;
  const iframeRef = useRef<HTMLIFrameElement>(null);

  const [template, setTemplate] = useState<TemplateInfo | null>(null);
  const [widgets, setWidgets] = useState<WidgetConfig[]>([]);
  const [loading, setLoading] = useState(true);
  const [config, setConfig] = useState<EditorConfig>(DEFAULT_CONFIG);
  const [activeTab, setActiveTab] = useState<"theme" | "content" | "connection">("theme");
  const [viewport, setViewport] = useState<Viewport>("desktop");
  const [downloading, setDownloading] = useState(false);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        const [t, w] = await Promise.all([
          getTemplate(templateName),
          getWidgets(),
        ]);
        setTemplate(t);
        setWidgets(w);
        setConfig((prev) => ({ ...prev, title: t.title }));
      } catch {
        setError("Template not found");
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [templateName]);

  const injectStyles = useCallback(() => {
    const iframe = iframeRef.current;
    if (!iframe?.contentDocument) return;
    try {
      const doc = iframe.contentDocument;
      let styleEl = doc.getElementById("retrieva-editor-vars");
      if (!styleEl) {
        styleEl = doc.createElement("style");
        styleEl.id = "retrieva-editor-vars";
        doc.head.appendChild(styleEl);
      }
      styleEl.textContent = `
        :root {
          --primary: ${config.primary_color} !important;
          --primary-hover: ${config.primary_hover} !important;
          --bg: ${config.background_color} !important;
          --text: ${config.text_color} !important;
          --border: ${config.border_color} !important;
        }
        body {
          font-family: ${config.font_family} !important;
        }
      `;
    } catch {
      // Cross-origin iframe, cannot inject
    }
  }, [config]);

  useEffect(() => {
    injectStyles();
  }, [injectStyles]);

  const handleIframeLoad = () => {
    injectStyles();
  };

  const updateConfig = (key: keyof EditorConfig, value: string) => {
    setConfig((prev) => ({ ...prev, [key]: value }));
  };

  const applyTheme = (theme: typeof PRESET_THEMES[0]) => {
    setConfig((prev) => ({
      ...prev,
      primary_color: theme.primary,
      primary_hover: theme.hover,
      background_color: theme.bg,
      text_color: theme.text,
      border_color: theme.border,
    }));
  };

  const resetConfig = () => {
    setConfig({ ...DEFAULT_CONFIG, title: template?.title || "" });
  };

  const handleDownload = async () => {
    if (!template) return;
    setDownloading(true);
    try {
      const blob = await downloadTemplate(template.name, {
        api_url: config.api_url,
        api_key: config.api_key,
        widget_id: config.widget_id,
        config: {
          primary_color: config.primary_color,
          title: config.title,
        },
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${template.name}.zip`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Download failed");
    } finally {
      setDownloading(false);
    }
  };

  const copySnippet = () => {
    const snippet = `<script src="${config.api_url}/widget/chatbot.js"
  data-widget-id="${config.widget_id}"
  data-key="${config.api_key}"
  data-api="${config.api_url}"></script>`;
    navigator.clipboard.writeText(snippet);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const viewportWidths: Record<Viewport, string> = {
    desktop: "100%",
    tablet: "768px",
    mobile: "375px",
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[80vh]">
        <div className="animate-spin h-8 w-8 border-2 border-brand-600 border-t-transparent rounded-full" />
      </div>
    );
  }

  if (error || !template) {
    return (
      <div className="space-y-4">
        <Button variant="ghost" icon={<ArrowLeft size={16} />} onClick={() => router.push("/templates")}>
          Retour
        </Button>
        <div className="text-center py-16">
          <p className="text-text-muted">{error || "Template introuvable"}</p>
        </div>
      </div>
    );
  }

  const previewUrl = `/api/v1/templates/${templateName}/preview/index.html`;

  return (
    <div className="h-[calc(100vh-2rem)] flex flex-col -mt-2">
      {/* Top bar */}
      <div className="flex items-center justify-between py-3 px-1 border-b border-border shrink-0">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="sm" icon={<ArrowLeft size={16} />} onClick={() => router.push("/templates")}>
            Templates
          </Button>
          <div className="h-5 w-px bg-border" />
          <h1 className="text-sm font-semibold text-text-primary">{template.title}</h1>
          <span className="text-xs px-2 py-0.5 rounded-full bg-brand-50 dark:bg-brand-950 text-brand-700 dark:text-brand-300">
            {template.template_type}
          </span>
        </div>

        <div className="flex items-center gap-2">
          {/* Viewport switcher */}
          <div className="flex items-center bg-surface-1 rounded-lg p-0.5 gap-0.5">
            {([
              ["desktop", Monitor],
              ["tablet", Tablet],
              ["mobile", Smartphone],
            ] as const).map(([vp, Icon]) => (
              <button
                key={vp}
                onClick={() => setViewport(vp)}
                className={`p-1.5 rounded-md transition-colors ${
                  viewport === vp
                    ? "bg-surface-0 shadow-sm text-text-primary"
                    : "text-text-muted hover:text-text-secondary"
                }`}
                title={vp}
              >
                <Icon size={16} />
              </button>
            ))}
          </div>

          <Button variant="outline" size="sm" icon={<RotateCcw size={14} />} onClick={resetConfig}>
            Reset
          </Button>
          <a href={previewUrl} target="_blank" rel="noopener noreferrer">
            <Button variant="outline" size="sm" icon={<ExternalLink size={14} />}>
              Ouvrir
            </Button>
          </a>
          <Button size="sm" icon={<Download size={14} />} onClick={handleDownload} loading={downloading}>
            Telecharger
          </Button>
        </div>
      </div>

      {/* Main editor area */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left panel — Config */}
        <div className="w-80 border-r border-border bg-surface-0 flex flex-col shrink-0 overflow-hidden">
          {/* Tabs */}
          <div className="flex border-b border-border shrink-0">
            {([
              ["theme", Palette, "Theme"],
              ["content", Type, "Contenu"],
              ["connection", Settings2, "Connexion"],
            ] as const).map(([tab, Icon, label]) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`flex-1 flex items-center justify-center gap-1.5 py-2.5 text-xs font-medium transition-colors border-b-2 ${
                  activeTab === tab
                    ? "border-brand-600 text-brand-700 dark:text-brand-300"
                    : "border-transparent text-text-muted hover:text-text-secondary"
                }`}
              >
                <Icon size={14} />
                {label}
              </button>
            ))}
          </div>

          {/* Tab content */}
          <div className="flex-1 overflow-y-auto p-4 space-y-5">
            {activeTab === "theme" && (
              <>
                {/* Preset themes */}
                <div>
                  <label className="block text-xs font-semibold text-text-primary mb-2">Themes</label>
                  <div className="grid grid-cols-4 gap-2">
                    {PRESET_THEMES.map((t) => (
                      <button
                        key={t.name}
                        onClick={() => applyTheme(t)}
                        className="group flex flex-col items-center gap-1 p-2 rounded-lg border border-border hover:border-brand-400 transition-colors"
                        title={t.name}
                      >
                        <div className="flex gap-0.5">
                          <div className="w-4 h-4 rounded-full border border-border/50" style={{ backgroundColor: t.primary }} />
                          <div className="w-4 h-4 rounded-full border border-border/50" style={{ backgroundColor: t.bg }} />
                        </div>
                        <span className="text-[10px] text-text-muted group-hover:text-text-secondary">{t.name}</span>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Color pickers */}
                <div className="space-y-3">
                  <label className="block text-xs font-semibold text-text-primary">Couleurs</label>
                  {([
                    ["primary_color", "Primaire"],
                    ["primary_hover", "Primaire hover"],
                    ["background_color", "Fond"],
                    ["text_color", "Texte"],
                    ["border_color", "Bordure"],
                  ] as const).map(([key, label]) => (
                    <div key={key} className="flex items-center gap-2">
                      <input
                        type="color"
                        value={config[key]}
                        onChange={(e) => updateConfig(key, e.target.value)}
                        className="w-8 h-8 rounded border border-border cursor-pointer shrink-0"
                      />
                      <div className="flex-1">
                        <span className="text-xs text-text-secondary">{label}</span>
                        <input
                          type="text"
                          value={config[key]}
                          onChange={(e) => updateConfig(key, e.target.value)}
                          className="block w-full text-xs bg-transparent border-0 text-text-primary p-0 font-mono focus:ring-0 focus:outline-none"
                        />
                      </div>
                    </div>
                  ))}
                </div>

                {/* Border radius */}
                <div>
                  <label className="block text-xs font-semibold text-text-primary mb-1.5">Border radius</label>
                  <div className="flex items-center gap-2">
                    <input
                      type="range"
                      min="0"
                      max="24"
                      value={config.border_radius}
                      onChange={(e) => updateConfig("border_radius", e.target.value)}
                      className="flex-1"
                    />
                    <span className="text-xs text-text-muted w-8 text-right">{config.border_radius}px</span>
                  </div>
                </div>

                {/* Font family */}
                <div>
                  <label className="block text-xs font-semibold text-text-primary mb-1.5">Police</label>
                  <select
                    value={config.font_family}
                    onChange={(e) => updateConfig("font_family", e.target.value)}
                    className="w-full rounded-lg border border-border bg-surface-0 px-3 py-2 text-xs text-text-primary focus:border-brand-600 outline-none"
                  >
                    {FONT_OPTIONS.map((f) => (
                      <option key={f} value={f}>{f.split(",")[0].replace(/'/g, "")}</option>
                    ))}
                  </select>
                </div>
              </>
            )}

            {activeTab === "content" && (
              <>
                <Input
                  label="Titre"
                  value={config.title}
                  onChange={(e) => updateConfig("title", e.target.value)}
                  placeholder="Mon assistant IA"
                />
                <Input
                  label="Sous-titre"
                  value={config.subtitle}
                  onChange={(e) => updateConfig("subtitle", e.target.value)}
                  placeholder="Posez vos questions en langage naturel"
                />
                <Input
                  label="Placeholder du champ de saisie"
                  value={config.placeholder}
                  onChange={(e) => updateConfig("placeholder", e.target.value)}
                  placeholder="Posez votre question..."
                />
                <div>
                  <label className="block text-sm font-medium text-text-primary mb-1.5">Message de bienvenue</label>
                  <textarea
                    value={config.welcome_message}
                    onChange={(e) => updateConfig("welcome_message", e.target.value)}
                    rows={3}
                    className="w-full rounded-lg border border-border bg-surface-0 px-3 py-2 text-sm text-text-primary focus:border-brand-600 focus:ring-1 focus:ring-brand-600 outline-none resize-none"
                    placeholder="Bonjour ! Comment puis-je vous aider ?"
                  />
                </div>
              </>
            )}

            {activeTab === "connection" && (
              <>
                <Input
                  label="URL de l'API"
                  value={config.api_url}
                  onChange={(e) => updateConfig("api_url", e.target.value)}
                  placeholder="https://api.retrieva.io"
                />
                <Input
                  label="Cle API publique"
                  value={config.api_key}
                  onChange={(e) => updateConfig("api_key", e.target.value)}
                  placeholder="rtv_pub_..."
                />
                <div>
                  <label className="block text-sm font-medium text-text-primary mb-1.5">Widget</label>
                  <select
                    value={config.widget_id}
                    onChange={(e) => updateConfig("widget_id", e.target.value)}
                    className="w-full rounded-lg border border-border bg-surface-0 px-3 py-2 text-sm text-text-primary focus:border-brand-600 outline-none"
                  >
                    <option value="">Selectionnez un widget...</option>
                    {widgets.map((w) => (
                      <option key={w.id} value={w.id}>
                        {w.name} ({w.widget_type})
                      </option>
                    ))}
                  </select>
                  <p className="text-xs text-text-muted mt-1">
                    Creez un widget dans Widgets pour obtenir un ID
                  </p>
                </div>

                {/* Embed snippet */}
                <div className="bg-surface-1 rounded-lg p-3">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-semibold text-text-primary">Code embed</span>
                    <button
                      onClick={copySnippet}
                      className="flex items-center gap-1 text-xs text-brand-600 hover:text-brand-700"
                    >
                      {copied ? <Check size={12} /> : <Copy size={12} />}
                      {copied ? "Copie !" : "Copier"}
                    </button>
                  </div>
                  <pre className="text-[11px] bg-gray-900 text-green-400 rounded p-2 font-mono overflow-x-auto whitespace-pre-wrap">
{`<script
  src="${config.api_url}/widget/chatbot.js"
  data-widget-id="${config.widget_id || "WIDGET_ID"}"
  data-key="${config.api_key || "rtv_pub_xxx"}"
  data-api="${config.api_url}">
</script>`}
                  </pre>
                </div>
              </>
            )}
          </div>
        </div>

        {/* Right panel — Preview */}
        <div className="flex-1 bg-[#f5f5f5] dark:bg-gray-900 flex items-start justify-center p-6 overflow-auto">
          <div
            className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl overflow-hidden transition-all duration-300 border border-border/50"
            style={{
              width: viewportWidths[viewport],
              maxWidth: "100%",
              height: viewport === "mobile" ? "667px" : viewport === "tablet" ? "600px" : "100%",
            }}
          >
            {/* Browser chrome */}
            <div className="h-8 bg-gray-100 dark:bg-gray-700 flex items-center px-3 gap-1.5 border-b border-border/30">
              <div className="w-2.5 h-2.5 rounded-full bg-red-400/70" />
              <div className="w-2.5 h-2.5 rounded-full bg-yellow-400/70" />
              <div className="w-2.5 h-2.5 rounded-full bg-green-400/70" />
              <div className="flex-1 mx-3">
                <div className="bg-white dark:bg-gray-600 rounded px-2 py-0.5 text-[10px] text-text-muted truncate max-w-xs mx-auto text-center">
                  {config.api_url || "localhost:8000"}
                </div>
              </div>
              <button
                onClick={() => {
                  const iframe = iframeRef.current;
                  if (iframe) {
                    iframe.src = iframe.src;
                  }
                }}
                className="p-0.5 text-text-muted hover:text-text-primary"
                title="Recharger"
              >
                <RefreshCw size={12} />
              </button>
            </div>
            <iframe
              ref={iframeRef}
              src={previewUrl}
              className="w-full border-0"
              style={{ height: viewport === "mobile" ? "639px" : viewport === "tablet" ? "572px" : "calc(80vh - 2rem)" }}
              title={`Preview ${template.title}`}
              onLoad={handleIframeLoad}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
