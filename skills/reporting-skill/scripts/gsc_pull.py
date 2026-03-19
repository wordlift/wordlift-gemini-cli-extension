#!/usr/bin/env python3
"""
Generic GSC data puller for the SEO Performance Report skill.
Pulls clicks, impressions, CTR, position by date × page from Google Search Console.
Supports optional variant/control URL groups for A/B analysis.

Usage:
    python3 scripts/gsc_pull.py --config config.yaml
"""

import argparse
import sys
import time
import numpy as np
import pandas as pd
import searchconsole
from pathlib import Path
from tqdm import tqdm

try:
    import yaml
except ImportError:
    print("❌ PyYAML not installed. Run: python3 scripts/setup.py")
    sys.exit(1)


# ─── Config ──────────────────────────────────────────────────────────────────

def load_config(config_path: str) -> dict:
    """Load and validate YAML configuration."""
    with open(config_path) as f:
        cfg = yaml.safe_load(f)

    required = ["site", "dates", "output"]
    for key in required:
        if key not in cfg:
            print(f"❌ Missing required config section: '{key}'")
            sys.exit(1)

    if not cfg.get("gsc", {}).get("enabled", False):
        print("⚠️  GSC is not enabled in config. Nothing to do.")
        sys.exit(0)

    return cfg


# ─── Auth ────────────────────────────────────────────────────────────────────

def authenticate_gsc(cfg: dict):
    """Authenticate with Google Search Console API."""
    gsc_cfg = cfg["gsc"]
    client_secret = Path(gsc_cfg["client_secret"])
    credentials_cache = Path(gsc_cfg.get("credentials_cache", "credentials.json"))

    if not client_secret.exists():
        print(f"❌ Client secret not found: {client_secret}")
        print("   Download it from: Google Cloud Console → APIs & Services → Credentials")
        sys.exit(1)

    print("🔐 Authenticating with Google Search Console...")

    if credentials_cache.exists():
        print(f"   Found cached credentials: {credentials_cache}")
        account = searchconsole.authenticate(
            client_config=str(client_secret),
            credentials=str(credentials_cache),
        )
    else:
        print("   No cached credentials — you'll need to authorize in your browser.")
        account = searchconsole.authenticate(
            client_config=str(client_secret),
            serialize=str(credentials_cache),
            flow="console",
        )

    print("✅ Authenticated!")
    print(f"   Available properties: {[str(wp) for wp in account.webproperties]}")

    domain = cfg["site"]["domain"]
    webproperty = account[domain]
    if webproperty is None:
        print(f"❌ Could not find property '{domain}'. Available:")
        for wp in account.webproperties:
            print(f"   - {wp}")
        sys.exit(1)

    print(f"   Using property: {domain}")
    return webproperty


# ─── Data Pull ───────────────────────────────────────────────────────────────

def pull_gsc_for_urls(webproperty, urls: list, start_date: str, end_date: str,
                      label: str = "") -> pd.DataFrame:
    """Pull clicks/impressions/ctr/position by date for a list of URLs."""
    all_data = []
    errors = []

    for i, url in enumerate(tqdm(urls, desc=f"Pulling {label}")):
        # Rate limit: pause every 400 requests
        if i > 0 and i % 400 == 0:
            print(f"\n   ⏸️  Pausing 60s to avoid API rate limits...")
            time.sleep(60)

        try:
            q = (webproperty.query
                 .range(start=start_date, stop=end_date)
                 .dimension('date', 'page')
                 .filter('page', url, 'equals'))
            result = q.get()

            if result.rows:
                df = pd.DataFrame(result.rows)
                all_data.append(df)
        except Exception as e:
            errors.append((url, str(e)))

    if errors:
        print(f"\n   ⚠️  {len(errors)} errors:")
        for url, err in errors[:5]:
            print(f"      {url}: {err}")

    if all_data:
        return pd.concat(all_data, ignore_index=True)
    return pd.DataFrame()


def pull_gsc_site_wide(webproperty, start_date: str, end_date: str) -> pd.DataFrame:
    """Pull site-wide GSC data (no URL filter)."""
    print("📡 Pulling site-wide GSC data...")
    try:
        q = (webproperty.query
             .range(start=start_date, stop=end_date)
             .dimension('date', 'page'))
        result = q.get()
        if result.rows:
            df = pd.DataFrame(result.rows)
            print(f"   Got {len(df)} rows")
            return df
    except Exception as e:
        print(f"   ⚠️ Error: {e}")
    return pd.DataFrame()


# ─── Metrics Computation ────────────────────────────────────────────────────

def compute_period_metrics(gsc_df: pd.DataFrame, before_start: str,
                           before_end: str, after_start: str,
                           after_end: str) -> pd.DataFrame:
    """Aggregate metrics per URL for before/after periods."""
    gsc_df = gsc_df.copy()
    gsc_df['date'] = pd.to_datetime(gsc_df['date'])

    before = gsc_df[(gsc_df['date'] >= before_start) & (gsc_df['date'] <= before_end)]
    after = gsc_df[(gsc_df['date'] >= after_start) & (gsc_df['date'] <= after_end)]

    before_agg = before.groupby('page').agg(
        Clicks_Before=('clicks', 'sum'),
        Impr_Before=('impressions', 'sum'),
        CTR_Before=('ctr', 'mean'),
        Pos_Before=('position', 'mean'),
    ).reset_index()

    after_agg = after.groupby('page').agg(
        Clicks_After=('clicks', 'sum'),
        Impr_After=('impressions', 'sum'),
        CTR_After=('ctr', 'mean'),
        Pos_After=('position', 'mean'),
    ).reset_index()

    merged = before_agg.merge(after_agg, on='page', how='outer').fillna(0)
    merged['Clicks_Diff'] = merged['Clicks_After'] - merged['Clicks_Before']
    merged['Impr_Diff'] = merged['Impr_After'] - merged['Impr_Before']
    merged['CTR_Diff'] = merged['CTR_After'] - merged['CTR_Before']
    merged['Pos_Diff'] = merged['Pos_After'] - merged['Pos_Before']
    merged.rename(columns={'page': 'URL'}, inplace=True)

    return merged


