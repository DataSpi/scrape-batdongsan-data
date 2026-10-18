"""
Sinh biểu đồ minh hoạ cho bài content/blog_drafts/cho-thue-2026-07-personal.md.

Query trực tiếp re_gold.mart_real_estate_rent + re_gold.mart_real_estate (BigQuery),
áp đúng bộ lọc outlier đã dùng khi viết bài (diện tích 15-200m², giá thuê 1-200 tr/tháng,
giá bán/m² 5-1.000 tr/m² cho `căn hộ chung cư`), rồi xuất PNG vào
content/blog_drafts/assets/cho-thue-2026-07/.

Chạy: python content/blog_drafts/cho_thue_2026_07_charts.py
"""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from google.cloud import bigquery
from google.oauth2 import service_account
from matplotlib.colors import LinearSegmentedColormap

REPO_ROOT = Path(__file__).resolve().parents[2]
KEYFILE = REPO_ROOT / "gcp_service_account.json"
OUT_DIR = Path(__file__).resolve().parent / "assets" / "cho-thue-2026-07"

# --- palette (dataviz skill default, light-mode slots) ---
HCM = "Hồ Chí Minh"
HN = "Hà Nội"
CITY_COLOR = {HCM: "#2a78d6", HN: "#eb6834"}  # categorical slot 1 / slot 2, fixed order
SEQ_STEPS = ["#cde2fb", "#9ec5f4", "#5598e7", "#2a78d6", "#1c5cab", "#104281"]  # blue 100→650
SEQ_CMAP = LinearSegmentedColormap.from_list("seq_blue", SEQ_STEPS)

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_SECONDARY = "#52514e"
INK_MUTED = "#898781"
GRIDLINE = "#e1e0d9"
BASELINE = "#c3c2b7"

RENT_FILTER = "area_num BETWEEN 15 AND 200 AND price_per_month BETWEEN 1 AND 200"
SALE_FILTER = "real_estate_type = 'căn hộ chung cư' AND price_1m2 BETWEEN 5 AND 1000"


def bq_client() -> bigquery.Client:
    creds = service_account.Credentials.from_service_account_file(str(KEYFILE))
    return bigquery.Client(credentials=creds, project=creds.project_id)


def q(client: bigquery.Client, sql: str) -> pd.DataFrame:
    return client.query(sql).to_dataframe()


def setup_style() -> None:
    sns.set_theme(
        style="white",
        rc={
            "axes.facecolor": SURFACE,
            "figure.facecolor": SURFACE,
            "savefig.facecolor": SURFACE,
            "axes.edgecolor": BASELINE,
            "axes.labelcolor": INK_SECONDARY,
            "text.color": INK,
            "xtick.color": INK_MUTED,
            "ytick.color": INK_MUTED,
            "grid.color": GRIDLINE,
            "font.family": "sans-serif",
            "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica"],
        },
    )


def save(fig: plt.Figure, name: str) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / name
    fig.savefig(path, dpi=200, bbox_inches="tight", facecolor=SURFACE)
    plt.close(fig)
    print(f"saved {path}")


def style_bar_axes(ax, ylabel: str = "") -> None:
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.spines["bottom"].set_color(BASELINE)
    ax.yaxis.grid(True, color=GRIDLINE, linewidth=1)
    ax.set_axisbelow(True)
    ax.set_ylabel(ylabel, color=INK_SECONDARY)
    ax.set_xlabel("")
    ax.tick_params(length=0)


# ---------------------------------------------------------------- queries --


def fetch_bucket_supply(client) -> pd.DataFrame:
    sql = f"""
    WITH base AS (SELECT * FROM re_gold.mart_real_estate_rent WHERE {RENT_FILTER})
    SELECT city_name,
      CASE WHEN price_per_month < 10 THEN '< 10'
           WHEN price_per_month < 20 THEN '10-20'
           WHEN price_per_month < 30 THEN '20-30'
           WHEN price_per_month < 50 THEN '30-50'
           ELSE '> 50' END AS bucket,
      COUNT(*) n
    FROM base GROUP BY city_name, bucket
    """
    df = q(client, sql)
    order = ["< 10", "10-20", "20-30", "30-50", "> 50"]
    df["bucket"] = pd.Categorical(df["bucket"], categories=order, ordered=True)
    df["pct"] = df.groupby("city_name")["n"].transform(lambda s: s / s.sum() * 100)
    return df.sort_values(["city_name", "bucket"])


def fetch_city_overall(client) -> pd.DataFrame:
    rent = q(
        client,
        f"""
        SELECT city_name, ROUND(AVG(price_per_month),2) rent_thang,
               ROUND(AVG(price_per_m2_per_month),3) rent_m2
        FROM re_gold.mart_real_estate_rent WHERE {RENT_FILTER}
        GROUP BY city_name
    """,
    )
    sale = q(
        client,
        f"""
        SELECT city_name, ROUND(AVG(price_1m2),2) sale_m2
        FROM re_gold.mart_real_estate WHERE {SALE_FILTER}
        GROUP BY city_name
    """,
    )
    df = rent.merge(sale, on="city_name")
    df = df[df.city_name.isin([HCM, HN])].copy()
    df["pr_ratio"] = df.sale_m2 / (df.rent_m2 * 12)
    return df


