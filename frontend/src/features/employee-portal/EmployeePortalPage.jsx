import { useState } from "react";
import { useOpenJobs, useMyReferrals, useSubmitReferral } from "./useEmployeePortal";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Input } from "../../components/ui/Input";

const STATUS_LABELS = {
  active: "In progress",
  hired: "Hired",
  rejected: "Not moving forward",
  withdrawn: "Withdrawn",
};

function ReferralForm({ jobs }) {
  const submitReferral = useSubmitReferral();
  const [form, setForm] = useState({ jobId: "", email: "", firstName: "", lastName: "", phone: "" });
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setSuccess(false);
    try {
      await submitReferral.mutateAsync(form);
      setForm({ jobId: "", email: "", firstName: "", lastName: "", phone: "" });
      setSuccess(true);
    } catch (err) {
      setError(err.response?.data?.error?.message ?? "Could not submit this referral.");
    }
  }

  return (
    <Card className="p-6">
      <p className="font-display text-lg text-[var(--text-primary)]">Refer a candidate</p>
      <form onSubmit={handleSubmit} className="mt-4 flex flex-col gap-4">
        <div className="flex flex-col gap-1.5">
          <label className="text-sm font-medium text-[var(--text-primary)]">Role</label>
          <select
            value={form.jobId}
            onChange={(e) => setForm({ ...form, jobId: e.target.value })}
            required
            className="rounded-md border border-[var(--border)] bg-[var(--surface-raised)] px-3 py-2 text-sm text-[var(--text-primary)]"
          >
            <option value="">Select an open role…</option>
            {jobs?.map((job) => (
              <option key={job.id} value={job.id}>
                {job.title}
              </option>
            ))}
          </select>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <Input
            id="referral-first-name"
            label="Their first name"
            value={form.firstName}
            onChange={(e) => setForm({ ...form, firstName: e.target.value })}
            required
          />
          <Input
            id="referral-last-name"
            label="Their last name"
            value={form.lastName}
            onChange={(e) => setForm({ ...form, lastName: e.target.value })}
            required
          />
        </div>
        <Input
          id="referral-email"
          type="email"
          label="Their email"
          value={form.email}
          onChange={(e) => setForm({ ...form, email: e.target.value })}
          required
        />
        {error && <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}
        {success && <p className="text-sm text-signal-600">Referral submitted.</p>}
        <Button type="submit" disabled={submitReferral.isPending || !jobs?.length} className="self-start">
          {submitReferral.isPending ? "Submitting…" : "Submit referral"}
        </Button>
        {!jobs?.length && <p className="text-xs text-[var(--text-muted)]">No open roles to refer into right now.</p>}
      </form>
    </Card>
  );
}

export function EmployeePortalPage() {
  const { data: jobs, isLoading: jobsLoading } = useOpenJobs();
  const { data: referrals, isLoading: referralsLoading } = useMyReferrals();

  return (
    <div className="mx-auto max-w-3xl">
      <h1 className="font-display text-2xl text-[var(--text-primary)]">Refer a candidate</h1>
      <p className="mt-1 text-sm text-[var(--text-secondary)]">
        See open roles and refer people you know — you'll be able to track their status here.
      </p>

      <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-2">
        <ReferralForm jobs={jobs} />

        <Card className="p-6">
          <p className="font-display text-lg text-[var(--text-primary)]">Open roles</p>
          <div className="mt-3 flex flex-col gap-1">
            {jobsLoading && <p className="text-sm text-[var(--text-muted)]">Loading…</p>}
            {jobs?.length === 0 && <p className="text-sm text-[var(--text-muted)]">No open roles right now.</p>}
            {jobs?.map((job) => (
              <div
                key={job.id}
                className="rounded-md bg-[var(--surface-hover)] px-3 py-2 text-sm text-[var(--text-secondary)]"
              >
                {job.title}
              </div>
            ))}
          </div>
        </Card>
      </div>

      <div className="mt-6">
        <h2 className="font-display text-lg text-[var(--text-primary)]">Your referrals</h2>
        <div className="mt-3 flex flex-col gap-2">
          {referralsLoading && <p className="text-sm text-[var(--text-muted)]">Loading…</p>}
          {referrals?.length === 0 && (
            <p className="text-sm text-[var(--text-muted)]">You haven't referred anyone yet.</p>
          )}
          {referrals?.map((r) => (
            <Card key={r.id} className="flex items-center justify-between p-4">
              <div>
                <p className="font-medium text-[var(--text-primary)]">{r.candidate_name}</p>
                <p className="text-sm text-[var(--text-secondary)]">{r.job_title}</p>
              </div>
              <span className="rounded-full bg-[var(--surface-hover)] px-3 py-1 text-xs text-[var(--text-secondary)]">
                {STATUS_LABELS[r.status] ?? r.status}
              </span>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}
