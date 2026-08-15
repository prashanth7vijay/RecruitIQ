import { FONT_STACKS } from "./useApplyBranding";

export function CareerBrandHeader({ company, isLoading }) {
  const branding = company?.branding ?? {};
  const headingFont = FONT_STACKS[branding.font_heading] ?? FONT_STACKS.fraunces;

  return (
    <header
      className="border-b border-[var(--border)] px-8 py-10"
      style={
        branding.cover_image_url
          ? {
              backgroundImage: `linear-gradient(0deg, var(--surface-raised) 0%, rgba(0,0,0,0.35) 100%), url(${branding.cover_image_url})`,
              backgroundSize: "cover",
              backgroundPosition: "center",
            }
          : { backgroundColor: "var(--surface-raised)" }
      }
    >
      <div className="mx-auto flex max-w-3xl items-center gap-4">
        {branding.logo_url && (
          <img src={branding.logo_url} alt={`${company?.name ?? ""} logo`} className="h-12 w-12 rounded-md bg-white/90 object-contain p-1" />
        )}
        <div>
          <p
            className="text-xs uppercase tracking-widest"
            style={{ color: branding.primary_color || undefined }}
          >
            Careers
          </p>
          <h1 style={{ fontFamily: headingFont }} className="mt-1 text-3xl text-[var(--text-primary)]">
            {isLoading ? "Loading…" : branding.careers_headline || `Work at ${company?.name ?? ""}`}
          </h1>
          {branding.careers_description && (
            <p className="mt-2 max-w-xl text-sm text-[var(--text-secondary)]">{branding.careers_description}</p>
          )}
        </div>
      </div>
    </header>
  );
}
