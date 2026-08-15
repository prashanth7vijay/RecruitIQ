import { Link, useParams } from "react-router-dom";
import { usePublicJobs, usePublicCompany } from "./usePublicJobs";
import { useApplyBranding } from "./useApplyBranding";
import { CareerBrandHeader } from "./CareerBrandHeader";

const SOCIAL_LABELS = {
  linkedin: "LinkedIn",
  twitter: "X / Twitter",
  instagram: "Instagram",
  facebook: "Facebook",
  glassdoor: "Glassdoor",
  youtube: "YouTube",
};

export function CareersPage() {
  const { companySlug } = useParams();
  const { data: jobs, isLoading, isError } = usePublicJobs(companySlug);
  const { data: company, isLoading: isCompanyLoading } = usePublicCompany(companySlug);
  useApplyBranding(company);

  const socialLinks = Object.entries(company?.branding?.social_links ?? {});
  const primaryColor = company?.branding?.primary_color;

  return (
    <div className="min-h-screen bg-[var(--surface)]">
      <CareerBrandHeader company={company} isLoading={isCompanyLoading} />

      <main className="mx-auto max-w-3xl px-8 py-10">
        {isLoading && <p className="text-sm text-[var(--text-muted)]">Loading open roles…</p>}
        {isError && (
          <p className="rounded-md bg-red-50 px-4 py-3 text-sm text-red-700">
            Could not load open roles for this organization.
          </p>
        )}
        {jobs && jobs.length === 0 && (
          <p className="text-sm text-[var(--text-secondary)]">No open roles right now — check back soon.</p>
        )}

        <ul className="flex flex-col gap-3">
          {jobs?.map((job) => (
            <li key={job.id}>
              <Link
                to={`/careers/${companySlug}/jobs/${job.id}`}
                className="block rounded-lg border border-[var(--border)] bg-[var(--surface-raised)] p-5 transition-shadow hover:shadow-panel"
              >
                <p className="font-display text-lg text-[var(--text-primary)]">{job.title}</p>
                <div className="mt-2 flex gap-3 text-xs text-[var(--text-muted)]">
                  {job.employment_type && (
                    <span
                      className="rounded-full px-2 py-0.5 capitalize text-white"
                      style={{ backgroundColor: primaryColor || "var(--accent)" }}
                    >
                      {job.employment_type}
                    </span>
                  )}
                  {job.salary_min && job.salary_max && (
                    <span className="self-center">
                      ${Number(job.salary_min).toLocaleString()} – $
                      {Number(job.salary_max).toLocaleString()}
                    </span>
                  )}
                </div>
              </Link>
            </li>
          ))}
        </ul>

        {socialLinks.length > 0 && (
          <div className="mt-10 flex gap-4 border-t border-[var(--border)] pt-6 text-xs text-[var(--text-muted)]">
            {socialLinks.map(([platform, url]) => (
              <a key={platform} href={url} target="_blank" rel="noreferrer" className="hover:text-[var(--text-primary)]">
                {SOCIAL_LABELS[platform] ?? platform}
              </a>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
