import { useState } from "react";
import { useTalentPools, useCreateTalentPool, usePoolMembers, useRemoveFromPool } from "./useTalentPools";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Input } from "../../components/ui/Input";

function PoolDetail({ pool }) {
  const { data: members, isLoading } = usePoolMembers(pool.id);
  const removeFromPool = useRemoveFromPool(pool.id);

  return (
    <Card className="mt-3 p-4">
      <p className="font-medium text-ink-800">{pool.name}</p>
      {pool.description && <p className="text-xs text-ink-500">{pool.description}</p>}
      <div className="mt-3 flex flex-col gap-1">
        {isLoading && <p className="text-xs text-ink-400">Loading members…</p>}
        {members?.length === 0 && (
          <p className="text-xs text-ink-400">
            No candidates yet — open a candidate's "Notes, tags & pools" panel on the Candidates
            page to add them here.
          </p>
        )}
        {members?.map((member) => (
          <div key={member.id} className="flex items-center justify-between rounded-md bg-ink-50 px-3 py-2 text-xs">
            <div>
              <span className="font-medium text-ink-800">
                {member.candidate.first_name} {member.candidate.last_name}
              </span>
              <span className="ml-2 text-ink-500">{member.current_location ?? "Location unknown"}</span>
            </div>
            <button
              onClick={() => removeFromPool.mutate(member.id)}
              disabled={removeFromPool.isPending}
              className="text-red-500 hover:text-red-600"
            >
              Remove
            </button>
          </div>
        ))}
      </div>
    </Card>
  );
}

export function TalentPoolsPage() {
  const { data: pools, isLoading } = useTalentPools();
  const createPool = useCreateTalentPool();
  const [name, setName] = useState("");
  const [selectedPoolId, setSelectedPoolId] = useState(null);

  async function handleCreate(e) {
    e.preventDefault();
    const pool = await createPool.mutateAsync({ name });
    setName("");
    setSelectedPoolId(pool.id);
  }

  return (
    <div className="mx-auto max-w-2xl">
      <h1 className="font-display text-2xl text-ink-900">Talent pools</h1>
      <p className="mt-1 text-sm text-ink-500">
        Candidates never disappear after a rejection — organize them here for future roles.
      </p>

      <Card className="mt-6 p-6">
        <form onSubmit={handleCreate} className="flex items-end gap-2">
          <Input id="pool-name" label="New pool" value={name} onChange={(e) => setName(e.target.value)} />
          <Button type="submit" disabled={createPool.isPending || !name}>
            {createPool.isPending ? "Creating…" : "Create pool"}
          </Button>
        </form>
      </Card>

      <div className="mt-6">
        {isLoading && <p className="text-sm text-ink-400">Loading…</p>}
        {pools?.length === 0 && <p className="text-sm text-ink-400">No talent pools yet.</p>}
        <div className="flex flex-wrap gap-2">
          {pools?.map((pool) => (
            <button
              key={pool.id}
              onClick={() => setSelectedPoolId(pool.id)}
              className={`rounded-full px-3 py-1.5 text-sm font-medium ${
                selectedPoolId === pool.id ? "bg-signal-500 text-white" : "bg-ink-100 text-ink-600"
              }`}
            >
              {pool.name}
            </button>
          ))}
        </div>
        {selectedPoolId && (
          <PoolDetail pool={pools.find((p) => p.id === selectedPoolId)} />
        )}
      </div>
    </div>
  );
}