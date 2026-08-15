import { useEffect, useState } from "react";
import { useAuth } from "../../stores/AuthContext";
import { useApprovalChain, useSetApprovalChain } from "./useApprovalChains";
import { useRoles } from "./useRoles";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";

function ChainEditor({ entityType, label }) {
  const { hasPermission } = useAuth();
  const canManage = hasPermission("approval.manage_chains");
  const { data: chain, isLoading } = useApprovalChain(entityType);
  const { data: roles } = useRoles();
  const setChain = useSetApprovalChain(entityType);

  const [roleIds, setRoleIds] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (chain) setRoleIds(chain.steps.map((s) => s.role_id));
  }, [chain]);

  function addStep() {
    setRoleIds((ids) => [...ids, roles?.[0]?.id ?? ""]);
  }

  function updateStep(index, roleId) {
    setRoleIds((ids) => ids.map((id, i) => (i === index ? roleId : id)));
  }

  function removeStep(index) {
    setRoleIds((ids) => ids.filter((_, i) => i !== index));
  }

  async function handleSave() {
    setError(null);
    try {
      await setChain.mutateAsync(roleIds);
    } catch (err) {
      setError(err.response?.data?.error?.message ?? "Could not save the approval chain.");
    }
  }

  if (isLoading) return <p className="text-sm text-[var(--text-muted)]">Loading…</p>;

  return (
    <Card className="p-6">
      <p className="font-display text-lg text-[var(--text-primary)]">{label}</p>
      <p className="mt-1 text-sm text-[var(--text-secondary)]">
        Every {entityType} must be approved by each of these roles, in order, before it goes live.
      </p>

      {!chain && !canManage && (
        <p className="mt-3 text-sm text-[var(--text-muted)]">No approval chain configured yet.</p>
      )}

      {(chain || canManage) && (
        <div className="mt-4 flex flex-col gap-2">
          {roleIds.map((roleId, index) => (
            <div key={index} className="flex items-center gap-2">
              <span className="w-5 text-sm text-[var(--text-muted)]">{index + 1}.</span>
              <select
                value={roleId}
                onChange={(e) => updateStep(index, e.target.value)}
                disabled={!canManage}
                className="flex-1 rounded-md border border-[var(--border)] bg-[var(--surface-raised)] px-3 py-2 text-sm capitalize text-[var(--text-primary)] disabled:opacity-60"
              >
                {roles?.map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.name.replace(/_/g, " ")}
                  </option>
                ))}
              </select>
              {canManage && (
                <button
                  type="button"
                  onClick={() => removeStep(index)}
                  className="text-xs text-red-500 hover:text-red-600"
                >
                  Remove
                </button>
              )}
            </div>
          ))}

          {canManage && (
            <div className="mt-2 flex items-center gap-2">
              <Button variant="secondary" type="button" onClick={addStep} disabled={!roles?.length}>
                + Add step
              </Button>
              <Button
                type="button"
                onClick={handleSave}
                disabled={setChain.isPending || roleIds.length === 0}
              >
                {setChain.isPending ? "Saving…" : "Save chain"}
              </Button>
            </div>
          )}
          {error && <p className="text-xs text-red-600">{error}</p>}
        </div>
      )}
    </Card>
  );
}

export function ApprovalChainsTab() {
  return (
    <div className="flex flex-col gap-6">
      <ChainEditor entityType="job" label="Job approval chain" />
      <ChainEditor entityType="offer" label="Offer approval chain" />
    </div>
  );
}
