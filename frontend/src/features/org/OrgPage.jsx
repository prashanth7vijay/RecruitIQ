import { useState } from "react";
import { useAuth } from "../../stores/AuthContext";
import {
  useDepartments,
  useCreateDepartment,
  useDeleteDepartment,
  useTeams,
  useCreateTeam,
  useDeleteTeam,
  useLocations,
  useCreateLocation,
  useDeleteLocation,
  useUpdateUserOrgPlacement,
} from "./useOrg";
import { useAdminUsers } from "../admin/useAdmin";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Input } from "../../components/ui/Input";

function DepartmentsSection({ canManage }) {
  const { data: departments, isLoading } = useDepartments();
  const createDepartment = useCreateDepartment();
  const deleteDepartment = useDeleteDepartment();
  const [name, setName] = useState("");
  const [parentId, setParentId] = useState("");
  const [error, setError] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    try {
      await createDepartment.mutateAsync({ name, parentId });
      setName("");
      setParentId("");
    } catch (err) {
      setError(err.response?.data?.error?.message ?? "Could not create department.");
    }
  }

  async function handleDelete(id) {
    setError(null);
    try {
      await deleteDepartment.mutateAsync(id);
    } catch (err) {
      setError(err.response?.data?.error?.message ?? "Could not delete department.");
    }
  }

  const byParent = (departments ?? []).reduce((acc, d) => {
    (acc[d.parent_id ?? "root"] ??= []).push(d);
    return acc;
  }, {});
  const rows = [];
  function pushChildren(parentKey, depth) {
    for (const dept of byParent[parentKey] ?? []) {
      rows.push({ dept, depth });
      pushChildren(dept.id, depth + 1);
    }
  }
  pushChildren("root", 0);

  return (
    <Card className="p-6">
      <h2 className="font-display text-lg text-[var(--text-primary)]">Departments</h2>

      {canManage && (
        <form onSubmit={handleSubmit} className="mt-4 flex flex-wrap items-end gap-2">
          <Input id="dept-name" label="New department" value={name} onChange={(e) => setName(e.target.value)} />
          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-medium text-[var(--text-primary)]">Parent (optional)</label>
            <select
              value={parentId}
              onChange={(e) => setParentId(e.target.value)}
              className="rounded-md border border-[var(--border)] bg-[var(--surface-raised)] px-3 py-2 text-sm text-[var(--text-primary)]"
            >
              <option value="">None — top level</option>
              {departments?.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name}
                </option>
              ))}
            </select>
          </div>
          <Button type="submit" disabled={createDepartment.isPending || !name}>
            {createDepartment.isPending ? "Adding…" : "Add"}
          </Button>
        </form>
      )}
      {error && <p className="mt-2 text-sm text-red-600">{error}</p>}

      <div className="mt-4 flex flex-col gap-1">
        {isLoading && <p className="text-sm text-[var(--text-muted)]">Loading…</p>}
        {departments?.length === 0 && <p className="text-sm text-[var(--text-muted)]">No departments yet.</p>}
        {rows.map(({ dept, depth }) => (
          <div
            key={dept.id}
            style={{ marginLeft: depth * 20 }}
            className="flex items-center justify-between rounded-md bg-[var(--surface-hover)] px-3 py-2 text-sm text-[var(--text-secondary)]"
          >
            {dept.name}
            {canManage && (
              <button
                onClick={() => handleDelete(dept.id)}
                className="text-xs text-red-500 hover:text-red-600"
              >
                Delete
              </button>
            )}
          </div>
        ))}
      </div>
    </Card>
  );
}

