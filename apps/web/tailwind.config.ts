import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#09090b",
        foreground: "#f4f4f5",
        surface: {
          50: "#1e1e24",
          100: "#18181f",
          200: "#131317",
          300: "#0e0e12",
          400: "#09090b",
        },
        border: {
          subtle: "#1c1c22",
          muted: "#272730",
          highlight: "#3a3a46",
        },
        steel: {
          50: "#f4f4f5",
          100: "#e4e4e7",
          200: "#d4d4d8",
          300: "#a1a1aa",
          400: "#71717a",
          500: "#52525b",
          600: "#3f3f46",
          700: "#27272a",
          800: "#18181b",
          900: "#09090b",
        },
      },
      fontFamily: {
        sans: [
          "Inter",
          "-apple-system",
          "BlinkMacSystemFont",
          "Segoe UI",
          "Roboto",
          "Helvetica Neue",
          "Arial",
          "sans-serif",
        ],
        mono: [
          "JetBrains Mono",
          "ui-monospace",
          "SFMono-Regular",
          "Menlo",
          "Monaco",
          "Consolas",
          "monospace",
        ],
      },
      borderRadius: {
        xs: "2px",
        sm: "3px",
        DEFAULT: "4px",
        md: "6px",
        lg: "8px",
        xl: "10px",
      },
    },
  },
  plugins: [],
};

export default config;
