"use client";

import React, { useState, useEffect } from "react";
import { Settings, Save, RotateCcw, X, Download, Upload, FileJson } from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Select } from "@/components/ui/select";
import { Slider } from "@/components/ui/slider";
import { Toggle } from "@/components/ui/toggle";
import { Badge } from "@/components/ui/badge";
import { getSettings, updateSettings, exportConfig, importConfig, type PlatformSettings } from "@/lib/api";

export default function SettingsPage() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [platform, setPlatform] = useState({
    name: "",
    language: "en",
    default_persona: "",
  });

  const [retrieval, setRetrieval] = useState({
    strategy: "hybrid",
    vector_weight: 0.7,
    top_k: 5,
    reranking: true,
  });

  const [generation, setGeneration] = useState({
    provider: "openai",
    model: "gpt-4o",
    temperature: 0.1,
    max_tokens: 1024,
  });

  const [webhook, setWebhook] = useState({
    url: "",
    events: [] as string[],
    secret: "",
  });

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const data = await getSettings();
        setPlatform({
          name: data.platform_name || "Retrieva",
          language: data.default_language || "en",
          default_persona: data.default_persona || "",
        });
        setRetrieval({
          strategy: data.retrieval_strategy || "hybrid",
          vector_weight: data.vector_weight ?? 0.7,
          top_k: data.default_top_k ?? 5,
          reranking: data.reranking ?? true,
        });
        setGeneration({
          provider: data.generation_provider || "openai",
          model: data.generation_model || "gpt-4o",
          temperature: data.temperature ?? 0.1,
          max_tokens: data.max_tokens ?? 1024,
        });
        setWebhook({
          url: data.webhook_url || "",
          events: data.webhook_events || [],
          secret: data.webhook_secret || "",
        });
      } catch {
        setError("Failed to load settings. Using defaults. Backend may be unavailable.");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    try {
      await updateSettings({
        platform_name: platform.name,
        default_language: platform.language,
        default_persona: platform.default_persona,
        retrieval_strategy: retrieval.strategy,
        vector_weight: retrieval.vector_weight,
        default_top_k: retrieval.top_k,
        reranking: retrieval.reranking,
        generation_provider: generation.provider,
        generation_model: generation.model,
        temperature: generation.temperature,
        max_tokens: generation.max_tokens,
        webhook_url: webhook.url,
        webhook_secret: webhook.secret,
        webhook_events: webhook.events,
      });
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save settings");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-8 w-48 bg-surface-2 rounded" />
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-64 bg-surface-2 rounded-xl" />
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">Settings</h1>
          <p className="text-sm text-text-secondary mt-1">
            Configure platform behavior and defaults
          </p>
        </div>
        <div className="flex items-center gap-2">
          {saved && (
            <Badge variant="success" dot>
              Settings saved
            </Badge>
          )}
          <Button
            icon={<Save size={16} />}
            onClick={handleSave}
            loading={saving}
          >
            Save Changes
          </Button>
        </div>
      </div>

      {error && (
        <div className="flex items-center justify-between rounded-lg border border-amber-200 bg-amber-50 dark:bg-amber-950 dark:border-amber-800 p-3 text-sm text-amber-700 dark:text-amber-300">
          <span>{error}</span>
          <button onClick={() => setError(null)}>
            <X size={16} />
          </button>
        </div>
      )}

      {/* Platform Settings */}
      <Card>
        <CardHeader>
          <CardTitle>Platform</CardTitle>
          <CardDescription>
            General platform configuration
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between p-3 rounded-lg bg-surface-1 mb-4">
            <div>
              <span className="text-sm font-medium text-text-primary">Plan actuel</span>
              <span className="text-xs text-text-muted ml-2">Gratuit</span>
            </div>
            <Badge variant="info">Free</Badge>
          </div>
          <Input
            label="Platform Name"
            value={platform.name}
            onChange={(e) =>
              setPlatform({ ...platform, name: e.target.value })
            }
          />
          <Select
            label="Default Language"
            value={platform.language}
            onChange={(e) =>
              setPlatform({ ...platform, language: e.target.value })
            }
            options={[
              { value: "en", label: "English" },
              { value: "fr", label: "French" },
              { value: "de", label: "German" },
              { value: "es", label: "Spanish" },
              { value: "ar", label: "Arabic" },
              { value: "zh", label: "Chinese" },
              { value: "ja", label: "Japanese" },
            ]}
          />
          <Textarea
            label="Default Persona / System Prompt"
            value={platform.default_persona}
            onChange={(e) =>
              setPlatform({ ...platform, default_persona: e.target.value })
            }
            rows={4}
          />
        </CardContent>
      </Card>

      {/* Retrieval Settings */}
      <Card>
        <CardHeader>
          <CardTitle>Retrieval</CardTitle>
          <CardDescription>
            Configure how documents are retrieved and ranked
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Select
            label="Search Strategy"
            value={retrieval.strategy}
            onChange={(e) =>
              setRetrieval({ ...retrieval, strategy: e.target.value })
            }
            options={[
              { value: "vector", label: "Vector (Semantic)" },
              { value: "keyword", label: "Keyword (BM25)" },
              { value: "hybrid", label: "Hybrid (Vector + Keyword)" },
            ]}
          />
          {retrieval.strategy === "hybrid" && (
            <Slider
              label="Vector Weight"
              value={retrieval.vector_weight}
              onChange={(v) =>
                setRetrieval({ ...retrieval, vector_weight: v })
              }
              min={0}
              max={1}
              step={0.05}
            />
          )}
          <Slider
            label="Default Top K"
            value={retrieval.top_k}
            onChange={(v) => setRetrieval({ ...retrieval, top_k: v })}
            min={1}
            max={20}
            step={1}
          />
          <Toggle
            label="Reranking"
            description="Apply a cross-encoder reranker to improve relevance"
            checked={retrieval.reranking}
            onChange={(v) => setRetrieval({ ...retrieval, reranking: v })}
          />
        </CardContent>
      </Card>

      {/* Generation Settings */}
      <Card>
        <CardHeader>
          <CardTitle>Generation</CardTitle>
          <CardDescription>
            Configure the language model for answer generation
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Select
            label="Provider"
            value={generation.provider}
            onChange={(e) =>
              setGeneration({ ...generation, provider: e.target.value })
            }
            options={[
              { value: "openai", label: "OpenAI" },
              { value: "anthropic", label: "Anthropic" },
              { value: "cohere", label: "Cohere" },
              { value: "local", label: "Local (Ollama)" },
            ]}
          />
          <Input
            label="Model"
            value={generation.model}
            onChange={(e) =>
              setGeneration({ ...generation, model: e.target.value })
            }
            placeholder="e.g., gpt-4o, claude-3-sonnet"
          />
          <Slider
            label="Temperature"
            value={generation.temperature}
            onChange={(v) =>
              setGeneration({ ...generation, temperature: v })
            }
            min={0}
            max={2}
            step={0.05}
          />
          <Slider
            label="Max Tokens"
            value={generation.max_tokens}
            onChange={(v) =>
              setGeneration({ ...generation, max_tokens: v })
            }
            min={128}
            max={4096}
            step={128}
          />
        </CardContent>
      </Card>

      {/* Webhook Settings */}
      <Card>
        <CardHeader>
          <CardTitle>Webhooks</CardTitle>
          <CardDescription>
            Configure webhook notifications for platform events
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Input
            label="Webhook URL"
            type="url"
            placeholder="https://example.com/webhook"
            value={webhook.url}
            onChange={(e) =>
              setWebhook({ ...webhook, url: e.target.value })
            }
          />
          <Input
            label="Webhook Secret"
            type="password"
            placeholder="Used to sign webhook payloads"
            value={webhook.secret}
            onChange={(e) =>
              setWebhook({ ...webhook, secret: e.target.value })
            }
          />
          <div className="space-y-2">
            <label className="text-sm font-medium text-text-primary">
              Events
            </label>
            <div className="space-y-2">
              {[
                { id: "document.indexed", label: "Document Indexed" },
                { id: "document.deleted", label: "Document Deleted" },
                { id: "query.completed", label: "Query Completed" },
                { id: "query.error", label: "Query Error" },
                { id: "collection.created", label: "Collection Created" },
              ].map((event) => (
                <Toggle
                  key={event.id}
                  label={event.label}
                  description={event.id}
                  checked={webhook.events.includes(event.id)}
                  onChange={(checked) => {
                    setWebhook({
                      ...webhook,
                      events: checked
                        ? [...webhook.events, event.id]
                        : webhook.events.filter((e) => e !== event.id),
                    });
                  }}
                />
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Import / Export */}
      <Card>
        <CardHeader>
          <CardTitle>Import / Export</CardTitle>
          <CardDescription>
            Sauvegardez ou restaurez votre configuration complete
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="border border-border rounded-xl p-5 space-y-3">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-brand-50 dark:bg-brand-950 flex items-center justify-center">
                  <Download size={20} className="text-brand-600" />
                </div>
                <div>
                  <h4 className="text-sm font-semibold text-text-primary">Exporter</h4>
                  <p className="text-xs text-text-muted">Telechargez la configuration complete</p>
                </div>
              </div>
              <p className="text-xs text-text-secondary">
                Inclut: parametres, collections, widgets, webhooks
              </p>
              <Button
                variant="outline"
                size="sm"
                icon={<Download size={14} />}
                onClick={async () => {
                  try {
                    const data = await exportConfig();
                    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement("a");
                    a.href = url;
                    a.download = `retrieva-config-${new Date().toISOString().split("T")[0]}.json`;
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                    URL.revokeObjectURL(url);
                  } catch (err) {
                    setError(err instanceof Error ? err.message : "Export failed");
                  }
                }}
              >
                Telecharger .json
              </Button>
            </div>

            <div className="border border-border rounded-xl p-5 space-y-3">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-amber-50 dark:bg-amber-950 flex items-center justify-center">
                  <Upload size={20} className="text-amber-600" />
                </div>
                <div>
                  <h4 className="text-sm font-semibold text-text-primary">Importer</h4>
                  <p className="text-xs text-text-muted">Restaurez depuis un fichier</p>
                </div>
              </div>
              <p className="text-xs text-text-secondary">
                Les elements existants ne seront pas ecrases
              </p>
              <div className="relative">
                <Button
                  variant="outline"
                  size="sm"
                  icon={<Upload size={14} />}
                >
                  Choisir un fichier .json
                </Button>
                <input
                  type="file"
                  accept=".json"
                  className="absolute inset-0 opacity-0 cursor-pointer"
                  onChange={async (e) => {
                    const file = e.target.files?.[0];
                    if (!file) return;
                    try {
                      const text = await file.text();
                      const data = JSON.parse(text);
                      const result = await importConfig(data, true);
                      setSaved(true);
                      setTimeout(() => setSaved(false), 3000);
                      setError(null);
                    } catch (err) {
                      setError(err instanceof Error ? err.message : "Import failed — invalid JSON file");
                    }
                  }}
                />
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="flex justify-end pb-8">
        <Button
          icon={<Save size={16} />}
          onClick={handleSave}
          loading={saving}
        >
          Save All Changes
        </Button>
      </div>
    </div>
  );
}
