# SEO Performance Report — Agent Skill

An [Agent Skill](https://agentskills.io) that generates comprehensive SEO performance reports using Google Search Console (GSC) and Google Analytics 4 (GA4) data.

## What It Does

- **Pulls live data** from GSC and GA4 APIs via authenticated OAuth
- **Computes before/after metrics** — clicks, impressions, CTR, position changes
- **Generates 16 chart types** — time series, distributions, comparisons, heatmaps
- **Runs CausalImpact analysis** — Bayesian statistical significance for A/B tests
- **Produces a branded PDF report** — structured, multi-section, conditional

## Features

| Feature | Description |
|---|---|
| **GSC + GA4** | Works with either or both data sources |
| **A/B Testing** | Compare variant/control URL groups |
| **Site-Wide** | Falls back to whole-site analysis when no groups |
| **AI Referral Tracking** | Detects ChatGPT, Perplexity, Gemini, Claude, etc. |
| **Schema Class Analysis** | Performance lift by schema.org type (optional) |
| **CausalImpact** | Bayesian causal inference with statistical confidence |
| **PDF Report** | Cover page, executive summary, charts, methodology |

## Quick Start

1. **Copy the config template**
   ```bash
   cp assets/config_template.yaml config.yaml
   ```

2. **Fill in your details** — site domain, GA4 property ID, date ranges, credential paths

3. **Run the pipeline**
   ```bash
   python3 scripts/setup.py                        # Install dependencies
   python3 scripts/gsc_pull.py --config config.yaml # Pull GSC data
   python3 scripts/ga4_pull.py --config config.yaml # Pull GA4 data
   python3 scripts/analyze.py --config config.yaml  # Generate charts
   python3 scripts/report.py  --config config.yaml  # Generate PDF report
   ```

4. **Find your report** in the configured output directory

## Prerequisites

- Python 3.9+
- A Google Cloud project with Search Console API and/or GA4 Data API enabled
- An OAuth 2.0 Client ID (Desktop app) downloaded as `client_secret.json`

## Skill Structure

```
reporting-skill/
├── SKILL.md                    # Skill manifest + agent instructions
├── scripts/
│   ├── setup.py                # Dependency installer
│   ├── gsc_pull.py             # GSC data extraction
│   ├── ga4_pull.py             # GA4 data extraction
│   ├── analyze.py              # Chart generation + statistics
│   └── report.py               # PDF report generator
├── references/
│   ├── CONFIG.md               # Configuration reference
│   └── METRICS.md              # Metrics reference
└── assets/
    ├── config_template.yaml    # Annotated config template
    └── report_template.md      # PDF report structure blueprint
```

## Configuration

See [references/CONFIG.md](references/CONFIG.md) for the full configuration reference, including:
- All YAML config options
- Google Cloud credential setup
- Variant/control CSV format

## Metrics

See [references/METRICS.md](references/METRICS.md) for detailed explanations of all tracked metrics.

## License

Apache-2.0
