import { useState } from "react";
import { Link } from "react-router-dom";
import { useJobsPaginated } from "./useJobs";
import { useCreateJob, usePipelineTemplates } from "./useJobMutations";
import { useAuth } from "../../stores/AuthContext";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Input } from "../../components/ui/Input";

const STATUS_STYLES = {
  draft: "bg-ink-100 text-ink-600",
  pending_approval: "bg-amber-100 text-amber-700",
  published: "bg-signal-100 text-signal-700",
  closed: "bg-ink-200 text-ink-700",
  archived: "bg-ink-100 text-ink-400",
};

export function JobsPage() {
  const [page, setPage] = useState(1);
  const { data, isLoading } = useJobsPaginated(page);
  const { data: templates } = usePipelineTemplates();
  const createJob = useCreateJob();
  const { hasPermission } = useAuth();
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ title: "", pipeline_template_id: "" });

  const jobs = data?.items;
  const pagination = data?.pagination;

  async function handleCreate(e) {
    e.preventDefault();
    await createJob.mutateAsync({
      title: form.title,
      pipeline_template_id: form.pipeline_template_id || undefined,
    });
    setForm({ title: "", pipeline_template_id: "" });
    setShowForm(false);
  }

  return (
    <div className="mx-auto max-w-4xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-2xl text-ink-900">Jobs</h1>
          <p className="mt-1 text-sm text-ink-500">Open requisitions and their pipelines.</p>
        </div>
        {!showForm && hasPermission("job.create") && <Button onClick={() => setShowForm(true)}>New job</Button>}
      </div>

      {showForm && (
        <Card className="mt-6 p-6">
          <form onSubmit={handleCreate} className="flex flex-col gap-4">
            <Input
              id="title"
              label="Job title"
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
              required
            />
            <div className="flex flex-col gap-1.5">
              <label className="text-sm font-medium text-ink-700">Pipeline template</label>
              <select
                className="rounded-md border border-ink-200 bg-white px-3 py-2 text-sm"
                value={form.pipeline_template_id}
                onChange={(e) => setForm({ ...form, pipeline_template_id: e.target.value })}
              >
                <option value="">No pipeline yet (can't publish until set)</option>
                {templates?.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.name}
                  </option>
                ))}
              </select>
              {templates?.length === 0 && (
                <p className="text-xs text-ink-400">
                  No pipeline templates exist yet — create one on the Pipelines page before publishing jobs.
                </p>
              )}
            </div>
            <div className="flex justify-end gap-2">
              <Button type="button" variant="ghost" onClick={() => setShowForm(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={createJob.isPending}>
                {createJob.isPending ? "Creating…" : "Create draft"}
              </Button>
            </div>
          </form>
        </Card>
      )}

      <div className="mt-6">
        {isLoading && <p className="text-sm text-ink-400">Loading jobs…</p>}
        {jobs && jobs.length === 0 && !showForm && (
          <Card className="p-12 text-center">
            <p className="font-display text-lg text-ink-800">No jobs yet</p>
            <p className="mt-2 text-sm text-ink-500">Create your first requisition to get started.</p>
          </Card>
        )}
        <div className="flex flex-col gap-2">
          {jobs?.map((job) => (
            <Link key={job.id} to={`/jobs/${job.id}`}>
              <Card className="flex items-center justify-between p-4 transition-shadow hover:shadow-md">
                <span className="font-medium text-ink-800">{job.title}</span>
                <span
                  className={`rounded-full px-2.5 py-1 text-xs font-medium capitalize ${STATUS_STYLES[job.status]}`}
                >
                  {job.status.replace("_", " ")}
                </span>
              </Card>
            </Link>
          ))}
        </div>

        {pagination && pagination.total_pages > 1 && (
          <div className="mt-4 flex items-center justify-between text-sm text-ink-500">
            <span>
              Page {pagination.page} of {pagination.total_pages} — {pagination.total_items} total
            </span>
            <div className="flex gap-2">
              <Button
                variant="secondary"
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={pagination.page <= 1}
              >
                Previous
              </Button>
              <Button
                variant="secondary"
                onClick={() => setPage((p) => p + 1)}
                disabled={pagination.page >= pagination.total_pages}
              >
                Next
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
