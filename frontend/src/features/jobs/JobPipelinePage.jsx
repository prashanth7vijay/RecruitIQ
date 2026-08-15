import { useState } from "react";
import { useParams } from "react-router-dom";
import {
  useJob,
  usePipelineTemplate,
  useApplicationsForJob,
  useMoveApplicationStage,
  useApprovalSteps,
  useApproveStep,
  useCloseJob,
  useArchiveJob,
  useRejectApplication,
} from "./useJobs";
import { useSubmitForApproval } from "./useJobMutations";
import { useScheduleInterview } from "../interviews/useInterviews";
import { OfferPanel } from "../offers/OfferPanel";
import { JobDescriptionPanel } from "../ai/JobDescriptionPanel";
import { useComputeMatchScore, useRankCandidates } from "../ai/useAI";
import { useUsers } from "../users/useUsers";
import { useAuth } from "../../stores/AuthContext";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";

function ScheduleInterviewButton({ applicationId }) {
  const scheduleInterview = useScheduleInterview(applicationId);
  const { user } = useAuth();
  const { data: users } = useUsers();
  const [showPicker, setShowPicker] = useState(false);
  const [selectedIds, setSelectedIds] = useState(() => new Set(user?.id ? [user.id] : []));

  function toggleUser(id) {
    const next = new Set(selectedIds);
    next.has(id) ? next.delete(id) : next.add(id);
    setSelectedIds(next);
  }

  function handleSchedule() {
    scheduleInterview.mutate({
      roundName: "Technical Round",
      panelistUserIds: Array.from(selectedIds),
    });
  }

  if (scheduleInterview.isSuccess) {
    return <span className="mt-2 block text-xs text-signal-600">Interview scheduled ✓</span>;
  }

  if (!showPicker) {
    return (
      <button
        onClick={() => setShowPicker(true)}
        className="mt-2 block text-xs font-medium text-ink-500 hover:text-ink-700"
      >
        Schedule interview
      </button>
    );
  }

  return (
    <div className="mt-2 rounded-md border border-ink-100 bg-ink-50 p-2">
      <p className="text-xs font-medium text-ink-600">Panelists</p>
      <div className="mt-1 flex flex-col gap-1">
        {users?.map((u) => (
          <label key={u.id} className="flex items-center gap-1.5 text-xs text-ink-700">
            <input
              type="checkbox"
              checked={selectedIds.has(u.id)}
              onChange={() => toggleUser(u.id)}
              className="h-3.5 w-3.5 rounded border-ink-300 text-signal-500"
            />
            {u.first_name} {u.last_name}
            {u.id === user?.id && <span className="text-ink-400"> (you)</span>}
          </label>
        ))}
      </div>
      <button
        onClick={handleSchedule}
        disabled={scheduleInterview.isPending || selectedIds.size === 0}
        className="mt-2 text-xs font-medium text-signal-600 hover:text-signal-700 disabled:opacity-50"
      >
        {scheduleInterview.isPending ? "Scheduling…" : "Confirm"}
      </button>
    </div>
  );
}

function PendingApprovalPanel({ jobId }) {
  const { data: steps } = useApprovalSteps(jobId, true);
  const approveStep = useApproveStep(jobId);
  const { hasPermission } = useAuth();

  const pendingSteps = steps?.filter((s) => s.status === "pending") ?? [];

  if (!steps) return null;

  return (
    <Card className="mt-4 p-4">
      <p className="text-sm font-medium text-ink-800">Pending approval</p>
      <div className="mt-2 flex flex-col gap-2">
        {steps.map((step) => (
          <div key={step.id} className="flex items-center justify-between text-sm">
            <span className="capitalize text-ink-600">
              {(step.approver_role_name ?? "unassigned").replace("_", " ")}
            </span>
            {step.status === "pending" ? (
              hasPermission("job.approve") ? (
                <Button
                  variant="secondary"
                  onClick={() => approveStep.mutate(step.id)}
                  disabled={approveStep.isPending}
                >
                  {approveStep.isPending ? "Approving…" : "Approve"}
                </Button>
              ) : (
                <span className="text-xs text-ink-400">Awaiting approval</span>
              )
            ) : (
              <span className="text-xs capitalize text-signal-600">{step.status}</span>
            )}
          </div>
        ))}
      </div>
      {pendingSteps.length === 0 && steps.length > 0 && (
        <p className="mt-2 text-xs text-ink-400">All steps resolved — refresh if the job hasn't published yet.</p>
      )}
    </Card>
  );
}

function MatchScoreBadge({ application, jobId }) {
  const computeMatchScore = useComputeMatchScore(jobId);
  // Prefer the persisted score on the application itself (survives a
  // page reload) over this mutation's own local result, which only
  // exists for the rest of this browser session.
  const score = application.match_score ?? computeMatchScore.data?.score;
  const explanation = computeMatchScore.data?.explanation;

  if (score != null) {
    return (
      <div className="mt-1 rounded-md bg-signal-50 px-2 py-1 text-xs text-signal-700">
        <span className="font-medium">{score}% match</span>
        {explanation && <> — {explanation}</>}
      </div>
    );
  }

  return (
    <button
      onClick={() => computeMatchScore.mutate(application.id)}
      disabled={computeMatchScore.isPending}
      className="text-xs font-medium text-ink-500 hover:text-ink-700 disabled:opacity-50"
    >
      {computeMatchScore.isPending ? "Scoring…" : "Compute match score"}
    </button>
  );
}

