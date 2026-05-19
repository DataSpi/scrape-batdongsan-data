"""
generate_report.py
------------------
Kết nối Malloy model (real_estate.malloy) qua PostgreSQL → lấy dữ liệu →
tạo charts Plotly → xuất báo cáo HTML tĩnh có thể chia sẻ.

Usage:
    python src/reports/generate_report.py

Output:
    reports/output/report_YYYY-MM-DD.html
"""

import asyncio
import os
import sys
from datetime import date
from pathlib import Path

import nest_asyncio
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())
nest_asyncio.apply()

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT   = Path(__file__).resolve().parent.parent.parent
MODEL_FILE  = REPO_ROOT / "models" / "real_estate.malloy"
OUTPUT_DIR  = REPO_ROOT / "reports" / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# HTML Template (embedded – no external file required)
# ---------------------------------------------------------------------------
HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Báo Cáo Bất Động Sản – {report_date}</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #f5f6fa; color: #222; }}
    header {{ background: #1a3c5e; color: white; padding: 28px 40px; }}
    header h1 {{ font-size: 1.8rem; font-weight: 700; }}
    header p  {{ font-size: 0.95rem; opacity: 0.75; margin-top: 4px; }}
    .container {{ max-width: 1200px; margin: 0 auto; padding: 32px 24px; }}
    .kpi-row {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 16px; margin-bottom: 36px;
    }}
    .kpi-card {{
      background: white; border-radius: 10px; padding: 22px 24px;
      box-shadow: 0 1px 4px rgba(0,0,0,.08); border-top: 4px solid #2d7dd2;
    }}
    .kpi-card .label {{ font-size: 0.78rem; text-transform: uppercase; color: #777; letter-spacing:.05em; }}
    .kpi-card .value {{ font-size: 1.75rem; font-weight: 700; color: #1a3c5e; margin-top: 6px; }}
    .kpi-card .unit  {{ font-size: 0.78rem; color: #999; margin-top: 2px; }}
    .section {{
      background: white; border-radius: 10px; padding: 24px;
      box-shadow: 0 1px 4px rgba(0,0,0,.08); margin-bottom: 28px;
    }}
    .section h2 {{
      font-size: 1.05rem; font-weight: 600; color: #1a3c5e;
      margin-bottom: 16px; padding-bottom: 10px; border-bottom: 1px solid #eee;
    }}
    footer {{ text-align: center; padding: 24px; font-size: 0.8rem; color: #aaa; }}
  </style>
</head>
<body>

<header>
  <h1>📊 Báo Cáo Thị Trường Bất Động Sản</h1>
  <p>Dữ liệu cập nhật ngày {report_date} &nbsp;|&nbsp; Nguồn: batdongsan.com.vn</p>
</header>

<div class="container">
  <div class="kpi-row">
    <div class="kpi-card">
      <div class="label">Tổng số tin</div>
      <div class="value">{property_count:,}</div>
      <div class="unit">bất động sản</div>
    </div>
    <div class="kpi-card" style="border-top-color:#e07b39;">
      <div class="label">Giá trung bình</div>
      <div class="value">{avg_price_b:.1f}</div>
      <div class="unit">tỷ VNĐ</div>
    </div>
    <div class="kpi-card" style="border-top-color:#27ae60;">
      <div class="label">Giá/m² TB</div>
      <div class="value">{avg_price_1m2_m:.1f}</div>
      <div class="unit">triệu VNĐ/m²</div>
    </div>
    <div class="kpi-card" style="border-top-color:#8e44ad;">
      <div class="label">Diện tích TB</div>
      <div class="value">{avg_area:.0f}</div>
      <div class="unit">m²</div>
    </div>
  </div>

  <div class="section">
    <h2>🏙️ Số lượng tin theo Thành phố / Quận-Huyện</h2>
    {chart_district}
  </div>

  <div class="section">
    <h2>🏗️ Giá trung bình theo Dự án (Top 20)</h2>
    {chart_project}
  </div>
</div>

<footer>Tự động tạo bởi hệ thống báo cáo &nbsp;·&nbsp; {report_date}</footer>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Malloy helpers
# ---------------------------------------------------------------------------
def _get_pg_connection():
    """Build a PostgresConnection using env vars (same creds as SQLAlchemy)."""
    try:
        from malloy.data.postgres import PostgresConnection
    except ImportError:
        print("[ERROR] malloy[postgres] not installed. Run: pip install 'malloy[postgres]'")
        sys.exit(1)

    return PostgresConnection(
        name="supabase",          # must match connection prefix in .malloy file
        host=os.environ["DB_HOST"],
        port=int(os.environ.get("DB_PORT", 5432)),
        database=os.environ["DB_DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
    )


async def run_malloy_view(runtime, view_name: str):
    """Run a named view from the loaded model and return a DataFrame."""
    import pandas as pd

    print(f"  Running view: {view_name} ...")
    source = runtime.load_file(str(MODEL_FILE))
    result = await source.run(named_query=view_name)
    df = result.to_dataframe()
    print(f"  → {len(df)} rows")
    return df


async def fetch_all_data():
    """Connect to Malloy runtime and run all required views."""
    import malloy

    conn = _get_pg_connection()
    with malloy.Runtime() as runtime:
        runtime.add_connection(conn)
        df_general    = await run_malloy_view(runtime, "general_info")
        df_district   = await run_malloy_view(runtime, "count_by_district")
        df_project    = await run_malloy_view(runtime, "avg_price_by_project")

    return df_general, df_district, df_project


# ---------------------------------------------------------------------------
# Chart builders (Plotly → inline HTML div, no external JS needed)
# ---------------------------------------------------------------------------
def _plotly_div(fig) -> str:
    """Return self-contained HTML div string for a Plotly figure."""
    return fig.to_html(full_html=False, include_plotlyjs="cdn")


def build_chart_district(df) -> str:
    import plotly.express as px

    # Sort by count descending, take top 30
    df = df.sort_values("property_count", ascending=False).head(30)
    label = df.apply(
        lambda r: f"{r.get('city_name', '')} – {r.get('d_name', '')}".strip(" –"),
        axis=1,
    )
    fig = px.bar(
        df,
        x="property_count",
        y=label,
        orientation="h",
        color="city_name" if "city_name" in df.columns else None,
        labels={"x": "Số lượng tin", "y": "Quận/Huyện"},
        height=max(400, len(df) * 22),
    )
    fig.update_layout(
        yaxis={"categoryorder": "total ascending"},
        margin=dict(l=0, r=0, t=10, b=0),
        legend_title_text="Thành phố",
        plot_bgcolor="white",
    )
    return _plotly_div(fig)


def build_chart_project(df) -> str:
    import plotly.express as px

    df = df.sort_values("avg_price", ascending=False).head(20)
    fig = px.bar(
        df,
        x="avg_price",
        y="project_name",
        orientation="h",
        color="city_name" if "city_name" in df.columns else None,
        labels={"avg_price": "Giá TB (VNĐ)", "project_name": "Dự án"},
        height=max(400, len(df) * 28),
    )
    fig.update_layout(
        yaxis={"categoryorder": "total ascending"},
        margin=dict(l=0, r=0, t=10, b=0),
        xaxis_tickformat=",.0f",
        legend_title_text="Thành phố",
        plot_bgcolor="white",
    )
    return _plotly_div(fig)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
async def main():
    print("[1] Fetching data from Malloy model ...")
    df_general, df_district, df_project = await fetch_all_data()

    print("[2] Extracting KPIs ...")
    kpi = df_general.iloc[0]

    print("[3] Building charts ...")
    chart_district = build_chart_district(df_district)
    chart_project  = build_chart_project(df_project)

    print("[4] Rendering HTML ...")
    report_date = date.today().isoformat()
    html = HTML_TEMPLATE.format(
        report_date=report_date,
        property_count=int(kpi.get("property_count", 0)),
        avg_price_b=float(kpi.get("avg_price", 0)) / 1e9,
        avg_price_1m2_m=float(kpi.get("avg_price_1m2", 0)) / 1e6,
        avg_area=float(kpi.get("avg_area", 0)),
        chart_district=chart_district,
        chart_project=chart_project,
    )

    output_path = OUTPUT_DIR / f"report_{report_date}.html"
    output_path.write_text(html, encoding="utf-8")
    print(f"[5] ✅ Report saved to: {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
