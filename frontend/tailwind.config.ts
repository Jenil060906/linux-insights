import type { Config } from "tailwindcss";
import animate from "tailwindcss-animate";

// Linux Insight design system — dark-only enterprise observability theme.
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
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      fontSize: {
        "2xs": ["11px", { lineHeight: "14px" }],
      },
      borderRadius: {
        DEFAULT: "12px",
        lg: "12px",
        md: "10px",
        sm: "8px",
      },
      spacing: {
        18: "4.5rem",
      },
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
