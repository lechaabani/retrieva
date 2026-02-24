"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import {
  FileText,
  Search,
  Trash2,
  Upload,
  ChevronLeft,
  ChevronRight,
  Filter,
  X,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Select } from "@/components/ui/select";
import { Modal } from "@/components/ui/modal";
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from "@/components/ui/table";
import {
  getDocuments,
  getCollections,
  uploadDocument,
  deleteDocument,
  type Document,
  type Collection,
} from "@/lib/api";
import { formatDate, truncate } from "@/lib/utils";

const statusBadge: Record<string, { variant: "success" | "warning" | "error" | "info" | "neutral"; label: string }> = {
  indexed: { variant: "success", label: "Indexed" },
  processing: { variant: "warning", label: "Processing" },
  error: { variant: "error", label: "Error" },
  pending: { variant: "neutral", label: "Pending" },
};

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [collections, setCollections] = useState<Collection[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [searchQuery, setSearchQuery] = useState("");
  const [filterCollection, setFilterCollection] = useState("");
  const [filterStatus, setFilterStatus] = useState("");
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);
  const [showUpload, setShowUpload] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadCollection, setUploadCollection] = useState("");
  const [error, setError] = useState<string | null>(null);

  const loadDocuments = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getDocuments({
        page,
        page_size: pageSize,
        search: searchQuery || undefined,
        collection_id: filterCollection || undefined,
        status: filterStatus || undefined,
      });
      setDocuments(data.documents);
      setTotal(data.total);
    } catch {
      setError("Failed to load documents. Backend may be unavailable.");
      setDocuments([]);
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, searchQuery, filterCollection, filterStatus]);

  useEffect(() => {
    loadDocuments();
  }, [loadDocuments]);

  useEffect(() => {
    getCollections().then(setCollections).catch(() => {});
  }, []);

  const totalPages = Math.ceil(total / pageSize);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files?.length) return;
    setUploading(true);
    try {
      for (const file of Array.from(files)) {
        await uploadDocument(file, uploadCollection || undefined);
      }
      setShowUpload(false);
      loadDocuments();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (ids: string[]) => {
    try {
      await Promise.all(ids.map(deleteDocument));
      setSelected(new Set());
      loadDocuments();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Delete failed");
    }
  };

  const toggleSelect = (id: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const toggleAll = () => {
    if (selected.size === documents.length) {
      setSelected(new Set());
    } else {
      setSelected(new Set(documents.map((d) => d.id)));
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">Documents</h1>
          <p className="text-sm text-text-secondary mt-1">
            {total} documents indexed
          </p>
        </div>
        <Button icon={<Upload size={16} />} onClick={() => setShowUpload(true)}>
          Upload
        </Button>
      </div>

      {error && (
        <div className="flex items-center justify-between rounded-lg border border-amber-200 bg-amber-50 dark:bg-amber-950 dark:border-amber-800 p-3 text-sm text-amber-700 dark:text-amber-300">
          <span>{error}</span>
          <button onClick={() => setError(null)}>
            <X size={16} />
          </button>
        </div>
      )}

      <div className="flex flex-col sm:flex-row gap-3">
        <div className="flex-1">
          <Input
            placeholder="Search documents..."
            icon={<Search size={16} />}
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value);
              setPage(1);
            }}
          />
        </div>
        <Select
          value={filterCollection}
          onChange={(e) => {
            setFilterCollection(e.target.value);
            setPage(1);
          }}
          placeholder="All Collections"
          options={[
            { value: "", label: "All Collections" },
            ...collections.map((c) => ({ value: c.id, label: c.name })),
          ]}
          className="w-full sm:w-48"
        />
        <Select
          value={filterStatus}
          onChange={(e) => {
            setFilterStatus(e.target.value);
            setPage(1);
          }}
          placeholder="All Statuses"
          options={[
            { value: "", label: "All Statuses" },
            { value: "indexed", label: "Indexed" },
            { value: "processing", label: "Processing" },
            { value: "error", label: "Error" },
            { value: "pending", label: "Pending" },
          ]}
          className="w-full sm:w-40"
        />
      </div>

      {selected.size > 0 && (
        <div className="flex items-center gap-3 p-3 rounded-lg bg-brand-50 dark:bg-brand-950 border border-brand-200 dark:border-brand-800">
          <span className="text-sm font-medium text-brand-700 dark:text-brand-300">
            {selected.size} selected
          </span>
          <Button
            variant="danger"
            size="sm"
            icon={<Trash2 size={14} />}
            onClick={() => handleDelete(Array.from(selected))}
          >
            Delete Selected
          </Button>
          <Button variant="ghost" size="sm" onClick={() => setSelected(new Set())}>
            Clear
          </Button>
        </div>
      )}

      <div className="rounded-xl border border-border bg-surface-0 shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-text-muted">
            <div className="animate-spin h-6 w-6 border-2 border-brand-600 border-t-transparent rounded-full mx-auto mb-3" />
            Loading documents...
          </div>
        ) : documents.length === 0 ? (
          <div className="p-12 text-center">
            <FileText size={48} className="mx-auto text-text-muted opacity-50 mb-4" />
            <h3 className="text-lg font-medium text-text-primary">No documents found</h3>
            <p className="text-sm text-text-muted mt-1">
              Upload documents to get started
            </p>
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-10">
                  <input
                    type="checkbox"
                    checked={selected.size === documents.length && documents.length > 0}
                    onChange={toggleAll}
                    className="rounded border-border"
                  />
                </TableHead>
                <TableHead>Title</TableHead>
                <TableHead>Collection</TableHead>
                <TableHead>Source</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Chunks</TableHead>
                <TableHead>Indexed At</TableHead>
                <TableHead className="w-10" />
              </TableRow>
            </TableHeader>
            <TableBody>
              {documents.map((doc) => {
                const badge = statusBadge[doc.status] || statusBadge.pending;
                return (
                  <TableRow key={doc.id}>
                    <TableCell>
                      <input
                        type="checkbox"
                        checked={selected.has(doc.id)}
                        onChange={() => toggleSelect(doc.id)}
                        className="rounded border-border"
                      />
                    </TableCell>
                    <TableCell className="font-medium">
                      <Link href={`/documents/${doc.id}`} className="text-brand-600 hover:underline">
                        {truncate(doc.title, 50)}
                      </Link>
                    </TableCell>
                    <TableCell className="text-text-secondary">
                      {doc.collection_name || doc.collection_id}
                    </TableCell>
                    <TableCell className="text-text-secondary text-xs">
                      {doc.source_connector}
                    </TableCell>
                    <TableCell>
                      <Badge variant={badge.variant} dot>
                        {badge.label}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-text-secondary">
                      {doc.chunks_count}
                    </TableCell>
                    <TableCell className="text-text-secondary text-xs">
                      {formatDate(doc.indexed_at || doc.created_at)}
                    </TableCell>
                    <TableCell>
                      <button
                        onClick={() => handleDelete([doc.id])}
                        className="p-1.5 rounded-lg text-text-muted hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-950 transition-colors"
                      >
                        <Trash2 size={14} />
                      </button>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        )}
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-text-muted">
            Page {page} of {totalPages} ({total} documents)
          </p>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              icon={<ChevronLeft size={14} />}
              disabled={page <= 1}
              onClick={() => setPage((p) => p - 1)}
            >
              Previous
            </Button>
            <Button
              variant="outline"
              size="sm"
              disabled={page >= totalPages}
              onClick={() => setPage((p) => p + 1)}
            >
              Next
              <ChevronRight size={14} />
            </Button>
          </div>
        </div>
      )}

      <Modal
        open={showUpload}
        onClose={() => setShowUpload(false)}
        title="Upload Documents"
        description="Upload files to ingest into the knowledge base"
      >
        <div className="space-y-4">
          <Select
            label="Target Collection (optional)"
            value={uploadCollection}
            onChange={(e) => setUploadCollection(e.target.value)}
            placeholder="Default collection"
            options={[
              { value: "", label: "Default collection" },
              ...collections.map((c) => ({ value: c.name, label: c.name })),
            ]}
          />
          <div className="border-2 border-dashed border-border rounded-xl p-8 text-center hover:border-brand-400 transition-colors">
            <Upload size={32} className="mx-auto text-text-muted mb-3" />
            <p className="text-sm text-text-primary font-medium">
              Drop files here or click to browse
            </p>
            <p className="text-xs text-text-muted mt-1">
              Supports PDF, DOCX, TXT, MD, HTML, CSV
            </p>
            <input
              type="file"
              multiple
              accept=".pdf,.docx,.txt,.md,.html,.csv,.json"
              onChange={handleUpload}
              className="absolute inset-0 opacity-0 cursor-pointer"
              style={{ position: "relative", marginTop: "12px" }}
              disabled={uploading}
            />
          </div>
          {uploading && (
            <div className="flex items-center gap-2 text-sm text-brand-600">
              <div className="animate-spin h-4 w-4 border-2 border-brand-600 border-t-transparent rounded-full" />
              Uploading...
            </div>
          )}
        </div>
      </Modal>
    </div>
  );
}
