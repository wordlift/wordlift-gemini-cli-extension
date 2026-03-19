#!/usr/bin/env python3
"""
Generic analysis and chart generation for the SEO Performance Report skill.
Reads CSVs produced by gsc_pull.py and ga4_pull.py, generates charts + summary JSON.

Usage:
    python3 scripts/analyze.py --config config.yaml
"""

import argparse
import json
import sys
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend — no GUI window
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import matplotlib.dates as mdates
import seaborn as sns
from pathlib import Path
from datetime import datetime

try:
    import yaml
except ImportError:
    print("❌ PyYAML not installed. Run: python3 scripts/setup.py")
    sys.exit(1)

sns.set_theme(style="whitegrid", font_scale=1.1)

# ─── Color Palette ───────────────────────────────────────────────────────────
C_VARIANT = "#2563EB"
C_CONTROL = "#DC2626"
C_ACCENT  = "#10B981"
C_BEFORE  = "#93C5FD"
C_NEUTRAL = "#9CA3AF"


# ─── Config ──────────────────────────────────────────────────────────────────

def load_config(config_path: str) -> dict:
    with open(config_path) as f:
        return yaml.safe_load(f)


# ─── GSC Analysis ────────────────────────────────────────────────────────────

def analyze_gsc_groups(out_dir: Path, dates: dict, dpi: int, summary: dict):
    """Generate GSC charts for variant/control A/B mode."""
    variant_raw = pd.read_csv(out_dir / "gsc_variant.csv")
    control_raw = pd.read_csv(out_dir / "gsc_control.csv")
    variant_metrics = pd.read_csv(out_dir / "gsc_variant_metrics.csv")
    control_metrics = pd.read_csv(out_dir / "gsc_control_metrics.csv")

    variant_raw['date'] = pd.to_datetime(variant_raw['date'])
    control_raw['date'] = pd.to_datetime(control_raw['date'])

    before_start, before_end = dates["before_start"], dates["before_end"]
    after_start, after_end = dates["after_start"], dates["after_end"]
    days_before = (pd.Timestamp(before_end) - pd.Timestamp(before_start)).days + 1
    days_after = (pd.Timestamp(after_end) - pd.Timestamp(after_start)).days + 1

    # Add daily normalized columns
    for df in [variant_metrics, control_metrics]:
        df['Clicks_Before_Daily'] = df['Clicks_Before'] / days_before
        df['Clicks_After_Daily'] = df['Clicks_After'] / days_after
        df['Impr_Before_Daily'] = df['Impr_Before'] / days_before
        df['Impr_After_Daily'] = df['Impr_After'] / days_after
        df['Clicks_Daily_Diff'] = df['Clicks_After_Daily'] - df['Clicks_Before_Daily']
        df['Impr_Daily_Diff'] = df['Impr_After_Daily'] - df['Impr_Before_Daily']

    # ── Chart 1: Daily Clicks & Impressions ──
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle("Daily Avg Clicks & Impressions (Normalized)", fontsize=15, fontweight='bold', y=1.02)

    for ax, metric, label in zip(axes, ['Clicks', 'Impr'], ['Clicks', 'Impressions']):
        v_before = variant_metrics[f'{metric}_Before_Daily'].sum()
        v_after = variant_metrics[f'{metric}_After_Daily'].sum()
        c_before = control_metrics[f'{metric}_Before_Daily'].sum()
        c_after = control_metrics[f'{metric}_After_Daily'].sum()

        x = np.arange(2)
        w = 0.35
        bars1 = ax.bar(x - w/2, [v_before, c_before], w, label='Before', color=C_BEFORE, edgecolor='white')
        bars2 = ax.bar(x + w/2, [v_after, c_after], w, label='After', color=C_VARIANT, edgecolor='white')
        ax.set_xticks(x)
        ax.set_xticklabels(['Variant', 'Control'])
        ax.set_ylabel(f'{label} / Day')
        ax.set_title(f'Daily {label}', fontweight='bold')
        ax.legend()
        ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f'{x:,.0f}'))
        for bar in [*bars1, *bars2]:
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                    f'{bar.get_height():,.0f}', ha='center', va='bottom', fontsize=9)
    plt.tight_layout()
    fig.savefig(out_dir / "chart_01_daily_clicks_impressions.png", dpi=dpi, bbox_inches='tight')
    plt.close()
    print("   ✅ chart_01_daily_clicks_impressions.png")

    # ── Chart 2: CTR & Position ──
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle("CTR & Position Changes", fontsize=15, fontweight='bold', y=1.02)
    for ax, metric, label in zip(axes, ['CTR', 'Pos'], ['CTR (%)', 'Avg Position']):
        v_before = variant_metrics[f'{metric}_Before'].mean()
        v_after = variant_metrics[f'{metric}_After'].mean()
        c_before = control_metrics[f'{metric}_Before'].mean()
        c_after = control_metrics[f'{metric}_After'].mean()
        x = np.arange(2)
        w = 0.35
        bars1 = ax.bar(x - w/2, [v_before, c_before], w, label='Before', color=C_BEFORE, edgecolor='white')
        bars2 = ax.bar(x + w/2, [v_after, c_after], w, label='After', color=C_VARIANT, edgecolor='white')
        ax.set_xticks(x)
        ax.set_xticklabels(['Variant', 'Control'])
        ax.set_ylabel(label)
        ax.set_title(f'Average {label}', fontweight='bold')
        ax.legend()
        for bar in [*bars1, *bars2]:
            val = bar.get_height()
            txt = f'{val:.1f}' if metric == 'Pos' else f'{val:.2%}'
            ax.text(bar.get_x() + bar.get_width()/2, val, txt, ha='center', va='bottom', fontsize=9)
    plt.tight_layout()
    fig.savefig(out_dir / "chart_02_ctr_position.png", dpi=dpi, bbox_inches='tight')
    plt.close()
    print("   ✅ chart_02_ctr_position.png")

    # ── Chart 3: Daily Clicks Time Series ──
    fig, ax = plt.subplots(figsize=(14, 6))
    v_daily = variant_raw.groupby('date')['clicks'].sum()
    c_daily = control_raw.groupby('date')['clicks'].sum()
    ax.plot(v_daily.index, v_daily.values, color=C_VARIANT, linewidth=2, label='Variant', marker='o', markersize=4)
    ax.plot(c_daily.index, c_daily.values, color=C_CONTROL, linewidth=2, label='Control', marker='o', markersize=4)
    ax.axvline(pd.Timestamp(after_start), color='black', linestyle='--', linewidth=1.5, alpha=0.7, label=f'Intervention ({after_start})')
    ax.fill_between(v_daily.index, 0, v_daily.values, alpha=0.1, color=C_VARIANT)
    ax.fill_between(c_daily.index, 0, c_daily.values, alpha=0.1, color=C_CONTROL)
    ax.set_xlabel('Date')
    ax.set_ylabel('Total Daily Clicks')
    ax.set_title('Daily Clicks Over Time: Variant vs Control', fontweight='bold', fontsize=14)
    ax.legend(fontsize=11)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
    ax.tick_params(axis='x', rotation=45)
    plt.tight_layout()
    fig.savefig(out_dir / "chart_03_daily_clicks_timeseries.png", dpi=dpi, bbox_inches='tight')
    plt.close()
    print("   ✅ chart_03_daily_clicks_timeseries.png")

    # ── Chart 4: Daily Impressions Time Series ──
    fig, ax = plt.subplots(figsize=(14, 6))
    v_daily_impr = variant_raw.groupby('date')['impressions'].sum()
    c_daily_impr = control_raw.groupby('date')['impressions'].sum()
    ax.plot(v_daily_impr.index, v_daily_impr.values, color=C_VARIANT, linewidth=2, label='Variant', marker='o', markersize=4)
    ax.plot(c_daily_impr.index, c_daily_impr.values, color=C_CONTROL, linewidth=2, label='Control', marker='o', markersize=4)
    ax.axvline(pd.Timestamp(after_start), color='black', linestyle='--', linewidth=1.5, alpha=0.7, label=f'Intervention ({after_start})')
    ax.set_xlabel('Date')
    ax.set_ylabel('Total Daily Impressions')
    ax.set_title('Daily Impressions Over Time: Variant vs Control', fontweight='bold', fontsize=14)
    ax.legend(fontsize=11)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
    ax.tick_params(axis='x', rotation=45)
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f'{x:,.0f}'))
    plt.tight_layout()
    fig.savefig(out_dir / "chart_04_daily_impressions_timeseries.png", dpi=dpi, bbox_inches='tight')
    plt.close()
    print("   ✅ chart_04_daily_impressions_timeseries.png")

    # ── Chart 5: Click Diff Distribution ──
    fig, ax = plt.subplots(figsize=(12, 6))
    bins = np.linspace(
        min(variant_metrics['Clicks_Daily_Diff'].min(), control_metrics['Clicks_Daily_Diff'].min()),
        max(variant_metrics['Clicks_Daily_Diff'].max(), control_metrics['Clicks_Daily_Diff'].max()),
        40,
    )
    ax.hist(variant_metrics['Clicks_Daily_Diff'], bins=bins, alpha=0.6, label='Variant', color=C_VARIANT, edgecolor='white')
    ax.hist(control_metrics['Clicks_Daily_Diff'], bins=bins, alpha=0.6, label='Control', color=C_CONTROL, edgecolor='white')
    ax.axvline(0, color='black', linestyle='--', linewidth=1, alpha=0.5)
    v_med = variant_metrics['Clicks_Daily_Diff'].median()
    c_med = control_metrics['Clicks_Daily_Diff'].median()
    ax.axvline(v_med, color=C_VARIANT, linestyle='--', linewidth=2, alpha=0.8, label=f'Variant Median ({v_med:+.2f})')
    ax.axvline(c_med, color=C_CONTROL, linestyle='--', linewidth=2, alpha=0.8, label=f'Control Median ({c_med:+.2f})')
    ax.set_xlabel('Daily Click Difference (After − Before)')
    ax.set_ylabel('Number of URLs')
    ax.set_title('Distribution of Daily Click Changes per URL', fontweight='bold', fontsize=14)
    ax.legend()
    plt.tight_layout()
    fig.savefig(out_dir / "chart_05_click_diff_distribution.png", dpi=dpi, bbox_inches='tight')
    plt.close()
    print("   ✅ chart_05_click_diff_distribution.png")

    # ── Chart 6: Positive vs Negative URLs ──
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle("% of URLs with Positive vs Negative Daily Click Changes", fontsize=15, fontweight='bold', y=1.02)
    for ax, (tag, df) in zip(axes, [('Variant', variant_metrics), ('Control', control_metrics)]):
        pos = (df['Clicks_Daily_Diff'] > 0).sum()
        neg = (df['Clicks_Daily_Diff'] < 0).sum()
        zero = (df['Clicks_Daily_Diff'] == 0).sum()
        total = len(df)
        values = [pos, neg, zero]
        labels_pie = [f'Positive\n({pos}, {pos/total:.0%})',
                      f'Negative\n({neg}, {neg/total:.0%})',
                      f'No Change\n({zero}, {zero/total:.0%})']
        colors = [C_ACCENT, C_CONTROL, C_NEUTRAL]
        ax.pie(values, labels=labels_pie, colors=colors, autopct='', startangle=90, textprops={'fontsize': 11})
        ax.set_title(f'{tag}\n(n={total})', fontweight='bold', fontsize=13)
    plt.tight_layout()
    fig.savefig(out_dir / "chart_06_positive_negative_urls.png", dpi=dpi, bbox_inches='tight')
    plt.close()
    print("   ✅ chart_06_positive_negative_urls.png")

    # ── Chart 7: Top 20 Gainers ──
    top = variant_metrics.nlargest(20, 'Clicks_Diff')[['URL', 'Clicks_Before', 'Clicks_After', 'Clicks_Diff']]
    top['URL_short'] = top['URL'].str[-60:]
    fig, ax = plt.subplots(figsize=(14, 8))
    colors = [C_ACCENT if d > 0 else C_CONTROL for d in top['Clicks_Diff']]
    bars = ax.barh(range(len(top)), top['Clicks_Diff'], color=colors, edgecolor='white')
    ax.set_yticks(range(len(top)))
    ax.set_yticklabels(top['URL_short'], fontsize=9)
    ax.invert_yaxis()
    ax.set_xlabel('Click Difference (Total)')
    ax.set_title(f'Top 20 Click Gainers — Variant ({after_start} – {after_end})', fontweight='bold', fontsize=14)
    ax.axvline(0, color='black', linewidth=0.5)
    for bar, val in zip(bars, top['Clicks_Diff']):
        ax.text(bar.get_width() + 2, bar.get_y() + bar.get_height()/2,
                f'{val:+.0f}', va='center', fontsize=9)
    plt.tight_layout()
    fig.savefig(out_dir / "chart_07_top_gainers.png", dpi=dpi, bbox_inches='tight')
    plt.close()
    print("   ✅ chart_07_top_gainers.png")

    # ── Chart 8: Net Change ──
    fig, ax = plt.subplots(figsize=(10, 6))
    categories = ['Daily Clicks', 'Daily Impressions']
    v_diffs = [variant_metrics['Clicks_Daily_Diff'].sum(), variant_metrics['Impr_Daily_Diff'].sum()]
    c_diffs = [control_metrics['Clicks_Daily_Diff'].sum(), control_metrics['Impr_Daily_Diff'].sum()]
    x = np.arange(len(categories))
    w = 0.35
    bars1 = ax.bar(x - w/2, v_diffs, w, label='Variant', color=C_VARIANT, edgecolor='white')
    bars2 = ax.bar(x + w/2, c_diffs, w, label='Control', color=C_CONTROL, edgecolor='white')
    ax.set_xticks(x)
    ax.set_xticklabels(categories, fontsize=12)
    ax.set_ylabel('Net Daily Difference')
    ax.set_title('Net Daily Change: Variant vs Control', fontweight='bold', fontsize=14)
    ax.axhline(0, color='black', linewidth=0.5)
    ax.legend(fontsize=12)
    for bar in [*bars1, *bars2]:
        val = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, val, f'{val:+,.0f}',
                ha='center', va='bottom' if val >= 0 else 'top', fontsize=11, fontweight='bold')
    plt.tight_layout()
    fig.savefig(out_dir / "chart_08_net_daily_change.png", dpi=dpi, bbox_inches='tight')
    plt.close()
    print("   ✅ chart_08_net_daily_change.png")

    # ── Build summary data ──
    v_cb = variant_metrics['Clicks_Before'].sum()
    v_ca = variant_metrics['Clicks_After'].sum()
    c_cb = control_metrics['Clicks_Before'].sum()
    c_ca = control_metrics['Clicks_After'].sum()

    summary["gsc"] = {
        "mode": "groups",
        "variant": {
            "n_urls": len(variant_metrics),
            "clicks_before": float(v_cb), "clicks_after": float(v_ca),
            "clicks_diff": float(v_ca - v_cb),
            "clicks_pct": float(((v_ca / v_cb) - 1) * 100) if v_cb > 0 else 0,
            "impr_before": float(variant_metrics['Impr_Before'].sum()),
            "impr_after": float(variant_metrics['Impr_After'].sum()),
            "avg_ctr_before": float(variant_metrics['CTR_Before'].mean()),
            "avg_ctr_after": float(variant_metrics['CTR_After'].mean()),
            "avg_pos_before": float(variant_metrics['Pos_Before'].mean()),
            "avg_pos_after": float(variant_metrics['Pos_After'].mean()),
            "urls_gaining": int((variant_metrics['Clicks_Diff'] > 0).sum()),
            "urls_losing": int((variant_metrics['Clicks_Diff'] < 0).sum()),
            "urls_flat": int((variant_metrics['Clicks_Diff'] == 0).sum()),
        },
        "control": {
            "n_urls": len(control_metrics),
            "clicks_before": float(c_cb), "clicks_after": float(c_ca),
            "clicks_diff": float(c_ca - c_cb),
            "clicks_pct": float(((c_ca / c_cb) - 1) * 100) if c_cb > 0 else 0,
            "impr_before": float(control_metrics['Impr_Before'].sum()),
            "impr_after": float(control_metrics['Impr_After'].sum()),
            "avg_ctr_before": float(control_metrics['CTR_Before'].mean()),
            "avg_ctr_after": float(control_metrics['CTR_After'].mean()),
            "avg_pos_before": float(control_metrics['Pos_Before'].mean()),
            "avg_pos_after": float(control_metrics['Pos_After'].mean()),
            "urls_gaining": int((control_metrics['Clicks_Diff'] > 0).sum()),
            "urls_losing": int((control_metrics['Clicks_Diff'] < 0).sum()),
            "urls_flat": int((control_metrics['Clicks_Diff'] == 0).sum()),
        },
        "days_before": days_before,
        "days_after": days_after,
    }

    return variant_raw, control_raw, variant_metrics, control_metrics


