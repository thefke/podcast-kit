import { defineConfig } from 'astro/config';

// SITE_URL und BASE_PATH kommen aus der Umgebung, damit dieselbe Seite unter einer eigenen Domain
// (BASE_PATH=/) oder als Projektseite auf GitHub Pages (BASE_PATH=/podcast-kit/) läuft.
export default defineConfig({
  site: process.env.SITE_URL || 'http://localhost:4321',
  base: process.env.BASE_PATH || '/',
  trailingSlash: 'always',
  build: { format: 'directory' },
});
