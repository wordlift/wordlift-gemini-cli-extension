# Configuration Reference

## Config File Format

The skill uses a YAML configuration file (`config.yaml`). All scripts accept `--config config.yaml`.

## Required Sections

### `site`

| Key | Required | Description |
|---|---|---|
| `domain` | Yes | Full domain URL including protocol and trailing slash. Must match GSC property exactly. |
| `name` | Yes | Human-readable site name. Used in report titles and file names. |

```yaml
site:
  domain: "https://www.example.com/"
  name: "Example Corp"
```

### `dates`

| Key | Required | Description |
|---|---|---|
| `before_start` | Yes | Start of "before" period (YYYY-MM-DD) |
| `before_end` | Yes | End of "before" period |
| `after_start` | Yes | Start of "after" period (typically day after `before_end`) |
| `after_end` | Yes | End of "after" period. Set 3+ days before today (GSC lag). |

```yaml
dates:
  before_start: "2026-02-01"
  before_end: "2026-02-14"
  after_start: "2026-02-15"
  after_end: "2026-03-10"
```

### `output`

| Key | Required | Default | Description |
|---|---|---|---|
| `directory` | Yes | — | Output directory for CSVs, charts, and PDF |
| `chart_dpi` | No | `150` | Resolution for chart PNGs |

## Data Source Sections

### `gsc`

| Key | Required | Description |
|---|---|---|
| `enabled` | Yes | `true` to pull GSC data |
| `client_secret` | If enabled | Path to OAuth client_secret.json |
| `credentials_cache` | No | Path to cache OAuth tokens (default: `credentials.json`) |

### `ga4`

| Key | Required | Description |
|---|---|---|
| `enabled` | Yes | `true` to pull GA4 data |
| `property_id` | If enabled | GA4 property ID (numeric string) |
| `client_secret` | If enabled | Path to OAuth client_secret.json |
| `credentials_cache` | No | Path to cache GA4 OAuth tokens (default: `ga4_credentials.json`) |

## Optional Sections

### `groups`

For A/B testing / variant vs control analysis:

| Key | Required | Description |
|---|---|---|
| `variant_csv` | No | CSV file with a `url` column listing variant URLs |
| `control_csv` | No | CSV file with a `url` column listing control URLs |

Both must be provided together. If omitted, site-wide analysis is performed.

### `analysis`

| Key | Default | Description |
|---|---|---|
| `causal_impact` | `false` | Run CausalImpact analysis (requires groups + GSC) |
| `schema_analysis` | `false` | Analyze performance by schema.org class |
| `entity_matrix_csv` | — | Path to entity matrix CSV (columns: url, then schema class names with ✅) |
| `ai_sources` | built-in list | Override the list of AI referral source domains |

### `report`

| Key | Default | Description |
|---|---|---|
| `author` | — | Author name shown on cover page |
| `logo_path` | — | Path to logo image for cover page |

## Credential Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create or select a project
3. Enable the **Search Console API** and/or **Google Analytics Data API**
4. Go to **APIs & Services → Credentials**
5. Create an **OAuth 2.0 Client ID** (Application type: **Desktop app**)
6. Download the JSON file → save as `client_secret.json`
7. Place it in a known path and reference it in `config.yaml`

On first run, each script will trigger an OAuth consent flow. After authorization, tokens are cached automatically.
