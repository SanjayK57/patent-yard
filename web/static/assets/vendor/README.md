# Third-party code served from Patent Yard

Served from this site rather than a CDN, so pages make no requests to other hosts (privacy, and the CSP stays `'self'`).
The version is in each file name; files are cached for a year, so a new version needs a new name.

| File | Source | License |
|---|---|---|
| `supabase-js-2.117.3.min.js` | `@supabase/supabase-js@2.117.3` from npm, bundled with esbuild (`export { createClient } from "@supabase/supabase-js"`, ESM, minified) | MIT |
| `jspdf-4.2.1.umd.min.js` | `jspdf@4.2.1` from npm, `dist/jspdf.umd.min.js` unchanged | MIT (`jspdf-LICENSE.txt`) |
| `../fonts/plex-*.woff2` | IBM Plex Sans (variable), Mono and Serif from `@fontsource` 5.3.0, Latin and Latin Extended subsets | SIL OFL 1.1 (`../fonts/OFL.txt`) |

`npm audit` on these exact versions: 0 vulnerabilities (2026-10-31).