function TeamsSection({ canManage }) {
  const { data: teams, isLoading } = useTeams();
  const { data: departments } = useDepartments();
  const createTeam = useCreateTeam();
  const deleteTeam = useDeleteTeam();
  const [name, setName] = useState("");
  const [departmentId, setDepartmentId] = useState("");
  const [error, setError] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    try {
      await createTeam.mutateAsync({ name, departmentId });
      setName("");
    } catch (err) {
      setError(err.response?.data?.error?.message ?? "Could not create team.");
    }
  }

  async function handleDelete(id) {
    setError(null);
    try {
      await deleteTeam.mutateAsync(id);
    } catch (err) {
      setError(err.response?.data?.error?.message ?? "Could not delete team.");
    }
  }

  function departmentName(id) {
    return departments?.find((d) => d.id === id)?.name;
  }

  return (
    <Card className="mt-6 p-6">
      <h2 className="font-display text-lg text-[var(--text-primary)]">Teams</h2>
      {canManage && (
        <form onSubmit={handleSubmit} className="mt-4 flex flex-wrap items-end gap-2">
          <Input id="team-name" label="New team" value={name} onChange={(e) => setName(e.target.value)} />
          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-medium text-[var(--text-primary)]">Department (optional)</label>
            <select
              value={departmentId}
              onChange={(e) => setDepartmentId(e.target.value)}
              className="rounded-md border border-[var(--border)] bg-[var(--surface-raised)] px-3 py-2 text-sm text-[var(--text-primary)]"
            >
              <option value="">None</option>
              {departments?.map((dept) => (
                <option key={dept.id} value={dept.id}>
                  {dept.name}
                </option>
              ))}
            </select>
          </div>
          <Button type="submit" disabled={createTeam.isPending || !name}>
            {createTeam.isPending ? "Adding…" : "Add"}
          </Button>
        </form>
      )}
      {error && <p className="mt-2 text-sm text-red-600">{error}</p>}

      <div className="mt-4 flex flex-col gap-1">
        {isLoading && <p className="text-sm text-[var(--text-muted)]">Loading…</p>}
        {teams?.length === 0 && <p className="text-sm text-[var(--text-muted)]">No teams yet.</p>}
        {teams?.map((team) => (
          <div
            key={team.id}
            className="flex items-center justify-between rounded-md bg-[var(--surface-hover)] px-3 py-2 text-sm text-[var(--text-secondary)]"
          >
            <span>
              {team.name}
              {departmentName(team.department_id) && (
                <span className="ml-2 text-xs text-[var(--text-muted)]">— {departmentName(team.department_id)}</span>
              )}
            </span>
            {canManage && (
              <button onClick={() => handleDelete(team.id)} className="text-xs text-red-500 hover:text-red-600">
                Delete
              </button>
            )}
          </div>
        ))}
      </div>
    </Card>
  );
}

function LocationsSection({ canManage }) {
  const { data: locations, isLoading } = useLocations();
  const createLocation = useCreateLocation();
  const deleteLocation = useDeleteLocation();
  const [name, setName] = useState("");
  const [city, setCity] = useState("");
  const [isRemote, setIsRemote] = useState(false);
  const [error, setError] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    try {
      await createLocation.mutateAsync({ name, city, isRemote });
      setName("");
      setCity("");
      setIsRemote(false);
    } catch (err) {
      setError(err.response?.data?.error?.message ?? "Could not create location.");
    }
  }

  async function handleDelete(id) {
    setError(null);
    try {
      await deleteLocation.mutateAsync(id);
    } catch (err) {
      setError(err.response?.data?.error?.message ?? "Could not delete location.");
    }
  }

  return (
    <Card className="mt-6 p-6">
      <h2 className="font-display text-lg text-[var(--text-primary)]">Locations</h2>
      {canManage && (
        <form onSubmit={handleSubmit} className="mt-4 flex flex-wrap items-end gap-2">
          <Input id="loc-name" label="Name" value={name} onChange={(e) => setName(e.target.value)} placeholder="Bangalore Office" />
          <Input id="loc-city" label="City (optional)" value={city} onChange={(e) => setCity(e.target.value)} />
          <label className="flex items-center gap-2 pb-2 text-sm text-[var(--text-secondary)]">
            <input type="checkbox" checked={isRemote} onChange={(e) => setIsRemote(e.target.checked)} className="accent-signal-500" />
            Remote
          </label>
          <Button type="submit" disabled={createLocation.isPending || !name}>
            {createLocation.isPending ? "Adding…" : "Add"}
          </Button>
        </form>
      )}
      {error && <p className="mt-2 text-sm text-red-600">{error}</p>}

      <div className="mt-4 flex flex-col gap-1">
        {isLoading && <p className="text-sm text-[var(--text-muted)]">Loading…</p>}
        {locations?.length === 0 && <p className="text-sm text-[var(--text-muted)]">No locations yet.</p>}
        {locations?.map((loc) => (
          <div
            key={loc.id}
            className="flex items-center justify-between rounded-md bg-[var(--surface-hover)] px-3 py-2 text-sm text-[var(--text-secondary)]"
          >
            <span>
              {loc.name}
              {loc.is_remote && (
                <span className="ml-2 rounded-full bg-signal-100 px-2 py-0.5 text-[10px] uppercase text-signal-700 dark:bg-signal-900 dark:text-signal-300">
                  Remote
                </span>
              )}
              {loc.city && <span className="ml-2 text-xs text-[var(--text-muted)]">{loc.city}</span>}
            </span>
            {canManage && (
              <button onClick={() => handleDelete(loc.id)} className="text-xs text-red-500 hover:text-red-600">
                Delete
              </button>
            )}
          </div>
        ))}
      </div>
    </Card>
  );
}