def analyze_gsc_sitewide(out_dir: Path, dates: dict, dpi: int, summary: dict):
    """Generate GSC charts for site-wide mode (no groups)."""
    gsc_raw = pd.read_csv(out_dir / "gsc_daily.csv")
    site_metrics = pd.read_csv(out_dir / "gsc_site_metrics.csv")
    gsc_raw['date'] = pd.to_datetime(gsc_raw['date'])

    before_start, before_end = dates["before_start"], dates["before_end"]
    after_start, after_end = dates["after_start"], dates["after_end"]
    days_before = (pd.Timestamp(before_end) - pd.Timestamp(before_start)).days + 1
    days_after = (pd.Timestamp(after_end) - pd.Timestamp(after_start)).days + 1

    # Daily normalized
    site_metrics['Clicks_Before_Daily'] = site_metrics['Clicks_Before'] / days_before
    site_metrics['Clicks_After_Daily'] = site_metrics['Clicks_After'] / days_after
    site_metrics['Clicks_Daily_Diff'] = site_metrics['Clicks_After_Daily'] - site_metrics['Clicks_Before_Daily']

    # ── Chart: Daily Clicks Time Series ──
    fig, ax = plt.subplots(figsize=(14, 6))
    daily = gsc_raw.groupby('date')['clicks'].sum()
    ax.plot(daily.index, daily.values, color=C_VARIANT, linewidth=2, marker='o', markersize=4)
    ax.axvline(pd.Timestamp(after_start), color='black', linestyle='--', linewidth=1.5, alpha=0.7, label=f'Intervention ({after_start})')
    ax.fill_between(daily.index, 0, daily.values, alpha=0.1, color=C_VARIANT)
    ax.set_xlabel('Date')
    ax.set_ylabel('Total Daily Clicks')
    ax.set_title('Daily Clicks Over Time', fontweight='bold', fontsize=14)
    ax.legend(fontsize=11)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
    ax.tick_params(axis='x', rotation=45)
    plt.tight_layout()
    fig.savefig(out_dir / "chart_03_daily_clicks_timeseries.png", dpi=dpi, bbox_inches='tight')
    plt.close()
    print("   ✅ chart_03_daily_clicks_timeseries.png")

    # ── Chart: Top 20 Gainers ──
    top = site_metrics.nlargest(20, 'Clicks_Diff')[['URL', 'Clicks_Before', 'Clicks_After', 'Clicks_Diff']]
    if len(top) > 0:
        top['URL_short'] = top['URL'].str[-60:]
        fig, ax = plt.subplots(figsize=(14, 8))
        colors = [C_ACCENT if d > 0 else C_CONTROL for d in top['Clicks_Diff']]
        bars = ax.barh(range(len(top)), top['Clicks_Diff'], color=colors, edgecolor='white')
        ax.set_yticks(range(len(top)))
        ax.set_yticklabels(top['URL_short'], fontsize=9)
        ax.invert_yaxis()
        ax.set_xlabel('Click Difference (Total)')
        ax.set_title('Top 20 Click Gainers', fontweight='bold', fontsize=14)
        ax.axvline(0, color='black', linewidth=0.5)
        plt.tight_layout()
        fig.savefig(out_dir / "chart_07_top_gainers.png", dpi=dpi, bbox_inches='tight')
        plt.close()
        print("   ✅ chart_07_top_gainers.png")

    cb = site_metrics['Clicks_Before'].sum()
    ca = site_metrics['Clicks_After'].sum()
    summary["gsc"] = {
        "mode": "sitewide",
        "all_pages": {
            "n_urls": len(site_metrics),
            "clicks_before": float(cb), "clicks_after": float(ca),
            "clicks_diff": float(ca - cb),
            "clicks_pct": float(((ca / cb) - 1) * 100) if cb > 0 else 0,
            "impr_before": float(site_metrics['Impr_Before'].sum()),
            "impr_after": float(site_metrics['Impr_After'].sum()),
            "avg_ctr_before": float(site_metrics['CTR_Before'].mean()),
            "avg_ctr_after": float(site_metrics['CTR_After'].mean()),
            "avg_pos_before": float(site_metrics['Pos_Before'].mean()),
            "avg_pos_after": float(site_metrics['Pos_After'].mean()),
            "urls_gaining": int((site_metrics['Clicks_Diff'] > 0).sum()),
            "urls_losing": int((site_metrics['Clicks_Diff'] < 0).sum()),
        },
        "days_before": days_before,
        "days_after": days_after,
    }


