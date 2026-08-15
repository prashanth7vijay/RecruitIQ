import { useEffect } from "react";

const GOOGLE_FONT_NAMES = {
  inter: "Inter",
  fraunces: "Fraunces",
  poppins: "Poppins",
  sora: "Sora",
  "ibm-plex-sans": "IBM+Plex+Sans",
  merriweather: "Merriweather",
  "playfair-display": "Playfair+Display",
  "space-grotesk": "Space+Grotesk",
};

function ensureFontLoaded(fontValue) {
  const family = GOOGLE_FONT_NAMES[fontValue];
  if (!family) return;
  const id = `career-font-${fontValue}`;
  if (document.getElementById(id)) return;

  const link = document.createElement("link");
  link.id = id;
  link.rel = "stylesheet";
  link.href = `https://fonts.googleapis.com/css2?family=${family}:wght@400;500;600;700&display=swap`;
  document.head.appendChild(link);
}

export function useApplyBranding(company) {
  useEffect(() => {
    if (!company) return;
    const branding = company.branding ?? {};

    if (branding.favicon_url) {
      let link = document.querySelector("link[rel='icon']");
      if (!link) {
        link = document.createElement("link");
        link.rel = "icon";
        document.head.appendChild(link);
      }
      link.href = branding.favicon_url;
    }

    document.title = branding.seo_title || `${company.name} — Careers`;

    if (branding.font_heading) ensureFontLoaded(branding.font_heading);
    if (branding.font_body) ensureFontLoaded(branding.font_body);

    const root = document.documentElement;
    if (branding.primary_color) root.style.setProperty("--brand-primary", branding.primary_color);
    if (branding.secondary_color) root.style.setProperty("--brand-secondary", branding.secondary_color);

    return () => {
      root.style.removeProperty("--brand-primary");
      root.style.removeProperty("--brand-secondary");
    };
  }, [company]);
}

export const FONT_STACKS = {
  inter: "'Inter', system-ui, sans-serif",
  fraunces: "'Fraunces', serif",
  poppins: "'Poppins', system-ui, sans-serif",
  sora: "'Sora', system-ui, sans-serif",
  "ibm-plex-sans": "'IBM Plex Sans', system-ui, sans-serif",
  merriweather: "'Merriweather', serif",
  "playfair-display": "'Playfair Display', serif",
  "space-grotesk": "'Space Grotesk', system-ui, sans-serif",
};
