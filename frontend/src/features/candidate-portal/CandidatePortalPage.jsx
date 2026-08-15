import { Link } from "react-router-dom";
import { useCandidateAuth } from "../../stores/CandidateAuthContext";
import { useMyApplications, useMyOffers, useAcceptMyOffer, useDeclineMyOffer } from "./useCandidatePortal";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";

const STATUS_LABELS = {
  active: "In progress",
  hired: "Hired",
  rejected: "Not moving forward",
  withdrawn: "Withdrawn",
};

function OffersSection() {
  const { data: offers, isLoading } = useMyOffers();
  const acceptOffer = useAcceptMyOffer();
  const declineOffer = useDeclineMyOffer();

  if (isLoading || !offers || offers.length === 0) return null;

  return (
    <div className="mb-6">
      <h2 className="font-display text-lg text-[var(--text-primary)]">Your offers</h2>
      <div className="mt-3 flex flex-col gap-2">
        {offers.map((row) => (
          <Card key={row.id} className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-[var(--text-primary)]">
                  {row.job_title} at {row.company_name}
                </p>
                <p className="text-sm text-[var(--text-secondary)]">
                  {row.salary_offered && `$${Number(row.salary_offered).toLocaleString()}`}
                  {row.joining_date && ` · Starts ${row.joining_date}`}
                </p>
              </div>
              {row.status === "sent" ? (
                <div className="flex gap-2">
                  <Button onClick={() => acceptOffer.mutate(row.id)} disabled={acceptOffer.isPending}>
                    Accept
                  </Button>
                  <Button
                    variant="secondary"
                    onClick={() => declineOffer.mutate(row.id)}
                    disabled={declineOffer.isPending}
                  >
                    Decline
                  </Button>
                </div>
              ) : (
                <span className="rounded-full bg-[var(--surface-hover)] px-3 py-1 text-xs capitalize text-[var(--text-secondary)]">
                  {row.status}
                </span>
              )}
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}

export function CandidatePortalPage() {
  const { logout } = useCandidateAuth();
  const { data: applications, isLoading } = useMyApplications();

  return (
    <div className="min-h-screen bg-[var(--surface)] px-4 py-10">
      <div className="mx-auto max-w-2xl">
        <div className="flex items-center justify-between">
          <h1 className="font-display text-2xl text-[var(--text-primary)]">Your applications</h1>
          <button onClick={logout} className="text-sm text-[var(--text-muted)] hover:text-[var(--text-primary)]">
            Sign out
          </button>
        </div>

        <div className="mt-6">
          <OffersSection />

          {isLoading && <p className="text-sm text-[var(--text-muted)]">Loading…</p>}
          {applications?.length === 0 && (
            <p className="text-sm text-[var(--text-muted)]">
              No applications yet — once you apply to a role, it'll show up here.
            </p>
          )}

          <div className="flex flex-col gap-2">
            {applications?.map((row) => (
              <Link key={row.id} to={`/portal/applications/${row.id}`}>
                <Card className="p-4 transition-shadow hover:shadow-panel">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium text-[var(--text-primary)]">{row.job_title}</p>
                      <p className="text-sm text-[var(--text-secondary)]">{row.company_name}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm text-[var(--text-secondary)]">
                        {STATUS_LABELS[row.status] ?? row.status}
                      </p>
                      {row.stage_name && row.status === "active" && (
                        <p className="text-xs text-[var(--text-muted)]">Currently: {row.stage_name}</p>
                      )}
                    </div>
                  </div>
                </Card>
              </Link>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
