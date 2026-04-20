---
name: reporting-skill
description: >
  Generate comprehensive SEO performance reports using Google Search Console (GSC)
  and Google Analytics 4 (GA4) data. Pulls live API data, computes before/after
  metrics, generates charts, runs optional CausalImpact analysis, and produces a
  PDF report. Also supports analyzing Google Ads / Paid Campaign CSV data for
  comprehensive performance audits. Use when the user asks for SEO reporting,
  traffic analysis, ads performance audits, or GA4/GSC data pulls.
license: Apache-2.0
compatibility: >
  Requires Python 3.9+, internet access for Google APIs, and a Google Cloud
  project with Search Console API and GA4 Data API enabled.
  OAuth client_secret.json required for authentication.
metadata:
  author: wordlift
  version: "1.0"
---

# SEO Performance Report Skill

Generate comprehensive, publication-ready SEO performance reports for **any website** with Google Search Console and/or Google Analytics 4 access.

## Overview

This skill automates the full reporting pipeline:

1. **Pull data** from GSC and/or GA4 via authenticated API calls
2. **Compute metrics** — before/after comparisons, daily averages, diffs
3. **Generate charts** — time series, distributions, comparisons, heatmaps
4. **Run statistical analysis** — optional CausalImpact for A/B testing
5. **Produce a PDF report** — structured, branded, with embedded charts

## Prerequisites

Before running this skill, ensure the user has:

- A **Google Cloud project** with the following APIs enabled:
  - Google Search Console API (for GSC data)
  - Google Analytics Data API v1 (for GA4 data)
- An **OAuth 2.0 Client ID** (Desktop app type) → downloaded as `client_secret.json`
- The **GA4 Property ID** (numeric, found in GA4 Admin → Property Settings)
- The **GSC property URL** (e.g., `https://www.example.com/`)

## Step-by-Step Instructions

### Step 1: Gather Configuration

Ask the user for the following information. Create a `config.yaml` file in the project's working directory using [the template](assets/config_template.yaml):

| Parameter | Required | Example |
|---|---|---|
| `site.domain` | Yes | `https://www.example.com` |
| `site.name` | Yes | `Example Corp` |
| `gsc.enabled` | Yes | `true` or `false` |
| `gsc.client_secret` | If GSC | Path to client_secret.json |
| `gsc.credentials_cache` | If GSC | Path to credentials.json (auto-created) |
| `ga4.enabled` | Yes | `true` or `false` |
| `ga4.property_id` | If GA4 | `396994319` |
| `ga4.client_secret` | If GA4 | Path to client_secret.json |
| `ga4.credentials_cache` | If GA4 | Path to ga4_credentials.json (auto-created) |
| `dates.before_start` | Yes | `2026-01-01` |
| `dates.before_end` | Yes | `2026-01-31` |
| `dates.after_start` | Yes | `2026-02-01` |
| `dates.after_end` | Yes | `2026-02-28` |
| `groups.variant_csv` | No | Path to CSV with `url` column |
| `groups.control_csv` | No | Path to CSV with `url` column |
| `output.directory` | Yes | `./output` |

> **Note on date ranges:** GSC data has approximately a 3-day lag. Set `dates.after_end` to at least 3 days before today.

> **Note on groups:** If variant/control CSVs are provided, the analysis includes A/B comparison charts and enables CausalImpact analysis. Without groups, the report shows site-wide metrics.

### Step 2: Install Dependencies

Run the setup script to install all required Python packages:

```bash
python3 scripts/setup.py
```

This installs: `google-api-python-client`, `google-auth-oauthlib`, `google-analytics-data`, `searchconsole`, `pandas`, `matplotlib`, `seaborn`, `numpy`, `pycausalimpact`, `openpyxl`, `tqdm`, `pyyaml`, `fpdf2`.

### Step 3: Pull GSC Data

If `gsc.enabled: true` in config:

```bash
python3 scripts/gsc_pull.py --config config.yaml
```

**First-time auth:** The script will print an authorization URL. The user must:
1. Visit the URL in their browser
2. Authorize with their Google account
3. Copy the authorization code and paste it back

After first auth, credentials are cached in the specified `credentials_cache` path.

**Output files** (in `output.directory`):
- `gsc_daily.csv` — daily metrics for all pages
- `gsc_variant.csv`, `gsc_control.csv` — if groups defined
- `gsc_variant_metrics.csv`, `gsc_control_metrics.csv` — before/after aggregates
- `gsc_site_metrics.csv` — site-wide before/after (when no groups)

### Step 4: Pull GA4 Data

If `ga4.enabled: true` in config:

```bash
python3 scripts/ga4_pull.py --config config.yaml
```

Same OAuth flow as GSC (may reuse same client_secret, separate credentials cache).