# ─── GA4 Analysis ────────────────────────────────────────────────────────────

def analyze_ga4(out_dir: Path, dpi: int, summary: dict, has_groups: bool):
    """Generate GA4 charts from pulled data."""

    # ── AI Referral Traffic ──
    traffic_path = out_dir / "ga4_traffic_by_source.csv"
    if traffic_path.exists():
        traffic = pd.read_csv(traffic_path)
        ai_only = traffic[traffic['is_ai'] == True]

        if len(ai_only) > 0:
            ai_by_source = ai_only.groupby('sessionSource').agg(
                sessions=('sessions', 'sum'),
                users=('totalUsers', 'sum'),
                pageviews=('screenPageViews', 'sum'),
            ).sort_values('sessions', ascending=True)

            fig, ax = plt.subplots(figsize=(12, 6))
            bars = ax.barh(ai_by_source.index, ai_by_source['sessions'], color=C_VARIANT, edgecolor='white')
            ax.set_xlabel('Sessions')
            ax.set_title('AI Referral Traffic by Source', fontweight='bold', fontsize=14)
            for bar, val in zip(bars, ai_by_source['sessions']):
                ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2,
                        f'{val:,.0f}', va='center', fontsize=10)
            plt.tight_layout()
            fig.savefig(out_dir / "chart_09_ai_by_source.png", dpi=dpi, bbox_inches='tight')
            plt.close()
            print("   ✅ chart_09_ai_by_source.png")

            # AI by group (if groups defined)
            if has_groups and 'group' in ai_only.columns:
                ai_by_group = ai_only.groupby('group')['sessions'].sum().sort_values(ascending=False)
                fig, ax = plt.subplots(figsize=(10, 5))
                ax.bar(ai_by_group.index, ai_by_group.values, color=[C_VARIANT, C_CONTROL, C_NEUTRAL][:len(ai_by_group)], edgecolor='white')
                ax.set_ylabel('AI Referral Sessions')
                ax.set_title('AI Referral Traffic by Page Group', fontweight='bold', fontsize=14)
                for i, (grp, val) in enumerate(ai_by_group.items()):
                    ax.text(i, val, f'{val:,.0f}', ha='center', va='bottom', fontsize=11, fontweight='bold')
                plt.tight_layout()
                fig.savefig(out_dir / "chart_10_ai_by_group.png", dpi=dpi, bbox_inches='tight')
                plt.close()
                print("   ✅ chart_10_ai_by_group.png")

            summary["ga4_ai"] = {
                "total_ai_sessions": float(ai_only['sessions'].sum()),
                "total_ai_users": float(ai_only['totalUsers'].sum()),
                "top_source": ai_by_source.index[-1] if len(ai_by_source) > 0 else "N/A",
                "by_source": {src: float(val) for src, val in ai_by_source['sessions'].items()},
            }

    # ── Engagement ──
    engagement_path = out_dir / "ga4_engagement.csv"
    if engagement_path.exists():
        engagement = pd.read_csv(engagement_path)

        if has_groups and 'group' in engagement.columns:
            groups_list = ['Variant', 'Control']
        else:
            groups_list = [None]

        eng_data = []
        for grp in groups_list:
            g = engagement[engagement['group'] == grp] if grp else engagement
            label = grp or "All Pages"
            if len(g):
                total_sessions = g['sessions'].sum()
                total_engaged = g['engagedSessions'].sum()
                eng_data.append({
                    "group": label,
                    "sessions": float(total_sessions),
                    "engaged_sessions": float(total_engaged),
                    "engagement_rate": float(total_engaged / total_sessions * 100) if total_sessions > 0 else 0,
                    "avg_bounce_rate": float(g['bounceRate'].mean() * 100),
                    "avg_duration": float(g['averageSessionDuration'].mean()),
                })

        if eng_data:
            fig, axes = plt.subplots(1, 3, figsize=(18, 6))
            fig.suptitle("Engagement Metrics", fontsize=15, fontweight='bold', y=1.02)
            labels = [d['group'] for d in eng_data]
            colors = [C_VARIANT, C_CONTROL][:len(eng_data)] if has_groups else [C_VARIANT]

            for ax, metric, title, fmt in zip(
                axes,
                ['engagement_rate', 'avg_bounce_rate', 'avg_duration'],
                ['Engagement Rate (%)', 'Avg Bounce Rate (%)', 'Avg Duration (s)'],
                ['.1f', '.1f', '.0f'],
            ):
                vals = [d[metric] for d in eng_data]
                bars = ax.bar(labels, vals, color=colors, edgecolor='white')
                ax.set_title(title, fontweight='bold')
                for bar, val in zip(bars, vals):
                    ax.text(bar.get_x() + bar.get_width()/2, val,
                            f'{val:{fmt}}', ha='center', va='bottom', fontsize=11)
            plt.tight_layout()
            fig.savefig(out_dir / "chart_11_engagement.png", dpi=dpi, bbox_inches='tight')
            plt.close()
            print("   ✅ chart_11_engagement.png")

            summary["ga4_engagement"] = eng_data

    # ── Channels ──
    channels_path = out_dir / "ga4_channels.csv"
    if channels_path.exists():
        channels = pd.read_csv(channels_path)

        if has_groups and 'group' in channels.columns:
            fig, axes = plt.subplots(1, 2, figsize=(16, 7))
            fig.suptitle('Traffic by Channel Group', fontsize=15, fontweight='bold', y=1.02)
            for ax, grp in zip(axes, ['Variant', 'Control']):
                g = channels[channels['group'] == grp]
                ch = g.groupby('sessionDefaultChannelGroup')['sessions'].sum().sort_values(ascending=True).tail(8)
                ax.barh(ch.index, ch.values, color=C_VARIANT if grp == 'Variant' else C_CONTROL, edgecolor='white')
                ax.set_xlabel('Sessions')
                ax.set_title(f'{grp}', fontweight='bold')
            plt.tight_layout()
            fig.savefig(out_dir / "chart_12_channels.png", dpi=dpi, bbox_inches='tight')
            plt.close()
        else:
            ch = channels.groupby('sessionDefaultChannelGroup')['sessions'].sum().sort_values(ascending=True).tail(10)
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.barh(ch.index, ch.values, color=C_VARIANT, edgecolor='white')
            ax.set_xlabel('Sessions')
            ax.set_title('Traffic by Channel Group', fontweight='bold', fontsize=14)
            plt.tight_layout()
            fig.savefig(out_dir / "chart_12_channels.png", dpi=dpi, bbox_inches='tight')
            plt.close()
        print("   ✅ chart_12_channels.png")