function ApplicationCard({ application, jobId, index, template }) {
  const moveStage = useMoveApplicationStage(jobId);
  const rejectApplication = useRejectApplication(jobId);
  const nextStage = template?.stages[index + 1];

  return (
    <Card className="p-3">
      <p className="text-sm font-medium text-ink-800">
        {application.candidate.first_name} {application.candidate.last_name}
      </p>
      <p className="text-xs text-ink-500">{application.candidate.email}</p>
      <MatchScoreBadge application={application} jobId={jobId} />
      <div className="mt-2 flex flex-col items-start gap-1">
        {nextStage && (
          <button
            onClick={() =>
              moveStage.mutate({ applicationId: application.id, targetStageId: nextStage.id })
            }
            disabled={moveStage.isPending}
            className="text-xs font-medium text-signal-600 hover:text-signal-700"
          >
            Move to {nextStage.name} →
          </button>
        )}
        <ScheduleInterviewButton applicationId={application.id} />
        {!rejectApplication.isSuccess && (
          <button
            onClick={() => rejectApplication.mutate({ applicationId: application.id })}
            disabled={rejectApplication.isPending}
            className="text-xs font-medium text-red-500 hover:text-red-600"
          >
            {rejectApplication.isPending ? "Rejecting…" : "Reject"}
          </button>
        )}
        {rejectApplication.isSuccess && <span className="text-xs text-red-500">Rejected</span>}
      </div>
      <OfferPanel applicationId={application.id} />
    </Card>
  );
}

export function JobPipelinePage() {
  const { jobId } = useParams();
  const { data: job, isLoading: jobLoading } = useJob(jobId);
  const { data: template } = usePipelineTemplate(job?.pipeline_template_id);
  const { data: applications } = useApplicationsForJob(jobId);
  const { hasPermission } = useAuth();
  const submitForApproval = useSubmitForApproval();
  const closeJob = useCloseJob(jobId);
  const archiveJob = useArchiveJob(jobId);
  const rankCandidates = useRankCandidates(jobId);
  const [submitError, setSubmitError] = useState(null);
  const [rankError, setRankError] = useState(null);

  if (jobLoading || !job) {
    return <div className="text-sm text-ink-400">Loading…</div>;
  }

  const applicationsByStage = (stageId) =>
    applications?.filter((a) => a.current_stage_id === stageId && a.status === "active") ?? [];

  async function handleSubmitForApproval() {
    setSubmitError(null);
    try {
      await submitForApproval.mutateAsync({ jobId });
    } catch (err) {
      setSubmitError(
        err.response?.data?.error?.message ??
          "Could not submit for approval. An admin may need to configure an approval chain first."
      );
    }
  }

  async function handleRankCandidates() {
    setRankError(null);
    try {
      await rankCandidates.mutateAsync(false);
    } catch (err) {
      setRankError(err.response?.data?.error?.message ?? "Could not rank candidates.");
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-2xl text-ink-900">{job.title}</h1>
          <p className="mt-1 text-sm capitalize text-ink-500">{job.status.replace("_", " ")}</p>
          {submitError && <p className="mt-2 text-sm text-red-600">{submitError}</p>}
        </div>
        <div className="flex gap-2">
          {job.status === "draft" && hasPermission("job.create") && (
            <Button
              onClick={handleSubmitForApproval}
              disabled={submitForApproval.isPending || !job.pipeline_template_id}
            >
              {submitForApproval.isPending ? "Submitting…" : "Submit for approval"}
            </Button>
          )}
          {job.status === "published" && hasPermission("job.close") && (
            <Button variant="secondary" onClick={() => closeJob.mutate()} disabled={closeJob.isPending}>
              {closeJob.isPending ? "Closing…" : "Close job"}
            </Button>
          )}
          {job.status === "closed" && hasPermission("job.close") && (
            <Button variant="secondary" onClick={() => archiveJob.mutate()} disabled={archiveJob.isPending}>
              {archiveJob.isPending ? "Archiving…" : "Archive"}
            </Button>
          )}
          {hasPermission("candidate.view_all") && applications?.length > 0 && (
            <Button variant="secondary" onClick={handleRankCandidates} disabled={rankCandidates.isPending}>
              {rankCandidates.isPending ? "Ranking…" : "Rank candidates"}
            </Button>
          )}
        </div>
      </div>
      {rankError && <p className="mt-2 text-sm text-red-600">{rankError}</p>}

      {!job.pipeline_template_id && (
        <p className="mt-4 rounded-md bg-amber-50 px-4 py-3 text-sm text-amber-700">
          This job has no pipeline template assigned — it can't be submitted or receive
          applications until one is set.
        </p>
      )}

      <JobDescriptionPanel job={job} />

      {job.status === "pending_approval" && <PendingApprovalPanel jobId={jobId} />}

      {job.status !== "published" && job.status !== "closed" && job.status !== "pending_approval" && (
        <p className="mt-4 text-sm text-ink-400">
          The pipeline board becomes active once this job is published.
        </p>
      )}

      {template && (job.status === "published" || job.status === "closed") && (
        <div className="mt-8 grid grid-cols-1 gap-4 md:grid-cols-3">
          {template.stages.map((stage, index) => (
            <div key={stage.id}>
              <h2 className="mb-2 text-xs font-semibold uppercase tracking-wide text-ink-500">
                {stage.name} ({applicationsByStage(stage.id).length})
              </h2>
              <div className="flex flex-col gap-2">
                {applicationsByStage(stage.id).map((application) => (
                  <ApplicationCard
                    key={application.id}
                    application={application}
                    jobId={jobId}
                    index={index}
                    template={template}
                  />
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
