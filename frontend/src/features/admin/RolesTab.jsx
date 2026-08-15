import { useState } from "react";
import { useAuth } from "../../stores/AuthContext";
import { useRoles, usePermissionCatalog, useCreateRole, useUpdateRole, useDeleteRole } from "./useRoles";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Input } from "../../components/ui/Input";

function permissionGroup(code) {
  return code.split(".")[0];
}

function PermissionPicker({ allPermissions, selected, onToggle }) {
  const groups = allPermissions.reduce((acc, p) => {
    const group = permissionGroup(p.code);
    (acc[group] ??= []).push(p);
    return acc;
  }, {});

  return (
    <div className="grid grid-cols-2 gap-x-6 gap-y-3 sm:grid-cols-3">
      {Object.entries(groups).map(([group, perms]) => (
        <div key={group}>
          <p className="text-xs font-semibold uppercase tracking-wide text-[var(--text-muted)]">{group}</p>
          <div className="mt-1.5 flex flex-col gap-1">
            {perms.map((p) => (
              <label key={p.code} className="flex items-center gap-2 text-sm text-[var(--text-secondary)]">
                <input
                  type="checkbox"
                  checked={selected.includes(p.code)}
                  onChange={() => onToggle(p.code)}
                  className="h-3.5 w-3.5 rounded border-[var(--border)] accent-signal-500"
                />
                {p.code}
              </label>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

function CreateRoleForm({ allPermissions, onDone }) {
  const [name, setName] = useState("");
  const [selected, setSelected] = useState([]);
  const [error, setError] = useState(null);
  const createRole = useCreateRole();

  function toggle(code) {
    setSelected((s) => (s.includes(code) ? s.filter((c) => c !== code) : [...s, code]));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    try {
      await createRole.mutateAsync({ name, permissionCodes: selected });
      setName("");
      setSelected([]);
      onDone();
    } catch (err) {
      setError(err.response?.data?.error?.message ?? "Could not create role.");
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      <Input
        label="Role name"
        value={name}
        onChange={(e) => setName(e.target.value)}
        placeholder="e.g. Sourcer"
        required
      />
      <div>
        <p className="text-sm font-medium text-[var(--text-primary)]">Permissions</p>
        <div className="mt-2">
          <PermissionPicker allPermissions={allPermissions} selected={selected} onToggle={toggle} />
        </div>
      </div>
      {error && <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}
      <Button type="submit" disabled={createRole.isPending || !name.trim()} className="self-start">
        {createRole.isPending ? "Creating…" : "Create role"}
      </Button>
    </form>
  );
}

function RoleRow({ role, allPermissions, canManage }) {
  const [editing, setEditing] = useState(false);
  const [selected, setSelected] = useState(role.permissions);
  const updateRole = useUpdateRole();
  const deleteRole = useDeleteRole();
  const [error, setError] = useState(null);

  function toggle(code) {
    setSelected((s) => (s.includes(code) ? s.filter((c) => c !== code) : [...s, code]));
  }

  async function handleSave() {
    setError(null);
    try {
      await updateRole.mutateAsync({ roleId: role.id, permissionCodes: selected });
      setEditing(false);
    } catch (err) {
      setError(err.response?.data?.error?.message ?? "Could not save.");
    }
  }

  async function handleDelete() {
    setError(null);
    try {
      await deleteRole.mutateAsync(role.id);
    } catch (err) {
      setError(err.response?.data?.error?.message ?? "Could not delete — it may still have users assigned.");
    }
  }

  return (
    <div className="border-b border-[var(--border)] px-4 py-3 last:border-0">
      <div className="flex items-center justify-between">
        <div>
          <span className="font-medium capitalize text-[var(--text-primary)]">
            {role.name.replace(/_/g, " ")}
          </span>
          {role.is_system_role && (
            <span className="ml-2 rounded-full bg-[var(--surface-hover)] px-2 py-0.5 text-[10px] uppercase tracking-wide text-[var(--text-muted)]">
              System
            </span>
          )}
        </div>
        {canManage && !role.is_system_role && (
          <div className="flex gap-2">
            <Button variant="ghost" className="!px-2 !py-1 text-xs" onClick={() => setEditing((e) => !e)}>
              {editing ? "Cancel" : "Edit"}
            </Button>
            <Button variant="ghost" className="!px-2 !py-1 text-xs text-red-600" onClick={handleDelete}>
              Delete
            </Button>
          </div>
        )}
      </div>

      {!editing && (
        <div className="mt-1.5 flex flex-wrap gap-1">
          {role.permissions.length === 0 && (
            <span className="text-xs text-[var(--text-muted)]">No permissions assigned</span>
          )}
          {role.permissions.map((code) => (
            <span
              key={code}
              className="rounded-full bg-[var(--surface-hover)] px-2 py-0.5 text-[11px] text-[var(--text-secondary)]"
            >
              {code}
            </span>
          ))}
        </div>
      )}

      {editing && (
        <div className="mt-3">
          <PermissionPicker allPermissions={allPermissions} selected={selected} onToggle={toggle} />
          {error && <p className="mt-2 text-xs text-red-600">{error}</p>}
          <Button className="mt-3" onClick={handleSave} disabled={updateRole.isPending}>
            {updateRole.isPending ? "Saving…" : "Save permissions"}
          </Button>
        </div>
      )}
      {!editing && error && <p className="mt-2 text-xs text-red-600">{error}</p>}
    </div>
  );
}

export function RolesTab() {
  const { hasPermission } = useAuth();
  const canManage = hasPermission("role.manage");

  const { data: roles, isLoading: rolesLoading } = useRoles();
  const { data: allPermissions, isLoading: permsLoading } = usePermissionCatalog();
  const [showCreate, setShowCreate] = useState(false);

  if (rolesLoading || permsLoading) {
    return <p className="text-sm text-[var(--text-muted)]">Loading roles…</p>;
  }

  return (
    <div className="flex flex-col gap-6">
      {canManage && (
        <div>
          {!showCreate ? (
            <Button onClick={() => setShowCreate(true)}>+ New custom role</Button>
          ) : (
            <Card className="p-5">
              <p className="font-display text-base text-[var(--text-primary)]">New custom role</p>
              <div className="mt-4">
                <CreateRoleForm allPermissions={allPermissions} onDone={() => setShowCreate(false)} />
              </div>
              <Button variant="ghost" className="mt-3" onClick={() => setShowCreate(false)}>
                Cancel
              </Button>
            </Card>
          )}
        </div>
      )}
      {!canManage && (
        <p className="text-sm text-[var(--text-muted)]">
          You can view roles and permissions but don't have permission to create or edit them.
        </p>
      )}

      <Card>
        {roles.map((role) => (
          <RoleRow key={role.id} role={role} allPermissions={allPermissions} canManage={canManage} />
        ))}
      </Card>
    </div>
  );
}
