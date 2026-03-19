#!/usr/bin/env python3
"""
Generic GA4 data puller for the SEO Performance Report skill.
Pulls engagement, AI referral traffic, channel data, and new/returning users.
Supports optional variant/control URL groups.

Usage:
    python3 scripts/ga4_pull.py --config config.yaml
"""

import argparse
import json
import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from urllib.parse import urlparse

try:
    import yaml
except ImportError:
    print("❌ PyYAML not installed. Run: python3 scripts/setup.py")
    sys.exit(1)

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    RunReportRequest, DateRange, Dimension, Metric,
    FilterExpression, Filter, OrderBy,
)

# Default AI referral sources
DEFAULT_AI_SOURCES = [
    'chatgpt.com', 'chat.openai.com', 'perplexity.ai',
    'gemini.google.com', 'copilot.microsoft.com', 'claude.ai',
    'bard.google.com', 'bing.com/chat', 'you.com',
    'poe.com', 'phind.com', 'meta.ai',
]

GA4_SCOPES = ['https://www.googleapis.com/auth/analytics.readonly']


# ─── Config ──────────────────────────────────────────────────────────────────

def load_config(config_path: str) -> dict:
    """Load and validate YAML configuration."""
    with open(config_path) as f:
        cfg = yaml.safe_load(f)

    if not cfg.get("ga4", {}).get("enabled", False):
        print("⚠️  GA4 is not enabled in config. Nothing to do.")
        sys.exit(0)

    ga4 = cfg["ga4"]
    if not ga4.get("property_id"):
        print("❌ GA4 property_id is required when ga4.enabled is true.")
        sys.exit(1)

    return cfg


# ─── Auth ────────────────────────────────────────────────────────────────────

def authenticate_ga4(cfg: dict) -> BetaAnalyticsDataClient:
    """Authenticate with GA4 Data API."""
    ga4_cfg = cfg["ga4"]
    client_secret = Path(ga4_cfg["client_secret"])
    creds_path = Path(ga4_cfg.get("credentials_cache", "ga4_credentials.json"))

    if not client_secret.exists():
        print(f"❌ Client secret not found: {client_secret}")
        sys.exit(1)

    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    print("🔐 Authenticating with GA4...")

    creds = None
    if creds_path.exists():
        creds = Credentials.from_authorized_user_file(str(creds_path), GA4_SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(client_secret), GA4_SCOPES)
            flow.redirect_uri = 'http://localhost:8080/'
            auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')
            print(f"\n1. Go to this URL:\n   {auth_url}")
            print("\n2. Authorize with your Google account")
            print("3. You'll be redirected to a localhost URL (will show error - that's OK)")
            print("4. Copy the entire localhost URL and paste it below\n")
            redirect_response = input("Paste the URL: ")
            flow.fetch_token(authorization_response=redirect_response)
            creds = flow.credentials
        with open(creds_path, 'w') as f:
            f.write(creds.to_json())

    client = BetaAnalyticsDataClient(credentials=creds)
    print("✅ Authenticated!")
    return client


# ─── GA4 Report Helper ──────────────────────────────────────────────────────

def run_ga4_report(client, property_id: str, dimensions: list, metrics: list,
                   date_start: str, date_end: str, limit: int = 10000) -> pd.DataFrame:
    """Run a GA4 report and return as DataFrame."""
    dim_objs = [Dimension(name=d) for d in dimensions]
    met_objs = [Metric(name=m) for m in metrics]

    request = RunReportRequest(
        property=f"properties/{property_id}",
        dimensions=dim_objs,
        metrics=met_objs,
        date_ranges=[DateRange(start_date=date_start, end_date=date_end)],
        limit=limit,
    )

    response = client.run_report(request)

    rows = []
    for row in response.rows:
        r = {}
        for i, dim in enumerate(dimensions):
            r[dim] = row.dimension_values[i].value
        for i, met in enumerate(metrics):
            val = row.metric_values[i].value
            try:
                r[met] = float(val)
            except (ValueError, TypeError):
                r[met] = val
        rows.append(r)

    return pd.DataFrame(rows)


# ─── URL Grouping ───────────────────────────────────────────────────────────

def to_path(url: str, domain: str) -> str:
    """Convert a full URL to its path component by stripping the domain."""
    parsed = urlparse(domain)
    domain_base = f"{parsed.scheme}://{parsed.netloc}"
    return url.replace(domain_base, '')


