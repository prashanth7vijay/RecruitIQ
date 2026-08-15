import { useEffect, useRef, useState } from "react";
import { useAuth } from "../../stores/AuthContext";
import { useBranding, useUpdateBranding, useUploadBrandingAsset } from "./useBranding";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Input } from "../../components/ui/Input";
import { Textarea } from "../../components/ui/Textarea";
import { UploadIcon } from "../../components/icons";

const FONT_OPTIONS = [
  { value: "inter", label: "Inter", stack: "'Inter', system-ui, sans-serif" },
  { value: "fraunces", label: "Fraunces", stack: "'Fraunces', serif" },
  { value: "poppins", label: "Poppins", stack: "'Poppins', system-ui, sans-serif" },
  { value: "sora", label: "Sora", stack: "'Sora', system-ui, sans-serif" },
  { value: "ibm-plex-sans", label: "IBM Plex Sans", stack: "'IBM Plex Sans', system-ui, sans-serif" },
  { value: "merriweather", label: "Merriweather", stack: "'Merriweather', serif" },
  { value: "playfair-display", label: "Playfair Display", stack: "'Playfair Display', serif" },
  { value: "space-grotesk", label: "Space Grotesk", stack: "'Space Grotesk', system-ui, sans-serif" },
];

const SOCIAL_PLATFORMS = ["linkedin", "twitter", "instagram", "facebook", "glassdoor", "youtube"];

function fontStack(value) {
  return FONT_OPTIONS.find((f) => f.value === value)?.stack ?? "'Inter', system-ui, sans-serif";
}

function AssetUploader({ label, assetType, currentUrl, onUpload, isUploading, disabled, aspect = "square" }) {
  const inputRef = useRef(null);
  return (
    <div>
      <p className="text-sm font-medium text-[var(--text-primary)]">{label}</p>
      <div
        className={`mt-2 flex items-center justify-center overflow-hidden rounded-lg border border-dashed border-[var(--border)] bg-[var(--surface)] ${
          aspect === "square" ? "h-24 w-24" : "h-24 w-full"
        }`}
      >
        {currentUrl ? (
          <img src={currentUrl} alt={label} className="h-full w-full object-contain" />
        ) : (
          <span className="text-xs text-[var(--text-muted)]">No {label.toLowerCase()}</span>
        )}
      </div>
      <input
        ref={inputRef}
        type="file"
        accept="image/png,image/jpeg,image/gif,image/webp,image/svg+xml"
        className="hidden"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) onUpload(assetType, file);
          e.target.value = "";
        }}
      />
      <Button
        type="button"
        variant="secondary"
        className="mt-2 w-full"
        disabled={disabled || isUploading}
        onClick={() => inputRef.current?.click()}
      >
        <UploadIcon className="h-4 w-4" />
        {isUploading ? "Uploading…" : currentUrl ? "Replace" : "Upload"}
      </Button>
    </div>
  );
}

