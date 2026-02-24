"use client";

import React, { useState, useEffect, useMemo } from "react";
import {
  Puzzle,
  Download,
  Trash2,
  Settings2,
  Database,
  Brain,
  MessageSquare,
  Scissors,
  Link2,
  Search,
  Shield,
  FileText,
  Repeat,
  Layout,
  Check,
  ChevronDown,
  ChevronRight,
} from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Toggle } from "@/components/ui/toggle";
import { Modal } from "@/components/ui/modal";
import { Input } from "@/components/ui/input";
import { PluginConfigPanel } from "@/components/plugin-config-panel";
import {
  getPlugins,
  enablePlugin,
  disablePlugin,
  installPlugin,
  uninstallPlugin,
  configurePlugin,
  type PluginInfo,
} from "@/lib/api";

// Category definitions with icons, descriptions and display order
const CATEGORIES: Record<
  string,
  { label: string; description: string; icon: React.ReactNode; order: number }
> = {
  embedder: {
    label: "Embedding",
    description: "Convertit le texte en vecteurs pour la recherche semantique",
    icon: <Brain size={20} />,
    order: 1,
  },
  generator: {
    label: "Generation IA",
    description: "Modeles de langage pour generer les reponses RAG",
    icon: <MessageSquare size={20} />,
    order: 2,
  },
  retriever: {
    label: "Vector Database",
    description: "Stocke et recherche les vecteurs d'embeddings",
    icon: <Database size={20} />,
    order: 3,
  },
  chunker: {
    label: "Chunking",
    description: "Decoupe les documents en segments pour l'indexation",
    icon: <Scissors size={20} />,
    order: 4,
  },
  connector: {
    label: "Connecteurs",
    description: "Import de donnees depuis des sources externes",
    icon: <Link2 size={20} />,
    order: 5,
  },
  extractor: {
    label: "Extracteurs",
    description: "Extrait le texte des fichiers (PDF, DOCX, etc.)",
    icon: <FileText size={20} />,
    order: 6,
  },
  guardrail: {
    label: "Guardrails",
    description: "Valide les reponses pour eviter les hallucinations",
    icon: <Shield size={20} />,
    order: 7,
  },
  reranker: {
    label: "Reranking",
    description: "Reordonne les resultats pour ameliorer la pertinence",
    icon: <Repeat size={20} />,
    order: 8,
  },
  transformer: {
    label: "Transformers",
    description: "Transforme les documents avant l'indexation",
    icon: <Search size={20} />,
    order: 9,
  },
  template: {
    label: "Templates",
    description: "Widgets et interfaces embarquables",
    icon: <Layout size={20} />,
    order: 10,
  },
};

function getCategoryInfo(type: string) {
  return (
    CATEGORIES[type] || {
      label: type.charAt(0).toUpperCase() + type.slice(1) + "s",
      description: "",
      icon: <Puzzle size={20} />,
      order: 99,
    }
  );
}

