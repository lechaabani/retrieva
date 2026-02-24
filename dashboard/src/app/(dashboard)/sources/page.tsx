"use client";

import React, { useState, useEffect } from "react";
import {
  Database,
  Plus,
  RefreshCw,
  Pencil,
  Trash2,
  Globe,
  FileUp,
  Cloud,
  Server,
  CheckCircle2,
  XCircle,
  Clock,
} from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Modal } from "@/components/ui/modal";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { formatRelativeTime } from "@/lib/utils";
import {
  getConnectors,
  createConnector,
  deleteConnector,
  syncConnector,
  type Connector,
} from "@/lib/api";

const typeIcons: Record<string, React.ReactNode> = {
  file_upload: <FileUp size={20} />,
  web_crawler: <Globe size={20} />,
  s3: <Cloud size={20} />,
  database: <Database size={20} />,
  api: <Server size={20} />,
};

const typeLabels: Record<string, string> = {
  file_upload: "File Upload",
  web_crawler: "Web Crawler",
  s3: "Amazon S3",
  database: "Database",
  api: "REST API",
};

const statusConfig: Record<string, { variant: "success" | "warning" | "error" | "neutral"; label: string }> = {
  connected: { variant: "success", label: "Connected" },
  syncing: { variant: "warning", label: "Syncing" },
  error: { variant: "error", label: "Error" },
  disconnected: { variant: "neutral", label: "Disconnected" },
};

export default function SourcesPage() {
  const [sources, setSources] = useState<Connector[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [newSource, setNewSource] = useState({ name: "", type: "file_upload" });
  const [syncing, setSyncing] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getConnectors();
      setSources(data);
    } catch {
      setError("Failed to load sources. The connectors API may be unavailable.");
      setSources([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleSync = async (id: string) => {
    setSyncing(id);
    setSources((prev) =>
      prev.map((s) => (s.id === id ? { ...s, status: "syncing" as const } : s))
    );
    try {
      await syncConnector(id);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sync failed");
      setSources((prev) =>
        prev.map((s) => (s.id === id ? { ...s, status: "error" as const } : s))
      );
    } finally {
      setSyncing(null);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await deleteConnector(id);
      setSources((prev) => prev.filter((s) => s.id !== id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Delete failed");
    }
  };

  const handleCreate = async () => {
    if (!newSource.name.trim()) return;
    setCreating(true);
    try {
      await createConnector({
        name: newSource.name,
        type: newSource.type,
      });
      setNewSource({ name: "", type: "file_upload" });
      setShowCreate(false);
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create source");
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">Sources</h1>
          <p className="text-sm text-text-secondary mt-1">
            Manage data source connectors
          </p>
        </div>
        <Button icon={<Plus size={16} />} onClick={() => setShowCreate(true)}>
          Add Source
        </Button>
      </div>

      {error && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 dark:bg-amber-950 dark:border-amber-800 p-3 text-sm text-amber-700 dark:text-amber-300">
          {error}
        </div>
      )}

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-48 bg-surface-2 rounded-xl animate-pulse" />
          ))}
        </div>
      ) : sources.length === 0 ? (
        <div className="text-center py-16">
          <Database size={48} className="mx-auto text-text-muted opacity-50 mb-4" />
          <h3 className="text-lg font-medium text-text-primary">No sources configured</h3>
          <p className="text-sm text-text-muted mt-1">
            Add a data source to start indexing documents
          </p>
          <Button className="mt-4" icon={<Plus size={16} />} onClick={() => setShowCreate(true)}>
            Add First Source
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {sources.map((source) => {
            const status = statusConfig[source.status] || statusConfig.disconnected;
            return (
              <Card key={source.id} className="hover:shadow-md transition-shadow">
                <CardContent className="p-5">
                  <div className="flex items-start gap-4">
                    <div className="w-10 h-10 rounded-lg bg-brand-50 dark:bg-brand-950 flex items-center justify-center text-brand-600 dark:text-brand-400 shrink-0">
                      {typeIcons[source.type] || <Database size={20} />}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between gap-2">
                        <h3 className="font-semibold text-text-primary truncate">
                          {source.name}
                        </h3>
                        <Badge variant={status.variant} dot>
                          {status.label}
                        </Badge>
                      </div>
                      <p className="text-sm text-text-muted mt-0.5">
                        {typeLabels[source.type] || source.type}
                      </p>
                      <div className="flex items-center gap-4 mt-3 text-xs text-text-muted">
                        <span className="flex items-center gap-1">
                          <FileUp size={12} />
                          {source.document_count} docs
                        </span>
                        {source.last_sync && (
                          <span className="flex items-center gap-1">
                            <Clock size={12} />
                            Synced {formatRelativeTime(source.last_sync)}
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-2 mt-3 pt-3 border-t border-border">
                        <Button
                          variant="ghost"
                          size="sm"
                          icon={<RefreshCw size={14} className={syncing === source.id ? "animate-spin" : ""} />}
                          onClick={() => handleSync(source.id)}
                          disabled={syncing === source.id}
                        >
                          Sync
                        </Button>
                        <Button variant="ghost" size="sm" icon={<Pencil size={14} />}>
                          Edit
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          icon={<Trash2 size={14} />}
                          className="text-red-500 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-950"
                          onClick={() => handleDelete(source.id)}
                        >
                          Delete
                        </Button>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      <Modal
        open={showCreate}
        onClose={() => setShowCreate(false)}
        title="Add Data Source"
        description="Connect a new data source to ingest documents"
      >
        <div className="space-y-4">
          <Input
            label="Source Name"
            placeholder="e.g., Product Documentation"
            value={newSource.name}
            onChange={(e) => setNewSource({ ...newSource, name: e.target.value })}
          />
          <Select
            label="Connector Type"
            value={newSource.type}
            onChange={(e) => setNewSource({ ...newSource, type: e.target.value })}
            options={Object.entries(typeLabels).map(([value, label]) => ({
              value,
              label,
            }))}
          />
          <div className="flex justify-end gap-3 pt-2">
            <Button variant="outline" onClick={() => setShowCreate(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleCreate}
              disabled={!newSource.name.trim()}
              loading={creating}
            >
              Create Source
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
