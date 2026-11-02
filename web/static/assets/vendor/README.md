# Third-party code served from Patent Yard

Served from this site rather than a CDN, so pages make no requests to other hosts (privacy, and the CSP stays `'self'`).
The version is in each file name; files are cached for a year, so a new version needs a new name.

| File | Source | License |
|---|---|---|
| `supabase-js-2.117.3.min.js` | `@supabase/supabase-js@2.117.3` from npm, bundled with esbuild (`export { createClient } from "@supabase/supabase-js"`, ESM, minified) | MIT |
| `jspdf-4.2.1.umd.min.js` | `jspdf@4.2.1` from npm, `dist/jspdf.umd.min.js` unchanged | MIT (`jspdf-LICENSE.txt`) |
| `../fonts/hanken-*.woff2` | Hanken Grotesk (variable, 300 to 800), Latin and Latin Extended subsets, from Google Fonts | SIL OFL 1.1 |
| `../fonts/sourceserif-*.woff2` | Source Serif 4 (variable, 400 to 600, and italic), Latin and Latin Extended subsets, from Google Fonts | SIL OFL 1.1 |

`npm audit` on these exact versions: 0 vulnerabilities (2026-10-31).
