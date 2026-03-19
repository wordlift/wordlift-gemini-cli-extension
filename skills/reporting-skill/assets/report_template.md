# SEO Performance Report — PDF Template

This document defines the structure and content of the generated PDF report. The `scripts/report.py` script uses this as the blueprint. Sections are **conditionally included** based on available data.

---

## Page Layout

| Property | Value |
|---|---|
| **Page size** | A4 (210 × 297 mm) |
| **Margins** | 25mm all sides |
| **Font family** | Helvetica (built-in) |
| **Title font** | 24pt bold |
| **Section headers** | 16pt bold, with colored underline |
| **Body text** | 10pt regular |
| **Chart width** | Full column width (160mm) |
| **Color palette** | Variant: `#2563EB`, Control: `#DC2626`, Accent: `#10B981` |

---

## Report Sections

### 1. Cover Page

```
┌──────────────────────────────────────┐
│                                      │
│           [Client Logo]              │
│        (if logo_path provided)       │
│                                      │
│   ─────────────────────────────────  │
│                                      │
│     SEO Performance Report           │
│     {site.name}                      │
│                                      │
│     Analysis Period:                 │
│     {dates.before_start} –           │
│         {dates.after_end}            │
│                                      │
│     Prepared by: {report.author}     │
│     Date: {generation_date}          │
│                                      │
│   ─────────────────────────────────  │
│                                      │
│          Powered by WordLift         │
│                                      │
└──────────────────────────────────────┘
```

---

### 2. Executive Summary (1 page)

**Always included.**

A single-page overview with key findings:

**Elements:**
- **Headline metric callouts** (large, colored boxes):
  - Total click change (↑/↓ with %)
  - Impression change
  - CTR change (pp)
  - Position change
- **Key Findings** bullet list (5–8 bullets, auto-generated from data)
- **AI Traffic highlight** (if GA4 data available): total AI referral sessions + top source

**Table: Performance Summary**

| Metric | Before Period | After Period | Change |
|---|---|---|---|
| Clicks | {value} | {value} | {+/-value} ({%}) |
| Impressions | {value} | {value} | {+/-value} ({%}) |
| Avg CTR | {value}% | {value}% | {+/-value}pp |
| Avg Position | {value} | {value} | {+/-value} |

If variant/control groups defined, show side-by-side:

| Metric | Variant (n URLs) | Control (n URLs) |
|---|---|---|
| Click Change | +X (+Y%) | -X (-Y%) |
| URLs Gaining | N (%) | N (%) |
| URLs Losing | N (%) | N (%) |

---

### 3. Google Search Console Analysis

**Included when:** `gsc.enabled: true`

#### 3a. Overall Performance (1–2 pages)

- **Chart**: Daily Clicks & Impressions — Before vs After (normalized bar chart)
- **Chart**: CTR & Position Changes (bar chart)
- **Table**: Period metrics (total clicks, impressions, avg CTR, avg position per group)
- **Narrative paragraph**: auto-generated comparison text

#### 3b. Time Series (1 page)

- **Chart**: Daily Clicks Over Time (line chart with intervention line)
- **Chart**: Daily Impressions Over Time (line chart)
- **Annotation**: Vertical dashed line at intervention date

#### 3c. Distribution Analysis (1 page)

- **Chart**: Click Diff Distribution (histogram, variant vs control overlay)
- **Chart**: Positive vs Negative URLs (pie charts, side by side)
- **Callout box**: Median click diff for each group

#### 3d. Top Performers (1 page)

- **Chart**: Top 20 Click Gainers (horizontal bar chart)
- **Table**: Top 10 URLs with before/after clicks, diff, and % change

#### 3e. Net Change Summary (1 page)

- **Chart**: Net Daily Change comparison (bar chart, variant vs control)
- **Insight box**: summarizing the net effect

---

### 4. Google Analytics 4 — Behavioral Analysis

**Included when:** `ga4.enabled: true`

#### 4a. AI Referral Traffic (1–2 pages)

- **Chart**: AI Sessions by Source (horizontal bar chart)
- **Chart**: AI Traffic by Page Group (if groups defined)
- **Table**: AI source breakdown (source, sessions, users, pageviews)
- **Callout**: Total AI referral share of traffic (%)
- **Chart**: AI Traffic Before vs After (if date ranges allow comparison)

#### 4b. Engagement Metrics (1 page)

- **Chart**: Engagement by Group (sessions, engaged sessions, bounce rate, avg duration)
- **Table**: Group-level engagement summary

#### 4c. Channel Mix (1 page)

- **Chart**: Traffic by Channel Group (stacked bar or grouped bar)
- **Top 8 channels** per group

#### 4d. New vs Returning Users (half page)

- **Table/Chart**: New vs returning split per group
- **Callout**: returning user % comparison

---

### 5. Causal Impact Analysis

**Included when:** `analysis.causal_impact: true` AND variant/control groups defined

#### 5a. Click Causal Impact (1 page)

- **Chart**: CausalImpact plot (3-panel: original, pointwise, cumulative)
- **Table**:

| Metric | Value |
|---|---|
| Observed daily avg | X clicks |
| Predicted (counterfactual) | X clicks |
| Absolute effect | +X clicks/day |
| Relative effect | +X% |
| 95% CI | [X%, Y%] |
| p-value | X |
| Prob. of causal effect | X% |

- **Narrative**: auto-generated CausalImpact report text

#### 5b. Impressions Causal Impact (1 page)

- Same structure as 5a but for impressions

---

### 6. Schema Class Performance

**Included when:** `analysis.schema_analysis: true` AND entity matrix CSV provided

#### 6a. Schema Class Lift (1 page)

- **Chart**: Click Performance Lift by Schema.org Class (horizontal bar)
- **Table**: Per-class metrics (URLs with, avg click Δ with/without, lift, % positive)

#### 6b. Schema Heatmap (1 page)

- **Chart**: Multi-metric heatmap (click Δ, CTR Δ, position Δ, % positive, n URLs)

---

### 7. Content Intervention Analysis

**Included when:** content intervention URLs + launch dates provided

#### 7a. Per-Page Performance (1–2 pages)

- **Table**: Each content page with launch date, clicks before/after, impressions, new queries gained
- **Chart**: New Queries by Page (bar chart)
- **Chart**: Daily Impressions Trend per Content Page (small multiples)

#### 7b. Query-Level Insights (1 page)

- **Table**: Top new queries across all content pages (query, impressions, clicks, avg position)
- **Callout**: Total new queries discovered post-intervention

---

### 8. Methodology & Data Sources (last page)

**Always included.**

- Data sources used (GSC API, GA4 API)
- Date ranges (before period, after period, days in each)
- Number of URLs analyzed per group
- Normalization method (per-day averages when periods differ)
- Statistical methods (CausalImpact model details, if used)
- AI source identification list
- Tool versions
- Disclaimer / data freshness note (GSC ~3-day lag)

---

## Conditional Logic Summary

```
IF gsc.enabled:
    Include Sections 3a–3e
IF ga4.enabled:
    Include Sections 4a–4d
IF groups defined (variant + control):
    Show side-by-side comparisons in all sections
    Enable Section 5 (Causal Impact)
ELSE:
    Show single-group (site-wide) metrics
IF schema_analysis + entity_matrix_csv:
    Include Section 6
IF content_urls + launch_dates:
    Include Section 7
ALWAYS:
    Include Cover, Executive Summary, Methodology
```