export default function PluginsPage() {
  const [plugins, setPlugins] = useState<PluginInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showInstall, setShowInstall] = useState(false);
  const [installSource, setInstallSource] = useState("");
  const [installing, setInstalling] = useState(false);
  const [configPlugin, setConfigPlugin] = useState<PluginInfo | null>(null);
  const [activeCategory, setActiveCategory] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    try {
      const data = await getPlugins();
      setPlugins(data);
    } catch {
      setError("Failed to load plugins");
      setPlugins([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  // Group by type and sort by category order
  const grouped = useMemo(() => {
    const groups: Record<string, PluginInfo[]> = {};
    for (const plugin of plugins) {
      const key = plugin.type;
      if (!groups[key]) groups[key] = [];
      groups[key].push(plugin);
    }
    return Object.entries(groups).sort(
      ([a], [b]) => getCategoryInfo(a).order - getCategoryInfo(b).order
    );
  }, [plugins]);

  // Stack summary: count active plugins per category
  const stackSummary = useMemo(() => {
    const summary: Record<string, { total: number; active: number }> = {};
    for (const plugin of plugins) {
      if (!summary[plugin.type]) summary[plugin.type] = { total: 0, active: 0 };
      summary[plugin.type].total++;
      if (plugin.status === "enabled") summary[plugin.type].active++;
    }
    return summary;
  }, [plugins]);

  const handleToggle = async (plugin: PluginInfo) => {
    try {
      if (plugin.status === "enabled") {
        await disablePlugin(plugin.name);
      } else {
        await enablePlugin(plugin.name);
      }
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to toggle plugin");
    }
  };

  const handleInstall = async () => {
    if (!installSource.trim()) return;
    setInstalling(true);
    try {
      await installPlugin(installSource.trim());
      setShowInstall(false);
      setInstallSource("");
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to install plugin");
    } finally {
      setInstalling(false);
    }
  };

  const handleUninstall = async (name: string) => {
    try {
      await uninstallPlugin(name);
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to uninstall plugin");
    }
  };

  const handleSaveConfig = async (config: Record<string, any>) => {
    if (!configPlugin) return;
    await configurePlugin(configPlugin.name, config);
    load();
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-48 bg-surface-2 rounded animate-pulse" />
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="h-24 bg-surface-2 rounded-xl animate-pulse" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">Plugins</h1>
          <p className="text-sm text-text-secondary mt-1">
            Configurez votre stack RAG : activez les composants dont vous avez besoin
          </p>
        </div>
        <Button
          icon={<Download size={16} />}
          onClick={() => {
            setInstallSource("");
            setShowInstall(true);
          }}
        >
          Installer
        </Button>
      </div>

      {error && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 dark:bg-amber-950 dark:border-amber-800 p-3 text-sm text-amber-700 dark:text-amber-300">
          {error}
        </div>
      )}

      {/* Stack Overview - category cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
        {grouped.map(([type]) => {
          const cat = getCategoryInfo(type);
          const stats = stackSummary[type] || { total: 0, active: 0 };
          const isSelected = activeCategory === type;

          return (
            <button
              key={type}
              onClick={() => setActiveCategory(isSelected ? null : type)}
              className={`text-left p-4 rounded-xl border-2 transition-all duration-200 ${
                isSelected
                  ? "border-brand-600 bg-brand-50 dark:bg-brand-950 shadow-sm"
                  : "border-border hover:border-brand-300 hover:shadow-sm bg-surface-0"
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <div
                  className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                    isSelected
                      ? "bg-brand-600 text-white"
                      : "bg-brand-50 dark:bg-brand-950 text-brand-600 dark:text-brand-400"
                  }`}
                >
                  {cat.icon}
                </div>
                {stats.active > 0 && (
                  <span className="flex items-center gap-1 text-xs font-medium text-green-600 dark:text-green-400">
                    <Check size={12} /> {stats.active}
                  </span>
                )}
              </div>
              <h3 className="text-sm font-semibold text-text-primary">{cat.label}</h3>
              <p className="text-xs text-text-muted mt-0.5">
                {stats.total} plugin{stats.total !== 1 ? "s" : ""}
              </p>
            </button>
          );
        })}
      </div>

      {/* Plugin list for selected category (or all) */}
      {grouped
        .filter(([type]) => !activeCategory || type === activeCategory)
        .map(([type, items]) => {
          const cat = getCategoryInfo(type);
          return (
            <div key={type} className="space-y-3">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-brand-50 dark:bg-brand-950 flex items-center justify-center text-brand-600 dark:text-brand-400">
                  {cat.icon}
                </div>
                <div>
                  <h2 className="text-lg font-semibold text-text-primary">{cat.label}</h2>
                  <p className="text-xs text-text-muted">{cat.description}</p>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {items.map((plugin) => (
                  <Card key={plugin.name} className="hover:shadow-md transition-shadow group">
                    <CardContent className="p-5">
                      <div className="flex items-start justify-between">
                        <div>
                          <h3 className="font-semibold text-text-primary">{plugin.name}</h3>
                          {plugin.description && (
                            <p className="mt-1 text-sm text-text-secondary line-clamp-2">
                              {plugin.description}
                            </p>
                          )}
                        </div>
                        <Toggle
                          checked={plugin.status === "enabled"}
                          onChange={() => handleToggle(plugin)}
                        />
                      </div>

                      <div className="flex flex-wrap items-center gap-2 mt-3">
                        <span className="text-xs text-text-muted">v{plugin.version}</span>
                        {plugin.bundled && <Badge variant="neutral">bundled</Badge>}
                        {plugin.status === "enabled" && (
                          <Badge variant="success" dot>active</Badge>
                        )}
                        {plugin.status === "error" && (
                          <Badge variant="error" dot>error</Badge>
                        )}
                      </div>

                      <div className="flex items-center gap-1 mt-3 pt-3 border-t border-border">
                        {Object.keys(plugin.config_schema).length > 0 && (
                          <button
                            onClick={() => setConfigPlugin(plugin)}
                            className="flex items-center gap-1.5 text-xs text-text-muted hover:text-text-primary hover:bg-surface-2 px-2 py-1.5 rounded-lg transition-colors"
                          >
                            <Settings2 size={13} /> Configurer
                          </button>
                        )}
                        {!plugin.bundled && (
                          <button
                            onClick={() => handleUninstall(plugin.name)}
                            className="flex items-center gap-1.5 text-xs text-text-muted hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-950 px-2 py-1.5 rounded-lg transition-colors ml-auto"
                          >
                            <Trash2 size={13} /> Supprimer
                          </button>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          );
        })}

      {plugins.length === 0 && (
        <div className="text-center py-16">
          <Puzzle size={48} className="mx-auto text-text-muted opacity-50 mb-4" />
          <h3 className="text-lg font-medium text-text-primary">Aucun plugin installe</h3>
          <p className="text-sm text-text-muted mt-1">
            Installez des plugins pour construire votre pipeline RAG
          </p>
          <Button
            className="mt-4"
            icon={<Download size={16} />}
            onClick={() => setShowInstall(true)}
          >
            Installer un plugin
          </Button>
        </div>
      )}

      {/* Install Modal */}
      <Modal
        open={showInstall}
        onClose={() => {
          setShowInstall(false);
          setInstallSource("");
        }}
        title="Installer un Plugin"
        description="Depuis un chemin local, une URL Git, ou un package PyPI"
      >
        <div className="space-y-4">
          <Input
            label="Source"
            placeholder="e.g., git+https://github.com/org/plugin.git"
            value={installSource}
            onChange={(e) => setInstallSource(e.target.value)}
          />
          <div className="flex justify-end gap-3 pt-2">
            <Button variant="outline" onClick={() => setShowInstall(false)}>
              Annuler
            </Button>
            <Button
              onClick={handleInstall}
              disabled={!installSource.trim()}
              loading={installing}
            >
              Installer
            </Button>
          </div>
        </div>
      </Modal>

      {/* Config Modal */}
      <Modal
        open={configPlugin !== null}
        onClose={() => setConfigPlugin(null)}
        title={`Configurer ${configPlugin?.name ?? ""}`}
        description="Modifiez la configuration du plugin"
      >
        {configPlugin && (
          <PluginConfigPanel
            configSchema={configPlugin.config_schema}
            currentConfig={configPlugin.config}
            onSave={handleSaveConfig}
          />
        )}
      </Modal>
    </div>
  );
}
