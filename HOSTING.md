# Hosting & delivery architecture

How this site and its products are served. Decision summary: **the 12TB NAS is the
private vault and backup origin — not the public web server.** Residential upload
bandwidth, uptime, and internet-exposure/ransomware risk make self-hosting the
storefront a bad trade.

## Domains (locked)

- **`northdenoise.com`** (apex) → the static site, hosted on **GitHub Pages**.
- **`read.northdenoise.com`** → the **North de Noise** newsletter (Substack custom
  domain).
- Site "subscribe" CTAs point at `https://read.northdenoise.com`.

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

## Deploying the site (GitHub Pages + northdenoise.com)

Plain static site, no build step. The repo includes a `CNAME` file
(`northdenoise.com`) so GitHub Pages serves the custom apex domain.

1. **Repo → Settings → Pages:** Source = deploy from branch, pick the default
   branch, folder `/ (root)`. Custom domain should auto-fill from `CNAME`.
2. **DNS at your registrar — apex `northdenoise.com`:** add GitHub Pages' four
   **A** records:
   - `185.199.108.153`
   - `185.199.109.153`
   - `185.199.110.153`
   - `185.199.111.153`
   (optionally the matching AAAA records for IPv6).
3. **`www` (optional):** add a **CNAME** record `www` → `<your-github-username>.github.io`.
4. Back in Pages, tick **Enforce HTTPS** once the certificate provisions.

## Newsletter domain (read.northdenoise.com via Substack)

1. In Substack: **Settings → custom domain**, enter `read.northdenoise.com`
   (one-time fee).
2. At your registrar: add the **CNAME** record Substack shows you for
   `read` → (their target). Wait for it to verify.
3. The site already links subscribers to `https://read.northdenoise.com`.

## Still to fill before launch

Replace the remaining `__PLACEHOLDER__` URLs (Stripe / Calendly, and the
newsletter post links `__POST_URL_*__`). Search the repo for `__` to find them.
