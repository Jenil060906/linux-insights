import type { Config } from "tailwindcss";
import animate from "tailwindcss-animate";

// ============================================================================
// Linux Insight — design token layer
// ============================================================================
// This file IS the design system's source of truth. Tokens are defined once
// here under `theme.extend` (never as raw hex in component files) so every
// component consumes the same palette, scale, and radii by construction.
//
// Tailwind v3 project: tokens live in config, not CSS custom properties.
// (CSS-variable tokens are the right call for a v4 project, or one that
// needs to swap themes at runtime — this app is dark-only with no runtime
// theme switch, so a config-based token layer is the simpler, idiomatic fit.)
//
// `extend` (not a top-level `theme` override) is deliberate: it layers our
// tokens on top of Tailwind's default scale instead of replacing it, so
// utilities like `text-sm`, `p-4`, `gap-2` keep working normally everywhere
// they're already used — only genuinely new tokens (`2xs`, `18`, `soft`,
// `card`) are additions.
export default {
  darkMode: ["class"],
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    container: {
      center: true,
      padding: "1.5rem",
      screens: {
        "2xl": "1440px",
      },
    },
    extend: {
      // ---- Color tokens -----------------------------------------------
      // Two families:
      //  1. Surface tokens (background/surface/card/border) — a 4-step dark
      //     elevation ramp, darkest to lightest: background < surface < card.
      //     Nesting a `card` on `surface` on `background` is what reads as
      //     "layered panels" without ever touching opacity or shadows.
      //  2. Status tokens (primary/success/warning/danger) — each carries a
      //     `DEFAULT` (the accent, used at low opacity for tints/borders and
      //     full opacity for icons/text) and a `foreground` (the color to
      //     put ON TOP of a solid fill of that color, for contrast). This is
      //     the same DEFAULT/foreground pairing shadcn/ui uses, which is why
      //     `bg-primary text-primary-foreground` reads correctly everywhere.
      // Status colors are reserved for state (good/warning/serious/critical)
      // and are never repurposed as decorative/categorical colors elsewhere
      // in the app (see the dataviz pass — chart series use a single neutral
      // hue precisely so these four keep their meaning unambiguous).
      colors: {
        background: "#0D1117",
        surface: "#161B22",
        card: "#1C2128",
        border: "#30363D",
        primary: {
          DEFAULT: "#3B82F6",
          foreground: "#F8FAFC",
        },
        success: {
          DEFAULT: "#22C55E",
          foreground: "#0D1117",
        },
        warning: {
          DEFAULT: "#F59E0B",
          foreground: "#0D1117",
        },
        danger: {
          DEFAULT: "#EF4444",
          foreground: "#F8FAFC",
        },
        foreground: "#F8FAFC",
        muted: {
          DEFAULT: "#161B22",
          foreground: "#9CA3AF",
        },
        accent: {
          DEFAULT: "#1C2128",
          foreground: "#F8FAFC",
        },
      },

      // ---- Typography tokens --------------------------------------------
      // Inter, loaded once in index.html. We do NOT introduce semantic size
      // names (e.g. "heading-lg") on top of Tailwind's own scale — the app
      // already has a consistent, documented scale using Tailwind's stock
      // sizes, and renaming them would be pure churn with no visual change.
      // The de facto scale in use, so future components stay consistent:
      //   text-2xs (11px)  → timestamps, meta captions, table headers
      //   text-xs   (12px) → secondary/muted body text, descriptions
      //   text-sm   (14px) → primary body text, card titles, labels
      //   text-lg / text-xl (18 / 20px) → card/section-level headings
      //   text-2xl (24px)  → stat values (MetricCard)
      //   text-4xl (36px)  → the ONE hero figure per view (SystemHealthHero)
      // `2xs` is the only genuinely missing step in Tailwind's default
      // scale, so it's the only one added here.
      fontSize: {
        "2xs": ["11px", { lineHeight: "14px" }],
      },

      // ---- Border radius tokens ------------------------------------------
      // A 3-step scale, largest to smallest, all rounder than Tailwind's
      // defaults to read as "soft enterprise software" per the brief:
      //   lg (12px, = DEFAULT) → Card, the outermost container everywhere
      //   md (10px)            → nothing currently opts out of `lg`, kept
      //                           as the "one step down" escape hatch
      //   sm (8px)              → inner controls nested inside a Card:
      //                           Button, Badge, Chip, IconTile, table wrap
      // The rule of thumb: an element nested inside another rounded element
      // uses the next radius down, so corners never look concentric/clashing.
      borderRadius: {
        DEFAULT: "12px",
        lg: "12px",
        md: "10px",
        sm: "8px",
      },

      // ---- Spacing tokens (8px system) ------------------------------------
      // Tailwind's default spacing scale is already 4px-based (spacing-1 =
      // 4px), which means every EVEN step lands exactly on an 8px grid
      // (spacing-2=8px, spacing-4=16px, spacing-6=24px, spacing-8=32px) — so
      // no override is needed to get an 8px system, only a usage rule:
      //   Macro layout (card padding, section gaps, page margins) MUST use
      //   even steps only (2/4/6/8) — this is the 8px grid.
      //   Micro adornments (icon-to-label gaps, chip padding, status dots)
      //   MAY use odd half-steps (1.5/2.5) — real 8px systems (Material's
      //   8dp grid included) allow 4px half-steps for exactly this, small
      //   inline elements where an 8px jump would look sloppy.
      // `18` (72px) is the one custom addition, reserved for the rare
      // larger fixed dimension a 4px step doesn't reach cleanly.
      spacing: {
        18: "4.5rem",
      },

      // ---- Shadow tokens ---------------------------------------------------
      // Two "soft shadow" levels (never a hard/large shadow — see the brief's
      // "no glassmorphism, no neon" rule, which extends to elevation too):
      //   card → the default for every panel (Card component)
      //   soft → one step more diffuse, reserved for the single most
      //          important element per view (SystemHealthHero) so it reads
      //          as elevated above the section cards, not just bigger text.
      boxShadow: {
        soft: "0 1px 2px 0 rgba(0, 0, 0, 0.35), 0 1px 3px 0 rgba(0, 0, 0, 0.2)",
        card: "0 1px 3px 0 rgba(0, 0, 0, 0.4)",
      },
      keyframes: {
        "pulse-dot": {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.4" },
        },
      },
      animation: {
        "pulse-dot": "pulse-dot 2s ease-in-out infinite",
      },
    },
  },
  plugins: [animate],
} satisfies Config;
