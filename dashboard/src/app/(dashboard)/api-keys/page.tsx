"use client";

import React, { useState, useEffect } from "react";
import {
  Key,
  Plus,
  Trash2,
  Copy,
  Check,
  Eye,
  EyeOff,
  AlertTriangle,
  Clock,
  Shield,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Modal } from "@/components/ui/modal";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Toggle } from "@/components/ui/toggle";
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from "@/components/ui/table";
import { getApiKeys, createApiKey, revokeApiKey, type ApiKey } from "@/lib/api";
import { formatDate, maskKey } from "@/lib/utils";

export default function ApiKeysPage() {
  const [keys, setKeys] = useState<ApiKey[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [creating, setCreating] = useState(false);
  const [newKeyRevealed, setNewKeyRevealed] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [formData, setFormData] = useState({
    name: "",
    permissions: { read: true, write: false, admin: false },
    expiresInDays: "90",
  });

  const load = async () => {
    setLoading(true);
    try {
      const data = await getApiKeys();
      setKeys(data);
    } catch {
      setError("Failed to load API keys");
      setKeys([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleCreate = async () => {
    if (!formData.name.trim()) return;
    setCreating(true);
    try {
      const permissions: string[] = [];
      if (formData.permissions.read) permissions.push("read");
      if (formData.permissions.write) permissions.push("write");
      if (formData.permissions.admin) permissions.push("admin");

      const result = await createApiKey({
        name: formData.name,
        permissions,
        expires_in_days: formData.expiresInDays
          ? parseInt(formData.expiresInDays)
          : undefined,
      });

      if (result.raw_key) {
        setNewKeyRevealed(result.raw_key);
      }

      setFormData({
        name: "",
        permissions: { read: true, write: false, admin: false },
        expiresInDays: "90",
      });
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create API key");
    } finally {
      setCreating(false);
    }
  };

  const handleRevoke = async (id: string) => {
    try {
      await revokeApiKey(id);
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to revoke key");
    }
  };

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">API Keys</h1>
          <p className="text-sm text-text-secondary mt-1">
            Manage API keys for programmatic access
          </p>
        </div>
        <Button icon={<Plus size={16} />} onClick={() => setShowCreate(true)}>
          Generate Key
        </Button>
      </div>

      {error && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 dark:bg-amber-950 dark:border-amber-800 p-3 text-sm text-amber-700 dark:text-amber-300">
          {error}
        </div>
      )}

      {newKeyRevealed && (
        <div className="rounded-lg border border-emerald-200 bg-emerald-50 dark:bg-emerald-950 dark:border-emerald-800 p-4">
          <div className="flex items-start gap-3">
            <AlertTriangle size={18} className="text-emerald-600 shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="text-sm font-medium text-emerald-800 dark:text-emerald-200">
                API Key Generated
              </p>
              <p className="text-xs text-emerald-700 dark:text-emerald-300 mt-1">
                Copy this key now. You will not be able to see it again.
              </p>
              <div className="flex items-center gap-2 mt-3">
                <code className="flex-1 bg-white dark:bg-surface-1 border border-emerald-200 dark:border-emerald-700 rounded-lg px-3 py-2 text-sm font-mono text-text-primary break-all">
                  {newKeyRevealed}
                </code>
                <Button
                  variant="outline"
                  size="sm"
                  icon={copied ? <Check size={14} /> : <Copy size={14} />}
                  onClick={() => handleCopy(newKeyRevealed)}
                >
                  {copied ? "Copied" : "Copy"}
                </Button>
              </div>
            </div>
            <button
              onClick={() => setNewKeyRevealed(null)}
              className="text-emerald-600 hover:text-emerald-800 text-sm"
            >
              Dismiss
            </button>
          </div>
        </div>
      )}

      <div className="rounded-xl border border-border bg-surface-0 shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-text-muted">
            <div className="animate-spin h-6 w-6 border-2 border-brand-600 border-t-transparent rounded-full mx-auto mb-3" />
            Loading API keys...
          </div>
        ) : keys.length === 0 ? (
          <div className="p-12 text-center">
            <Key size={48} className="mx-auto text-text-muted opacity-50 mb-4" />
            <h3 className="text-lg font-medium text-text-primary">No API keys</h3>
            <p className="text-sm text-text-muted mt-1">
              Generate an API key to access the platform programmatically
            </p>
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Key</TableHead>
                <TableHead>Permissions</TableHead>
                <TableHead>Last Used</TableHead>
                <TableHead>Expires</TableHead>
                <TableHead className="w-10" />
              </TableRow>
            </TableHeader>
            <TableBody>
              {keys.map((key) => (
                <TableRow key={key.id}>
                  <TableCell className="font-medium">{key.name}</TableCell>
                  <TableCell>
                    <code className="text-xs font-mono text-text-secondary bg-surface-2 px-2 py-0.5 rounded">
                      {key.key_prefix}...
                    </code>
                  </TableCell>
                  <TableCell>
                    <div className="flex gap-1">
                      {(Array.isArray(key.permissions)
                        ? key.permissions
                        : Object.keys(key.permissions)
                      ).map((p) => (
                        <Badge
                          key={p}
                          variant={
                            p === "admin"
                              ? "warning"
                              : p === "write"
                              ? "info"
                              : "neutral"
                          }
                        >
                          {p}
                        </Badge>
                      ))}
                    </div>
                  </TableCell>
                  <TableCell className="text-text-secondary text-sm">
                    {key.last_used_at
                      ? formatDate(key.last_used_at)
                      : "Never"}
                  </TableCell>
                  <TableCell className="text-text-secondary text-sm">
                    {key.expires_at
                      ? formatDate(key.expires_at)
                      : "Never"}
                  </TableCell>
                  <TableCell>
                    <button
                      onClick={() => handleRevoke(key.id)}
                      className="p-1.5 rounded-lg text-text-muted hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-950 transition-colors"
                      title="Revoke key"
                    >
                      <Trash2 size={14} />
                    </button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </div>

      <Modal
        open={showCreate}
        onClose={() => setShowCreate(false)}
        title="Generate API Key"
        description="Create a new API key for programmatic access"
      >
        <div className="space-y-4">
          <Input
            label="Key Name"
            placeholder="e.g., Production Server"
            value={formData.name}
            onChange={(e) =>
              setFormData({ ...formData, name: e.target.value })
            }
          />
          <div className="space-y-2">
            <label className="text-sm font-medium text-text-primary">
              Permissions
            </label>
            <div className="space-y-2">
              <Toggle
                label="Read"
                description="Query and search documents"
                checked={formData.permissions.read}
                onChange={(v) =>
                  setFormData({
                    ...formData,
                    permissions: { ...formData.permissions, read: v },
                  })
                }
              />
              <Toggle
                label="Write"
                description="Ingest and manage documents"
                checked={formData.permissions.write}
                onChange={(v) =>
                  setFormData({
                    ...formData,
                    permissions: { ...formData.permissions, write: v },
                  })
                }
              />
              <Toggle
                label="Admin"
                description="Full administrative access"
                checked={formData.permissions.admin}
                onChange={(v) =>
                  setFormData({
                    ...formData,
                    permissions: { ...formData.permissions, admin: v },
                  })
                }
              />
            </div>
          </div>
          <Select
            label="Expires In"
            value={formData.expiresInDays}
            onChange={(e) =>
              setFormData({ ...formData, expiresInDays: e.target.value })
            }
            options={[
              { value: "30", label: "30 days" },
              { value: "90", label: "90 days" },
              { value: "180", label: "180 days" },
              { value: "365", label: "1 year" },
              { value: "", label: "Never" },
            ]}
          />
          <div className="flex justify-end gap-3 pt-2">
            <Button variant="outline" onClick={() => setShowCreate(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleCreate}
              loading={creating}
              disabled={!formData.name.trim()}
            >
              Generate Key
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
