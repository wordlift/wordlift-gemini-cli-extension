# Metrics Reference

## Google Search Console Metrics

| Metric | API Name | Description |
|---|---|---|
| **Clicks** | `clicks` | Number of times a user clicked through to the site from search results |
| **Impressions** | `impressions` | Number of times a page appeared in search results |
| **CTR** | `ctr` | Click-through rate = Clicks / Impressions (0–1 scale) |
| **Position** | `position` | Average ranking position in search results (lower = better) |

## Google Analytics 4 Metrics

| Metric | API Name | Description |
|---|---|---|
| **Sessions** | `sessions` | Total number of sessions |
| **Total Users** | `totalUsers` | Number of unique users |
| **Engaged Sessions** | `engagedSessions` | Sessions lasting >10s, with conversion, or 2+ page views |
| **Engagement Duration** | `userEngagementDuration` | Total time users were actively engaged (seconds) |
| **Page Views** | `screenPageViews` | Total page views |
| **Bounce Rate** | `bounceRate` | % of sessions that were NOT engaged (0–1 scale) |
| **Avg Session Duration** | `averageSessionDuration` | Average session length in seconds |
| **Conversions** | `conversions` | Total conversion events |

## Derived Metrics

| Metric | Formula | Description |
|---|---|---|
| **Clicks Diff** | `Clicks_After − Clicks_Before` | Absolute click change per URL |
| **Click % Change** | `(After/Before − 1) × 100` | Percentage change in total clicks |
| **Daily Click Avg** | `Clicks / Days in Period` | Per-day normalized clicks |
| **Daily Click Diff** | `After_Daily − Before_Daily` | Normalized click change per URL |
| **CTR Diff (pp)** | `CTR_After − CTR_Before` | CTR change in percentage points |
| **Position Diff** | `Pos_After − Pos_Before` | Position change (negative = improvement) |
| **Engagement Rate** | `Engaged / Total × 100` | % of sessions that were engaged |
| **Schema Lift** | `Avg Δ (with class) − Avg Δ (without class)` | Per-class click performance differential |

## AI Referral Sources

The following domains are recognized as AI referral sources by default:

| Source | Platform |
|---|---|
| `chatgpt.com` | ChatGPT |
| `chat.openai.com` | ChatGPT (legacy) |
| `perplexity.ai` | Perplexity |
| `gemini.google.com` | Google Gemini |
| `copilot.microsoft.com` | Microsoft Copilot |
| `claude.ai` | Anthropic Claude |
| `bard.google.com` | Google Bard (legacy) |
| `bing.com/chat` | Bing Chat |
| `you.com` | You.com |
| `poe.com` | Poe |
| `phind.com` | Phind |
| `meta.ai` | Meta AI |

Override this list in config under `analysis.ai_sources`.

## CausalImpact Analysis

The CausalImpact model uses a Bayesian structural time-series approach:
- **Pre-period**: "before" dates used to learn the relationship between variant and control
- **Post-period**: "after" dates where the model predicts what would have happened without intervention
- **Effect**: difference between observed and predicted (counterfactual)
- **p-value**: probability that the observed effect is due to chance
- Requires minimum ~7 days in both periods for reliable results
