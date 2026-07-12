/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          DEFAULT: "#0f766e",
          dark: "#0b1120",
          light: "#14b8a6"
        }
      },
      fontFamily: {
        sans: ['"Inter"', "system-ui", "sans-serif"]
      }
    }
  },
  plugins: []
};
