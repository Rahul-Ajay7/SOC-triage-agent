/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: "#0b0f1a",
        panel: "#131a2b",
        panel2: "#1b2438",
        edge: "#26314a",
        muted: "#8a97b1",
        accent: "#5b8cff",
        benign: "#2ecc71",
        suspicious: "#f1c40f",
        critical: "#ff5470",
      },
    },
  },
  plugins: [],
};
