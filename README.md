# GetOffGrounds

Static apartment-review map hosted with GitHub Pages. The map runs in the
visitor's browser; Fillout handles review submissions. No Python server or EC2
instance is needed. Apartment data remains a snapshot: new Fillout responses
must be processed into `static/apartments.json` and committed to update the map.

## Build and preview

```sh
npm ci --prefix map
npm run build --prefix map
python3 -m http.server 8080 --directory dist
```

Open http://localhost:8080. The output is `dist/`, containing `/`, `/about/`, and
`/review/` plus compiled assets. Only this directory is published; source CSVs,
notebooks, and repository files are excluded. The old Flask templates and
`app.py` are retained as historical source and are not used by the static build.

## GitHub Pages

In repository Settings → Pages, select **GitHub Actions** as the source. The
workflow builds pull requests and deploys pushes to `main`. Hosting a public
Pages website from a private repository requires an eligible paid GitHub plan.
Do not change repository visibility to enable hosting.

Configure the custom domain as `getoffgrounds.com` in Settings → Pages before
changing DNS. For a workflow deployment, the Pages setting controls the domain;
a `CNAME` file is not required.

At the domain's DNS provider, replace the old root website A record with four
A records, each named `@`:

```text
185.199.108.153
185.199.109.153
185.199.110.153
185.199.111.153
```

Set `www` to a CNAME with value `dw61.github.io` (no scheme or `/gog` path).
Remove conflicting old website A/AAAA/CNAME records at those names. Preserve
email and other unrelated DNS records. After DNS and certificate provisioning
complete, enable **Enforce HTTPS** in Pages settings.

The existing Google Maps browser API key remains in the map source. Browser
keys are visible to visitors by design; restrict it in Google Cloud to the Maps
JavaScript API and website referrers `https://getoffgrounds.com/*` and
`https://www.getoffgrounds.com/*`. Previewing on another hostname may require an
additional allowed referrer. Google Maps billing/API access and the existing
Fillout form must remain active independently of GitHub hosting.
