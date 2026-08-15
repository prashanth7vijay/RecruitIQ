import { useEffect, useState } from "react";
import { useCompany, useUpdateCompany } from "./useCompany";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Input } from "../../components/ui/Input";

export function CompanySettingsPage() {
  const { data: company, isLoading } = useCompany();
  const updateCompany = useUpdateCompany();
  const [name, setName] = useState("");
  const [error, setError] = useState(null);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (company) setName(company.name);
  }, [company]);

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setSaved(false);
    try {
      await updateCompany.mutateAsync({ name });
      setSaved(true);
    } catch (err) {
      setError(
        err.response?.status === 403
          ? "You don't have permission to change company settings."
          : err.response?.data?.error?.message ?? "Could not save changes."
      );
    }
  }

  return (
    <div className="mx-auto max-w-lg">
      <h1 className="font-display text-2xl text-ink-900">Company settings</h1>

      {isLoading && <p className="mt-4 text-sm text-ink-400">Loading…</p>}

      {company && (
        <Card className="mt-6 p-6">
          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <Input id="name" label="Company name" value={name} onChange={(e) => setName(e.target.value)} />
            <p className="text-xs text-ink-400">
              Career portal URL: <code className="text-ink-600">/careers/{company.slug}</code> — the
              slug can't be changed here since it's already used in shared application links.
            </p>
            {error && <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}
            {saved && <p className="text-sm text-signal-600">Saved.</p>}
            <Button type="submit" disabled={updateCompany.isPending} className="self-start">
              {updateCompany.isPending ? "Saving…" : "Save changes"}
            </Button>
          </form>
        </Card>
      )}
    </div>
  );
}
