/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./src/**/*.{ts,tsx}",
    "../../packages/ui/src/**/*.{ts,tsx}",
  ],
  presets: [require("nativewind/preset")],
  theme: {
    extend: {
      colors: {
        bg: {
          primary: "#07090F",
          secondary: "#0D1117",
          elevated: "#13191F",
          border: "#1E2733",
        },
        brand: {
          primary: "#0EA5E9",
          secondary: "#6366F1",
          glow: "#38BDF8",
        },
        muted: "#8FA3B8",
      },
      fontFamily: {
        sans: ["Inter"],
      },
    },
  },
  plugins: [],
};
