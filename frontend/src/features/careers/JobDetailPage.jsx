import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { usePublicJob, useApplyToJob, usePublicCompany } from "./usePublicJobs";
import { useApplyBranding } from "./useApplyBranding";
import { Input } from "../../components/ui/Input";
import { Button } from "../../components/ui/Button";

export function JobDetailPage() {
  const { companySlug, jobId } = useParams();
  const { data: job, isLoading } = usePublicJob(companySlug, jobId);
  const { data: company } = usePublicCompany(companySlug);
  useApplyBranding(company);
  const applyMutation = useApplyToJob(companySlug, jobId);
  const [form, setForm] = useState({ email: "", firstName: "", lastName: "", phone: "" });
  const [resumeFile, setResumeFile] = useState(null);
  const [error, setError] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    try {
      await applyMutation.mutateAsync({ ...form, resumeFile });
    } catch (err) {
      const msg = err.response?.data?.error?.message;
      setError(
        err.response?.status === 409
          ? "Looks like you've already applied to this role with this email."
          : msg ?? "Something went wrong submitting your application."
      );
    }
  }

  if (isLoading) {
    return <div className="p-8 text-sm text-[var(--text-muted)]">Loading…</div>;
  }

  if (applyMutation.isSuccess) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[var(--surface)] px-8">
        <div className="max-w-md text-center">
          <p className="font-display text-2xl text-[var(--text-primary)]">Application received</p>
          <p className="mt-2 text-sm text-[var(--text-secondary)]">
            Thanks for applying to {job?.title}. The team will be in touch if there's a fit.
          </p>
          <Link to={`/careers/${companySlug}`} className="mt-6 inline-block text-sm text-signal-600">
            ← Back to open roles
          </Link>
        </div>
      </div>
    );
  }

  const primaryColor = company?.branding?.primary_color;

  return (
    <div className="min-h-screen bg-[var(--surface)] px-8 py-10">
      <div className="mx-auto max-w-2xl">
        <Link to={`/careers/${companySlug}`} className="text-sm text-[var(--text-muted)] hover:text-[var(--text-primary)]">
          ← All open roles
        </Link>

        <h1 className="mt-4 font-display text-3xl text-[var(--text-primary)]">{job?.title}</h1>
        {job?.description && (
          <p className="mt-4 whitespace-pre-line text-sm text-[var(--text-secondary)]">{job.description}</p>
        )}

        <div className="mt-10 rounded-lg border border-[var(--border)] bg-[var(--surface-raised)] p-6">
          <h2 className="font-display text-lg text-[var(--text-primary)]">Apply</h2>
          <form onSubmit={handleSubmit} className="mt-4 flex flex-col gap-4">
            <div className="grid grid-cols-2 gap-4">
              <Input
                id="firstName"
                label="First name"
                value={form.firstName}
                onChange={(e) => setForm({ ...form, firstName: e.target.value })}
                required
              />
              <Input
                id="lastName"
                label="Last name"
                value={form.lastName}
                onChange={(e) => setForm({ ...form, lastName: e.target.value })}
                required
              />
            </div>
            <Input
              id="email"
              label="Email"
              type="email"
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              required
            />
            <Input
              id="phone"
              label="Phone (optional)"
              value={form.phone}
              onChange={(e) => setForm({ ...form, phone: e.target.value })}
            />
            <div className="flex flex-col gap-1.5">
              <label className="text-sm font-medium text-[var(--text-primary)]">Resume (optional)</label>
              <input
                type="file"
                accept=".pdf,.docx,.doc"
                onChange={(e) => setResumeFile(e.target.files?.[0] ?? null)}
                className="text-sm text-[var(--text-secondary)] file:mr-3 file:rounded-md file:border-0 file:bg-[var(--surface-hover)] file:px-3 file:py-1.5 file:text-sm file:font-medium file:text-[var(--text-primary)]"
              />
            </div>
            {error && <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}
            <Button
              type="submit"
              disabled={applyMutation.isPending}
              className="mt-2 w-full"
              style={primaryColor ? { backgroundColor: primaryColor } : undefined}
            >
              {applyMutation.isPending ? "Submitting…" : "Submit application"}
            </Button>
          </form>
        </div>
      </div>
    </div>
  );
}
