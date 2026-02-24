"use client";

import React, { useState, useEffect } from "react";
import { Users, Plus, Pencil, Trash2, Shield, Mail } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Modal } from "@/components/ui/modal";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from "@/components/ui/table";
import { getUsers, createUser, updateUser, deleteUser, type User } from "@/lib/api";
import { formatDate } from "@/lib/utils";

const roleBadge: Record<string, "info" | "warning" | "neutral"> = {
  admin: "warning",
  editor: "info",
  viewer: "neutral",
};

export default function UsersPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [creating, setCreating] = useState(false);
  const [formData, setFormData] = useState({
    email: "",
    role: "viewer",
    password: "",
  });

  // Edit state
  const [editUser, setEditUser] = useState<User | null>(null);
  const [editData, setEditData] = useState({ email: "", role: "", password: "" });
  const [saving, setSaving] = useState(false);

  // Delete state
  const [deleteTarget, setDeleteTarget] = useState<User | null>(null);
  const [deleting, setDeleting] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const data = await getUsers();
      setUsers(data);
    } catch {
      setError("Failed to load users");
      setUsers([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleCreate = async () => {
    if (!formData.email || !formData.password) return;
    setCreating(true);
    try {
      await createUser(formData);
      setShowCreate(false);
      setFormData({ email: "", role: "viewer", password: "" });
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create user");
    } finally {
      setCreating(false);
    }
  };

  const handleEdit = (user: User) => {
    setEditUser(user);
    setEditData({ email: user.email, role: user.role, password: "" });
  };

  const handleSaveEdit = async () => {
    if (!editUser) return;
    setSaving(true);
    try {
      const payload: Record<string, string> = {};
      if (editData.email !== editUser.email) payload.email = editData.email;
      if (editData.role !== editUser.role) payload.role = editData.role;
      if (editData.password) payload.password = editData.password;
      if (Object.keys(payload).length > 0) {
        await updateUser(editUser.id, payload);
      }
      setEditUser(null);
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update user");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      await deleteUser(deleteTarget.id);
      setDeleteTarget(null);
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete user");
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">Users</h1>
          <p className="text-sm text-text-secondary mt-1">
            Manage platform users and roles
          </p>
        </div>
        <Button icon={<Plus size={16} />} onClick={() => setShowCreate(true)}>
          Add User
        </Button>
      </div>

      {error && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 dark:bg-amber-950 dark:border-amber-800 p-3 text-sm text-amber-700 dark:text-amber-300">
          {error}
        </div>
      )}

      <div className="rounded-xl border border-border bg-surface-0 shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-text-muted">
            <div className="animate-spin h-6 w-6 border-2 border-brand-600 border-t-transparent rounded-full mx-auto mb-3" />
            Loading users...
          </div>
        ) : users.length === 0 ? (
          <div className="p-12 text-center">
            <Users size={48} className="mx-auto text-text-muted opacity-50 mb-4" />
            <h3 className="text-lg font-medium text-text-primary">No users found</h3>
            <p className="text-sm text-text-muted mt-1">
              Add users to manage access
            </p>
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Email</TableHead>
                <TableHead>Role</TableHead>
                <TableHead>Created</TableHead>
                <TableHead className="w-20">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {users.map((user) => (
                <TableRow key={user.id}>
                  <TableCell>
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-full bg-brand-100 dark:bg-brand-900 flex items-center justify-center text-brand-600 dark:text-brand-400 text-sm font-medium">
                        {user.email.charAt(0).toUpperCase()}
                      </div>
                      <span className="font-medium">{user.email}</span>
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge variant={roleBadge[user.role] || "neutral"}>
                      <Shield size={12} className="mr-1" />
                      {user.role}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-text-secondary text-sm">
                    {formatDate(user.created_at)}
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-1">
                      <button
                        onClick={() => handleEdit(user)}
                        className="p-1.5 rounded-lg text-text-muted hover:text-text-primary hover:bg-surface-2 transition-colors"
                      >
                        <Pencil size={14} />
                      </button>
                      <button
                        onClick={() => setDeleteTarget(user)}
                        className="p-1.5 rounded-lg text-text-muted hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-950 transition-colors"
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </div>

      {/* Create Modal */}
      <Modal
        open={showCreate}
        onClose={() => setShowCreate(false)}
        title="Add User"
        description="Create a new platform user"
      >
        <div className="space-y-4">
          <Input
            label="Email"
            type="email"
            placeholder="user@example.com"
            icon={<Mail size={16} />}
            value={formData.email}
            onChange={(e) =>
              setFormData({ ...formData, email: e.target.value })
            }
          />
          <Input
            label="Password"
            type="password"
            placeholder="Minimum 8 characters"
            value={formData.password}
            onChange={(e) =>
              setFormData({ ...formData, password: e.target.value })
            }
          />
          <Select
            label="Role"
            value={formData.role}
            onChange={(e) =>
              setFormData({ ...formData, role: e.target.value })
            }
            options={[
              { value: "viewer", label: "Viewer" },
              { value: "member", label: "Member" },
              { value: "admin", label: "Admin" },
            ]}
          />
          <div className="flex justify-end gap-3 pt-2">
            <Button variant="outline" onClick={() => setShowCreate(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleCreate}
              loading={creating}
              disabled={!formData.email || !formData.password}
            >
              Create User
            </Button>
          </div>
        </div>
      </Modal>

      {/* Edit Modal */}
      <Modal
        open={editUser !== null}
        onClose={() => setEditUser(null)}
        title="Edit User"
        description={editUser ? `Modify ${editUser.email}` : ""}
      >
        <div className="space-y-4">
          <Input
            label="Email"
            type="email"
            value={editData.email}
            onChange={(e) => setEditData({ ...editData, email: e.target.value })}
          />
          <Select
            label="Role"
            value={editData.role}
            onChange={(e) => setEditData({ ...editData, role: e.target.value })}
            options={[
              { value: "viewer", label: "Viewer" },
              { value: "member", label: "Member" },
              { value: "admin", label: "Admin" },
            ]}
          />
          <Input
            label="New Password (optional)"
            type="password"
            placeholder="Leave empty to keep current"
            value={editData.password}
            onChange={(e) => setEditData({ ...editData, password: e.target.value })}
          />
          <div className="flex justify-end gap-3 pt-2">
            <Button variant="outline" onClick={() => setEditUser(null)}>
              Cancel
            </Button>
            <Button onClick={handleSaveEdit} loading={saving}>
              Save
            </Button>
          </div>
        </div>
      </Modal>

      {/* Delete Confirmation */}
      <Modal
        open={deleteTarget !== null}
        onClose={() => setDeleteTarget(null)}
        title="Delete User"
        description={`Are you sure you want to delete ${deleteTarget?.email}? This action cannot be undone.`}
      >
        <div className="flex justify-end gap-3 pt-2">
          <Button variant="outline" onClick={() => setDeleteTarget(null)}>
            Cancel
          </Button>
          <Button
            onClick={handleDelete}
            loading={deleting}
            className="bg-red-600 hover:bg-red-700 text-white"
          >
            Delete
          </Button>
        </div>
      </Modal>
    </div>
  );
}