def fetch_top_district(client, n_min: int = 30, top_n: int = 5) -> pd.DataFrame:
    sql = f"""
    WITH rent_base AS (SELECT * FROM re_gold.mart_real_estate_rent WHERE {RENT_FILTER}),
    rent_d AS (
      SELECT city_name, district_name, COUNT(*) n_rent,
             ROUND(AVG(price_per_m2_per_month),3) rent_m2
      FROM rent_base GROUP BY city_name, district_name HAVING COUNT(*) >= {n_min}
    ),
    sale_d AS (
      SELECT city_name, district_name, ROUND(AVG(price_1m2),2) sale_m2
      FROM re_gold.mart_real_estate WHERE {SALE_FILTER}
      GROUP BY city_name, district_name
    )
    SELECT r.city_name, r.district_name, r.n_rent, r.rent_m2, s.sale_m2,
           ROUND(s.sale_m2 / (r.rent_m2 * 12), 1) pr_ratio
    FROM rent_d r LEFT JOIN sale_d s USING(city_name, district_name)
    """
    df = q(client, sql)
    return df.sort_values(["city_name", "rent_m2"], ascending=[True, False]).groupby("city_name").head(top_n)


def fetch_bedroom_summary(client) -> pd.DataFrame:
    sql = f"""
    WITH rent_base AS (
      SELECT * FROM re_gold.mart_real_estate_rent
      WHERE {RENT_FILTER} AND bedrooms IN ('1','2','3')
    ),
    rent_agg AS (
      SELECT city_name, bedrooms, COUNT(*) n_rent,
             ROUND(AVG(price_per_month),2) rent_thang,
             ROUND(AVG(price_per_m2_per_month),3) rent_m2
      FROM rent_base GROUP BY city_name, bedrooms
    ),
    sale_agg AS (
      SELECT city_name, bedrooms, ROUND(AVG(price_1m2),2) sale_m2
      FROM re_gold.mart_real_estate
      WHERE {SALE_FILTER} AND bedrooms IN ('1','2','3')
      GROUP BY city_name, bedrooms
    )
    SELECT r.city_name, r.bedrooms, r.n_rent, r.rent_thang, r.rent_m2,
           s.sale_m2, ROUND(s.sale_m2/(r.rent_m2*12), 1) pr_ratio
    FROM rent_agg r LEFT JOIN sale_agg s USING(city_name, bedrooms)
    """
    df = q(client, sql)
    df["bedrooms"] = df["bedrooms"] + " PN"
    return df


def fetch_bedroom_district(client, bedroom: str, top_n: int = 5) -> pd.DataFrame:
    sql = f"""
    WITH rent_base AS (
      SELECT * FROM re_gold.mart_real_estate_rent
      WHERE {RENT_FILTER} AND bedrooms = '{bedroom}'
    )
    SELECT city_name, district_name, COUNT(*) n
    FROM rent_base GROUP BY city_name, district_name
    """
    df = q(client, sql)
    df["pct"] = df.groupby("city_name")["n"].transform(lambda s: s / s.sum() * 100)
    return df.sort_values(["city_name", "n"], ascending=[True, False]).groupby("city_name").head(top_n)


# ----------------------------------------------------------------- charts --


def chart_nguon_cung(df: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(7, 4.5))
    sns.barplot(data=df, x="bucket", y="pct", hue="city_name", ax=ax, palette=CITY_COLOR, hue_order=[HCM, HN])
    for cont in ax.containers:
        ax.bar_label(cont, fmt="%.1f%%", padding=2, color=INK_SECONDARY, fontsize=9)
    style_bar_axes(ax, ylabel="% tổng tin (theo TP)")
    ax.set_title("Phân bổ nguồn cung theo khoảng giá thuê (tr/tháng)", color=INK, fontsize=13, loc="left", pad=12)
    ax.legend(title="", frameon=False, loc="upper right")
    save(fig, "01_nguon_cung_gia_thue.png")


def chart_gia_hcm_hn(df: pd.DataFrame) -> None:
    df = df.set_index("city_name").loc[[HCM, HN]].reset_index()
    panels = [
        ("rent_thang", "Giá thuê TB (tr/tháng)", "%.1f"),
        ("rent_m2", "Giá thuê TB (tr/m²/tháng)", "%.3f"),
        ("sale_m2", "Giá bán TB (tr/m²)", "%.1f"),
        ("pr_ratio", "P/R ratio (năm)", "%.1f"),
    ]
    fig, axes = plt.subplots(1, 4, figsize=(14, 4))
    for ax, (col, title, fmt) in zip(axes, panels):
        bars = ax.bar(df.city_name, df[col], color=[CITY_COLOR[c] for c in df.city_name], width=0.55)
        ax.bar_label(bars, fmt=fmt, padding=3, color=INK_SECONDARY, fontsize=9)
        style_bar_axes(ax)
        ax.set_title(title, color=INK, fontsize=10.5, loc="left")
        ax.margins(y=0.18)
    fig.suptitle("Giá thuê & giá bán chung cư — HCM vs HN", color=INK, fontsize=13, x=0.02, ha="left", y=1.04)
    save(fig, "02_gia_hcm_vs_hn.png")