# ─── Causal Impact ───────────────────────────────────────────────────────────

def run_causal_impact(out_dir: Path, dates: dict, dpi: int, summary: dict):
    """Run CausalImpact analysis on variant vs control daily data."""
    try:
        from causalimpact import CausalImpact
    except ImportError:
        print("   ⚠️ pycausalimpact not installed — skipping causal impact analysis.")
        return

    variant_raw = pd.read_csv(out_dir / "gsc_variant.csv")
    control_raw = pd.read_csv(out_dir / "gsc_control.csv")
    variant_raw['date'] = pd.to_datetime(variant_raw['date'])
    control_raw['date'] = pd.to_datetime(control_raw['date'])

    before_start = dates["before_start"]
    before_end = dates["before_end"]
    after_start = dates["after_start"]
    after_end = dates["after_end"]

    print("\n📈 Running Causal Impact Analysis...")

    # Clicks
    v_ts = variant_raw.groupby('date')['clicks'].sum().rename('variant')
    c_ts = control_raw.groupby('date')['clicks'].sum().rename('control')
    ci_data = pd.concat([v_ts, c_ts], axis=1).sort_index().fillna(0)

    pre_period = [before_start, before_end]
    post_period = [after_start, after_end]

    try:
        ci = CausalImpact(ci_data, pre_period, post_period)
        ci_summary = ci.summary()
        ci_report = ci.summary(output='report')

        fig = ci.plot()
        fig.savefig(out_dir / "chart_13_causal_impact_clicks.png", dpi=dpi, bbox_inches='tight')
        plt.close()
        print("   ✅ chart_13_causal_impact_clicks.png")

        # Impressions
        v_ts_i = variant_raw.groupby('date')['impressions'].sum().rename('variant')
        c_ts_i = control_raw.groupby('date')['impressions'].sum().rename('control')
        ci_data_i = pd.concat([v_ts_i, c_ts_i], axis=1).sort_index().fillna(0)
        ci_impr = CausalImpact(ci_data_i, pre_period, post_period)

        fig_i = ci_impr.plot()
        fig_i.savefig(out_dir / "chart_14_causal_impact_impressions.png", dpi=dpi, bbox_inches='tight')
        plt.close()
        print("   ✅ chart_14_causal_impact_impressions.png")

        # Save text report
        with open(out_dir / "causal_impact_report.txt", 'w') as f:
            f.write("CAUSAL IMPACT ANALYSIS — CLICKS\n")
            f.write("=" * 60 + "\n")
            f.write(ci_summary + "\n\n")
            f.write(ci_report + "\n\n")
            f.write("\nCAUSAL IMPACT ANALYSIS — IMPRESSIONS\n")
            f.write("=" * 60 + "\n")
            f.write(ci_impr.summary() + "\n\n")
            f.write(ci_impr.summary(output='report') + "\n")
        print("   ✅ causal_impact_report.txt")

        summary["causal_impact"] = {
            "clicks_summary": ci_summary,
            "clicks_report": ci_report,
            "impressions_summary": ci_impr.summary(),
        }
    except Exception as e:
        print(f"   ⚠️ CausalImpact failed: {e}")


