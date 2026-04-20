#!/usr/bin/env python3
"""
compute_roas.py — Deterministic ROAS & Causal Impact computation
=================================================================
Two-phase design:

  PHASE 1 (schema inspection) — run with --inspect-only:
      python3 compute_roas.py --inspect-only \
          --campaign <path> --groups <path> [--keywords <path>]

      Prints the detected column headers as JSON so the LLM can map
      them to standard fields and pass back a --column-map.

  PHASE 2 (compute) — run with --column-map:
      python3 compute_roas.py \
          --campaign <path> --groups <path> \
          --column-map '{"cost":"Budget","revenue":"Conv. value","...":"..."}'

      Uses the exact column names supplied by the LLM. Numbers are
      computed with fixed formulas — same inputs always produce same outputs.

Column map keys (all optional, fall back to auto-detect):
    cost          Spend / budget column in campaigns file
    revenue       Revenue / conversion value column
    conversions   Conversions / leads column
    impressions   Impressions column
    clicks        Clicks column
    campaign_id   Campaign name or ID for group matching
    url           Final URL column for group matching
    group_url     Page/URL column in the groups file
    group_label   Variant/Control label column in groups file
"""
from __future__ import annotations

import argparse
import base64
import io
import json
import sys
import warnings
from pathlib import Path
from typing import Optional

warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.ticker as mticker
    HAS_MPL = True
except ImportError:
    HAS_MPL = False


# ── Helpers ───────────────────────────────────────────────────────────────────

def read_file(path: str) -> pd.DataFrame:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"File not found: {path}")
    if p.suffix.lower() in (".xlsx", ".xls"):
        return pd.read_excel(p, dtype=str)
    return pd.read_csv(p, dtype=str)


def _coerce_numeric(df: pd.DataFrame, *cols: str) -> pd.DataFrame:
    for c in cols:
        if c and c in df.columns:
            df[c] = pd.to_numeric(
                df[c].astype(str)
                    .str.replace(",", "", regex=False)
                    .str.replace("$", "", regex=False)
                    .str.replace("%", "", regex=False)
                    .str.strip(),
                errors="coerce",
            )
    return df


def _fig_to_b64(fig) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=130, bbox_inches="tight")
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode()


def _pick_col(columns: list[str], *hints: str) -> Optional[str]:
    """Return the first column name containing any of the hint substrings."""
    low = [c.lower() for c in columns]
    for hint in hints:
        for i, c in enumerate(low):
            if hint in c:
                return columns[i]
    return None


# ── Phase 1: Schema inspection ────────────────────────────────────────────────

def inspect_schemas(campaign_path: str, groups_path: str,
                    keywords_path: Optional[str]) -> dict:
    """Return raw column headers from each file so the LLM can map them."""
    result = {}
    for label, path in [("campaigns", campaign_path),
                        ("groups", groups_path),
                        ("keywords", keywords_path)]:
        if not path:
            continue
        try:
            df = read_file(path)
            result[label] = {
                "columns": list(df.columns),
                "sample_row": df.iloc[0].to_dict() if len(df) > 0 else {},
                "row_count": len(df),
            }
        except Exception as e:
            result[label] = {"error": str(e)}
    return result


# ── Phase 2: Deterministic computation ───────────────────────────────────────

def load_groups(path: str, col_map: dict) -> dict[str, str]:
    """Return {page_url: group_label} from the Variant/Control spreadsheet."""
    df = read_file(path)
    cols = list(df.columns)

    url_col = col_map.get("group_url") or _pick_col(cols, "page", "url", "landing") or cols[0]
    grp_col = col_map.get("group_label") or _pick_col(cols, "group", "variant", "control", "label", "type") or cols[1]

    mapping: dict[str, str] = {}
    for _, row in df.iterrows():
        url = str(row.get(url_col, "")).strip().lower().rstrip("/")
        grp = str(row.get(grp_col, "")).strip()
        if url and grp and url not in ("nan", ""):
            mapping[url] = grp
    return mapping