**Output files** (in `output.directory`):
- `ga4_traffic_by_source.csv` — all traffic with AI source tagging
- `ga4_engagement.csv` — engagement metrics by landing page
- `ga4_channels.csv` — traffic by channel group
- `ga4_new_vs_returning.csv` — new vs returning users

### Step 5: Generate Analysis & Charts

```bash
python3 scripts/analyze.py --config config.yaml
```

Generates PNG charts and an `analysis_summary.json` with computed statistics. Charts are conditional based on available data:

**GSC charts** (when GSC data present):
- Before/after clicks & impressions
- CTR & position comparison
- Daily clicks time series
- Daily impressions time series
- Click diff distribution
- Positive vs negative URLs
- Top 20 click gainers
- Net change comparison

**GA4 charts** (when GA4 data present):
- AI referral traffic by source
- AI traffic by page group
- Engagement comparison
- Channel mix
- New vs returning users

**Optional:**
- CausalImpact plots (when variant/control + `analysis.causal_impact: true`)
- Schema class lift + heatmap (when `analysis.schema_analysis: true` + entity matrix CSV)

### Step 6: Generate PDF Report

```bash
python3 scripts/report.py --config config.yaml
```

### Step 7: Analyze Google Ads (Optional)

If the user provides a Google Ads campaign or keyword report as a CSV:

```bash
python3 scripts/google_ads_analysis.py --csv path/to/ads.csv --out ./output
```

This generates `chart_ads_campaigns.png` and `ads_summary.json` which can be integrated into the final report or summarized by the agent.

### Step 8: Deterministic ROAS Computation (Paid Campaigns)

When analyzing Paid Campaigns for ROAS with a Variant/Control group mapping, use the deterministic `compute_roas.py` script. This requires a two-phase execution:

**Phase 1 — Inspect the Schema**
```bash
python3 scripts/compute_roas.py --inspect-only \
  --campaign <path_to_campaigns_file> \
  --groups <path_to_groups_mapping_file>
```
Parse the JSON output and build a `--column-map` JSON mapping the standard keys (`cost`, `revenue`, `conversions`, `clicks`, `impressions`, `url`, `campaign_id`, `group_url`, `group_label`) to the actual column names based on the sample row provided.

**Phase 2 — Deterministic Computation**
```bash
python3 scripts/compute_roas.py \
  --campaign <path_to_campaigns_file> \
  --groups <path_to_groups_mapping_file> \
  --column-map '{"cost":"...", "revenue":"..."}'
```
**CRITICAL**: Parse the JSON (`COMPUTE_ROAS_RESULT_START` to `COMPUTE_ROAS_RESULT_END`). Use these computed numbers verbatim for your HTML report. Do not re-interpret or re-calculate the data yourself. Base64 chart PNGs are provided in the payload for direct embedding.

Produces `{site.name}_SEO_Report.pdf` (or an HTML artifact if requested) in the output directory. Report structure follows [the template](assets/report_template.md). Sections are conditionally included based on available data.

## Configuration Reference

See [references/CONFIG.md](references/CONFIG.md) for the full configuration reference, including all optional parameters and environment variable overrides.

## Metrics Reference

See [references/METRICS.md](references/METRICS.md) for detailed explanations of all tracked metrics, AI source identification logic, and derived metric formulas.

## Common Issues

| Issue | Solution |
|---|---|
| `credentials.json` not found | Run the script — it will trigger OAuth flow on first run |
| GSC returns no data | Verify the domain property matches exactly (including `https://` and trailing `/`) |
| GA4 "permission denied" | Ensure the authenticated account has Viewer access to the GA4 property |
| CausalImpact fails | Needs at minimum 7 days in both before and after periods |
| Charts look empty | Check that the date ranges contain data — GSC has ~3 day lag |

## Example Usage

**Minimal (GSC only, no groups):**
```yaml
site:
  domain: "https://www.example.com/"
  name: "Example Corp"
gsc:
  enabled: true
  client_secret: "./client_secret.json"
ga4:
  enabled: false
dates:
  before_start: "2026-01-01"
  before_end: "2026-01-31"
  after_start: "2026-02-01"
  after_end: "2026-02-28"
output:
  directory: "./output"
```

**Full (GSC + GA4, variant/control A/B test):**
```yaml
site:
  domain: "https://www.example.com/"
  name: "Example Corp"
gsc:
  enabled: true
  client_secret: "./client_secret.json"
ga4:
  enabled: true
  property_id: "396994319"
  client_secret: "./client_secret.json"
dates:
  before_start: "2026-02-07"
  before_end: "2026-02-17"
  after_start: "2026-02-18"
  after_end: "2026-03-10"
groups:
  variant_csv: "./variant_urls.csv"
  control_csv: "./control_urls.csv"
output:
  directory: "./output"
analysis:
  causal_impact: true
```
