# Hosting & delivery architecture

How this site and its products are served. Decision summary: **the 12TB NAS is the
private vault and backup origin — not the public web server.** Residential upload
bandwidth, uptime, and internet-exposure/ransomware risk make self-hosting the
storefront a bad trade.

## Domains (locked)

- **`northdenoise.com`** (apex) → the static site, hosted on **Cloudflare Pages**
  (deploys from a **private** GitHub repo — free; GitHub Pages would require Pro).
- **`read.northdenoise.com`** → the **North de Noise** newsletter (Substack custom
  domain).
- Site "subscribe" CTAs point at `https://read.northdenoise.com`.

## Repo layout & what gets served (important)

A static host serves whatever's in its output directory. To keep the business IP
off the public internet, only the website lives in the deploy folder:

- **`site/`** — the *only* thing published (all `.html` + `Assets/`). Cloudflare's
  **build output directory** is set to `site`.
- **Root (never served):** `newsletter/` (paid drafts), `salad-scout/`,
  `lead-magnet/`, `SOP.md`, `HOSTING.md`, `README.md`.

This is the layer that actually protects the paid drafts — making the *repo* private
hides the source on GitHub, but a host still serves whatever it's pointed at, so the
sensitive folders must stay *outside* `site/`.

## The split

| Layer | Where it lives | Why |
|-------|----------------|-----|
| **Public static site** | Free global CDN host — GitHub Pages, Cloudflare Pages, or Netlify | Fast worldwide, zero maintenance, never served from home |
| **Checkout / payments** | Stripe (Payment Links) | Never self-host payments — avoids PCI scope |
| **Paid-file delivery** | Stripe-hosted file links or a delivery service (SendOwl, Lemon Squeezy) — secure, expiring URLs | Buyers can't share a permanent link; scales without touching home network |
| **Master files + backups** | The 12TB NAS | Source of truth for models, course video, and code; private |
| **Staging (optional)** | A private copy on the NAS | Preview changes before pushing live |

A Cloudflare-Tunnel-fronted NAS origin (to serve large files from home behind signed
URLs + edge caching) was considered and **declined for now** in favor of the lower-risk
managed delivery above. Revisit if course video volume makes a managed host expensive.

## Backups — 3-2-1 rule

Keep **3** copies of anything you can't recreate (models, videos, source), on **2**
different media, with **1** copy offsite:

1. Working copy (laptop / this repo on GitHub).
2. NAS copy (the vault), on a redundant volume (e.g. RAID — note RAID is *not* a backup).
3. Offsite copy — encrypted cloud backup (Backblaze B2 / S3) or a rotated external drive
   stored away from home.

Test a restore periodically — an untested backup is a hope, not a backup.

## Deploying the site (Cloudflare Pages + private repo)

Plain static site, no build step. Cloudflare Pages deploys it from the GitHub repo —
private repo supported on the free plan.

1. **GitHub:** make the repo **private** (Settings → Danger Zone → Change visibility).
2. **Cloudflare:** Workers & Pages → **Create → Pages → Connect to Git** → authorize
   GitHub → select `Updated-Portfolio`.
3. **Build settings:** Framework preset = **None**, Build command = **(blank)**,
   **Build output directory = `site`** → Save & Deploy.
4. **Custom domain:** Pages project → **Custom domains** → add `northdenoise.com`
   (+ `www`). DNS is on Cloudflare, so the records and HTTPS cert are wired
   automatically.
5. **Retire GitHub Pages:** repo Settings → Pages → Source = **None** (avoid
   double-hosting / a domain conflict). The old `CNAME` file has been removed.

## Newsletter domain (read.northdenoise.com via Substack)

1. In Substack: **Settings → custom domain**, enter `read.northdenoise.com`
   (one-time fee).
2. At your registrar: add the **CNAME** record Substack shows you for
   `read` → (their target). Wait for it to verify.
3. The site already links subscribers to `https://read.northdenoise.com`.

## Still to fill before launch

Replace the remaining `__PLACEHOLDER__` URLs (Stripe / Calendly, and the
newsletter post links `__POST_URL_*__`). Search the repo for `__` to find them.