def chart_top_district(df: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    for ax, city in zip(axes, [HCM, HN]):
        sub = df[df.city_name == city].sort_values("rent_m2")
        norm = (sub.rent_m2 - sub.rent_m2.min()) / (sub.rent_m2.max() - sub.rent_m2.min() + 1e-9)
        colors = [SEQ_CMAP(0.35 + 0.65 * v) for v in norm]
        bars = ax.barh(sub.district_name, sub.rent_m2, color=colors, height=0.6)
        for bar, pr in zip(bars, sub.pr_ratio):
            ax.text(
                bar.get_width() + sub.rent_m2.max() * 0.02,
                bar.get_y() + bar.get_height() / 2,
                f"{bar.get_width():.3f} · P/R {pr:.1f}",
                va="center",
                fontsize=9,
                color=INK_SECONDARY,
            )
        ax.spines[["top", "right", "left"]].set_visible(False)
        ax.spines["bottom"].set_color(BASELINE)
        ax.xaxis.grid(True, color=GRIDLINE, linewidth=1)
        ax.set_axisbelow(True)
        ax.tick_params(length=0)
        ax.set_xlim(0, sub.rent_m2.max() * 1.5)
        ax.set_title(f"{city} — top quận theo giá thuê/m²", color=INK, fontsize=11, loc="left")
    fig.suptitle(
        "Giá thuê/m² và P/R ratio theo quận (n ≥ 30 tin/quận)", color=INK, fontsize=13, x=0.02, ha="left", y=1.02
    )
    save(fig, "03_top_quan_gia_thue.png")


def chart_pr_by_bedroom(df: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    sns.barplot(
        data=df,
        x="bedrooms",
        y="pr_ratio",
        hue="city_name",
        ax=ax,
        palette=CITY_COLOR,
        hue_order=[HCM, HN],
        order=["1 PN", "2 PN", "3 PN"],
    )
    for cont in ax.containers:
        ax.bar_label(cont, fmt="%.1f", padding=2, color=INK_SECONDARY, fontsize=9)
    ax.axhline(20, color=INK_MUTED, linewidth=1, linestyle="--")
    ax.text(0.6, 21.3, 'ngưỡng "nên thuê" (20)', color=INK_MUTED, fontsize=8.5, ha="center")
    style_bar_axes(ax, ylabel="P/R ratio (năm)")
    ax.set_title("P/R ratio theo phân khúc phòng ngủ — HCM vs HN", color=INK, fontsize=13, loc="left", pad=12)
    ax.legend(title="", frameon=False, loc="upper left")
    save(fig, "04_pr_ratio_theo_phong_ngu.png")


def chart_bedroom_district(df: pd.DataFrame, bedroom_label: str, filename: str) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    for ax, city in zip(axes, [HCM, HN]):
        sub = df[df.city_name == city].sort_values("pct")
        bars = ax.barh(sub.district_name, sub.pct, color=CITY_COLOR[city], height=0.55)
        ax.bar_label(bars, fmt="%.1f%%", padding=3, color=INK_SECONDARY, fontsize=9)
        ax.spines[["top", "right", "left"]].set_visible(False)
        ax.spines["bottom"].set_color(BASELINE)
        ax.xaxis.grid(True, color=GRIDLINE, linewidth=1)
        ax.set_axisbelow(True)
        ax.tick_params(length=0)
        ax.set_xlim(0, sub.pct.max() * 1.25)
        ax.set_title(city, color=INK, fontsize=11, loc="left")
    fig.suptitle(
        f"Phân bổ nguồn cung {bedroom_label} cho thuê theo quận (% trong TP)",
        color=INK,
        fontsize=13,
        x=0.02,
        ha="left",
        y=1.03,
    )
    save(fig, filename)


def main() -> None:
    setup_style()
    client = bq_client()

    chart_nguon_cung(fetch_bucket_supply(client))
    chart_gia_hcm_hn(fetch_city_overall(client))
    chart_top_district(fetch_top_district(client))

    bedroom_summary = fetch_bedroom_summary(client)
    chart_pr_by_bedroom(bedroom_summary)

    for code, label, filename in [
        ("1", "1PN", "05_phan_bo_quan_1pn.png"),
        ("2", "2PN", "06_phan_bo_quan_2pn.png"),
        ("3", "3PN", "07_phan_bo_quan_3pn.png"),
    ]:
        chart_bedroom_district(fetch_bedroom_district(client, code), label, filename)

    print(f"\nXong — {len(list(OUT_DIR.glob('*.png')))} ảnh trong {OUT_DIR}")


if __name__ == "__main__":
    main()
