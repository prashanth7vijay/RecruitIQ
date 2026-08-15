import { Link, useParams } from "react-router-dom";
import { useMyApplication, useMyInterviews } from "./useCandidatePortal";
import { Card } from "../../components/ui/Card";

export function CandidateApplicationDetailPage() {
  const { applicationId } = useParams();
  const { data: row, isLoading } = useMyApplication(applicationId);
  const { data: interviews } = useMyInterviews(applicationId);

  if (isLoading || !row) {
    return <div className="p-8 text-sm text-[var(--text-muted)]">Loading…</div>;
  }

  return (
    <div className="min-h-screen bg-[var(--surface)] px-4 py-10">
      <div className="mx-auto max-w-2xl">
        <Link to="/portal" className="text-sm text-[var(--text-muted)] hover:text-[var(--text-primary)]">
          ← All applications
        </Link>

        <h1 className="mt-4 font-display text-2xl text-[var(--text-primary)]">{row.job_title}</h1>
        <p className="mt-1 text-sm text-[var(--text-secondary)]">{row.company_name}</p>
        {row.stage_name && (
          <p className="mt-2 inline-block rounded-full bg-[var(--surface-hover)] px-3 py-1 text-xs text-[var(--text-secondary)]">
            Currently: {row.stage_name}
          </p>
        )}

        <div className="mt-8">
          <h2 className="font-display text-lg text-[var(--text-primary)]">Interviews</h2>
          {!interviews || interviews.length === 0 ? (
            <p className="mt-2 text-sm text-[var(--text-muted)]">No interviews scheduled yet.</p>
          ) : (
            <div className="mt-3 flex flex-col gap-2">
              {interviews.map((interview) => (
                <Card key={interview.id} className="p-4">
                  <p className="font-medium text-[var(--text-primary)]">{interview.round_name}</p>
                  <p className="mt-1 text-sm text-[var(--text-secondary)]">
                    {interview.scheduled_at
                      ? new Date(interview.scheduled_at).toLocaleString()
                      : "Time to be confirmed"}
                    {interview.duration_minutes && ` · ${interview.duration_minutes} min`}
                  </p>
                  {interview.meeting_link && (
                    <a
                      href={interview.meeting_link}
                      target="_blank"
                      rel="noreferrer"
                      className="mt-2 inline-block text-sm text-signal-600"
                    >
                      Join meeting
                    </a>
                  )}
                  <p className="mt-1 text-xs capitalize text-[var(--text-muted)]">{interview.status}</p>
                </Card>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
