import { useState } from "react";
import { useAdminUsers, useUpdateUserStatus, useAuditLogs, useSystemHealth } from "./useAdmin";
import { useRoles, useUpdateUserRole } from "./useRoles";
import { RolesTab } from "./RolesTab";
import { ApprovalChainsTab } from "./ApprovalChainsTab";
import { InviteUserForm } from "./InviteUserForm";
import { Card } from "../../components/ui/Card";
import { useAuth } from "../../stores/AuthContext";

const STATUS_OPTIONS = ["active", "locked", "disabled"];

function UsersTab() {
  const { hasPermission } = useAuth();
  const canManageUsers = hasPermission("admin.manage_users");
  const { data: users, isLoading } = useAdminUsers();
  const { data: roles } = useRoles();
  const updateStatus = useUpdateUserStatus();
  const updateUserRole = useUpdateUserRole();

  return (
    <div className="flex flex-col gap-4">
      {canManageUsers && <InviteUserForm />}

      <Card>
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-[var(--border)] text-xs uppercase tracking-wide text-[var(--text-muted)]">
              <th className="px-4 py-3 font-medium">Name</th>
              <th className="px-4 py-3 font-medium">Email</th>
              <th className="px-4 py-3 font-medium">Role</th>
              <th className="px-4 py-3 font-medium">Status</th>
            </tr>
          </thead>
          <tbody>
            {isLoading && (
              <tr>
                <td colSpan={4} className="px-4 py-3 text-[var(--text-muted)]">Loading…</td>
              </tr>
            )}
            {users?.map((user) => (
              <tr key={user.id} className="border-b border-[var(--border)] last:border-0">
                <td className="px-4 py-3 font-medium text-[var(--text-primary)]">
                  {user.first_name} {user.last_name}
                  {user.must_change_password && (
                    <span className="ml-2 rounded-full bg-amber-100 px-2 py-0.5 text-[10px] uppercase tracking-wide text-amber-700 dark:bg-amber-900 dark:text-amber-300">
                      Pending first login
                    </span>
                  )}
                </td>
                <td className="px-4 py-3 text-[var(--text-secondary)]">{user.email}</td>
                <td className="px-4 py-3">
                  {canManageUsers && roles ? (
                    <select
                      value={user.role_id}
                      onChange={(e) => updateUserRole.mutate({ userId: user.id, roleId: e.target.value })}
                      disabled={updateUserRole.isPending}
                      className="rounded-md border border-[var(--border)] bg-[var(--surface-raised)] px-2 py-1 text-xs capitalize text-[var(--text-primary)]"
                    >
                      {roles.map((r) => (
                        <option key={r.id} value={r.id}>
                          {r.name.replace(/_/g, " ")}
                        </option>
                      ))}
                    </select>
                  ) : (
                    <span className="capitalize text-[var(--text-secondary)]">{user.role_name?.replace(/_/g, " ")}</span>
                  )}
                </td>
                <td className="px-4 py-3">
                  <select
                    value={user.status}
                    onChange={(e) => updateStatus.mutate({ userId: user.id, status: e.target.value })}
                    disabled={updateStatus.isPending}
                    className="rounded-md border border-[var(--border)] bg-[var(--surface-raised)] px-2 py-1 text-xs capitalize text-[var(--text-primary)]"
                  >
                    {STATUS_OPTIONS.map((s) => (
                      <option key={s} value={s}>
                        {s}
                      </option>
                    ))}
                  </select>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
}

function AuditLogTab() {
  const { data: logs, isLoading } = useAuditLogs();

  return (
    <Card>
      <div className="flex flex-col divide-y divide-[var(--border)]">
        {isLoading && <p className="p-4 text-sm text-[var(--text-muted)]">Loading…</p>}
        {logs?.length === 0 && <p className="p-4 text-sm text-[var(--text-muted)]">No audit entries yet.</p>}
        {logs?.map((log) => (
          <div key={log.id} className="px-4 py-3 text-sm">
            <div className="flex justify-between">
              <span className="font-medium text-[var(--text-primary)]">
                {log.entity_type} {log.action.replace(/_/g, " ")}
              </span>
              <span className="text-xs text-[var(--text-muted)]">{new Date(log.created_at).toLocaleString()}</span>
            </div>
            {log.new_value && (
              <p className="mt-1 text-xs text-[var(--text-secondary)]">{JSON.stringify(log.new_value)}</p>
            )}
          </div>
        ))}
      </div>
    </Card>
  );
}

function SystemHealthTab() {
  const { data: health, isLoading } = useSystemHealth();

  if (isLoading) return <p className="text-sm text-[var(--text-muted)]">Loading…</p>;

  return (
    <div className="grid grid-cols-3 gap-4">
      <Card className="p-4">
        <p className="text-xs uppercase tracking-wide text-[var(--text-muted)]">Status</p>
        <p className="mt-1 text-2xl font-semibold capitalize text-signal-600">{health?.status}</p>
      </Card>
      <Card className="p-4">
        <p className="text-xs uppercase tracking-wide text-[var(--text-muted)]">Users</p>
        <p className="mt-1 text-2xl font-semibold text-[var(--text-primary)]">{health?.user_count}</p>
      </Card>
      <Card className="p-4">
        <p className="text-xs uppercase tracking-wide text-[var(--text-muted)]">Published jobs</p>
        <p className="mt-1 text-2xl font-semibold text-[var(--text-primary)]">{health?.active_job_count}</p>
      </Card>
    </div>
  );
}

const TABS = [
  { id: "users", label: "Users", Component: UsersTab, requiredPermission: "admin.manage_users" },
  { id: "roles", label: "Roles & Permissions", Component: RolesTab, requiredPermission: "role.manage" },
  {
    id: "approvals",
    label: "Approval Chains",
    Component: ApprovalChainsTab,
    requiredPermission: "approval.manage_chains",
  },
  { id: "audit", label: "Audit Log", Component: AuditLogTab, requiredPermission: "admin.manage_users" },
  { id: "health", label: "System Health", Component: SystemHealthTab, requiredPermission: "admin.manage_users" },
];

export function AdminPage() {
  const { hasPermission } = useAuth();
  const visibleTabs = TABS.filter((tab) => hasPermission(tab.requiredPermission));
  const [activeTab, setActiveTab] = useState(visibleTabs[0]?.id);

  if (visibleTabs.length === 0) {
    return (
      <p className="text-sm text-[var(--text-muted)]">
        You don't have permission to view any administration area.
      </p>
    );
  }

  const ActiveComponent = (visibleTabs.find((t) => t.id === activeTab) ?? visibleTabs[0]).Component;

  return (
    <div className="mx-auto max-w-4xl">
      <h1 className="font-display text-2xl text-[var(--text-primary)]">Admin</h1>
      <p className="mt-1 text-sm text-[var(--text-secondary)]">Organization-level administration.</p>

      <div className="mt-6 flex gap-1 border-b border-[var(--border)]">
        {visibleTabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-2 text-sm font-medium transition-colors ${
              (activeTab ?? visibleTabs[0].id) === tab.id
                ? "border-b-2 border-signal-500 text-signal-700 dark:text-signal-300"
                : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <div className="mt-6">
        <ActiveComponent />
      </div>
    </div>
  );
}