def tag_groups(df: pd.DataFrame, path_col: str, variant_paths: list,
               control_paths: list) -> pd.DataFrame:
    """Tag rows with their URL group."""
    df = df.copy()
    df['group'] = 'Other'
    for idx, row in df.iterrows():
        path = row[path_col]
        if path in variant_paths:
            df.loc[idx, 'group'] = 'Variant'
        elif path in control_paths:
            df.loc[idx, 'group'] = 'Control'
    return df


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Pull GA4 data for SEO report")
    parser.add_argument("--config", required=True, help="Path to config.yaml")
    args = parser.parse_args()

    cfg = load_config(args.config)
    client = authenticate_ga4(cfg)

    property_id = str(cfg["ga4"]["property_id"])
    domain = cfg["site"]["domain"]
    dates = cfg["dates"]
    date_start = dates["before_start"]
    date_end = dates["after_end"]
    out_dir = Path(cfg["output"]["directory"])
    out_dir.mkdir(parents=True, exist_ok=True)

    # AI sources — allow override in config
    ai_sources = cfg.get("analysis", {}).get("ai_sources", DEFAULT_AI_SOURCES)

    # Load URL groups if defined
    groups = cfg.get("groups", {})
    has_groups = bool(groups.get("variant_csv") and groups.get("control_csv"))
    variant_paths, control_paths = [], []

    if has_groups:
        variant_urls = pd.read_csv(groups["variant_csv"])['url'].dropna().unique().tolist()
        control_urls = pd.read_csv(groups["control_csv"])['url'].dropna().unique().tolist()
        variant_paths = [to_path(u, domain) for u in variant_urls]
        control_paths = [to_path(u, domain) for u in control_urls]
        print(f"   Variant: {len(variant_paths)} pages")
        print(f"   Control: {len(control_paths)} pages")

    # ── Report 1: Traffic by Source (AI referral detection) ──
    print("\n📡 Pulling traffic by source...")
    try:
        traffic = run_ga4_report(
            client, property_id,
            dimensions=['sessionSource', 'pagePath'],
            metrics=['sessions', 'totalUsers', 'engagedSessions',
                     'userEngagementDuration', 'screenPageViews', 'conversions'],
            date_start=date_start, date_end=date_end,
            limit=50000,
        )
        print(f"   Got {len(traffic)} source × page rows")

        traffic['is_ai'] = traffic['sessionSource'].isin(ai_sources)
        if has_groups:
            traffic = tag_groups(traffic, 'pagePath', variant_paths, control_paths)

        traffic.to_csv(out_dir / "ga4_traffic_by_source.csv", index=False)

        # AI summary
        ai_only = traffic[traffic['is_ai']]
        print(f"\n   AI Referral Traffic: {len(ai_only)} rows")
        if len(ai_only):
            ai_summary = ai_only.groupby('sessionSource').agg(
                sessions=('sessions', 'sum'),
                users=('totalUsers', 'sum'),
                pageviews=('screenPageViews', 'sum'),
            ).sort_values('sessions', ascending=False)
            print(ai_summary.to_string())
    except Exception as e:
        print(f"   ⚠️ Error: {e}")

    # ── Report 2: Engagement by landing page ──
    print("\n📡 Pulling engagement metrics...")
    try:
        engagement = run_ga4_report(
            client, property_id,
            dimensions=['landingPage', 'date', 'sessionDefaultChannelGroup'],
            metrics=['sessions', 'totalUsers', 'engagedSessions',
                     'userEngagementDuration', 'screenPageViews',
                     'bounceRate', 'averageSessionDuration'],
            date_start=date_start, date_end=date_end,
            limit=50000,
        )
        print(f"   Got {len(engagement)} rows")

        if has_groups:
            engagement = tag_groups(engagement, 'landingPage', variant_paths, control_paths)

        engagement.to_csv(out_dir / "ga4_engagement.csv", index=False)

        # Summary by group
        group_col = 'group' if has_groups else None
        groups_to_report = ['Variant', 'Control'] if has_groups else [None]
        for grp in groups_to_report:
            g = engagement[engagement['group'] == grp] if grp else engagement
            label = grp or "All Pages"
            if len(g):
                total_sessions = g['sessions'].sum()
                total_engaged = g['engagedSessions'].sum()
                eng_rate = total_engaged / total_sessions * 100 if total_sessions > 0 else 0
                avg_bounce = g['bounceRate'].mean() * 100
                avg_duration = g['averageSessionDuration'].mean()
                print(f"\n   📊 {label}:")
                print(f"      Sessions: {total_sessions:.0f}")
                print(f"      Engaged: {total_engaged:.0f} ({eng_rate:.1f}%)")
                print(f"      Avg Bounce: {avg_bounce:.1f}%")
                print(f"      Avg Duration: {avg_duration:.0f}s")
    except Exception as e:
        print(f"   ⚠️ Error: {e}")

    # ── Report 3: New vs Returning ──
    print("\n📡 Pulling new vs returning user data...")
    try:
        new_ret = run_ga4_report(
            client, property_id,
            dimensions=['landingPage', 'newVsReturning'],
            metrics=['sessions', 'totalUsers', 'engagedSessions'],
            date_start=date_start, date_end=date_end,
            limit=50000,
        )
        print(f"   Got {len(new_ret)} rows")

        if has_groups:
            new_ret = tag_groups(new_ret, 'landingPage', variant_paths, control_paths)

        new_ret.to_csv(out_dir / "ga4_new_vs_returning.csv", index=False)
    except Exception as e:
        print(f"   ⚠️ Error: {e}")

    # ── Report 4: Traffic by channel group ──
    print("\n📡 Pulling traffic by channel...")
    try:
        channels = run_ga4_report(
            client, property_id,
            dimensions=['landingPage', 'sessionDefaultChannelGroup'],
            metrics=['sessions', 'totalUsers', 'engagedSessions', 'conversions'],
            date_start=date_start, date_end=date_end,
            limit=50000,
        )
        print(f"   Got {len(channels)} rows")

        if has_groups:
            channels = tag_groups(channels, 'landingPage', variant_paths, control_paths)

        channels.to_csv(out_dir / "ga4_channels.csv", index=False)
    except Exception as e:
        print(f"   ⚠️ Error: {e}")

    print("\n✅ All GA4 data saved!")
    print(f"   ga4_traffic_by_source.csv")
    print(f"   ga4_engagement.csv")
    print(f"   ga4_new_vs_returning.csv")
    print(f"   ga4_channels.csv")


if __name__ == "__main__":
    main()