def print_summary(tag: str, df: pd.DataFrame):
    """Print a summary of metrics for a group."""
    c_before = df['Clicks_Before'].sum()
    c_after = df['Clicks_After'].sum()
    pct = ((c_after / c_before) - 1) * 100 if c_before > 0 else 0

    print(f"\n📊 {tag} ({len(df)} URLs):")
    print(f"   Clicks:      {c_before:,.0f} → {c_after:,.0f} ({c_after - c_before:+,.0f}, {pct:+.1f}%)")
    print(f"   Impressions: {df['Impr_Before'].sum():,.0f} → {df['Impr_After'].sum():,.0f} ({df['Impr_Diff'].sum():+,.0f})")
    print(f"   Avg CTR:     {df['CTR_Before'].mean():.2%} → {df['CTR_After'].mean():.2%} ({df['CTR_Diff'].mean()*100:+.3f}pp)")
    print(f"   Avg Pos:     {df['Pos_Before'].mean():.1f} → {df['Pos_After'].mean():.1f} ({df['Pos_Diff'].mean():+.1f})")

    up = (df['Clicks_Diff'] > 0).sum()
    down = (df['Clicks_Diff'] < 0).sum()
    flat = (df['Clicks_Diff'] == 0).sum()
    print(f"   ↑ Gaining: {up} ({up/len(df):.0%})  ↓ Losing: {down} ({down/len(df):.0%})  = Flat: {flat} ({flat/len(df):.0%})")


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Pull GSC data for SEO report")
    parser.add_argument("--config", required=True, help="Path to config.yaml")
    args = parser.parse_args()

    cfg = load_config(args.config)
    webproperty = authenticate_gsc(cfg)

    dates = cfg["dates"]
    date_start = dates["before_start"]
    date_end = dates["after_end"]
    out_dir = Path(cfg["output"]["directory"])
    out_dir.mkdir(parents=True, exist_ok=True)

    groups = cfg.get("groups", {})
    has_groups = bool(groups.get("variant_csv") and groups.get("control_csv"))

    if has_groups:
        # ── A/B Mode: pull variant + control separately ──
        variant_csv = groups["variant_csv"]
        control_csv = groups["control_csv"]

        print(f"\n📊 Loading URL groups...")
        variant_urls = pd.read_csv(variant_csv)['url'].dropna().unique().tolist()
        control_urls = pd.read_csv(control_csv)['url'].dropna().unique().tolist()
        print(f"   Variant URLs: {len(variant_urls)}")
        print(f"   Control URLs: {len(control_urls)}")

        print(f"\n📡 Pulling GSC data: {date_start} → {date_end}")

        variant_gsc = pull_gsc_for_urls(webproperty, variant_urls, date_start, date_end, "Variant")
        control_gsc = pull_gsc_for_urls(webproperty, control_urls, date_start, date_end, "Control")

        # Save raw daily data
        variant_gsc.to_csv(out_dir / "gsc_variant.csv", index=False)
        control_gsc.to_csv(out_dir / "gsc_control.csv", index=False)
        print(f"\n💾 Saved raw data:")
        print(f"   gsc_variant.csv  ({len(variant_gsc)} rows)")
        print(f"   gsc_control.csv  ({len(control_gsc)} rows)")

        # Compute before/after metrics
        variant_metrics = compute_period_metrics(
            variant_gsc, dates["before_start"], dates["before_end"],
            dates["after_start"], dates["after_end"]
        )
        control_metrics = compute_period_metrics(
            control_gsc, dates["before_start"], dates["before_end"],
            dates["after_start"], dates["after_end"]
        )
        variant_metrics['Group'] = 'Variant'
        control_metrics['Group'] = 'Control'

        variant_metrics.to_csv(out_dir / "gsc_variant_metrics.csv", index=False)
        control_metrics.to_csv(out_dir / "gsc_control_metrics.csv", index=False)

        # Print summary
        print("\n" + "=" * 70)
        print(f"GSC ANALYSIS: Before ({dates['before_start']}–{dates['before_end']}) → After ({dates['after_start']}–{dates['after_end']})")
        print("=" * 70)
        print_summary("Variant", variant_metrics)
        print_summary("Control", control_metrics)
    else:
        # ── Site-wide mode ──
        gsc_data = pull_gsc_site_wide(webproperty, date_start, date_end)
        if gsc_data.empty:
            print("❌ No GSC data retrieved!")
            sys.exit(1)

        gsc_data.to_csv(out_dir / "gsc_daily.csv", index=False)
        print(f"\n💾 Saved gsc_daily.csv ({len(gsc_data)} rows)")

        site_metrics = compute_period_metrics(
            gsc_data, dates["before_start"], dates["before_end"],
            dates["after_start"], dates["after_end"]
        )
        site_metrics['Group'] = 'All Pages'
        site_metrics.to_csv(out_dir / "gsc_site_metrics.csv", index=False)

        print("\n" + "=" * 70)
        print(f"GSC ANALYSIS: Before ({dates['before_start']}–{dates['before_end']}) → After ({dates['after_start']}–{dates['after_end']})")
        print("=" * 70)
        print_summary("All Pages", site_metrics)

    print("\n✅ GSC data pull complete!")


if __name__ == "__main__":
    main()
