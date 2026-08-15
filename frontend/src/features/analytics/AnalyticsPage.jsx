import { useState } from "react";
import { useJobs } from "../jobs/useJobs";
import {
  useHiringFunnel,
  useTimeToHire,
  useRecruiterPerformance,
  useHiringVelocity,
  usePipelineHealth,
  useOfferAcceptanceRate,
  useDepartmentHiring,
} from "./useAnalytics";
import { Card } from "../../components/ui/Card";

const STAGE_TYPE_LABELS = {
  screening: "Screening",
  interview: "Interview",
  assessment: "Assessment",
  offer: "Offer",
  terminal: "Terminal",
};

function MetricCard({ label, value, sublabel }) {
  return (
    <Card className="p-5">
      <p className="text-xs uppercase tracking-wide text-[var(--text-muted)]">{label}</p>
      <p className="mt-2 text-3xl font-semibold text-[var(--text-primary)]">{value}</p>
      {sublabel && <p className="mt-1 text-xs text-[var(--text-muted)]">{sublabel}</p>}
    </Card>
  );
}

function FunnelChart({ jobId }) {
  const { data: funnel, isLoading } = useHiringFunnel(jobId);

  if (isLoading) return <p className="text-sm text-[var(--text-muted)]">Loading funnel…</p>;
  if (!funnel || funnel.length === 0) {
    return <p className="text-sm text-[var(--text-muted)]">No pipeline data for this job yet.</p>;
  }

  const max = Math.max(...funnel.map((f) => f.candidate_count), 1);

  return (
    <div className="flex flex-col gap-3">
      {funnel.map((stage) => (
        <div key={stage.stage_id}>
          <div className="flex justify-between text-xs text-[var(--text-secondary)]">
            <span>{stage.stage_name}</span>
            <span>{stage.candidate_count}</span>
          </div>
          <div className="mt-1 h-3 w-full rounded-full bg-[var(--surface-hover)]">
            <div
              className="h-3 rounded-full bg-signal-400"
              style={{ width: `${(stage.candidate_count / max) * 100}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}

function PipelineHealthCard() {
  const { data: health, isLoading } = usePipelineHealth();

  if (isLoading) return <Card className="p-6"><p className="text-sm text-[var(--text-muted)]">Loading…</p></Card>;

  const stages = health?.by_stage_type ?? [];
  const max = Math.max(...stages.map((s) => s.candidate_count), 1);

  return (
    <Card className="p-6">
      <h2 className="font-display text-lg text-[var(--text-primary)]">Pipeline health</h2>
      <p className="mt-1 text-xs text-[var(--text-muted)]">
        Active candidates across every job, by stage type. Avg{" "}
        {health?.avg_days_in_current_stage != null ? `${health.avg_days_in_current_stage} days` : "—"} in current stage.
      </p>
      <div className="mt-4 flex flex-col gap-3">
        {stages.length === 0 && <p className="text-sm text-[var(--text-muted)]">No active candidates yet.</p>}
        {stages.map((s) => (
          <div key={s.stage_type}>
            <div className="flex justify-between text-xs text-[var(--text-secondary)]">
              <span>{STAGE_TYPE_LABELS[s.stage_type] ?? s.stage_type}</span>
              <span>{s.candidate_count}</span>
            </div>
            <div className="mt-1 h-3 w-full rounded-full bg-[var(--surface-hover)]">
              <div
                className="h-3 rounded-full bg-signal-400"
                style={{ width: `${(s.candidate_count / max) * 100}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}

function DepartmentHiringCard() {
  const { data: departments, isLoading } = useDepartmentHiring();

  return (
    <Card className="p-6">
      <h2 className="font-display text-lg text-[var(--text-primary)]">Hiring by department</h2>
      <div className="mt-4 flex flex-col gap-1">
        {isLoading && <p className="text-sm text-[var(--text-muted)]">Loading…</p>}
        {departments?.length === 0 && (
          <p className="text-sm text-[var(--text-muted)]">No department-assigned jobs yet.</p>
        )}
        {departments?.map((d) => (
          <div
            key={d.department_id}
            className="flex justify-between rounded-md bg-[var(--surface-hover)] px-3 py-2 text-sm text-[var(--text-secondary)]"
          >
            <span className="font-medium text-[var(--text-primary)]">{d.department_name}</span>
            <span>
              {d.job_count} open · {d.hires} hired
            </span>
          </div>
        ))}
      </div>
    </Card>
  );
}

function RecruiterPerformanceCard() {
  const { data: recruiterPerf, isLoading } = useRecruiterPerformance();

  return (
    <Card className="p-6">
      <h2 className="font-display text-lg text-[var(--text-primary)]">Recruiter performance</h2>
      <div className="mt-3 flex flex-col gap-1">
        {isLoading && <p className="text-sm text-[var(--text-muted)]">Loading…</p>}
        {recruiterPerf?.length === 0 && <p className="text-sm text-[var(--text-muted)]">No data yet.</p>}
        {recruiterPerf?.map((r) => (
          <div
            key={r.recruiter_id}
            className="flex items-center justify-between border-b border-[var(--border)] py-2 text-sm last:border-0"
          >
            <span className="font-medium text-[var(--text-primary)]">{r.recruiter_name}</span>
            <span className="text-[var(--text-secondary)]">
              {r.application_count} applications · {r.offers_sent} offers · {r.hires} hires
            </span>
          </div>
        ))}
      </div>
    </Card>
  );
}

export function AnalyticsPage() {
  const { data: jobs } = useJobs();
  const [selectedJobId, setSelectedJobId] = useState("");
  const { data: timeToHire } = useTimeToHire(selectedJobId || undefined);
  const { data: velocity } = useHiringVelocity(30);
  const { data: offerAcceptance } = useOfferAcceptanceRate();

  return (
    <div className="mx-auto max-w-4xl">
      <h1 className="font-display text-2xl text-[var(--text-primary)]">Analytics</h1>
      <p className="mt-1 text-sm text-[var(--text-secondary)]">
        Hiring velocity, pipeline health, and recruiter performance across your organization.
      </p>

      <div className="mt-6 grid grid-cols-2 gap-4 sm:grid-cols-4">
        <MetricCard
          label="Jobs published (30d)"
          value={velocity?.jobs_published ?? "—"}
        />
        <MetricCard label="Hires (30d)" value={velocity?.hires ?? "—"} />
        <MetricCard
          label="Avg. time to hire"
          value={timeToHire?.avg_days_to_hire != null ? `${timeToHire.avg_days_to_hire}d` : "—"}
        />
        <MetricCard
          label="Offer acceptance"
          value={
            offerAcceptance?.acceptance_rate != null
              ? `${Math.round(offerAcceptance.acceptance_rate * 100)}%`
              : "—"
          }
          sublabel={
            offerAcceptance
              ? `${offerAcceptance.accepted} accepted · ${offerAcceptance.rejected} declined · ${offerAcceptance.expired} expired`
              : undefined
          }
        />
      </div>

      <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-2">
        <PipelineHealthCard />
        <DepartmentHiringCard />
      </div>

      <div className="mt-6">
        <RecruiterPerformanceCard />
      </div>

      <Card className="mt-6 p-6">
        <div className="flex items-center justify-between">
          <h2 className="font-display text-lg text-[var(--text-primary)]">Hiring funnel by job</h2>
          <select
            value={selectedJobId}
            onChange={(e) => setSelectedJobId(e.target.value)}
            className="rounded-md border border-[var(--border)] bg-[var(--surface-raised)] px-3 py-2 text-sm text-[var(--text-primary)]"
          >
            <option value="">Select a job…</option>
            {jobs?.map((job) => (
              <option key={job.id} value={job.id}>
                {job.title}
              </option>
            ))}
          </select>
        </div>
        <div className="mt-4">
          {selectedJobId ? (
            <FunnelChart jobId={selectedJobId} />
          ) : (
            <p className="text-sm text-[var(--text-muted)]">Pick a job to see its stage-by-stage funnel.</p>
          )}
        </div>
      </Card>
    </div>
  );
}
