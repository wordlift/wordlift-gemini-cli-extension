#!/usr/bin/env python3
"""
Google Ads performance analysis for the reporting-skill.
Processes campaign/keyword CSVs and generates branded charts.
"""
import argparse
import json
import sys
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from pathlib import Path
from datetime import datetime

# WordLift Colors
C_SPEND = "#D55471" # Berry
C_CONV  = "#22A286" # Leaf
C_SKY   = "#3452DB" # Sky
C_GRAY  = "#9CA3AF"

def analyze_ads(csv_path: Path, out_dir: Path, dpi: int = 150):
    print(f"📈 Analyzing Google Ads data: {csv_path}")
    
    try:
        # Load data (try different encodings commonly exported by ads platforms)
        try:
            df = pd.read_csv(csv_path, encoding='utf-16', sep='\t')
        except:
            df = pd.read_csv(csv_path)

        # Basic cleaning (strip decimals from currency strings if needed)
        def clean_numeric(val):
            if isinstance(val, str):
                return float(val.replace(',', '').replace('$', '').replace('€', '').replace('%', '').strip())
            return val

        # Map common Google Ads column names to standard keys
        col_map = {
            'Campaign': 'campaign',
            'Clicks': 'clicks',
            'Impressions': 'impressions',
            'Cost': 'cost',
            'Conversions': 'conversions',
            'Conv. value': 'value',
            'CTR': 'ctr',
            'Avg. CPC': 'cpc'
        }
        
        # Identify available columns
        df.columns = [c.strip() for c in df.columns]
        standard_cols = {}
        for k, v in col_map.items():
            for real_col in df.columns:
                if k.lower() in real_col.lower():
                    standard_cols[v] = real_col
                    break
        
        if 'cost' not in standard_cols or 'clicks' not in standard_cols:
            print(f"❌ Could not find required columns (Cost, Clicks) in {csv_path}")
            return

        # Prepare metrics
        df['Cost'] = df[standard_cols['cost']].apply(clean_numeric)
        df['Clicks'] = df[standard_cols['clicks']].apply(clean_numeric)
        df['Impressions'] = df[standard_cols['impressions']].apply(clean_numeric)
        
        if 'conversions' in standard_cols:
            df['Conversions'] = df[standard_cols['conversions']].apply(clean_numeric)
        else:
            df['Conversions'] = 0
            
        if 'value' in standard_cols:
            df['Value'] = df[standard_cols['value']].apply(clean_numeric)
        else:
            df['Value'] = 0

        # Calculations
        total_spend = df['Cost'].sum()
        total_conversions = df['Conversions'].sum()
        total_value = df['Value'].sum()
        roas = total_value / total_spend if total_spend > 0 else 0
        cpa = total_spend / total_conversions if total_conversions > 0 else 0

        # ── Chart 1: Top Campaigns by Spend vs conversions ──
        top_camps = df.groupby(standard_cols['campaign']).agg({
            'Cost': 'sum',
            'Conversions': 'sum'
        }).nlargest(10, 'Cost')

        fig, ax1 = plt.subplots(figsize=(12, 6))
        ax2 = ax1.twinx()
        
        x = np.arange(len(top_camps))
        width = 0.35
        
        ax1.bar(x - width/2, top_camps['Cost'], width, label='Spend', color=C_SPEND, alpha=0.8)
        ax2.bar(x + width/2, top_camps['Conversions'], width, label='Conversions', color=C_CONV, alpha=0.8)
        
        ax1.set_ylabel('Spend')
        ax2.set_ylabel('Conversions')
        ax1.set_title('Top 10 Campaigns: Spend vs Conversions', fontweight='bold')
        ax1.set_xticks(x)
        ax1.set_xticklabels(top_camps.index, rotation=45, ha='right')
        
        # Combine legends
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right')
        
        plt.tight_layout()
        fig.savefig(out_dir / "chart_ads_campaigns.png", dpi=dpi)
        plt.close()

        # Save summary
        summary = {
            "google_ads": {
                "total_spend": float(total_spend),
                "total_conversions": float(total_conversions),
                "total_value": float(total_value),
                "roas": float(roas),
                "cpa": float(cpa),
                "top_campaigns": top_camps.index.tolist()[:3]
            }
        }
        
        with open(out_dir / "ads_summary.json", 'w') as f:
            json.dump(summary, f, indent=2)
            
        print("✅ Ads analysis complete")
        return summary

    except Exception as e:
        print(f"❌ Failed to analyze Ads CSV: {e}")
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    analyze_ads(Path(args.csv), Path(args.out))
