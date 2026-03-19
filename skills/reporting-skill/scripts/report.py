#!/usr/bin/env python3
"""
PDF report generator for the SEO Performance Report skill.
Reads analysis_summary.json and chart PNGs, produces a branded PDF report.

Usage:
    python3 scripts/report.py --config config.yaml
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

try:
    import yaml
except ImportError:
    print("❌ PyYAML not installed. Run: python3 scripts/setup.py")
    sys.exit(1)

try:
    from fpdf import FPDF
except ImportError:
    print("❌ fpdf2 not installed. Run: python3 scripts/setup.py")
    sys.exit(1)


# ─── Color Palette ───────────────────────────────────────────────────────────
C_PRIMARY = (37, 99, 235)      # #2563EB
C_SECONDARY = (220, 38, 38)    # #DC2626
C_ACCENT = (16, 185, 129)      # #10B981
C_DARK = (30, 30, 30)
C_GRAY = (100, 100, 100)
C_LIGHT_GRAY = (200, 200, 200)
C_WHITE = (255, 255, 255)
C_BG = (245, 247, 250)


class SEOReport(FPDF):
    """Custom PDF report with branding and helper methods."""

    def __init__(self, site_name: str, logo_path: str = None):
        super().__init__('P', 'mm', 'A4')
        self.site_name = site_name
        self.logo_path = logo_path
        self.set_auto_page_break(auto=True, margin=25)

    def header(self):
        """Page header with site name."""
        if self.page_no() == 1:
            return  # Skip header on cover page
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(*C_GRAY)
        self.cell(0, 8, f'{self.site_name} — SEO Performance Report', align='L')
        self.cell(0, 8, f'Page {self.page_no()}', align='R', new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(*C_LIGHT_GRAY)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(4)

    def footer(self):
        """Page footer."""
        if self.page_no() == 1:
            return
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 7)
        self.set_text_color(*C_GRAY)
        self.cell(0, 10, 'Powered by WordLift', align='C')

    def section_title(self, title: str):
        """Add a section title with colored underline."""
        self.set_font('Helvetica', 'B', 16)
        self.set_text_color(*C_PRIMARY)
        self.cell(0, 12, title, new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(*C_PRIMARY)
        self.set_line_width(0.8)
        self.line(self.l_margin, self.get_y(), self.l_margin + 60, self.get_y())
        self.ln(6)
        self.set_text_color(*C_DARK)

    def subsection_title(self, title: str):
        """Add a subsection title."""
        self.set_font('Helvetica', 'B', 13)
        self.set_text_color(*C_DARK)
        self.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def body_text(self, text: str):
        """Add body text."""
        self.set_font('Helvetica', '', 10)
        self.set_text_color(*C_DARK)
        self.multi_cell(0, 5.5, text)
        self.ln(3)

    def metric_callout(self, label: str, value: str, color=C_PRIMARY):
        """Add a metric callout box."""
        x = self.get_x()
        y = self.get_y()
        w = 40
        h = 22
        self.set_fill_color(*color)
        self.rect(x, y, w, h, 'F')
        self.set_xy(x, y + 2)
        self.set_font('Helvetica', '', 8)
        self.set_text_color(*C_WHITE)
        self.cell(w, 5, label, align='C', new_x="LMARGIN", new_y="NEXT")
        self.set_xy(x, y + 8)
        self.set_font('Helvetica', 'B', 13)
        self.cell(w, 10, value, align='C')
        self.set_xy(x + w + 4, y)
        self.set_text_color(*C_DARK)

    def add_chart(self, chart_path: Path, caption: str = ""):
        """Add a chart image, fitting to page width."""
        if not chart_path.exists():
            return
        avail_width = self.w - self.l_margin - self.r_margin
        # Check if we need a new page for the image
        if self.get_y() > 200:
            self.add_page()
        self.image(str(chart_path), x=self.l_margin, w=avail_width)
        if caption:
            self.set_font('Helvetica', 'I', 8)
            self.set_text_color(*C_GRAY)
            self.cell(0, 5, caption, align='C', new_x="LMARGIN", new_y="NEXT")
            self.set_text_color(*C_DARK)
        self.ln(4)

    def add_table(self, headers: list, rows: list, col_widths: list = None):
        """Add a formatted table."""
        avail = self.w - self.l_margin - self.r_margin
        if col_widths is None:
            col_widths = [avail / len(headers)] * len(headers)

        # Header row
        self.set_font('Helvetica', 'B', 9)
        self.set_fill_color(*C_PRIMARY)
        self.set_text_color(*C_WHITE)
        for i, header in enumerate(headers):
            self.cell(col_widths[i], 8, str(header), border=1, fill=True, align='C')
        self.ln()

        # Data rows
        self.set_font('Helvetica', '', 9)
        self.set_text_color(*C_DARK)
        for row_idx, row in enumerate(rows):
            if row_idx % 2 == 0:
                self.set_fill_color(*C_BG)
            else:
                self.set_fill_color(*C_WHITE)
            for i, cell in enumerate(row):
                self.cell(col_widths[i], 7, str(cell), border=1, fill=True, align='C')
            self.ln()
        self.ln(4)


# ─── Report Builder ─────────────────────────────────────────────────────────

def build_cover_page(pdf: SEOReport, cfg: dict, summary: dict):
    """Build the cover page."""
    pdf.add_page()
    pdf.ln(40)

    # Logo
    if pdf.logo_path and Path(pdf.logo_path).exists():
        pdf.image(pdf.logo_path, x=70, w=70)
        pdf.ln(15)

    # Line
    pdf.set_draw_color(*C_PRIMARY)
    pdf.set_line_width(1)
    pdf.line(40, pdf.get_y(), 170, pdf.get_y())
    pdf.ln(10)

    # Title
    pdf.set_font('Helvetica', 'B', 28)
    pdf.set_text_color(*C_PRIMARY)
    pdf.cell(0, 15, 'SEO Performance Report', align='C', new_x="LMARGIN", new_y="NEXT")

    # Site name
    pdf.set_font('Helvetica', '', 18)
    pdf.set_text_color(*C_DARK)
    pdf.cell(0, 12, cfg["site"]["name"], align='C', new_x="LMARGIN", new_y="NEXT")
    pdf.ln(8)

    # Date range
    dates = cfg["dates"]
    pdf.set_font('Helvetica', '', 12)
    pdf.set_text_color(*C_GRAY)
    pdf.cell(0, 8, f'Analysis Period: {dates["before_start"]} – {dates["after_end"]}', align='C', new_x="LMARGIN", new_y="NEXT")

    # Author
    author = cfg.get("report", {}).get("author", "")
    if author:
        pdf.cell(0, 8, f'Prepared by: {author}', align='C', new_x="LMARGIN", new_y="NEXT")

    pdf.cell(0, 8, f'Generated: {datetime.now().strftime("%B %d, %Y")}', align='C', new_x="LMARGIN", new_y="NEXT")

    # Bottom line
    pdf.ln(15)
    pdf.set_draw_color(*C_PRIMARY)
    pdf.line(40, pdf.get_y(), 170, pdf.get_y())
    pdf.ln(10)

    pdf.set_font('Helvetica', 'I', 10)
    pdf.set_text_color(*C_GRAY)
    pdf.cell(0, 8, 'Powered by WordLift', align='C', new_x="LMARGIN", new_y="NEXT")


def build_executive_summary(pdf: SEOReport, summary: dict):
    """Build the executive summary page."""
    pdf.add_page()
    pdf.section_title('Executive Summary')

    gsc = summary.get("gsc", {})
    mode = gsc.get("mode", "")

    if mode == "groups":
        v = gsc["variant"]
        c = gsc["control"]

        # Metric callouts
        pdf.metric_callout('Click Change (Variant)', f'{v["clicks_diff"]:+,.0f} ({v["clicks_pct"]:+.1f}%)',
                          C_ACCENT if v["clicks_diff"] > 0 else C_SECONDARY)
        pdf.metric_callout('Click Change (Control)', f'{c["clicks_diff"]:+,.0f} ({c["clicks_pct"]:+.1f}%)',
                          C_ACCENT if c["clicks_diff"] > 0 else C_SECONDARY)
        pdf.metric_callout('URLs Gaining (V)', f'{v["urls_gaining"]}',
                          C_ACCENT)
        pdf.metric_callout('URLs Losing (V)', f'{v["urls_losing"]}',
                          C_SECONDARY)
        pdf.ln(28)

        # Summary table
        pdf.add_table(
            headers=['Metric', 'Variant', 'Control'],
            rows=[
                ['Clicks Before', f'{v["clicks_before"]:,.0f}', f'{c["clicks_before"]:,.0f}'],
                ['Clicks After', f'{v["clicks_after"]:,.0f}', f'{c["clicks_after"]:,.0f}'],
                ['Click Change', f'{v["clicks_diff"]:+,.0f} ({v["clicks_pct"]:+.1f}%)',
                 f'{c["clicks_diff"]:+,.0f} ({c["clicks_pct"]:+.1f}%)'],
                ['Avg CTR Before', f'{v["avg_ctr_before"]:.2%}', f'{c["avg_ctr_before"]:.2%}'],
                ['Avg CTR After', f'{v["avg_ctr_after"]:.2%}', f'{c["avg_ctr_after"]:.2%}'],
                ['Avg Position Before', f'{v["avg_pos_before"]:.1f}', f'{c["avg_pos_before"]:.1f}'],
                ['Avg Position After', f'{v["avg_pos_after"]:.1f}', f'{c["avg_pos_after"]:.1f}'],
                ['URLs Gaining', f'{v["urls_gaining"]} ({v["urls_gaining"]/v["n_urls"]*100:.0f}%)',
                 f'{c["urls_gaining"]} ({c["urls_gaining"]/c["n_urls"]*100:.0f}%)'],
                ['URLs Losing', f'{v["urls_losing"]} ({v["urls_losing"]/v["n_urls"]*100:.0f}%)',
                 f'{c["urls_losing"]} ({c["urls_losing"]/c["n_urls"]*100:.0f}%)'],
            ],
            col_widths=[50, 55, 55],
        )

    elif mode == "sitewide":
        p = gsc["all_pages"]
        pdf.metric_callout('Click Change', f'{p["clicks_diff"]:+,.0f} ({p["clicks_pct"]:+.1f}%)',
                          C_ACCENT if p["clicks_diff"] > 0 else C_SECONDARY)
        pdf.metric_callout('URLs Analyzed', f'{p["n_urls"]:,}', C_PRIMARY)
        pdf.metric_callout('URLs Gaining', f'{p["urls_gaining"]}', C_ACCENT)
        pdf.metric_callout('URLs Losing', f'{p["urls_losing"]}', C_SECONDARY)
        pdf.ln(28)

        pdf.add_table(
            headers=['Metric', 'Before', 'After', 'Change'],
            rows=[
                ['Clicks', f'{p["clicks_before"]:,.0f}', f'{p["clicks_after"]:,.0f}',
                 f'{p["clicks_diff"]:+,.0f} ({p["clicks_pct"]:+.1f}%)'],
                ['Impressions', f'{p["impr_before"]:,.0f}', f'{p["impr_after"]:,.0f}',
                 f'{p["impr_after"] - p["impr_before"]:+,.0f}'],
                ['Avg CTR', f'{p["avg_ctr_before"]:.2%}', f'{p["avg_ctr_after"]:.2%}',
                 f'{(p["avg_ctr_after"] - p["avg_ctr_before"])*100:+.3f}pp'],
                ['Avg Position', f'{p["avg_pos_before"]:.1f}', f'{p["avg_pos_after"]:.1f}',
                 f'{p["avg_pos_after"] - p["avg_pos_before"]:+.1f}'],
            ],
            col_widths=[35, 40, 40, 45],
        )

    # AI traffic summary
    ai = summary.get("ga4_ai")
    if ai:
        pdf.ln(4)
        pdf.subsection_title('AI Referral Highlight')
        pdf.body_text(
            f'Total AI referral sessions: {ai["total_ai_sessions"]:,.0f}  |  '
            f'Top source: {ai["top_source"]}  |  '
            f'Total AI users: {ai["total_ai_users"]:,.0f}'
        )


def build_gsc_section(pdf: SEOReport, out_dir: Path, summary: dict):
    """Build GSC analysis pages."""
    pdf.add_page()
    pdf.section_title('Google Search Console Analysis')

    mode = summary.get("gsc", {}).get("mode", "")
    days_before = summary.get("gsc", {}).get("days_before", "?")
    days_after = summary.get("gsc", {}).get("days_after", "?")
    pdf.body_text(
        f'Before period: {days_before} days  |  After period: {days_after} days  |  '
        f'Metrics are per-day normalized for fair comparison.'
    )

    # Charts
    if mode == "groups":
        pdf.subsection_title('Clicks & Impressions (Before vs After)')
        pdf.add_chart(out_dir / "chart_01_daily_clicks_impressions.png")

        pdf.subsection_title('CTR & Position')
        pdf.add_chart(out_dir / "chart_02_ctr_position.png")

    pdf.add_page()
    pdf.subsection_title('Daily Clicks Over Time')
    pdf.add_chart(out_dir / "chart_03_daily_clicks_timeseries.png")

    if (out_dir / "chart_04_daily_impressions_timeseries.png").exists():
        pdf.subsection_title('Daily Impressions Over Time')
        pdf.add_chart(out_dir / "chart_04_daily_impressions_timeseries.png")

    if (out_dir / "chart_05_click_diff_distribution.png").exists():
        pdf.add_page()
        pdf.subsection_title('Click Change Distribution')
        pdf.add_chart(out_dir / "chart_05_click_diff_distribution.png")

    if (out_dir / "chart_06_positive_negative_urls.png").exists():
        pdf.subsection_title('Positive vs Negative URLs')
        pdf.add_chart(out_dir / "chart_06_positive_negative_urls.png")

    if (out_dir / "chart_07_top_gainers.png").exists():
        pdf.add_page()
        pdf.subsection_title('Top 20 Click Gainers')
        pdf.add_chart(out_dir / "chart_07_top_gainers.png")

    if (out_dir / "chart_08_net_daily_change.png").exists():
        pdf.subsection_title('Net Daily Change')
        pdf.add_chart(out_dir / "chart_08_net_daily_change.png")


def build_ga4_section(pdf: SEOReport, out_dir: Path, summary: dict):
    """Build GA4 analysis pages."""
    pdf.add_page()
    pdf.section_title('Google Analytics 4 — Behavioral Analysis')

    # AI Referral
    if (out_dir / "chart_09_ai_by_source.png").exists():
        pdf.subsection_title('AI Referral Traffic by Source')
        ai = summary.get("ga4_ai", {})
        if ai:
            pdf.body_text(f'Total AI sessions: {ai.get("total_ai_sessions", 0):,.0f}  |  Top source: {ai.get("top_source", "N/A")}')
        pdf.add_chart(out_dir / "chart_09_ai_by_source.png")

    if (out_dir / "chart_10_ai_by_group.png").exists():
        pdf.subsection_title('AI Traffic by Page Group')
        pdf.add_chart(out_dir / "chart_10_ai_by_group.png")

    # Engagement
    if (out_dir / "chart_11_engagement.png").exists():
        pdf.add_page()
        pdf.subsection_title('Engagement Metrics')
        eng = summary.get("ga4_engagement", [])
        if eng:
            rows = []
            for d in eng:
                rows.append([
                    d['group'],
                    f'{d["sessions"]:,.0f}',
                    f'{d["engagement_rate"]:.1f}%',
                    f'{d["avg_bounce_rate"]:.1f}%',
                    f'{d["avg_duration"]:.0f}s',
                ])
            pdf.add_table(
                headers=['Group', 'Sessions', 'Eng. Rate', 'Bounce Rate', 'Avg Duration'],
                rows=rows,
                col_widths=[35, 30, 30, 30, 35],
            )
        pdf.add_chart(out_dir / "chart_11_engagement.png")

    # Channels
    if (out_dir / "chart_12_channels.png").exists():
        pdf.subsection_title('Traffic by Channel')
        pdf.add_chart(out_dir / "chart_12_channels.png")


def build_causal_impact_section(pdf: SEOReport, out_dir: Path, summary: dict):
    """Build Causal Impact analysis pages."""
    ci = summary.get("causal_impact")
    if not ci:
        return

    pdf.add_page()
    pdf.section_title('Causal Impact Analysis')

    pdf.body_text(
        'Using the CausalImpact model with the Control group as the counterfactual, '
        'analyzing the daily time series to determine statistical significance of the intervention.'
    )

    # Clicks CI
    if (out_dir / "chart_13_causal_impact_clicks.png").exists():
        pdf.subsection_title('Causal Impact — Clicks')
        pdf.add_chart(out_dir / "chart_13_causal_impact_clicks.png")

        # Add summary text
        clicks_summary = ci.get("clicks_summary", "")
        if clicks_summary:
            pdf.set_font('Courier', '', 8)
            pdf.multi_cell(0, 4, clicks_summary)
            pdf.ln(4)
            pdf.set_font('Helvetica', '', 10)

    # Impressions CI
    if (out_dir / "chart_14_causal_impact_impressions.png").exists():
        pdf.add_page()
        pdf.subsection_title('Causal Impact — Impressions')
        pdf.add_chart(out_dir / "chart_14_causal_impact_impressions.png")

        impr_summary = ci.get("impressions_summary", "")
        if impr_summary:
            pdf.set_font('Courier', '', 8)
            pdf.multi_cell(0, 4, impr_summary)
            pdf.ln(4)
            pdf.set_font('Helvetica', '', 10)


def build_schema_section(pdf: SEOReport, out_dir: Path, summary: dict):
    """Build schema class analysis pages."""
    schema = summary.get("schema_classes")
    if not schema:
        return

    pdf.add_page()
    pdf.section_title('Schema Class Performance')

    pdf.body_text(
        'Analysis of click performance by Schema.org class. '
        '"Lift" = avg daily click change for URLs with the class minus those without.'
    )

    if (out_dir / "chart_15_schema_class_lift.png").exists():
        pdf.subsection_title('Click Lift by Schema.org Class')
        pdf.add_chart(out_dir / "chart_15_schema_class_lift.png")

    if (out_dir / "chart_16_schema_heatmap.png").exists():
        pdf.subsection_title('Performance Heatmap')
        pdf.add_chart(out_dir / "chart_16_schema_heatmap.png")


def build_methodology_page(pdf: SEOReport, cfg: dict, summary: dict):
    """Build the methodology appendix."""
    pdf.add_page()
    pdf.section_title('Methodology & Data Sources')

    dates = cfg["dates"]
    gsc = summary.get("gsc", {})

    items = [
        ("Data Sources", "Google Search Console API, Google Analytics 4 Data API"),
        ("Before Period", f'{dates["before_start"]} – {dates["before_end"]} ({gsc.get("days_before", "?")} days)'),
        ("After Period", f'{dates["after_start"]} – {dates["after_end"]} ({gsc.get("days_after", "?")} days)'),
        ("Normalization", "Per-day averages used when before/after periods differ in length"),
        ("GSC Data Lag", "Google Search Console data has approximately a 3-day lag"),
    ]

    mode = gsc.get("mode", "")
    if mode == "groups":
        v = gsc.get("variant", {})
        c = gsc.get("control", {})
        items.append(("Variant URLs", str(v.get("n_urls", "?"))))
        items.append(("Control URLs", str(c.get("n_urls", "?"))))

    if summary.get("causal_impact"):
        items.append(("Statistical Method", "CausalImpact (Bayesian structural time-series)"))

    for label, value in items:
        pdf.set_font('Helvetica', 'B', 10)
        pdf.cell(55, 7, label + ":")
        pdf.set_font('Helvetica', '', 10)
        pdf.cell(0, 7, value, new_x="LMARGIN", new_y="NEXT")

    pdf.ln(10)
    pdf.set_font('Helvetica', 'I', 9)
    pdf.set_text_color(*C_GRAY)
    pdf.multi_cell(0, 5, (
        'Disclaimer: This report is generated from live API data. '
        'Metrics may differ slightly from the Google Search Console or GA4 web interfaces '
        'due to data processing delays, sampling, and rounding.'
    ))


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Generate SEO PDF report")
    parser.add_argument("--config", required=True, help="Path to config.yaml")
    args = parser.parse_args()

    with open(args.config) as f:
        cfg = yaml.safe_load(f)

    out_dir = Path(cfg["output"]["directory"])
    summary_path = out_dir / "analysis_summary.json"

    if not summary_path.exists():
        print("❌ analysis_summary.json not found. Run analyze.py first.")
        sys.exit(1)

    with open(summary_path) as f:
        summary = json.load(f)

    site_name = cfg["site"]["name"]
    logo_path = cfg.get("report", {}).get("logo_path", "")

    print(f"📄 Generating PDF report for {site_name}...")

    pdf = SEOReport(site_name=site_name, logo_path=logo_path)

    # Build sections
    build_cover_page(pdf, cfg, summary)
    build_executive_summary(pdf, summary)

    # GSC section
    if summary.get("gsc"):
        build_gsc_section(pdf, out_dir, summary)

    # GA4 section
    ga4_enabled = cfg.get("ga4", {}).get("enabled", False)
    if ga4_enabled:
        build_ga4_section(pdf, out_dir, summary)

    # Causal Impact
    if summary.get("causal_impact"):
        build_causal_impact_section(pdf, out_dir, summary)

    # Schema classes
    if summary.get("schema_classes"):
        build_schema_section(pdf, out_dir, summary)

    # Methodology
    build_methodology_page(pdf, cfg, summary)

    # Save
    safe_name = site_name.replace(' ', '_').replace('/', '_')
    pdf_path = out_dir / f"{safe_name}_SEO_Report.pdf"
    pdf.output(str(pdf_path))
    print(f"\n✅ Report saved: {pdf_path}")
    print(f"   Pages: {pdf.page_no()}")


if __name__ == "__main__":
    main()
