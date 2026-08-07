/**
 * FILE: frontend/postcss.config.js
 * PURPOSE: Configures PostCSS build processing plugins.
 * WHY WE NEED IT: Instructs Vite to compile Tailwind directives (@tailwind) into standard CSS and auto-prefix properties for cross-browser support.
 */

export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}