export function BrandingCenterPage() {
  const { hasPermission } = useAuth();
  const canEdit = hasPermission("company.manage_settings");

  const { data: branding, isLoading } = useBranding();
  const updateBranding = useUpdateBranding();
  const uploadAsset = useUploadBrandingAsset();

  const [form, setForm] = useState(null);
  const [error, setError] = useState(null);
  const [saved, setSaved] = useState(false);
  const [uploadingAsset, setUploadingAsset] = useState(null);

  useEffect(() => {
    if (branding) {
      setForm({
        primary_color: branding.primary_color ?? "#2f8c81",
        secondary_color: branding.secondary_color ?? "#171c20",
        font_heading: branding.font_heading ?? "fraunces",
        font_body: branding.font_body ?? "inter",
        mission: branding.mission ?? "",
        vision: branding.vision ?? "",
        culture: branding.culture ?? "",
        careers_headline: branding.careers_headline ?? "",
        careers_description: branding.careers_description ?? "",
        social_links: branding.social_links ?? {},
        seo_title: branding.seo_title ?? "",
        seo_description: branding.seo_description ?? "",
      });
    }
  }, [branding]);

  function setField(key, value) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  function setSocialLink(platform, value) {
    setForm((f) => ({ ...f, social_links: { ...f.social_links, [platform]: value } }));
  }

  async function handleUpload(assetType, file) {
    setError(null);
    setUploadingAsset(assetType);
    try {
      await uploadAsset.mutateAsync({ assetType, file });
    } catch (err) {
      setError(err.response?.data?.error?.message ?? "Could not upload image.");
    } finally {
      setUploadingAsset(null);
    }
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setSaved(false);
    const cleanedSocialLinks = Object.fromEntries(
      Object.entries(form.social_links).filter(([, v]) => v && v.trim().length > 0)
    );
    try {
      await updateBranding.mutateAsync({ ...form, social_links: cleanedSocialLinks });
      setSaved(true);
    } catch (err) {
      setError(
        err.response?.status === 403
          ? "You don't have permission to change branding."
          : err.response?.data?.error?.message ?? "Could not save changes."
      );
    }
  }

  if (isLoading || !form) {
    return <p className="text-sm text-[var(--text-muted)]">Loading branding…</p>;
  }

  const fieldsetProps = { disabled: !canEdit };

  return (
    <div className="mx-auto max-w-5xl">
      <div>
        <h1 className="font-display text-2xl text-[var(--text-primary)]">Branding Center</h1>
        <p className="mt-1 text-sm text-[var(--text-secondary)]">
          Controls how your organization looks on the public career page — logo, colors, typography, and copy.
        </p>
      </div>

      {!canEdit && (
        <p className="mt-4 rounded-md border border-[var(--border)] bg-[var(--surface-hover)] px-3 py-2 text-sm text-[var(--text-secondary)]">
          You can view branding but don't have permission to make changes.
        </p>
      )}

      <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-[1fr_360px]">
        <form onSubmit={handleSubmit}>
          <fieldset {...fieldsetProps} className="flex flex-col gap-6 disabled:opacity-70">
            <Card className="p-6">
              <p className="font-display text-lg text-[var(--text-primary)]">Assets</p>
              <div className="mt-4 grid grid-cols-3 gap-4">
                <AssetUploader
                  label="Logo"
                  assetType="logo"
                  currentUrl={branding.logo_url}
                  onUpload={handleUpload}
                  isUploading={uploadingAsset === "logo"}
                  disabled={!canEdit}
                />
                <AssetUploader
                  label="Favicon"
                  assetType="favicon"
                  currentUrl={branding.favicon_url}
                  onUpload={handleUpload}
                  isUploading={uploadingAsset === "favicon"}
                  disabled={!canEdit}
                />
                <AssetUploader
                  label="Cover image"
                  assetType="cover"
                  currentUrl={branding.cover_image_url}
                  onUpload={handleUpload}
                  isUploading={uploadingAsset === "cover"}
                  disabled={!canEdit}
                  aspect="wide"
                />
              </div>
            </Card>

            <Card className="p-6">
              <p className="font-display text-lg text-[var(--text-primary)]">Colors & typography</p>
              <div className="mt-4 grid grid-cols-2 gap-4">
                <div className="flex flex-col gap-1.5">
                  <label className="text-sm font-medium text-[var(--text-primary)]">Primary color</label>
                  <div className="flex items-center gap-2">
                    <input
                      type="color"
                      value={form.primary_color}
                      onChange={(e) => setField("primary_color", e.target.value)}
                      className="h-9 w-9 shrink-0 cursor-pointer rounded border border-[var(--border)] bg-transparent"
                    />
                    <Input
                      value={form.primary_color}
                      onChange={(e) => setField("primary_color", e.target.value)}
                    />
                  </div>
                </div>
                <div className="flex flex-col gap-1.5">
                  <label className="text-sm font-medium text-[var(--text-primary)]">Secondary color</label>
                  <div className="flex items-center gap-2">
                    <input
                      type="color"
                      value={form.secondary_color}
                      onChange={(e) => setField("secondary_color", e.target.value)}
                      className="h-9 w-9 shrink-0 cursor-pointer rounded border border-[var(--border)] bg-transparent"
                    />
                    <Input
                      value={form.secondary_color}
                      onChange={(e) => setField("secondary_color", e.target.value)}
                    />
                  </div>
                </div>

                <div className="flex flex-col gap-1.5">
                  <label className="text-sm font-medium text-[var(--text-primary)]">Heading font</label>
                  <select
                    value={form.font_heading}
                    onChange={(e) => setField("font_heading", e.target.value)}
                    className="rounded-md border border-[var(--border)] bg-[var(--surface-raised)] px-3 py-2 text-sm text-[var(--text-primary)]"
                  >
                    {FONT_OPTIONS.map((f) => (
                      <option key={f.value} value={f.value}>
                        {f.label}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="flex flex-col gap-1.5">
                  <label className="text-sm font-medium text-[var(--text-primary)]">Body font</label>
                  <select
                    value={form.font_body}
                    onChange={(e) => setField("font_body", e.target.value)}
                    className="rounded-md border border-[var(--border)] bg-[var(--surface-raised)] px-3 py-2 text-sm text-[var(--text-primary)]"
                  >
                    {FONT_OPTIONS.map((f) => (
                      <option key={f.value} value={f.value}>
                        {f.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </Card>

            <Card className="p-6">
              <p className="font-display text-lg text-[var(--text-primary)]">Company story</p>
              <div className="mt-4 flex flex-col gap-4">
                <Textarea
                  label="Mission"
                  rows={3}
                  value={form.mission}
                  onChange={(e) => setField("mission", e.target.value)}
                  maxLength={2000}
                />
                <Textarea
                  label="Vision"
                  rows={3}
                  value={form.vision}
                  onChange={(e) => setField("vision", e.target.value)}
                  maxLength={2000}
                />
                <Textarea
                  label="Culture"
                  rows={3}
                  value={form.culture}
                  onChange={(e) => setField("culture", e.target.value)}
                  maxLength={2000}
                />
              </div>
            </Card>

            <Card className="p-6">
              <p className="font-display text-lg text-[var(--text-primary)]">Career page</p>
              <div className="mt-4 flex flex-col gap-4">
                <Input
                  label="Headline"
                  value={form.careers_headline}
                  onChange={(e) => setField("careers_headline", e.target.value)}
                  maxLength={200}
                  placeholder="Build the future of hiring with us"
                />
                <Textarea
                  label="Description"
                  rows={4}
                  value={form.careers_description}
                  onChange={(e) => setField("careers_description", e.target.value)}
                  maxLength={5000}
                />
              </div>
            </Card>

            <Card className="p-6">
              <p className="font-display text-lg text-[var(--text-primary)]">Social links</p>
              <div className="mt-4 grid grid-cols-2 gap-4">
                {SOCIAL_PLATFORMS.map((platform) => (
                  <Input
                    key={platform}
                    label={platform[0].toUpperCase() + platform.slice(1)}
                    value={form.social_links[platform] ?? ""}
                    onChange={(e) => setSocialLink(platform, e.target.value)}
                    placeholder={`https://${platform}.com/yourcompany`}
                  />
                ))}
              </div>
            </Card>

            <Card className="p-6">
              <p className="font-display text-lg text-[var(--text-primary)]">SEO</p>
              <div className="mt-4 flex flex-col gap-4">
                <Input
                  label={`Page title (${form.seo_title.length}/70)`}
                  value={form.seo_title}
                  onChange={(e) => setField("seo_title", e.target.value)}
                  maxLength={70}
                />
                <Textarea
                  label={`Meta description (${form.seo_description.length}/160)`}
                  rows={2}
                  value={form.seo_description}
                  onChange={(e) => setField("seo_description", e.target.value)}
                  maxLength={160}
                />
              </div>
            </Card>

            {error && <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}
            {saved && <p className="text-sm text-signal-600">Saved.</p>}

            <Button type="submit" disabled={!canEdit || updateBranding.isPending} className="self-start">
              {updateBranding.isPending ? "Saving…" : "Save changes"}
            </Button>
          </fieldset>
        </form>

        {/* Live preview — same visual language the public career page will
            actually render with, driven by the same CSS-variable approach
            (see CareersPage), so this preview can never silently drift
            from what applicants see. */}
        <div className="lg:sticky lg:top-20 lg:self-start">
          <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)]">
            Career page preview
          </p>
          <div
            className="overflow-hidden rounded-xl border border-[var(--border)] shadow-panel"
            style={{ "--brand-primary": form.primary_color, "--brand-secondary": form.secondary_color }}
          >
            <div
              className="flex h-28 items-end bg-[var(--brand-secondary)] p-4"
              style={
                branding.cover_image_url
                  ? {
                      backgroundImage: `linear-gradient(0deg, var(--brand-secondary), transparent 120%), url(${branding.cover_image_url})`,
                      backgroundSize: "cover",
                      backgroundPosition: "center",
                    }
                  : undefined
              }
            >
              {branding.logo_url ? (
                <img src={branding.logo_url} alt="Logo" className="h-8 rounded bg-white/90 p-1" />
              ) : (
                <div className="h-8 w-8 rounded bg-white/20" />
              )}
            </div>
            <div className="bg-white p-4 dark:bg-ink-900">
              <p style={{ fontFamily: fontStack(form.font_heading) }} className="text-lg text-[var(--text-primary)]">
                {form.careers_headline || "Open roles"}
              </p>
              <p className="mt-1 line-clamp-2 text-xs text-[var(--text-secondary)]" style={{ fontFamily: fontStack(form.font_body) }}>
                {form.careers_description || form.mission || "Your careers page description will appear here."}
              </p>
              <div className="mt-3 rounded-md border border-[var(--border)] p-2.5 text-xs">
                <span className="font-medium text-[var(--text-primary)]">Sample Job Title</span>
                <span
                  className="ml-2 rounded-full px-2 py-0.5 text-[10px] text-white"
                  style={{ backgroundColor: "var(--brand-primary)" }}
                >
                  Full-time
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
