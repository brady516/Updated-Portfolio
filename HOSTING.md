# Hosting & delivery architecture

How this site and its products are served. Decision summary: **the 12TB NAS is the
private vault and backup origin — not the public web server.** Residential upload
bandwidth, uptime, and internet-exposure/ransomware risk make self-hosting the
storefront a bad trade.

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

## Deploying the site

This is a plain static site (no build step). To publish:

- **GitHub Pages:** enable Pages on the repo, serve from the default branch / root.
- **Cloudflare Pages / Netlify:** connect the repo; no build command, output dir = root.

Before going live, fill in every `__PLACEHOLDER__` URL (Stripe / Substack / Calendly) —
search the repo for `__` to find them.