def load_campaigns(path: str, col_map: dict) -> pd.DataFrame:
    df = read_file(path)
    cols = list(df.columns)

    # Resolve column names — prefer explicit map, fall back to auto-detect
    cost_col   = col_map.get("cost")        or _pick_col(cols, "cost", "spend", "budget", "amount")
    rev_col    = col_map.get("revenue")     or _pick_col(cols, "conv. value", "conversion value", "revenue", "value")
    conv_col   = col_map.get("conversions") or _pick_col(cols, "conversion", "lead", "submit")
    impr_col   = col_map.get("impressions") or _pick_col(cols, "impression")
    click_col  = col_map.get("clicks")      or _pick_col(cols, "click")
    url_col    = col_map.get("url")         or _pick_col(cols, "final url", "url", "landing page")
    name_col   = col_map.get("campaign_id") or _pick_col(cols, "campaign name", "campaign", "name")

    df = _coerce_numeric(df, cost_col, rev_col, conv_col, impr_col, click_col)

    # Standardise to internal names
    rename = {}
    for internal, actual in [
        ("_cost", cost_col), ("_revenue", rev_col), ("_conversions", conv_col),
        ("_impressions", impr_col), ("_clicks", click_col),
        ("_url", url_col), ("_campaign", name_col),
    ]:
        if actual and actual in df.columns:
            rename[actual] = internal

    df = df.rename(columns=rename)

    # Store resolved column map for transparency
    df.attrs["resolved_cols"] = {
        "cost": cost_col, "revenue": rev_col, "conversions": conv_col,
        "impressions": impr_col, "clicks": click_col,
        "url": url_col, "campaign": name_col,
    }
    return df


def compute_roas_by_group(campaigns: pd.DataFrame, groups: dict[str, str]) -> dict:
    """Assign rows to Variant/Control and aggregate; ROAS = _revenue / _cost."""

    def assign_group(row) -> str:
        candidates = []
        if "_url" in row.index:
            candidates.append(str(row["_url"]).strip().lower().rstrip("/"))
        if "_campaign" in row.index:
            candidates.append(str(row["_campaign"]).strip().lower())
        for candidate in candidates:
            if not candidate or candidate == "nan":
                continue
            for url, grp in groups.items():
                if url in candidate or candidate in url:
                    return grp
        return "Unclassified"

    campaigns = campaigns.copy()
    campaigns["_group"] = campaigns.apply(assign_group, axis=1)

    result = {}
    for group, sub in campaigns.groupby("_group"):
        cost  = sub["_cost"].sum()        if "_cost"        in sub else 0.0
        rev   = sub["_revenue"].sum()     if "_revenue"     in sub else 0.0
        conv  = sub["_conversions"].sum() if "_conversions" in sub else 0.0
        impr  = sub["_impressions"].sum() if "_impressions" in sub else 0.0
        clk   = sub["_clicks"].sum()      if "_clicks"      in sub else 0.0

        roas = round(float(rev)  / float(cost), 4) if cost  > 0 else None
        ctr  = round(float(clk)  / float(impr), 4) if impr  > 0 else None
        cpa  = round(float(cost) / float(conv), 2)  if conv  > 0 else None

        result[str(group)] = {
            "spend":       round(float(cost), 2),
            "revenue":     round(float(rev),  2),
            "conversions": round(float(conv), 1),
            "impressions": round(float(impr), 0),
            "clicks":      round(float(clk),  0),
            "roas":        roas,
            "ctr":         ctr,
            "cpa":         cpa,
            "row_count":   len(sub),
        }
    return result


def causal_impact_did(roas_by_group: dict) -> dict:
    variant_keys = [k for k in roas_by_group
                    if any(t in k.lower() for t in ("variant", "kg", "treat", "exposed"))]
    control_keys = [k for k in roas_by_group
                    if any(t in k.lower() for t in ("control", "baseline", "untreated"))]

    if not variant_keys or not control_keys:
        all_keys = list(roas_by_group.keys())
        return {
            "error": (
                "Could not auto-identify Variant and Control groups. "
                f"Groups found: {all_keys}. "
                "Pass --column-map with 'group_label' to use exact column values."
            )
        }

    v = roas_by_group[variant_keys[0]]
    c = roas_by_group[control_keys[0]]
    v_roas, c_roas = v.get("roas"), c.get("roas")

    if v_roas is None or c_roas is None:
        return {"error": "ROAS undefined for one or both groups — missing cost or revenue data."}

    diff = round(v_roas - c_roas, 4)
    pct  = round(diff / c_roas * 100, 2) if c_roas else None
    direction = "positive" if diff > 0 else "negative" if diff < 0 else "neutral"

    return {
        "variant_group":  variant_keys[0],
        "control_group":  control_keys[0],
        "variant_roas":   v_roas,
        "control_roas":   c_roas,
        "absolute_diff":  diff,
        "relative_pct":   pct,
        "direction":      direction,
        "verdict": (
            f"Variant ROAS ({v_roas:.2f}x) is {abs(pct or 0):.1f}% "
            f"{'higher' if diff > 0 else 'lower'} than Control ROAS ({c_roas:.2f}x)."
        ),
    }


# ── Charts ────────────────────────────────────────────────────────────────────

