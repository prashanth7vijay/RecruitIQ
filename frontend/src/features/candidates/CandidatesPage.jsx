import { useState, Fragment } from "react";
import { useCandidates } from "./useCandidates";
import { CandidateCRMPanel } from "./CandidateCRMPanel";
import { ResumeLink } from "./ResumeLink";
import { useAuth } from "../../stores/AuthContext";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";

export function CandidatesPage() {
  const [page, setPage] = useState(1);
  const { data, isLoading, isError, error } = useCandidates(page);
  const { hasPermission } = useAuth();
  const [expandedId, setExpandedId] = useState(null);

  const candidates = data?.items;
  const pagination = data?.pagination;

  return (
    <div className="mx-auto max-w-4xl">
      <div>
        <h1 className="font-display text-2xl text-ink-900">Candidates</h1>
        <p className="mt-1 text-sm text-ink-500">
          Everyone who's applied — nobody disappears after a "no." Candidates create their own
          profiles by applying; use notes, tags, and pools below to organize them.
        </p>
      </div>

      <div className="mt-6">
        {isLoading && <p className="text-sm text-ink-400">Loading candidates…</p>}

        {isError && (
          <p className="rounded-md bg-red-50 px-4 py-3 text-sm text-red-700">
            {error.response?.data?.error?.message ?? "Could not load candidates."}
          </p>
        )}

        {candidates && candidates.length === 0 && (
          <Card className="flex flex-col items-center gap-3 p-12 text-center">
            <p className="font-display text-lg text-ink-800">No candidates yet</p>
            <p className="max-w-sm text-sm text-ink-500">
              Candidates show up here once someone applies to one of your published jobs, or an
              employee referral turns into an application.
            </p>
          </Card>
        )}

        {candidates && candidates.length > 0 && (
          <>
            <Card>
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-ink-100 text-xs uppercase tracking-wide text-ink-400">
                    <th className="px-4 py-3 font-medium">Name</th>
                    <th className="px-4 py-3 font-medium">Email</th>
                    <th className="px-4 py-3 font-medium">Location</th>
                    <th className="px-4 py-3 font-medium">Resume</th>
                    <th className="px-4 py-3 font-medium"></th>
                  </tr>
                </thead>
                <tbody>
                  {candidates.map((profile) => (
                    <Fragment key={profile.id}>
                      <tr className="border-b border-ink-50 last:border-0">
                        <td className="px-4 py-3 font-medium text-ink-800">
                          {profile.candidate.first_name} {profile.candidate.last_name}
                        </td>
                        <td className="px-4 py-3 text-ink-500">{profile.candidate.email}</td>
                        <td className="px-4 py-3 text-ink-500">
                          {profile.current_location ?? "—"}
                        </td>
                        <td className="px-4 py-3">
                          {profile.resume_id ? (
                            <ResumeLink profileId={profile.id} />
                          ) : (
                            <span className="text-xs text-ink-400">Not provided</span>
                          )}
                        </td>
                        <td className="px-4 py-3">
                          {hasPermission("candidate.manage") && (
                            <button
                              onClick={() => setExpandedId(expandedId === profile.id ? null : profile.id)}
                              className="text-xs font-medium text-ink-500 hover:text-ink-700"
                            >
                              {expandedId === profile.id ? "Hide" : "Notes, tags & pools"}
                            </button>
                          )}
                        </td>
                      </tr>
                      {expandedId === profile.id && (
                        <tr>
                          <td colSpan={5} className="p-0">
                            <CandidateCRMPanel profileId={profile.id} />
                          </td>
                        </tr>
                      )}
                    </Fragment>
                  ))}
                </tbody>
              </table>
            </Card>

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
          </>
        )}
      </div>
    </div>
  );
}