"use client";

import React, { useState, useEffect } from "react";
import {
  Layout,
  MessageSquare,
  Search,
  HelpCircle,
  Download,
  Eye,
  Copy,
  Check,
  ExternalLink,
  Paintbrush,
  X,
} from "lucide-react";
import { useRouter } from "next/navigation";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Modal } from "@/components/ui/modal";
import {
  getTemplates,
  downloadTemplate,
  getWidgets,
  type TemplateInfo,
  type WidgetConfig,
} from "@/lib/api";

const TYPE_ICONS: Record<string, React.ReactNode> = {
  chatbot: <MessageSquare size={24} />,
  search: <Search size={24} />,
  faq: <HelpCircle size={24} />,
};

const TYPE_COLORS: Record<string, string> = {
  chatbot: "from-indigo-500 to-purple-600",
  search: "from-emerald-500 to-teal-600",
  faq: "from-amber-500 to-orange-600",
};

export default function TemplatesPage() {
  const router = useRouter();
  const [templates, setTemplates] = useState<TemplateInfo[]>([]);
  const [widgets, setWidgets] = useState<WidgetConfig[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Download config modal
  const [downloadModal, setDownloadModal] = useState<TemplateInfo | null>(null);
  const [previewModal, setPreviewModal] = useState<TemplateInfo | null>(null);
  const [downloadConfig, setDownloadConfig] = useState({
    api_url: typeof window !== "undefined" ? window.location.origin : "http://localhost:8000",
    api_key: "",
    widget_id: "",
    config: {
      primary_color: "#4F46E5",
      title: "",
    },
  });
  const [downloading, setDownloading] = useState(false);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    const load = async () => {
      try {
        const [t, w] = await Promise.all([getTemplates(), getWidgets()]);
        setTemplates(t);
        setWidgets(w);
      } catch {
        setError("Failed to load templates");
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const handleDownload = async () => {
    if (!downloadModal) return;
    setDownloading(true);
    try {
      const blob = await downloadTemplate(downloadModal.name, downloadConfig);
      // Trigger browser download
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${downloadModal.name}.zip`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      setDownloadModal(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Download failed");
    } finally {
      setDownloading(false);
    }
  };

  const copyDeployCommand = (name: string) => {
    navigator.clipboard.writeText(
      `# Unzip and deploy\nunzip ${name}.zip -d my-rag-app\ncd my-rag-app\n# Open index.html or deploy to any static host\nnpx serve .`
    );
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-48 bg-surface-2 rounded animate-pulse" />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-72 bg-surface-2 rounded-xl animate-pulse" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-text-primary">Templates</h1>
        <p className="text-sm text-text-secondary mt-1">
          Applications standalone a deployer sur votre serveur. Configurez, telechargez, deployez.
        </p>
      </div>

      {error && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 dark:bg-amber-950 dark:border-amber-800 p-3 text-sm text-amber-700 dark:text-amber-300">
          {error}
        </div>
      )}

      {/* How it works */}
      <div className="bg-gradient-to-r from-brand-50 to-indigo-50 dark:from-brand-950 dark:to-indigo-950 rounded-xl p-6 border border-brand-100 dark:border-brand-900">
        <h2 className="text-lg font-semibold text-text-primary mb-3">Comment ca marche ?</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-full bg-brand-600 text-white flex items-center justify-center text-sm font-bold shrink-0">
              1
            </div>
            <div>
              <h3 className="text-sm font-semibold text-text-primary">Choisir un template</h3>
              <p className="text-xs text-text-secondary mt-0.5">
                Chatbot, portail de recherche, ou FAQ interactive
              </p>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-full bg-brand-600 text-white flex items-center justify-center text-sm font-bold shrink-0">
              2
            </div>
            <div>
              <h3 className="text-sm font-semibold text-text-primary">Configurer et telecharger</h3>
              <p className="text-xs text-text-secondary mt-0.5">
                Selectionnez votre widget et vos couleurs, telechargez le zip
              </p>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-full bg-brand-600 text-white flex items-center justify-center text-sm font-bold shrink-0">
              3
            </div>
            <div>
              <h3 className="text-sm font-semibold text-text-primary">Deployer</h3>
              <p className="text-xs text-text-secondary mt-0.5">
                Sur Vercel, Netlify, votre VPS, ou tout hebergeur statique
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Template Gallery */}
      {templates.length === 0 ? (
        <div className="text-center py-16">
          <Layout size={48} className="mx-auto text-text-muted opacity-50 mb-4" />
          <h3 className="text-lg font-medium text-text-primary">Aucun template disponible</h3>
          <p className="text-sm text-text-muted mt-1">
            Les templates seront disponibles prochainement
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {templates.map((t) => (
            <Card key={t.name} className="overflow-hidden hover:shadow-lg transition-shadow group">
              {/* Preview header with gradient */}
              <div
                className={`h-40 bg-gradient-to-br ${TYPE_COLORS[t.template_type] || TYPE_COLORS.chatbot} relative flex items-center justify-center`}
              >
                <div className="text-white/90 transform group-hover:scale-110 transition-transform">
                  {TYPE_ICONS[t.template_type] || <Layout size={24} />}
                </div>
                {/* Mockup overlay */}
                <div className="absolute inset-4 top-8 bg-white/10 backdrop-blur-sm rounded-lg border border-white/20">
                  <div className="h-3 bg-white/20 rounded-t-lg flex items-center px-2 gap-1">
                    <div className="w-1.5 h-1.5 rounded-full bg-white/40" />
                    <div className="w-1.5 h-1.5 rounded-full bg-white/40" />
                    <div className="w-1.5 h-1.5 rounded-full bg-white/40" />
                  </div>
                  <div className="p-2 space-y-1.5">
                    <div className="h-1.5 w-3/4 bg-white/15 rounded" />
                    <div className="h-1.5 w-1/2 bg-white/15 rounded" />
                    <div className="h-1.5 w-2/3 bg-white/15 rounded" />
                  </div>
                </div>
              </div>

              <CardContent className="p-5">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-brand-50 dark:bg-brand-950 text-brand-700 dark:text-brand-300">
                    {t.template_type}
                  </span>
                </div>
                <h3 className="text-lg font-semibold text-text-primary">{t.title}</h3>
                <p className="text-sm text-text-secondary mt-1 line-clamp-2">
                  {t.description}
                </p>
                <div className="flex items-center gap-2 mt-4 pt-3 border-t border-border">
                  <Button
                    size="sm"
                    icon={<Paintbrush size={14} />}
                    onClick={() => router.push(`/templates/${t.name}`)}
                  >
                    Personnaliser
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    icon={<Download size={14} />}
                    onClick={() => {
                      setDownloadConfig((prev) => ({
                        ...prev,
                        config: { ...prev.config, title: t.title },
                      }));
                      setDownloadModal(t);
                    }}
                  >
                    Telecharger
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    icon={<Eye size={14} />}
                    onClick={() => setPreviewModal(t)}
                  >
                    Preview
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Download Configuration Modal */}
      <Modal
        open={downloadModal !== null}
        onClose={() => setDownloadModal(null)}
        title={`Configurer ${downloadModal?.title || ""}`}
        description="Le template sera pre-configure avec ces parametres"
      >
        <div className="space-y-4">
          <Input
            label="URL de l'API Retrieva"
            placeholder="https://api.example.com"
            value={downloadConfig.api_url}
            onChange={(e) =>
              setDownloadConfig({ ...downloadConfig, api_url: e.target.value })
            }
          />
          <Input
            label="Cle API Publique"
            placeholder="rtv_pub_..."
            value={downloadConfig.api_key}
            onChange={(e) =>
              setDownloadConfig({ ...downloadConfig, api_key: e.target.value })
            }
          />
          <div>
            <label className="block text-sm font-medium text-text-primary mb-1.5">Widget</label>
            <select
              value={downloadConfig.widget_id}
              onChange={(e) =>
                setDownloadConfig({ ...downloadConfig, widget_id: e.target.value })
              }
              className="w-full rounded-lg border border-border bg-surface-0 px-3 py-2 text-sm text-text-primary focus:border-brand-600 focus:ring-1 focus:ring-brand-600 outline-none"
            >
              <option value="">Selectionnez un widget...</option>
              {widgets.map((w) => (
                <option key={w.id} value={w.id}>
                  {w.name} ({w.widget_type})
                </option>
              ))}
            </select>
            <p className="text-xs text-text-muted mt-1">
              Creez un widget dans la page Widgets pour obtenir une cle publique
            </p>
          </div>
          <div>
            <label className="block text-sm font-medium text-text-primary mb-1.5">Couleur principale</label>
            <div className="flex items-center gap-2">
              <input
                type="color"
                value={downloadConfig.config.primary_color}
                onChange={(e) =>
                  setDownloadConfig({
                    ...downloadConfig,
                    config: { ...downloadConfig.config, primary_color: e.target.value },
                  })
                }
                className="w-10 h-10 rounded-lg border border-border cursor-pointer"
              />
              <Input
                value={downloadConfig.config.primary_color}
                onChange={(e) =>
                  setDownloadConfig({
                    ...downloadConfig,
                    config: { ...downloadConfig.config, primary_color: e.target.value },
                  })
                }
              />
            </div>
          </div>

          <div className="bg-surface-1 rounded-lg p-3 space-y-2">
            <h4 className="text-xs font-semibold text-text-primary">Apres le telechargement :</h4>
            <div className="flex items-start gap-2">
              <pre className="flex-1 text-xs bg-gray-900 text-green-400 rounded p-2 font-mono overflow-x-auto">
{`unzip ${downloadModal?.name || "template"}.zip
cd ${downloadModal?.name || "template"}
npx serve .`}
              </pre>
              <button
                onClick={() => copyDeployCommand(downloadModal?.name || "template")}
                className="p-1.5 rounded-lg hover:bg-surface-2 text-text-muted"
              >
                {copied ? <Check size={14} /> : <Copy size={14} />}
              </button>
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-2">
            <Button variant="outline" onClick={() => setDownloadModal(null)}>
              Annuler
            </Button>
            <Button
              icon={<Download size={16} />}
              onClick={handleDownload}
              loading={downloading}
            >
              Telecharger .zip
            </Button>
          </div>
        </div>
      </Modal>

      {/* Preview Modal */}
      {previewModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
          <div className="bg-surface-0 rounded-xl shadow-2xl w-[90vw] h-[80vh] flex flex-col overflow-hidden">
            <div className="flex items-center justify-between px-4 py-3 border-b border-border">
              <div className="flex items-center gap-3">
                <span className="text-sm font-semibold text-text-primary">
                  Preview: {previewModal.title}
                </span>
                <a
                  href={`/api/v1/templates/${previewModal.name}/preview/index.html`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-1 text-xs text-brand-600 hover:underline"
                >
                  <ExternalLink size={12} /> Ouvrir dans un nouvel onglet
                </a>
              </div>
              <button
                onClick={() => setPreviewModal(null)}
                className="p-1.5 rounded-lg hover:bg-surface-2 text-text-muted"
              >
                <X size={18} />
              </button>
            </div>
            <iframe
              src={`/api/v1/templates/${previewModal.name}/preview/index.html`}
              className="flex-1 w-full border-0"
              title={`Preview ${previewModal.title}`}
            />
          </div>
        </div>
      )}
    </div>
  );
}