def chart_roas_comparison(roas_by_group: dict) -> Optional[str]:
    if not HAS_MPL:
        return None
    groups = [g for g, v in roas_by_group.items() if v.get("roas") is not None]
    if not groups:
        return None
    values = [roas_by_group[g]["roas"] for g in groups]
    colors = [
        "#3452DB" if any(t in g.lower() for t in ("variant", "kg")) else
        "#22A286" if "control" in g.lower() else "#A1A7AF"
        for g in groups
    ]
    fig, ax = plt.subplots(figsize=(7, 3.5))
    bars = ax.bar(groups, values, color=colors, width=0.45, zorder=2)
    ax.set_ylabel("ROAS (Revenue / Spend)", fontsize=10)
    ax.set_title("ROAS by Group: Variant vs Control", fontsize=12, fontweight="bold")
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.2fx"))
    ax.bar_label(bars, fmt="%.2fx", padding=3, fontsize=9)
    ax.set_ylim(0, max(values) * 1.35)
    ax.grid(axis="y", alpha=0.3, zorder=1)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    return _fig_to_b64(fig)


def chart_spend_vs_revenue(roas_by_group: dict) -> Optional[str]:
    if not HAS_MPL:
        return None
    groups  = list(roas_by_group.keys())
    spend   = [roas_by_group[g].get("spend",   0) for g in groups]
    revenue = [roas_by_group[g].get("revenue", 0) for g in groups]
    x = np.arange(len(groups))
    w = 0.35
    fig, ax = plt.subplots(figsize=(7, 3.5))
    ax.bar(x - w/2, spend,   w, label="Spend",   color="#3452DB", alpha=0.85, zorder=2)
    ax.bar(x + w/2, revenue, w, label="Revenue", color="#22A286", alpha=0.85, zorder=2)
    ax.set_xticks(x); ax.set_xticklabels(groups)
    ax.set_ylabel("USD", fontsize=10)
    ax.set_title("Spend vs Revenue by Group", fontsize=12, fontweight="bold")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"${v:,.0f}"))
    ax.legend(); ax.grid(axis="y", alpha=0.3, zorder=1)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    return _fig_to_b64(fig)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description="Deterministic ROAS computation (two-phase)")
    ap.add_argument("--campaign",     required=True,  help="Campaigns CSV/XLSX")
    ap.add_argument("--groups",       required=True,  help="Variant/Control groups XLSX")
    ap.add_argument("--keywords",     required=False, help="Search keywords CSV/XLSX")
    ap.add_argument("--ga4-id",       default="",    help="GA4 Property ID (metadata only)")
    ap.add_argument("--inspect-only", action="store_true",
                    help="Phase 1: print column headers JSON only, skip computation")
    ap.add_argument("--column-map",   default="{}",
                    help='Phase 2: JSON mapping of standard fields to actual column names')
    args = ap.parse_args()

    # ── Phase 1 ──
    if args.inspect_only:
        schema = inspect_schemas(args.campaign, args.groups, args.keywords)
        print("SCHEMA_INSPECT_START")
        print(json.dumps(schema, indent=2))
        print("SCHEMA_INSPECT_END")
        return

    # ── Phase 2 ──
    try:
        col_map: dict = json.loads(args.column_map)
    except json.JSONDecodeError as e:
        col_map = {}
        print(f"[WARN] --column-map JSON parse failed: {e}", file=sys.stderr)

    errors: list[str] = []
    result: dict = {
        "meta": {"ga4_property": args.ga4_id, "column_map_used": col_map},
    }

    # Groups
    groups: dict[str, str] = {}
    try:
        groups = load_groups(args.groups, col_map)
        result["group_count"]  = len(groups)
        result["group_sample"] = dict(list(groups.items())[:5])
    except Exception as e:
        errors.append(f"groups: {e}")

    # Campaigns
    roas_by_group: dict = {}
    try:
        campaigns = load_campaigns(args.campaign, col_map)
        result["campaign_rows"]    = len(campaigns)
        result["resolved_columns"] = campaigns.attrs.get("resolved_cols", {})
        roas_by_group = compute_roas_by_group(campaigns, groups)
        result["roas_by_group"]    = roas_by_group
    except Exception as e:
        errors.append(f"campaigns: {e}")

    # Causal impact (DiD)
    try:
        result["causal_impact"] = causal_impact_did(roas_by_group)
    except Exception as e:
        errors.append(f"causal_impact: {e}")

    # Charts
    charts: dict[str, str] = {}
    try:
        c1 = chart_roas_comparison(roas_by_group)
        if c1: charts["roas_comparison"] = c1
        c2 = chart_spend_vs_revenue(roas_by_group)
        if c2: charts["spend_vs_revenue"] = c2
    except Exception as e:
        errors.append(f"charts: {e}")

    result["charts"] = charts
    result["errors"] = errors

    print("COMPUTE_ROAS_RESULT_START")
    print(json.dumps(result, indent=2))
    print("COMPUTE_ROAS_RESULT_END")


if __name__ == "__main__":
    main()
