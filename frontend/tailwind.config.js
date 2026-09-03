/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: {
          50: "#f4f6f7",
          100: "#e4e8ea",
          200: "#c7cfd3",
          300: "#9fabb2",
          400: "#71818b",
          500: "#54646e",
          600: "#44515a",
          700: "#39434a",
          800: "#262d33", // primary dark surface
          900: "#171c20", // near-black ink
          950: "#0e1114",
        },
        signal: {
          50: "#eef8f7",
          100: "#d3ede9",
          200: "#a7dbd4",
          300: "#72c3b8",
          400: "#42a89b", // accent — muted teal, "signal" as in signal-to-noise
          500: "#2f8c81",
          600: "#256f67",
          700: "#215a54",
          800: "#1f4844",
          900: "#1c3b38",
        },
      },
      fontFamily: {
        display: ["'Fraunces'", "serif"],
        sans: ["'Inter'", "system-ui", "sans-serif"],
        mono: ["'IBM Plex Mono'", "monospace"],
      },
      boxShadow: {
        soft: "0 1px 2px 0 rgb(15 23 27 / 0.04), 0 1px 3px 0 rgb(15 23 27 / 0.06)",
        panel: "0 4px 16px -2px rgb(15 23 27 / 0.10), 0 2px 6px -2px rgb(15 23 27 / 0.06)",
        elevated: "0 12px 32px -6px rgb(15 23 27 / 0.16), 0 4px 12px -4px rgb(15 23 27 / 0.08)",
      },
      keyframes: {
        "fade-in": { from: { opacity: 0 }, to: { opacity: 1 } },
        "panel-in": {
          from: { opacity: 0, transform: "translateY(-4px) scale(0.98)" },
          to: { opacity: 1, transform: "translateY(0) scale(1)" },
        },
      },
      animation: {
        "fade-in": "fade-in 120ms ease-out",
        "panel-in": "panel-in 140ms cubic-bezier(0.16, 1, 0.3, 1)",
      },
    },
  },
  plugins: [],
};