function PeoplePlacementSection({ canManage }) {
  const { data: users, isLoading: usersLoading } = useAdminUsers();
  const { data: departments } = useDepartments();
  const { data: teams } = useTeams();
  const { data: locations } = useLocations();
  const updatePlacement = useUpdateUserOrgPlacement();

  if (!canManage) return null;

  return (
    <Card className="mt-6 p-6">
      <h2 className="font-display text-lg text-[var(--text-primary)]">People</h2>
      <p className="mt-1 text-sm text-[var(--text-secondary)]">
        Assign each person's department, team, manager, and location.
      </p>

      <div className="mt-4 overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-[var(--border)] text-xs uppercase tracking-wide text-[var(--text-muted)]">
              <th className="px-3 py-2 font-medium">Name</th>
              <th className="px-3 py-2 font-medium">Department</th>
              <th className="px-3 py-2 font-medium">Team</th>
              <th className="px-3 py-2 font-medium">Manager</th>
              <th className="px-3 py-2 font-medium">Location</th>
            </tr>
          </thead>
          <tbody>
            {usersLoading && (
              <tr>
                <td colSpan={5} className="px-3 py-3 text-[var(--text-muted)]">Loading…</td>
              </tr>
            )}
            {users?.map((user) => (
              <tr key={user.id} className="border-b border-[var(--border)] last:border-0">
                <td className="px-3 py-2 font-medium text-[var(--text-primary)]">
                  {user.first_name} {user.last_name}
                </td>
                <td className="px-3 py-2">
                  <select
                    defaultValue={user.department_id ?? ""}
                    onChange={(e) => updatePlacement.mutate({ userId: user.id, departmentId: e.target.value })}
                    className="rounded-md border border-[var(--border)] bg-[var(--surface-raised)] px-2 py-1 text-xs text-[var(--text-primary)]"
                  >
                    <option value="">—</option>
                    {departments?.map((d) => (
                      <option key={d.id} value={d.id}>
                        {d.name}
                      </option>
                    ))}
                  </select>
                </td>
                <td className="px-3 py-2">
                  <select
                    defaultValue={user.team_id ?? ""}
                    onChange={(e) => updatePlacement.mutate({ userId: user.id, teamId: e.target.value })}
                    className="rounded-md border border-[var(--border)] bg-[var(--surface-raised)] px-2 py-1 text-xs text-[var(--text-primary)]"
                  >
                    <option value="">—</option>
                    {teams?.map((t) => (
                      <option key={t.id} value={t.id}>
                        {t.name}
                      </option>
                    ))}
                  </select>
                </td>
                <td className="px-3 py-2">
                  <select
                    defaultValue={user.manager_id ?? ""}
                    onChange={(e) => updatePlacement.mutate({ userId: user.id, managerId: e.target.value })}
                    className="rounded-md border border-[var(--border)] bg-[var(--surface-raised)] px-2 py-1 text-xs text-[var(--text-primary)]"
                  >
                    <option value="">—</option>
                    {users?.filter((u) => u.id !== user.id).map((u) => (
                      <option key={u.id} value={u.id}>
                        {u.first_name} {u.last_name}
                      </option>
                    ))}
                  </select>
                </td>
                <td className="px-3 py-2">
                  <select
                    defaultValue={user.location_id ?? ""}
                    onChange={(e) => updatePlacement.mutate({ userId: user.id, locationId: e.target.value })}
                    className="rounded-md border border-[var(--border)] bg-[var(--surface-raised)] px-2 py-1 text-xs text-[var(--text-primary)]"
                  >
                    <option value="">—</option>
                    {locations?.map((l) => (
                      <option key={l.id} value={l.id}>
                        {l.name}
                      </option>
                    ))}
                  </select>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}

export function OrgPage() {
  const { hasPermission } = useAuth();
  const canManage = hasPermission("org.manage_structure");

  return (
    <div className="mx-auto max-w-4xl">
      <h1 className="font-display text-2xl text-[var(--text-primary)]">Organization</h1>
      <p className="mt-1 text-sm text-[var(--text-secondary)]">
        Departments, teams, locations, and reporting structure for your company.
      </p>
      {!canManage && (
        <p className="mt-4 rounded-md border border-[var(--border)] bg-[var(--surface-hover)] px-3 py-2 text-sm text-[var(--text-secondary)]">
          You can view the org structure but don't have permission to make changes.
        </p>
      )}
      <div className="mt-6">
        <DepartmentsSection canManage={canManage} />
        <TeamsSection canManage={canManage} />
        <LocationsSection canManage={canManage} />
        <PeoplePlacementSection canManage={canManage} />
      </div>
    </div>
  );
}
