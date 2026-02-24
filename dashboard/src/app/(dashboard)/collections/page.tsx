"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  FolderOpen,
  Plus,
  FileText,
  Clock,
  Pencil,
  Trash2,
  MoreVertical,
  GitCompareArrows,
} from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Modal } from "@/components/ui/modal";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  getCollections,
  createCollection,
  updateCollection,
  deleteCollection,
  type Collection,
} from "@/lib/api";
import { formatRelativeTime } from "@/lib/utils";

export default function CollectionsPage() {
  const [collections, setCollections] = useState<Collection[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [formData, setFormData] = useState({ name: "", description: "" });
  const [saving, setSaving] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const data = await getCollections();
      setCollections(data);
    } catch {
      setError("Failed to load collections");
      setCollections([]);
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
      await createCollection({
        name: formData.name,
        description: formData.description,
      });
      setShowCreate(false);
      setFormData({ name: "", description: "" });
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create collection");
    } finally {
      setSaving(false);
    }
  };

  const handleUpdate = async () => {
    if (!editingId || !formData.name.trim()) return;
    setSaving(true);
    try {
      await updateCollection(editingId, {
        name: formData.name,
        description: formData.description,
      });
      setEditingId(null);
      setFormData({ name: "", description: "" });
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update collection");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await deleteCollection(id);
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete collection");
    }
  };

  const openEdit = (col: Collection) => {
    setFormData({ name: col.name, description: col.description || "" });
    setEditingId(col.id);
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
          <h1 className="text-2xl font-bold text-text-primary">Collections</h1>
          <p className="text-sm text-text-secondary mt-1">
            Organize documents into collections
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Link href="/collections/compare">
            <Button variant="outline" icon={<GitCompareArrows size={16} />}>
              Comparer
            </Button>
          </Link>
          <Button
            icon={<Plus size={16} />}
            onClick={() => {
              setFormData({ name: "", description: "" });
              setShowCreate(true);
            }}
          >
            New Collection
          </Button>
        </div>
      </div>

      {error && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 dark:bg-amber-950 dark:border-amber-800 p-3 text-sm text-amber-700 dark:text-amber-300">
          {error}
        </div>
      )}

      {collections.length === 0 ? (
        <div className="text-center py-16">
          <FolderOpen size={48} className="mx-auto text-text-muted opacity-50 mb-4" />
          <h3 className="text-lg font-medium text-text-primary">No collections yet</h3>
          <p className="text-sm text-text-muted mt-1">
            Create a collection to organize your documents
          </p>
          <Button
            className="mt-4"
            icon={<Plus size={16} />}
            onClick={() => setShowCreate(true)}
          >
            Create First Collection
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {collections.map((col) => (
            <Card key={col.id} className="hover:shadow-md transition-shadow group">
              <CardContent className="p-5">
                <div className="flex items-start justify-between">
                  <div className="w-10 h-10 rounded-lg bg-brand-50 dark:bg-brand-950 flex items-center justify-center text-brand-600 dark:text-brand-400">
                    <FolderOpen size={20} />
                  </div>
                  <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button
                      onClick={() => openEdit(col)}
                      className="p-1.5 rounded-lg text-text-muted hover:text-text-primary hover:bg-surface-2 transition-colors"
                    >
                      <Pencil size={14} />
                    </button>
                    <button
                      onClick={() => handleDelete(col.id)}
                      className="p-1.5 rounded-lg text-text-muted hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-950 transition-colors"
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                </div>
                <h3 className="mt-3 font-semibold text-text-primary">
                  {col.name}
                </h3>
                {col.description && (
                  <p className="mt-1 text-sm text-text-secondary line-clamp-2">
                    {col.description}
                  </p>
                )}
                <div className="flex items-center gap-4 mt-4 pt-3 border-t border-border text-xs text-text-muted">
                  <span className="flex items-center gap-1">
                    <FileText size={12} />
                    {col.documents_count} documents
                  </span>
                  <span className="flex items-center gap-1">
                    <Clock size={12} />
                    {formatRelativeTime(col.created_at)}
                  </span>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <Modal
        open={showCreate || editingId !== null}
        onClose={() => {
          setShowCreate(false);
          setEditingId(null);
          setFormData({ name: "", description: "" });
        }}
        title={editingId ? "Edit Collection" : "New Collection"}
        description={
          editingId
            ? "Update collection details"
            : "Create a new document collection"
        }
      >
        <div className="space-y-4">
          <Input
            label="Name"
            placeholder="e.g., Product Documentation"
            value={formData.name}
            onChange={(e) =>
              setFormData({ ...formData, name: e.target.value })
            }
          />
          <Textarea
            label="Description"
            placeholder="What documents belong in this collection?"
            value={formData.description}
            onChange={(e) =>
              setFormData({ ...formData, description: e.target.value })
            }
            rows={3}
          />
          <div className="flex justify-end gap-3 pt-2">
            <Button
              variant="outline"
              onClick={() => {
                setShowCreate(false);
                setEditingId(null);
              }}
            >
              Cancel
            </Button>
            <Button
              onClick={editingId ? handleUpdate : handleCreate}
              disabled={!formData.name.trim()}
              loading={saving}
            >
              {editingId ? "Update" : "Create"}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
