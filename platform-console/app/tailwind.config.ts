import type { Config } from "tailwindcss";

// shadcn/ui init (shadcn@2.10.0, base color "neutral") emits CSS variables in
// app/globals.css as full oklch() color functions. The CLI's own generated
// template still wraps every reference as hsl(var(--x)), which is invalid
// nested-color-function CSS once the variable itself is oklch(...) (produces
// hsl(oklch(0.145 0 0)) -- not a real color). Fixed here by referencing the
// variables directly; base color values are already complete color functions.
const config: Config = {
  darkMode: ["class"],
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // Legacy console tokens -- kept byte-identical so every page not
        // touched by the shadcn restyle (secrets, backups, logs, iam,
        // registry, api-gateway, compliance, gitops, autofde-lab, gymact,
        // ggen, ggen-marketplace, pricing, login, observability,
        // projects/[name]/*) keeps rendering exactly as before.
        bg: "#0b0e14",
        panel: "#111521",
        accent: {
          DEFAULT: "#5b8dee",
          foreground: "#f8faff",
        },
        // shadcn/ui semantic tokens, driven by the CSS variables in
        // app/globals.css (:root is unused here -- html carries the `dark`
        // class in app/layout.tsx, since this console has no light theme).
        border: "var(--border)",
        input: "var(--input)",
        ring: "var(--ring)",
        background: "var(--background)",
        foreground: "var(--foreground)",
        primary: {
          DEFAULT: "var(--primary)",
          foreground: "var(--primary-foreground)",
        },
        secondary: {
          DEFAULT: "var(--secondary)",
          foreground: "var(--secondary-foreground)",
        },
        destructive: {
          DEFAULT: "var(--destructive)",
          foreground: "var(--destructive-foreground)",
        },
        muted: {
          DEFAULT: "var(--muted)",
          foreground: "var(--muted-foreground)",
        },
        card: {
          DEFAULT: "var(--card)",
          foreground: "var(--card-foreground)",
        },
        popover: {
          DEFAULT: "var(--popover)",
          foreground: "var(--popover-foreground)",
        },
        chart: {
          "1": "var(--chart-1)",
          "2": "var(--chart-2)",
          "3": "var(--chart-3)",
          "4": "var(--chart-4)",
          "5": "var(--chart-5)",
        },
        sidebar: {
          DEFAULT: "var(--sidebar)",
          foreground: "var(--sidebar-foreground)",
          primary: "var(--sidebar-primary)",
          "primary-foreground": "var(--sidebar-primary-foreground)",
          accent: "var(--sidebar-accent)",
          "accent-foreground": "var(--sidebar-accent-foreground)",
          border: "var(--sidebar-border)",
          ring: "var(--sidebar-ring)",
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};

export default config;