# ─── Schema Class Analysis ──────────────────────────────────────────────────

def analyze_schema_classes(out_dir: Path, entity_csv: str, dpi: int, summary: dict):
    """Analyze performance by schema.org class from entity matrix."""
    entity_df = pd.read_csv(entity_csv)
    variant_metrics = pd.read_csv(out_dir / "gsc_variant_metrics.csv")

    # Add daily diff if missing
    if 'Clicks_Daily_Diff' not in variant_metrics.columns:
        # Approximate — full normalization done elsewhere
        variant_metrics['Clicks_Daily_Diff'] = variant_metrics['Clicks_Diff']

    schema_classes = [c for c in entity_df.columns if c != 'url']
    for col in schema_classes:
        entity_df[col] = entity_df[col].apply(lambda x: x == '✅' if isinstance(x, str) else bool(x))

    merged = variant_metrics.merge(entity_df, left_on='URL', right_on='url', how='left')
    for col in schema_classes:
        merged[col] = merged[col].fillna(False)

    rows = []
    for cls in schema_classes:
        has = merged[merged[cls] == True]
        hasnt = merged[merged[cls] == False]
        if len(has) < 3:
            continue
        rows.append({
            'Schema Class': cls,
            'URLs With': len(has),
            'Avg Daily Click Δ (With)': has['Clicks_Daily_Diff'].mean(),
            'Avg Daily Click Δ (Without)': hasnt['Clicks_Daily_Diff'].mean(),
            'Avg CTR Δ (With)': has['CTR_Diff'].mean(),
            'Avg Pos Δ (With)': has['Pos_Diff'].mean(),
            '% Positive (With)': (has['Clicks_Daily_Diff'] > 0).mean() * 100,
        })

    if not rows:
        print("   ⚠️ No schema classes with enough data.")
        return

    perf_df = pd.DataFrame(rows)
    perf_df['Lift'] = perf_df['Avg Daily Click Δ (With)'] - perf_df['Avg Daily Click Δ (Without)']
    perf_df = perf_df.sort_values('Lift', ascending=False)

    # Schema class lift chart
    fig, ax = plt.subplots(figsize=(14, 7))
    colors = [C_ACCENT if v > 0 else '#EF4444' for v in perf_df['Lift']]
    bars = ax.barh(perf_df['Schema Class'], perf_df['Lift'], color=colors, edgecolor='white')
    ax.set_xlabel('Lift in Avg Daily Click Δ (With − Without)', fontsize=12)
    ax.set_title('Click Performance Lift by Schema.org Class', fontweight='bold', fontsize=14)
    ax.axvline(0, color='black', linewidth=0.5)
    ax.invert_yaxis()
    for bar, n in zip(bars, perf_df['URLs With']):
        val = bar.get_width()
        ax.text(val + (0.1 if val >= 0 else -0.1), bar.get_y() + bar.get_height()/2,
                f'{val:+.2f}  (n={n})', va='center', ha='left' if val >= 0 else 'right', fontsize=9)
    plt.tight_layout()
    fig.savefig(out_dir / "chart_15_schema_class_lift.png", dpi=dpi, bbox_inches='tight')
    plt.close()
    print("   ✅ chart_15_schema_class_lift.png")

    # Heatmap
    heat_data = perf_df.set_index('Schema Class')[
        ['Avg Daily Click Δ (With)', 'Avg CTR Δ (With)', 'Avg Pos Δ (With)', '% Positive (With)', 'URLs With']
    ].copy()
    heat_data.columns = ['Avg Daily Click Δ', 'Avg CTR Δ', 'Avg Pos Δ', '% URLs +Clicks', 'n URLs']
    fig, ax = plt.subplots(figsize=(12, 8))
    sns.heatmap(heat_data, annot=True, fmt='.2f', cmap='RdYlGn', center=0,
                linewidths=0.5, ax=ax, cbar_kws={'label': 'Value'})
    ax.set_title('Schema Class Performance Heatmap', fontweight='bold', fontsize=14)
    plt.tight_layout()
    fig.savefig(out_dir / "chart_16_schema_heatmap.png", dpi=dpi, bbox_inches='tight')
    plt.close()
    print("   ✅ chart_16_schema_heatmap.png")

    summary["schema_classes"] = perf_df.to_dict(orient='records')


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Generate SEO analysis charts")
    parser.add_argument("--config", required=True, help="Path to config.yaml")
    args = parser.parse_args()

    cfg = load_config(args.config)
    dates = cfg["dates"]
    out_dir = Path(cfg["output"]["directory"])
    dpi = cfg.get("output", {}).get("chart_dpi", 150)
    analysis = cfg.get("analysis", {})
    groups = cfg.get("groups", {})
    has_groups = bool(groups.get("variant_csv") and groups.get("control_csv"))

    summary = {
        "site": cfg["site"],
        "dates": dates,
        "generated_at": datetime.now().isoformat(),
    }

    # ── GSC Analysis ──
    gsc_enabled = cfg.get("gsc", {}).get("enabled", False)
    if gsc_enabled:
        print("\n📊 Generating GSC analysis charts...")
        if has_groups:
            analyze_gsc_groups(out_dir, dates, dpi, summary)
        else:
            analyze_gsc_sitewide(out_dir, dates, dpi, summary)

    # ── GA4 Analysis ──
    ga4_enabled = cfg.get("ga4", {}).get("enabled", False)
    if ga4_enabled:
        print("\n📊 Generating GA4 analysis charts...")
        analyze_ga4(out_dir, dpi, summary, has_groups)

    # ── Causal Impact ──
    if analysis.get("causal_impact", False) and has_groups and gsc_enabled:
        run_causal_impact(out_dir, dates, dpi, summary)
    elif analysis.get("causal_impact", False):
        print("\n⚠️ Causal impact requires variant/control groups and GSC data — skipping.")

    # ── Schema Class Analysis ──
    entity_csv = analysis.get("entity_matrix_csv", "")
    if analysis.get("schema_analysis", False) and entity_csv and has_groups:
        print("\n📊 Analyzing schema class performance...")
        analyze_schema_classes(out_dir, entity_csv, dpi, summary)

    # ── Save Summary ──
    summary_path = out_dir / "analysis_summary.json"
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2, default=str)
    print(f"\n💾 Saved analysis_summary.json")

    plt.close('all')
    print("\n✅ All analysis and charts complete!")


if __name__ == "__main__":
    main()
