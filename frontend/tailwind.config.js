/**
 * FILE: frontend/tailwind.config.js
 * PURPOSE: Configures Tailwind CSS design tokens, content paths, and custom theme colors.
 * WHY WE NEED IT: Enforces consistent design system colors (brand chocolate/amber hues and medical blue accent) across all React UI components.
 */

/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#FFF8F0',  // Cream background
          100: '#FFE8D6', // User bubble tint
          200: '#FFD0B0', // Light border
          500: '#C05800', // Amber accent
          700: '#713600', // Deep chocolate accent
          900: '#38240D', // Espresso primary text
        },
        clinical: {
          50: '#F0F9FF',
          100: '#E0F2FE',
          500: '#0284C7', // Medical Blue
          700: '#0369A1',
        }
      }
    },
  },
  plugins: [],
}