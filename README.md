# GetOffGrounds

Static apartment-review map hosted with GitHub Pages. The map runs in the
visitor's browser; Fillout handles review submissions. No Python server or EC2
instance is needed. A GitHub Action fetches completed Fillout reviews, validates
them, and publishes changes to the map. Processing dates are recorded in
`static/data-status.json`; review dates and sync status are not displayed on the
public map.

## Connect Fillout once

1. In Fillout account settings → Developer settings, copy an API key. Never
   commit it or put it in browser code.
2. In this repository's Settings → Secrets and variables → Actions, add the
   repository **secret** `FILLOUT_API_KEY`.
3. Run **Sync reviews and deploy GitHub Pages** manually from the Actions tab.
   The first successful run saves the form's field IDs in `config/fillout.json`,
   so renaming questions later does not disconnect their answers.
4. After verifying the first sync, add the repository **variable**
   `FILLOUT_SYNC_ENABLED` with value `true` to enable scheduled runs.

Use the API key from the **Forms API** section of Developer settings. This
form's verified base URL is `https://api.fillout.com/v1/api`. If questions were
renamed before the first connection, run the workflow with **inspect_schema**
selected to list question IDs, labels, and types without fetching answers or
deploying. Use those IDs in `config/fillout.json` to connect the correct fields.

The schedule requests one run each day at **3:17 AM America/Los_Angeles**,
following Pacific daylight-saving changes, plus build/deploy time. GitHub can
delay scheduled jobs and disables schedules in public repositories after 60 days
without repository activity. A new review normally appears after the next daily
run, so allow up to about 24 hours plus publishing time. Manual runs also fetch
the latest reviews. Code pushes deploy the existing review snapshot without
fetching Fillout. Visitors reload the page to see a new deployment. Unchanged
scheduled runs do not commit or deploy. The API credential is only passed to
the sync step on scheduled or manual runs; pull requests run tests and build
without it.

`scripts/sync_fillout.py` fetches all completed, non-preview submissions, so edits
and deletions are reflected. It deduplicates submission IDs, takes the median
rent per person, averages available ratings, and removes repeated tags. Only
the map's public fields are saved; submission IDs, login details, edit links,
and raw API responses are not saved or logged. The source form and reviews
must be intended for public publication. Obvious contact details in comments
are held, but this is not a complete content moderation system.

Reviews with invalid numbers, rent outside $200–$10,000 per person, or an unknown
building are held. The workflow summary reports counts and reasons; inspect
the actual answers privately in Fillout and correct them there when needed.
Limits are configurable in `config/fillout.json`. To approve a new building,
add its canonical street address and verified latitude/longitude to
`config/buildings.json`; an optional `aliases` array handles alternate spellings.
Only Charlottesville-area coordinates with a numbered street address qualify.
New reviews at approved buildings publish automatically. A brand-new building
needs this one-time map-pin approval. The existing browser Maps key cannot
geocode server-side; the sync uses the approved address catalog and incurs no
additional Google API charges.

API errors, missing required fields, an empty result, or a sudden loss of more
than 25% of published reviews stop the sync and preserve the previous website.
Investigate the source/schema before intentionally replacing a large part of
the dataset. Ordinary data changes are committed by the Action and deployed
in the same workflow (GitHub does not trigger another push workflow for a
commit made with its built-in token). Deployments are serialized, and a
conflicting push stops publishing until the next run.

Run the processing checks locally without credentials:

```sh
python3 -m unittest discover -s tests -v
```

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
workflow builds pull requests and deploys pushes to `main`. This repository is
public so GitHub Pages can host it on the free plan. All tracked source files
and commit history are also publicly accessible on GitHub. Only `dist/` is
published as the website. Hosting from a private repository instead requires an
eligible paid GitHub plan.

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
