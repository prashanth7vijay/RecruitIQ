import { useState } from "react";
import { useCreateUser } from "./useAdmin";
import { useRoles } from "./useRoles";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Input } from "../../components/ui/Input";

function TempPasswordModal({ result, onClose }) {
  const [copied, setCopied] = useState(false);

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(result.temp_password);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Clipboard API can fail (permissions, non-HTTPS context) — the
      // password is still visible and selectable in the field either way.
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-ink-950/40 px-4">
      <Card className="w-full max-w-md p-6">
        <h2 className="font-display text-lg text-[var(--text-primary)]">
          {result.first_name} {result.last_name} was added
        </h2>
        <p className="mt-2 text-sm text-[var(--text-secondary)]">
          Share this temporary password with them directly (Slack DM, in person, etc). It
          <strong className="text-[var(--text-primary)]"> won't be shown again</strong> after you
          close this — they'll be required to set their own password on first login.
        </p>

        <div className="mt-4 flex items-center gap-2 rounded-md border border-[var(--border)] bg-[var(--surface)] px-3 py-2">
          <code className="flex-1 select-all break-all text-sm text-[var(--text-primary)]">
            {result.temp_password}
          </code>
          <Button variant="secondary" className="!px-2 !py-1 text-xs" onClick={handleCopy}>
            {copied ? "Copied" : "Copy"}
          </Button>
        </div>

        <p className="mt-3 text-xs text-[var(--text-muted)]">
          Valid for 7 days. Signs in as: <span className="font-medium">{result.email}</span>
        </p>

        <Button className="mt-5 w-full" onClick={onClose}>
          Done
        </Button>
      </Card>
    </div>
  );
}

export function InviteUserForm() {
  const { data: roles } = useRoles();
  const createUser = useCreateUser();
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ email: "", firstName: "", lastName: "", roleId: "" });
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    try {
      const created = await createUser.mutateAsync(form);
      setResult(created);
      setForm({ email: "", firstName: "", lastName: "", roleId: "" });
      setOpen(false);
    } catch (err) {
      setError(err.response?.data?.error?.message ?? "Could not create user.");
    }
  }

  return (
    <>
      {!open ? (
        <Button onClick={() => setOpen(true)}>+ New user</Button>
      ) : (
        <Card className="p-5">
          <p className="font-display text-base text-[var(--text-primary)]">New user</p>
          <form onSubmit={handleSubmit} className="mt-4 flex flex-col gap-4">
            <div className="grid grid-cols-2 gap-3">
              <Input
                id="invite-first-name"
                label="First name"
                value={form.firstName}
                onChange={(e) => setForm({ ...form, firstName: e.target.value })}
                required
              />
              <Input
                id="invite-last-name"
                label="Last name"
                value={form.lastName}
                onChange={(e) => setForm({ ...form, lastName: e.target.value })}
                required
              />
            </div>
            <Input
              id="invite-email"
              type="email"
              label="Email"
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              required
            />
            <div className="flex flex-col gap-1.5">
              <label className="text-sm font-medium text-[var(--text-primary)]">Role</label>
              <select
                value={form.roleId}
                onChange={(e) => setForm({ ...form, roleId: e.target.value })}
                required
                className="rounded-md border border-[var(--border)] bg-[var(--surface-raised)] px-3 py-2 text-sm capitalize text-[var(--text-primary)]"
              >
                <option value="">Select a role…</option>
                {roles?.map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.name.replace(/_/g, " ")}
                  </option>
                ))}
              </select>
            </div>
            {error && <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}
            <div className="flex gap-2">
              <Button type="submit" disabled={createUser.isPending}>
                {createUser.isPending ? "Creating…" : "Create user"}
              </Button>
              <Button type="button" variant="ghost" onClick={() => setOpen(false)}>
                Cancel
              </Button>
            </div>
          </form>
        </Card>
      )}

      {result && <TempPasswordModal result={result} onClose={() => setResult(null)} />}
    </>
  );
}
