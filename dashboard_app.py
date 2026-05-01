"""
============================================================
 JAKLINGKO INTERACTIVE DASHBOARD - ENHANCED VERSION
 FILE  : dashboard_app.py
 DESC  : Dashboard interaktif dengan fitur:
         - Real-time monitoring (auto-refresh)
         - Interpretasi otomatis berbasis data
         - Generate & unduh laporan PDF
         - Palet warna brand JakLingko
 STACK : Streamlit + Plotly + SQLAlchemy + ReportLab
============================================================
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine
from datetime import datetime, timedelta
import time
import io
import matplotlib
matplotlib.use("Agg")   # non-interactive backend, aman untuk Streamlit
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.ticker import FuncFormatter

# PDF generation
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether, Image as RLImage
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import PageBreak


# ============================================================
# BRAND COLORS & CONSTANTS
# ============================================================
C_GREEN  = "#b0de38"   # Lime green - accent utama
C_BLUE   = "#0083b3"   # Ocean blue - warna primer
C_WHITE  = "#FFFFFF"   # Putih
C_DARK   = "#0a2940"   # Dark navy - teks utama
C_LIGHT  = "#e8f4f8"   # Light blue tint - background card
C_GRAY   = "#6b7f8e"   # Abu-abu medium - teks sekunder
C_GREEN2 = "#8cb82e"   # Green gelap untuk kontras

PLOTLY_COLORS = [C_BLUE, C_GREEN, "#00a8e8", "#7ec832", "#004d6e", "#d4f56a"]


# ============================================================
# 1. KONFIGURASI HALAMAN
# ============================================================
st.set_page_config(
    page_title="JakLingko Analytics Command Center",
    page_icon="https://upload.wikimedia.org/wikipedia/en/d/d1/JakLingko.svg",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown(f"""
<style>
    /* ---- IMPORT FONT ---- */
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&display=swap');

    /* ---- GLOBAL ---- */
    html, body, [class*="css"] {{
        font-family: 'DM Sans', sans-serif;
        background-color: {C_DARK};
        color: {C_WHITE};
    }}
    .main {{
        background-color: {C_DARK};
    }}
    .block-container {{
        padding: 1.5rem 2rem 3rem 2rem;
        max-width: 1400px;
    }}

    /* ---- HEADER ---- */
    .dash-header {{
        background: linear-gradient(135deg, {C_BLUE} 0%, #005580 60%, {C_DARK} 100%);
        border-radius: 16px;
        padding: 2rem 2.5rem;
        margin-bottom: 1.5rem;
        border-left: 6px solid {C_GREEN};
        position: relative;
        overflow: hidden;
    }}
    .dash-header::before {{
        content: '';
        position: absolute;
        top: -40px; right: -40px;
        width: 200px; height: 200px;
        background: radial-gradient(circle, {C_GREEN}33 0%, transparent 70%);
    }}
    .dash-header h1 {{
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1.9rem;
        font-weight: 700;
        color: {C_WHITE};
        margin: 0;
        letter-spacing: -0.5px;
    }}
    .dash-header p {{
        color: {C_GREEN};
        font-size: 0.85rem;
        font-weight: 500;
        margin: 0.4rem 0 0 0;
        letter-spacing: 0.5px;
        text-transform: uppercase;
    }}

    /* ---- KPI CARDS ---- */
    .kpi-card {{
        background: linear-gradient(145deg, #0f3555 0%, #0a2940 100%);
        border: 1px solid {C_BLUE}44;
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        position: relative;
        overflow: hidden;
        transition: transform 0.2s, box-shadow 0.2s;
    }}
    .kpi-card:hover {{
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(0,131,179,0.25);
    }}
    .kpi-card::after {{
        content: '';
        position: absolute;
        bottom: 0; left: 0; right: 0;
        height: 3px;
        background: linear-gradient(90deg, {C_GREEN}, {C_BLUE});
    }}
    .kpi-label {{
        font-size: 0.72rem;
        font-weight: 600;
        color: {C_GRAY};
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 0.5rem;
    }}
    .kpi-value {{
        font-family: 'Space Grotesk', sans-serif;
        font-size: 2rem;
        font-weight: 700;
        color: {C_WHITE};
        line-height: 1;
    }}
    .kpi-delta {{
        font-size: 0.75rem;
        margin-top: 0.4rem;
        color: {C_GREEN};
        font-weight: 500;
    }}
    .kpi-icon {{
        position: absolute;
        top: 1rem; right: 1rem;
        font-size: 1.5rem;
        opacity: 0.15;
    }}

    /* ---- SECTION HEADERS ---- */
    .section-header {{
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1rem;
        font-weight: 600;
        color: {C_GREEN};
        text-transform: uppercase;
        letter-spacing: 1.5px;
        border-left: 3px solid {C_GREEN};
        padding-left: 0.75rem;
        margin: 1.5rem 0 1rem 0;
    }}

    /* ---- CHART CONTAINER ---- */
    .chart-card {{
        background: linear-gradient(145deg, #0f3555 0%, #0a2940 100%);
        border: 1px solid {C_BLUE}33;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
    }}

    /* ---- INTERPRETATION BOX ---- */
    .interp-box {{
        background: linear-gradient(135deg, #003d5c 0%, #0a2940 100%);
        border: 1px solid {C_GREEN}55;
        border-left: 4px solid {C_GREEN};
        border-radius: 10px;
        padding: 1.1rem 1.4rem;
        margin-top: 0.75rem;
    }}
    .interp-title {{
        font-size: 0.72rem;
        font-weight: 700;
        color: {C_GREEN};
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 0.5rem;
    }}
    .interp-text {{
        font-size: 0.85rem;
        color: #c5dde8;
        line-height: 1.65;
    }}
    .interp-text strong {{
        color: {C_WHITE};
    }}

    /* ---- ALERT ---- */
    .alert-box {{
        background: #1a0a00;
        border: 1px solid #ff6b35;
        border-left: 4px solid #ff6b35;
        border-radius: 8px;
        padding: 0.8rem 1.2rem;
        margin-top: 0.5rem;
        font-size: 0.82rem;
        color: #ffc4a0;
    }}

    /* ---- SIDEBAR ---- */
    [data-testid="stSidebar"] {{
        background: #07202e;
        border-right: 1px solid {C_BLUE}33;
    }}
    [data-testid="stSidebar"] .stSelectbox label,
    [data-testid="stSidebar"] .stSlider label,
    [data-testid="stSidebar"] .stCheckbox label {{
        color: {C_WHITE} !important;
        font-size: 0.82rem;
        font-weight: 500;
    }}
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3 {{
        color: {C_GREEN} !important;
        font-family: 'Space Grotesk', sans-serif;
    }}

    /* ---- STATUS INDICATOR ---- */
    .status-live {{
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: {C_GREEN}22;
        border: 1px solid {C_GREEN}66;
        border-radius: 20px;
        padding: 3px 10px;
        font-size: 0.7rem;
        font-weight: 600;
        color: {C_GREEN};
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    .status-dot {{
        width: 6px; height: 6px;
        background: {C_GREEN};
        border-radius: 50%;
        animation: pulse 1.5s ease-in-out infinite;
    }}
    @keyframes pulse {{
        0%, 100% {{ opacity: 1; transform: scale(1); }}
        50% {{ opacity: 0.4; transform: scale(0.8); }}
    }}

    /* ---- DIVIDER ---- */
    .divider {{
        border: none;
        border-top: 1px solid {C_BLUE}33;
        margin: 1.2rem 0;
    }}

    /* ---- STREAMLIT OVERRIDES ---- */
    .stMetric {{ display: none; }}
    div[data-testid="stHorizontalBlock"] > div {{ padding: 0 0.3rem; }}
    .stPlotlyChart {{ border-radius: 8px; overflow: hidden; }}
    button[kind="primary"] {{
        background: {C_GREEN} !important;
        color: {C_DARK} !important;
        font-weight: 700 !important;
        border: none !important;
        border-radius: 8px !important;
    }}
    button[kind="primary"]:hover {{
        background: {C_GREEN2} !important;
    }}
    .stDownloadButton button {{
        background: linear-gradient(135deg, {C_GREEN} 0%, {C_GREEN2} 100%) !important;
        color: {C_DARK} !important;
        font-weight: 700 !important;
        border: none !important;
        border-radius: 8px !important;
        width: 100%;
        padding: 0.6rem;
        font-size: 0.85rem;
    }}
    .stSpinner > div {{
        border-top-color: {C_GREEN} !important;
    }}
    h1, h2, h3, h4 {{ color: {C_WHITE} !important; }}

    /* ---- LAST UPDATE BADGE ---- */
    .update-badge {{
        font-size: 0.7rem;
        color: {C_GRAY};
        text-align: right;
        padding: 0.25rem 0;
    }}

    /* ---- TABLE ---- */
    .styled-table {{
        width: 100%;
        border-collapse: collapse;
        font-size: 0.82rem;
        color: {C_WHITE};
    }}
    .styled-table th {{
        background: {C_BLUE}44;
        color: {C_GREEN};
        font-weight: 600;
        padding: 0.5rem 0.8rem;
        text-align: left;
        font-size: 0.72rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    .styled-table td {{
        padding: 0.45rem 0.8rem;
        border-bottom: 1px solid {C_BLUE}22;
        color: #c5dde8;
    }}
</style>
""", unsafe_allow_html=True)


# ============================================================
# 2. KONEKSI & CACHING DATA
# ============================================================
@st.cache_data(ttl=60)   # Cache 60 detik untuk quasi-realtime
def load_data():
    engine = create_engine("mysql+pymysql://root:Bintang123@localhost:3306/jaklingko_dwh")
    query = """
        SELECT
            w.tanggal, w.nama_hari, w.is_weekend,
            f.jam_tap_in, f.total_bayar, f.transaksi_id,
            p.segment_pengguna, p.gender, p.bank_kartu,
            r.jenis_koridor
        FROM fact_transaksi_perjalanan f
        LEFT JOIN dim_waktu        w ON f.waktu_key    = w.waktu_key
        LEFT JOIN dim_pengguna     p ON f.pengguna_key = p.pengguna_key
        LEFT JOIN dim_rute         r ON f.rute_key     = r.rute_key
        WHERE w.tanggal != '1900-01-01'
    """
    df = pd.read_sql(query, engine)
    df['tanggal']    = pd.to_datetime(df['tanggal'])
    df['jam_tap_in'] = pd.to_numeric(df['jam_tap_in'], errors='coerce')
    df['total_bayar']= pd.to_numeric(df['total_bayar'], errors='coerce')
    return df


# ============================================================
# 3. HELPER: PLOTLY THEME
# ============================================================
PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor ="rgba(0,0,0,0)",
    font         =dict(family="DM Sans", color=C_WHITE, size=12),
    title_font   =dict(family="Space Grotesk", color=C_WHITE, size=14),
    xaxis        =dict(gridcolor="rgba(0,131,179,0.2)", zeroline=False, tickfont=dict(size=11)),
    yaxis        =dict(gridcolor="rgba(0,131,179,0.2)", zeroline=False, tickfont=dict(size=11)),
    margin       =dict(l=10, r=10, t=40, b=10),
    colorway     =PLOTLY_COLORS,
    hoverlabel   =dict(bgcolor=C_DARK, font_color=C_WHITE, bordercolor=C_BLUE),
)

# Default legend style — merge ke PLOTLY_LAYOUT saat dibutuhkan
_LEGEND_DEFAULT = dict(bgcolor="rgba(0,0,0,0)", font=dict(color=C_WHITE))

def layout(**overrides):
    """Return PLOTLY_LAYOUT merged dengan overrides per-chart.
    Menghindari duplikasi keyword argument saat **PLOTLY_LAYOUT digunakan bersama
    parameter tambahan yang mungkin sudah ada di PLOTLY_LAYOUT."""
    base = {**PLOTLY_LAYOUT, "legend": _LEGEND_DEFAULT}
    base.update(overrides)
    return base


# ============================================================
# 4. HELPER: INTERPRETASI OTOMATIS
# ============================================================
def interpret_trend(tren_df):
    """Analisis tren volume harian dan beri interpretasi."""
    if len(tren_df) < 3:
        return "Data tren belum cukup untuk dianalisis."
    recent_7  = tren_df.tail(7)['volume'].mean()
    before_7  = tren_df.iloc[-14:-7]['volume'].mean() if len(tren_df) >= 14 else tren_df.head(7)['volume'].mean()
    delta_pct = ((recent_7 - before_7) / before_7 * 100) if before_7 > 0 else 0
    peak_day  = tren_df.loc[tren_df['volume'].idxmax(), 'tanggal'].strftime('%d %b %Y')
    peak_vol  = int(tren_df['volume'].max())

    if delta_pct >= 5:
        trend_text = f"tumbuh positif sebesar <strong>{delta_pct:.1f}%</strong> dibandingkan 7 hari sebelumnya"
    elif delta_pct <= -5:
        trend_text = f"mengalami penurunan <strong>{abs(delta_pct):.1f}%</strong> dibandingkan 7 hari sebelumnya"
    else:
        trend_text = "relatif stabil tanpa fluktuasi signifikan"

    return (f"Volume perjalanan harian {trend_text}. "
            f"Puncak aktivitas tertinggi terjadi pada <strong>{peak_day}</strong> "
            f"dengan <strong>{peak_vol:,} transaksi</strong>. "
            f"Rata-rata 7 hari terakhir: <strong>{recent_7:.0f} transaksi/hari</strong>.")


def interpret_rush_hour(rush_df):
    """Identifikasi jam sibuk dan beri rekomendasi."""
    if rush_df.empty:
        return "Data jam tidak tersedia."
    top3     = rush_df.nlargest(3, 'volume')['jam_tap_in'].tolist()
    morning  = rush_df[rush_df['jam_tap_in'].between(6, 9)]['volume'].sum()
    evening  = rush_df[rush_df['jam_tap_in'].between(16, 19)]['volume'].sum()
    dominant = "pagi" if morning >= evening else "sore"
    top3_str = ", ".join([f"pukul {int(h):02d}.00" for h in top3])

    return (f"Pola distribusi jam menunjukkan jam sibuk dominan pada <strong>{top3_str}</strong>. "
            f"Lonjakan utama terjadi di periode <strong>{dominant} hari</strong>, "
            f"sehingga penambahan armada di jam tersebut akan berdampak signifikan terhadap kepuasan penumpang.")


def interpret_segment(demo_df):
    """Analisis komposisi segmen pengguna."""
    if demo_df.empty:
        return "Data segmen tidak tersedia."
    total    = demo_df['total'].sum()
    top_seg  = demo_df.loc[demo_df['total'].idxmax()]
    top_pct  = top_seg['total'] / total * 100
    n_seg    = len(demo_df)

    if top_pct > 60:
        concentration = f"terkonsentrasi kuat pada segmen <strong>{top_seg['segment_pengguna']}</strong> ({top_pct:.1f}%)"
    elif top_pct > 40:
        concentration = f"didominasi oleh segmen <strong>{top_seg['segment_pengguna']}</strong> ({top_pct:.1f}%)"
    else:
        concentration = f"tersebar merata di antara <strong>{n_seg} segmen</strong>"

    return (f"Basis penumpang {concentration}. "
            f"Program loyalitas dan tarif diferensiasi dapat dioptimalkan berdasarkan proporsi segmen ini "
            f"untuk meningkatkan retensi dan daya beli.")


def interpret_bank(bank_df):
    """Analisis preferensi bank."""
    if bank_df.empty:
        return "Data kartu tidak tersedia."
    total   = bank_df['total'].sum()
    top_bank = bank_df.loc[bank_df['total'].idxmax()]
    top_pct  = top_bank['total'] / total * 100
    bottom   = bank_df.loc[bank_df['total'].idxmin()]['bank_kartu']

    return (f"<strong>{top_bank['bank_kartu']}</strong> mendominasi penggunaan kartu dengan pangsa <strong>{top_pct:.1f}%</strong>. "
            f"Kerjasama co-branding atau diskon khusus bersama bank tersebut berpotensi meningkatkan loyalitas. "
            f"Sebaliknya, adopsi kartu <strong>{bottom}</strong> masih rendah dan perlu strategi edukasi pengguna lebih lanjut.")


# ============================================================
# 5A. HELPER: MATPLOTLIB CHARTS UNTUK PDF
# ============================================================

# Warna brand sebagai tuple RGB (0-1) untuk Matplotlib
MPL_BLUE  = (0/255, 131/255, 179/255)
MPL_GREEN = (176/255, 222/255, 56/255)
MPL_DARK  = (10/255, 41/255, 64/255)
MPL_GRAY  = (107/255, 127/255, 142/255)
MPL_LIGHT = (232/255, 244/255, 248/255)

def _mpl_style(ax, fig):
    """Terapkan style brand JakLingko ke figure Matplotlib."""
    fig.patch.set_facecolor("white")
    ax.set_facecolor("#f5fafc")
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color("#ccddee")
    ax.spines['bottom'].set_color("#ccddee")
    ax.tick_params(colors="#444444", labelsize=8)
    ax.yaxis.label.set_color("#444444")
    ax.xaxis.label.set_color("#444444")
    ax.grid(axis='y', color="#ccddee", linewidth=0.6, linestyle='--')
    ax.set_axisbelow(True)


def _fig_to_rl_image(fig, width_cm=17, height_cm=7):
    """Render Matplotlib figure ke ReportLab Image (embed sebagai PNG in-memory)."""
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close(fig)
    buf.seek(0)
    return RLImage(buf, width=width_cm * cm, height=height_cm * cm)


def _chart_tren(tren_df) -> RLImage:
    """Line chart tren volume harian + MA7."""
    fig, ax = plt.subplots(figsize=(10, 3.8))
    _mpl_style(ax, fig)

    ax.fill_between(tren_df['tanggal'], tren_df['volume'],
                    alpha=0.15, color=MPL_BLUE)
    ax.plot(tren_df['tanggal'], tren_df['volume'],
            color=MPL_BLUE, linewidth=2, label='Volume Harian', zorder=3)
    ax.scatter(tren_df['tanggal'], tren_df['volume'],
               color=MPL_GREEN, s=20, zorder=4)

    if len(tren_df) >= 7:
        ma7 = tren_df['volume'].rolling(7).mean()
        ax.plot(tren_df['tanggal'], ma7,
                color=MPL_GREEN, linewidth=1.8, linestyle='--',
                label='MA 7 Hari', zorder=3)

    # Tandai puncak
    idx_peak = tren_df['volume'].idxmax()
    ax.annotate(
        f"Puncak\n{tren_df.loc[idx_peak,'volume']:,}",
        xy=(tren_df.loc[idx_peak,'tanggal'], tren_df.loc[idx_peak,'volume']),
        xytext=(0, 14), textcoords='offset points',
        ha='center', fontsize=7.5, color=MPL_BLUE,
        arrowprops=dict(arrowstyle='->', color=MPL_BLUE, lw=1.2),
    )

    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{int(x):,}"))
    ax.set_xlabel("Tanggal", fontsize=8)
    ax.set_ylabel("Jumlah Transaksi", fontsize=8)
    fig.autofmt_xdate(rotation=30, ha='right')
    ax.legend(fontsize=8, framealpha=0.5)
    fig.tight_layout()
    return _fig_to_rl_image(fig, width_cm=17, height_cm=5)


def _chart_rush(df_f) -> RLImage:
    """Bar chart distribusi jam tap-in."""
    rush = df_f.groupby('jam_tap_in').size().reset_index(name='volume')
    rush = rush.sort_values('jam_tap_in')

    fig, ax = plt.subplots(figsize=(10, 3.5))
    _mpl_style(ax, fig)

    bar_colors = [MPL_GREEN if v == rush['volume'].max() else MPL_BLUE
                  for v in rush['volume']]
    bars = ax.bar(rush['jam_tap_in'].astype(int), rush['volume'],
                  color=bar_colors, width=0.7, zorder=3)

    # Label nilai di atas bar tertinggi saja
    max_v = rush['volume'].max()
    for bar, v in zip(bars, rush['volume']):
        if v == max_v:
            ax.text(bar.get_x() + bar.get_width()/2, v + max_v*0.01,
                    f"{v:,}", ha='center', va='bottom', fontsize=7.5,
                    color=MPL_BLUE, fontweight='bold')

    ax.set_xticks(rush['jam_tap_in'].astype(int))
    ax.set_xticklabels([f"{int(h):02d}:00" for h in rush['jam_tap_in']],
                       rotation=45, ha='right', fontsize=7.5)
    ax.set_xlabel("Jam", fontsize=8)
    ax.set_ylabel("Volume Transaksi", fontsize=8)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{int(x):,}"))

    legend_patches = [
        mpatches.Patch(color=MPL_GREEN, label='Jam Puncak'),
        mpatches.Patch(color=MPL_BLUE,  label='Jam Lainnya'),
    ]
    ax.legend(handles=legend_patches, fontsize=8, framealpha=0.5)
    fig.tight_layout()
    return _fig_to_rl_image(fig, width_cm=17, height_cm=5)


def _chart_segmen(df_f) -> RLImage:
    """Donut chart + bar komposisi segmen penumpang (side by side)."""
    seg = df_f.groupby('segment_pengguna').size().reset_index(name='total')
    seg = seg.sort_values('total', ascending=False)
    total = seg['total'].sum()
    seg['pct'] = seg['total'] / total * 100

    palette = [MPL_BLUE, MPL_GREEN, (0/255,168/255,232/255),
               (126/255,200/255,50/255), (0/255,77/255,110/255)]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
    fig.patch.set_facecolor("white")

    # --- Donut ---
    wedges, texts, autotexts = ax1.pie(
        seg['total'],
        labels=seg['segment_pengguna'],
        colors=palette[:len(seg)],
        autopct='%1.1f%%',
        startangle=90,
        wedgeprops=dict(width=0.5, edgecolor='white', linewidth=1.5),
        pctdistance=0.78,
    )
    for t in texts:
        t.set_fontsize(8)
    for at in autotexts:
        at.set_fontsize(7.5)
        at.set_color('white')
        at.set_fontweight('bold')
    ax1.set_facecolor("white")
    ax1.set_title("Proporsi Segmen", fontsize=9, color="#333333", pad=8)

    # --- Horizontal bar ---
    _mpl_style(ax2, fig)
    bars = ax2.barh(seg['segment_pengguna'], seg['pct'],
                    color=palette[:len(seg)], height=0.55, zorder=3)
    for bar, pct in zip(bars, seg['pct']):
        ax2.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height()/2,
                 f"{pct:.1f}%", va='center', fontsize=8, color="#333333")
    ax2.set_xlabel("Persentase (%)", fontsize=8)
    ax2.set_xlim(0, seg['pct'].max() * 1.2)
    ax2.invert_yaxis()
    ax2.set_title("Persentase per Segmen", fontsize=9, color="#333333", pad=8)
    ax2.grid(axis='x', color="#ccddee", linewidth=0.6, linestyle='--')
    ax2.grid(axis='y', visible=False)

    fig.tight_layout(w_pad=3)
    return _fig_to_rl_image(fig, width_cm=17, height_cm=5.5)


def _chart_bank(df_f) -> RLImage:
    """Horizontal bar chart preferensi bank + pie share."""
    bank = df_f.groupby('bank_kartu').size().reset_index(name='total')
    bank = bank.sort_values('total', ascending=True)
    total = bank['total'].sum()
    bank['pct'] = bank['total'] / total * 100

    n = len(bank)
    palette = plt.cm.Blues_r(
        [0.3 + 0.6*(i/max(n-1,1)) for i in range(n)]
    )
    # Override bar tertinggi dengan green
    colors_bar = list(palette)
    colors_bar[-1] = MPL_GREEN  # bar terpanjang (sorted ascending → last)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, max(3.5, n*0.6+1)))
    fig.patch.set_facecolor("white")

    # --- Horizontal bar ---
    _mpl_style(ax1, fig)
    bars = ax1.barh(bank['bank_kartu'], bank['total'],
                    color=colors_bar, height=0.6, zorder=3)
    for bar, v in zip(bars, bank['total']):
        ax1.text(bar.get_width() + total*0.005, bar.get_y() + bar.get_height()/2,
                 f"{v:,}", va='center', fontsize=8, color="#333333")
    ax1.set_xlabel("Jumlah Transaksi", fontsize=8)
    ax1.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{int(x):,}"))
    ax1.set_xlim(0, bank['total'].max() * 1.2)
    ax1.set_title("Volume per Bank", fontsize=9, color="#333333", pad=8)
    ax1.grid(axis='y', visible=False)

    # --- Pie share ---
    ax2.set_facecolor("white")
    wedge_colors = list(plt.cm.Blues_r(
        [0.3 + 0.6*(i/max(n-1,1)) for i in range(n)]
    ))
    wedge_colors[bank['total'].values.argmax()] = MPL_GREEN
    wedges, texts, autotexts = ax2.pie(
        bank['total'],
        labels=bank['bank_kartu'],
        colors=wedge_colors,
        autopct='%1.1f%%',
        startangle=90,
        wedgeprops=dict(edgecolor='white', linewidth=1.2),
        pctdistance=0.75,
    )
    for t in texts: t.set_fontsize(7.5)
    for at in autotexts:
        at.set_fontsize(7)
        at.set_color('white')
        at.set_fontweight('bold')
    ax2.set_title("Pangsa Pasar Bank", fontsize=9, color="#333333", pad=8)

    fig.tight_layout(w_pad=3)
    return _fig_to_rl_image(fig, width_cm=17, height_cm=max(4.5, n*0.7+1))


def _chart_weekend(df_f) -> RLImage:
    """Line chart perbandingan hari kerja vs akhir pekan per jam."""
    if 'is_weekend' not in df_f.columns:
        return None
    wk = df_f.groupby(['is_weekend', 'jam_tap_in']).size().reset_index(name='volume')
    weekday = wk[wk['is_weekend']==0].sort_values('jam_tap_in')
    weekend = wk[wk['is_weekend']==1].sort_values('jam_tap_in')

    fig, ax = plt.subplots(figsize=(10, 3.5))
    _mpl_style(ax, fig)

    ax.plot(weekday['jam_tap_in'], weekday['volume'],
            color=MPL_BLUE, linewidth=2, marker='o', markersize=4,
            label='Hari Kerja', zorder=3)
    ax.fill_between(weekday['jam_tap_in'], weekday['volume'],
                    alpha=0.1, color=MPL_BLUE)
    ax.plot(weekend['jam_tap_in'], weekend['volume'],
            color=MPL_GREEN, linewidth=2, marker='s', markersize=4,
            label='Akhir Pekan', zorder=3)
    ax.fill_between(weekend['jam_tap_in'], weekend['volume'],
                    alpha=0.1, color=MPL_GREEN)

    ax.set_xlabel("Jam", fontsize=8)
    ax.set_ylabel("Volume Transaksi", fontsize=8)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{int(x):,}"))
    ax.set_xticks(range(0, 24, 2))
    ax.set_xticklabels([f"{h:02d}:00" for h in range(0, 24, 2)],
                       rotation=45, ha='right', fontsize=7.5)
    ax.legend(fontsize=8, framealpha=0.5)
    fig.tight_layout()
    return _fig_to_rl_image(fig, width_cm=17, height_cm=5)


# ============================================================
# 5. HELPER: GENERATE PDF REPORT
# ============================================================
def generate_pdf_report(df_f, metrics: dict, interpretations: dict) -> bytes:
    """Hasilkan laporan PDF eksekutif JakLingko."""

    buffer = io.BytesIO()

    # --- Warna brand dalam format ReportLab ---
    RL_BLUE  = colors.HexColor(C_BLUE)
    RL_GREEN = colors.HexColor(C_GREEN)
    RL_DARK  = colors.HexColor(C_DARK)
    RL_GRAY  = colors.HexColor(C_GRAY)
    RL_LIGHT = colors.HexColor("#e8f4f8")
    RL_GREEN2= colors.HexColor(C_GREEN2)

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm,
        topMargin=2.5*cm, bottomMargin=2*cm,
        title="Laporan Analitik JakLingko",
        author="JakLingko Analytics Command Center",
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'BrandTitle', parent=styles['Title'],
        fontName='Helvetica-Bold', fontSize=22,
        textColor=RL_BLUE, spaceAfter=4,
        alignment=TA_LEFT,
    )
    subtitle_style = ParagraphStyle(
        'BrandSub', parent=styles['Normal'],
        fontName='Helvetica', fontSize=9,
        textColor=RL_GRAY, spaceAfter=2, alignment=TA_LEFT,
    )
    section_style = ParagraphStyle(
        'BrandSection', parent=styles['Heading2'],
        fontName='Helvetica-Bold', fontSize=11,
        textColor=RL_BLUE, spaceBefore=14, spaceAfter=6,
        borderPad=(0, 0, 4, 0),
    )
    body_style = ParagraphStyle(
        'BrandBody', parent=styles['Normal'],
        fontName='Helvetica', fontSize=9,
        textColor=colors.HexColor("#333333"),
        leading=14, spaceAfter=4,
        alignment=TA_JUSTIFY,
    )
    caption_style = ParagraphStyle(
        'Caption', parent=styles['Normal'],
        fontName='Helvetica-Oblique', fontSize=8,
        textColor=RL_GRAY, spaceAfter=6, alignment=TA_CENTER,
    )
    label_style = ParagraphStyle(
        'Label', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=8,
        textColor=RL_GRAY, spaceAfter=2,
    )
    kpi_style = ParagraphStyle(
        'KPI', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=18,
        textColor=RL_BLUE, leading=22,
    )
    footer_style = ParagraphStyle(
        'Footer', parent=styles['Normal'],
        fontName='Helvetica', fontSize=7.5,
        textColor=RL_GRAY, alignment=TA_CENTER,
    )

    story = []
    now = datetime.now()

    # ---- HEADER ----
    story.append(Spacer(1, 0.2*cm))
    header_data = [[
        Paragraph("JAKLINGKO", ParagraphStyle('Logo', fontName='Helvetica-Bold', fontSize=26,
                                               textColor=RL_BLUE)),
        Paragraph(
            f"LAPORAN ANALITIK OPERASIONAL<br/>"
            f"<font color='#{C_GRAY[1:]}' size='8'>Digenerate otomatis pada {now.strftime('%d %B %Y, %H:%M WIB')}</font>",
            ParagraphStyle('HeaderRight', fontName='Helvetica-Bold', fontSize=12,
                           textColor=RL_DARK, alignment=TA_RIGHT)
        ),
    ]]
    header_tbl = Table(header_data, colWidths=[9*cm, 8*cm])
    header_tbl.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(header_tbl)
    story.append(HRFlowable(width="100%", thickness=3, color=RL_GREEN, spaceAfter=10))

    # ---- FILTER INFO ----
    date_min = df_f['tanggal'].min().strftime('%d %b %Y')
    date_max = df_f['tanggal'].max().strftime('%d %b %Y')
    story.append(Paragraph(
        f"Periode Data: <b>{date_min}</b> s.d. <b>{date_max}</b>  |  "
        f"Total Record: <b>{len(df_f):,}</b> transaksi",
        ParagraphStyle('InfoBar', fontName='Helvetica', fontSize=8.5,
                       textColor=RL_DARK, backColor=RL_LIGHT,
                       borderPad=6, borderRadius=4, spaceAfter=12)
    ))

    # ---- KPI SECTION ----
    story.append(Paragraph("RINGKASAN KINERJA UTAMA", section_style))

    kpi_data = [
        [
            Paragraph("Total Transaksi Perjalanan", label_style),
            Paragraph("Total Pendapatan (Rp)", label_style),
            Paragraph("Rata-Rata Tarif per Transaksi", label_style),
            Paragraph("Hari Operasional", label_style),
        ],
        [
            Paragraph(f"{metrics['total_trx']:,}", kpi_style),
            Paragraph(f"Rp {metrics['total_rev']:,.0f}", kpi_style),
            Paragraph(f"Rp {metrics['avg_rev']:,.0f}", kpi_style),
            Paragraph(f"{metrics['active_days']}", kpi_style),
        ],
    ]
    kpi_tbl = Table(kpi_data, colWidths=[4.25*cm]*4)
    kpi_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#e8f4f8")),
        ('BACKGROUND', (0,1), (-1,1), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#ccddee")),
        ('BOX', (0,0), (-1,-1), 1.5, RL_BLUE),
        ('TOPPADDING',    (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING',   (0,0), (-1,-1), 8),
        ('RIGHTPADDING',  (0,0), (-1,-1), 8),
        ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(kpi_tbl)
    story.append(Spacer(1, 0.5*cm))

    # ---- ANALISIS TREN ----
    story.append(HRFlowable(width="100%", thickness=1, color=RL_GREEN, spaceAfter=6))
    story.append(Paragraph("1. ANALISIS TREN VOLUME PERJALANAN HARIAN", section_style))
    story.append(Paragraph(
        _strip_html(interpretations.get('tren', '-')),
        body_style
    ))

    # Grafik tren
    tren_df = df_f.groupby('tanggal').size().reset_index(name='volume')
    story.append(Spacer(1, 0.3*cm))
    story.append(_chart_tren(tren_df))
    story.append(Paragraph(
        "Gambar 1. Tren volume perjalanan harian beserta Moving Average 7 hari.",
        caption_style
    ))

    # Top 5 hari tertinggi
    top5 = tren_df.nlargest(5, 'volume')[['tanggal', 'volume']].copy()
    top5['tanggal'] = top5['tanggal'].dt.strftime('%d %b %Y')
    top5.columns = ['Tanggal', 'Volume Transaksi']

    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph("Top 5 Hari Tersibuk:", label_style))
    tbl_data = [list(top5.columns)] + [[str(v) for v in row] for row in top5.values]
    _add_table(story, tbl_data, RL_BLUE, RL_GREEN, RL_LIGHT)

    # ---- ANALISIS JAM SIBUK ----
    story.append(Spacer(1, 0.3*cm))
    story.append(HRFlowable(width="100%", thickness=1, color=RL_GREEN, spaceAfter=6))
    story.append(Paragraph("2. ANALISIS DISTRIBUSI JAM OPERASIONAL", section_style))
    story.append(Paragraph(
        _strip_html(interpretations.get('rush', '-')),
        body_style
    ))

    # Grafik jam sibuk
    story.append(Spacer(1, 0.3*cm))
    story.append(_chart_rush(df_f))
    story.append(Paragraph(
        "Gambar 2. Distribusi volume transaksi per jam tap-in. Batang hijau menandai jam puncak tertinggi.",
        caption_style
    ))

    rush_df = df_f.groupby('jam_tap_in').size().reset_index(name='volume')
    rush_df = rush_df.sort_values('volume', ascending=False).head(6)
    rush_df['jam_tap_in'] = rush_df['jam_tap_in'].apply(lambda x: f"{int(x):02d}.00")
    rush_df.columns = ['Jam', 'Volume Transaksi']

    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph("Top 6 Jam Terpadat:", label_style))
    tbl_data2 = [list(rush_df.columns)] + [[str(v) for v in row] for row in rush_df.values]
    _add_table(story, tbl_data2, RL_BLUE, RL_GREEN, RL_LIGHT)

    # ---- ANALISIS SEGMEN ----
    story.append(PageBreak())
    story.append(HRFlowable(width="100%", thickness=1, color=RL_GREEN, spaceAfter=6))
    story.append(Paragraph("3. ANALISIS KOMPOSISI SEGMEN PENUMPANG", section_style))
    story.append(Paragraph(
        _strip_html(interpretations.get('segment', '-')),
        body_style
    ))

    # Grafik segmen
    story.append(Spacer(1, 0.3*cm))
    story.append(_chart_segmen(df_f))
    story.append(Paragraph(
        "Gambar 3. Komposisi segmen penumpang — donut chart proporsi (kiri) dan bar persentase (kanan).",
        caption_style
    ))

    demo_df = df_f.groupby('segment_pengguna').size().reset_index(name='total')
    demo_df['persen'] = (demo_df['total'] / demo_df['total'].sum() * 100).round(1)
    demo_df = demo_df.sort_values('total', ascending=False)
    demo_df.columns = ['Segmen', 'Jumlah', 'Persentase (%)']

    story.append(Spacer(1, 0.2*cm))
    tbl_data3 = [list(demo_df.columns)] + [[str(v) for v in row] for row in demo_df.values]
    _add_table(story, tbl_data3, RL_BLUE, RL_GREEN, RL_LIGHT)

    # ---- ANALISIS BANK ----
    story.append(Spacer(1, 0.3*cm))
    story.append(HRFlowable(width="100%", thickness=1, color=RL_GREEN, spaceAfter=6))
    story.append(Paragraph("4. ANALISIS PREFERENSI KARTU BANK", section_style))
    story.append(Paragraph(
        _strip_html(interpretations.get('bank', '-')),
        body_style
    ))

    # Grafik bank
    story.append(Spacer(1, 0.3*cm))
    story.append(_chart_bank(df_f))
    story.append(Paragraph(
        "Gambar 4. Volume transaksi per bank (kiri) dan pangsa pasar relatif (kanan). "
        "Hijau menandai bank dengan penggunaan tertinggi.",
        caption_style
    ))

    bank_df = df_f.groupby('bank_kartu').size().reset_index(name='total')
    bank_df['persen'] = (bank_df['total'] / bank_df['total'].sum() * 100).round(1)
    bank_df = bank_df.sort_values('total', ascending=False)
    bank_df.columns = ['Bank / Kartu', 'Jumlah Transaksi', 'Persentase (%)']

    story.append(Spacer(1, 0.2*cm))
    tbl_data4 = [list(bank_df.columns)] + [[str(v) for v in row] for row in bank_df.values]
    _add_table(story, tbl_data4, RL_BLUE, RL_GREEN, RL_LIGHT)

    # ---- ANALISIS WEEKEND (opsional) ----
    if 'is_weekend' in df_f.columns and df_f['is_weekend'].nunique() > 1:
        story.append(Spacer(1, 0.3*cm))
        story.append(HRFlowable(width="100%", thickness=1, color=RL_GREEN, spaceAfter=6))
        story.append(Paragraph("5. PERBANDINGAN POLA HARI KERJA VS AKHIR PEKAN", section_style))
        wkday_vol = df_f[df_f['is_weekend']==0].shape[0]
        wkend_vol = df_f[df_f['is_weekend']==1].shape[0]
        ratio = wkend_vol / wkday_vol if wkday_vol else 0
        story.append(Paragraph(
            f"Volume hari kerja sebesar <b>{wkday_vol:,}</b> transaksi, sementara akhir pekan "
            f"<b>{wkend_vol:,}</b> transaksi (rasio {ratio:.0%} terhadap hari kerja). "
            f"Grafik berikut menampilkan perbandingan pola per jam untuk kedua kategori hari.",
            body_style
        ))
        story.append(Spacer(1, 0.3*cm))
        wk_img = _chart_weekend(df_f)
        if wk_img:
            story.append(wk_img)
            story.append(Paragraph(
                "Gambar 5. Perbandingan distribusi volume per jam antara hari kerja (biru) dan akhir pekan (hijau).",
                caption_style
            ))

    # ---- REKOMENDASI ----
    story.append(PageBreak())
    story.append(Paragraph("REKOMENDASI STRATEGIS", section_style))
    story.append(HRFlowable(width="100%", thickness=2, color=RL_GREEN, spaceAfter=10))

    recommendations = _build_recommendations(df_f, metrics)
    for i, rec in enumerate(recommendations, 1):
        story.append(Paragraph(
            f"<b>{i}. {rec['title']}</b>",
            ParagraphStyle('RecTitle', fontName='Helvetica-Bold', fontSize=10,
                           textColor=RL_BLUE, spaceBefore=8, spaceAfter=2)
        ))
        story.append(Paragraph(rec['detail'], body_style))

    # ---- FOOTER ----
    story.append(Spacer(1, 1*cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=RL_GRAY, spaceAfter=6))
    story.append(Paragraph(
        f"Laporan ini digenerate secara otomatis oleh JakLingko Analytics Command Center "
        f"pada {now.strftime('%d %B %Y pukul %H:%M WIB')}. "
        f"Seluruh data bersumber dari Data Warehouse JakLingko.",
        footer_style
    ))

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes


def _add_table(story, data, col_blue, col_green, col_light):
    """Render styled table ke story."""
    tbl = Table(data, hAlign='LEFT')
    style = TableStyle([
        ('BACKGROUND',    (0,0), (-1,0), col_blue),
        ('TEXTCOLOR',     (0,0), (-1,0), colors.white),
        ('FONTNAME',      (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE',      (0,0), (-1,0), 8),
        ('FONTNAME',      (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE',      (0,1), (-1,-1), 8),
        ('TEXTCOLOR',     (0,1), (-1,-1), colors.HexColor("#333333")),
        ('BACKGROUND',    (0,1), (-1,-1), colors.white),
        ('ROWBACKGROUNDS',(0,1), (-1,-1), [colors.white, col_light]),
        ('GRID',          (0,0), (-1,-1), 0.4, colors.HexColor("#ccddee")),
        ('BOX',           (0,0), (-1,-1), 1, col_blue),
        ('TOPPADDING',    (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING',   (0,0), (-1,-1), 6),
        ('RIGHTPADDING',  (0,0), (-1,-1), 6),
        ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
    ])
    tbl.setStyle(style)
    story.append(tbl)


def _strip_html(text: str) -> str:
    """Konversi tag HTML ke format ReportLab Paragraph yang aman."""
    import re
    text = re.sub(r'<strong>(.*?)</strong>', r'<b>\1</b>', text)
    return text


def _build_recommendations(df_f, metrics):
    """Build list rekomendasi dinamis berdasarkan data."""
    recs = []

    # Rekomendasi 1: Jam Sibuk
    rush_df = df_f.groupby('jam_tap_in').size().reset_index(name='volume')
    if not rush_df.empty:
        peak_hour = int(rush_df.loc[rush_df['volume'].idxmax(), 'jam_tap_in'])
        recs.append({
            'title': 'Optimasi Armada pada Jam Puncak',
            'detail': (
                f"Data menunjukkan puncak permintaan konsisten terjadi pada pukul {peak_hour:02d}.00. "
                f"Disarankan agar penambahan frekuensi keberangkatan dan penempatan armada cadangan "
                f"diprioritaskan pada rentang jam tersebut untuk meminimalkan waktu tunggu penumpang "
                f"dan mengurangi risiko overcrowding."
            )
        })

    # Rekomendasi 2: Segmen dominan
    seg_df = df_f.groupby('segment_pengguna').size().reset_index(name='total')
    if not seg_df.empty:
        top_seg = seg_df.loc[seg_df['total'].idxmax(), 'segment_pengguna']
        recs.append({
            'title': f'Program Loyalitas untuk Segmen {top_seg}',
            'detail': (
                f"Segmen {top_seg} merupakan kontributor transaksi terbesar. "
                f"Pengembangan program poin reward, tarif bundling bulanan, atau fitur prioritas boarding "
                f"dapat meningkatkan retensi segmen ini sekaligus mendorong peningkatan frekuensi perjalanan."
            )
        })

    # Rekomendasi 3: Bank
    bank_df = df_f.groupby('bank_kartu').size().reset_index(name='total')
    if not bank_df.empty:
        top_bank   = bank_df.loc[bank_df['total'].idxmax(), 'bank_kartu']
        bottom_bank= bank_df.loc[bank_df['total'].idxmin(), 'bank_kartu']
        recs.append({
            'title': 'Kemitraan Strategis Perbankan',
            'detail': (
                f"Dominasi transaksi oleh kartu {top_bank} membuka peluang negosiasi co-branding eksklusif "
                f"(cashback atau diskon tarif). Secara paralel, perlu kampanye edukasi untuk mendorong "
                f"adopsi kartu {bottom_bank} yang saat ini masih rendah penetrasinya."
            )
        })

    # Rekomendasi 4: Weekend vs Weekday
    if 'is_weekend' in df_f.columns:
        wk_df = df_f.groupby('is_weekend').size().reset_index(name='total')
        if len(wk_df) == 2:
            weekend_vol  = wk_df[wk_df['is_weekend']==1]['total'].values[0] if 1 in wk_df['is_weekend'].values else 0
            weekday_vol  = wk_df[wk_df['is_weekend']==0]['total'].values[0] if 0 in wk_df['is_weekend'].values else 1
            ratio = weekend_vol / weekday_vol if weekday_vol else 0
            if ratio < 0.7:
                recs.append({
                    'title': 'Stimulasi Perjalanan Akhir Pekan',
                    'detail': (
                        f"Volume akhir pekan hanya {ratio:.0%} dari hari kerja, menunjukkan potensi pasar "
                        f"yang belum digarap. Program diskon weekend, paket wisata terintegrasi, atau "
                        f"konten promosi berbasis destinasi rekreasi dapat meningkatkan utilisasi armada "
                        f"di luar jam kerja."
                    )
                })

    return recs


# ============================================================
# 6. SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown(f"""
    <div style="padding: 1.2rem 0 1.5rem; border-bottom: 1px solid {C_BLUE}44; margin-bottom: 1rem;">
        <div style="font-family:'Space Grotesk',sans-serif; font-size:0.65rem;
                    font-weight:600; color:{C_GRAY}; letter-spacing:3px;
                    text-transform:uppercase; margin-bottom:4px;">
            TransJakarta
        </div>
        <div style="font-family:'Space Grotesk',sans-serif; font-size:1.25rem;
                    font-weight:700; color:{C_WHITE}; letter-spacing:1px; line-height:1.2;">
            OLAP Dashboard
        </div>
        <div style="font-family:'Space Grotesk',sans-serif; font-size:0.68rem;
                    font-weight:500; color:{C_GREEN}; letter-spacing:1.5px;
                    text-transform:uppercase; margin-top:4px;">
            JakLingko Analytics
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f'<div style="font-family:Space Grotesk; font-weight:700; font-size:0.9rem; color:{C_GREEN}; margin-bottom:0.5rem;">FILTER DATA</div>', unsafe_allow_html=True)

    # --- LOAD DATA ---
    with st.spinner("Memuat data warehouse..."):
        df_raw = load_data()

    koridor_list = ["Semua"] + sorted(df_raw['jenis_koridor'].dropna().unique().tolist())
    segmen_list  = ["Semua"] + sorted(df_raw['segment_pengguna'].dropna().unique().tolist())

    selected_koridor = st.selectbox("Jenis Koridor", koridor_list)
    selected_segmen  = st.selectbox("Segmen Pengguna", segmen_list)

    st.markdown('<hr style="border-color:#0083b333;">', unsafe_allow_html=True)

    # --- REALTIME CONTROL ---
    st.markdown(f'<div style="font-family:Space Grotesk; font-weight:700; font-size:0.9rem; color:{C_GREEN}; margin-bottom:0.5rem;">MONITORING REALTIME</div>', unsafe_allow_html=True)
    auto_refresh    = st.toggle("Aktifkan Auto-Refresh", value=True)
    refresh_interval= st.slider("Interval Refresh (detik)", 15, 300, 60, step=15,
                                disabled=not auto_refresh)

    if auto_refresh:
        st.markdown(f"""
        <div class="status-live">
            <div class="status-dot"></div> LIVE
        </div>
        <div style="font-size:0.7rem; color:{C_GRAY}; margin-top:4px;">
            Refresh setiap {refresh_interval}s
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f'<div style="font-size:0.7rem; color:{C_GRAY};">Mode statis - data tidak diperbarui otomatis</div>', unsafe_allow_html=True)

    st.markdown('<hr style="border-color:#0083b333;">', unsafe_allow_html=True)
    st.markdown(f'<div style="font-size:0.7rem; color:{C_GRAY}; margin-bottom:0.3rem;">Terakhir dimuat:</div>', unsafe_allow_html=True)
    st.markdown(f'<div style="font-size:0.8rem; color:{C_WHITE}; font-weight:600;">{datetime.now().strftime("%d %b %Y, %H:%M:%S")}</div>', unsafe_allow_html=True)

# ============================================================
# 7. FILTER DATA
# ============================================================
df_filtered = df_raw.copy()
if selected_koridor != "Semua":
    df_filtered = df_filtered[df_filtered['jenis_koridor'] == selected_koridor]
if selected_segmen != "Semua":
    df_filtered = df_filtered[df_filtered['segment_pengguna'] == selected_segmen]

# ============================================================
# 8. HEADER UTAMA
# ============================================================
st.markdown(f"""
<div class="dash-header">
    <div style="display:flex; justify-content:space-between; align-items:flex-start;">
        <div>
            <h1>ANALYTICS COMMAND CENTER</h1>
            <p>TransJakarta JakLingko &mdash; Data Warehouse Intelligence Platform</p>
        </div>
        <div class="status-live" style="margin-top:0.3rem;">
            <div class="status-dot"></div> LIVE DATA
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ============================================================
# 9. KPI METRICS
# ============================================================
total_trx   = len(df_filtered)
total_rev   = df_filtered['total_bayar'].sum()
avg_rev     = total_rev / total_trx if total_trx > 0 else 0
active_days = df_filtered['tanggal'].nunique()
peak_hour   = (df_filtered.groupby('jam_tap_in').size().idxmax()
               if not df_filtered.empty else 0)

metrics_dict = {
    'total_trx'  : total_trx,
    'total_rev'  : total_rev,
    'avg_rev'    : avg_rev,
    'active_days': active_days,
}

col1, col2, col3, col4 = st.columns(4)
kpi_items = [
    (col1, "TOTAL TRANSAKSI",    f"{total_trx:,}",           "Seluruh perjalanan tercatat"),
    (col2, "TOTAL PENDAPATAN",   f"Rp {total_rev:,.0f}",     "Kumulatif seluruh tarif"),
    (col3, "RATA-RATA TARIF",    f"Rp {avg_rev:,.0f}",       "Per transaksi perjalanan"),
    (col4, "HARI OPERASIONAL",   f"{active_days}",            "Hari dengan aktivitas transaksi"),
]
for col, label, value, sub in kpi_items:
    with col:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-delta">{sub}</div>
        </div>
        """, unsafe_allow_html=True)

# ============================================================
# 10. VISUALISASI
# ============================================================

# --- CHART 1: TREN HARIAN ---
st.markdown('<div class="section-header">TREN VOLUME PERJALANAN HARIAN</div>', unsafe_allow_html=True)

tren_df = df_filtered.groupby('tanggal').size().reset_index(name='volume')

fig_tren = go.Figure()
# Area fill
fig_tren.add_trace(go.Scatter(
    x=tren_df['tanggal'], y=tren_df['volume'],
    fill='tozeroy',
    fillcolor=f"rgba(0,131,179,0.15)",
    line=dict(color=C_BLUE, width=2.5),
    mode='lines+markers',
    marker=dict(size=4, color=C_GREEN, line=dict(color=C_BLUE, width=1)),
    hovertemplate='%{x|%d %b %Y}<br>Volume: <b>%{y:,}</b><extra></extra>',
    name='Volume'
))
# Trendline MA7
if len(tren_df) >= 7:
    tren_df['ma7'] = tren_df['volume'].rolling(7).mean()
    fig_tren.add_trace(go.Scatter(
        x=tren_df['tanggal'], y=tren_df['ma7'],
        line=dict(color=C_GREEN, width=2, dash='dot'),
        mode='lines', name='MA 7 Hari',
        hovertemplate='MA7: <b>%{y:.0f}</b><extra></extra>',
    ))

fig_tren.update_layout(**layout(
    height=300,
    legend=dict(bgcolor='rgba(0,0,0,0)', font=dict(color=C_WHITE), orientation='h', y=1.08, x=0),
))
st.plotly_chart(fig_tren, use_container_width=True)

interp_tren = interpret_trend(tren_df)
st.markdown(f"""
<div class="interp-box">
    <div class="interp-title">Interpretasi Analitik</div>
    <div class="interp-text">{interp_tren}</div>
</div>
""", unsafe_allow_html=True)

# --- CHART 2 & 3: SEGMEN + JAM SIBUK ---
st.markdown('<div class="section-header">DEMOGRAFI PENUMPANG & POLA JAM OPERASIONAL</div>', unsafe_allow_html=True)
col_a, col_b = st.columns(2, gap="medium")

with col_a:
    demo_df = df_filtered.groupby('segment_pengguna').size().reset_index(name='total')
    fig_demo = px.pie(
        demo_df, values='total', names='segment_pengguna', hole=0.5,
        color_discrete_sequence=PLOTLY_COLORS,
    )
    fig_demo.update_traces(
        textfont_color=C_WHITE,
        hovertemplate='<b>%{label}</b><br>%{value:,} transaksi (%{percent})<extra></extra>'
    )
    fig_demo.update_layout(**layout(
        height=300,
        annotations=[dict(text='SEGMEN', x=0.5, y=0.5, font_size=12, font_color=C_GRAY, showarrow=False)],
    ))
    st.plotly_chart(fig_demo, use_container_width=True)
    interp_seg = interpret_segment(demo_df)
    st.markdown(f'<div class="interp-box"><div class="interp-title">Interpretasi</div><div class="interp-text">{interp_seg}</div></div>', unsafe_allow_html=True)

with col_b:
    rush_df = df_filtered.groupby('jam_tap_in').size().reset_index(name='volume')
    rush_df  = rush_df.sort_values('jam_tap_in')
    colors_bar = [C_GREEN if v == rush_df['volume'].max() else C_BLUE for v in rush_df['volume']]

    fig_rush = go.Figure(go.Bar(
        x=rush_df['jam_tap_in'], y=rush_df['volume'],
        marker_color=colors_bar,
        hovertemplate='Pukul %{x}:00<br>Volume: <b>%{y:,}</b><extra></extra>',
    ))
    fig_rush.update_layout(**layout(
        height=300,
        xaxis=dict(tickmode='linear', tick0=0, dtick=2,
                   tickformat='%02d:00', gridcolor="rgba(0,131,179,0.2)"),
        yaxis=dict(gridcolor="rgba(0,131,179,0.2)"),
        bargap=0.25,
    ))
    st.plotly_chart(fig_rush, use_container_width=True)
    interp_rush = interpret_rush_hour(rush_df)
    st.markdown(f'<div class="interp-box"><div class="interp-title">Interpretasi</div><div class="interp-text">{interp_rush}</div></div>', unsafe_allow_html=True)

# --- CHART 4: BANK ---
st.markdown('<div class="section-header">PREFERENSI PEMBAYARAN KARTU BANK</div>', unsafe_allow_html=True)

bank_df = (df_filtered.groupby('bank_kartu').size()
           .reset_index(name='total').sort_values('total', ascending=True))
fig_bank = go.Figure(go.Bar(
    x=bank_df['total'], y=bank_df['bank_kartu'],
    orientation='h',
    marker=dict(
        color=bank_df['total'],
        colorscale=[[0, C_BLUE], [0.5, "#00a8e8"], [1, C_GREEN]],
        showscale=False,
    ),
    text=[f"  {v:,}" for v in bank_df['total']],
    textposition='outside',
    textfont=dict(color=C_WHITE, size=11),
    hovertemplate='<b>%{y}</b><br>%{x:,} transaksi<extra></extra>',
))
fig_bank.update_layout(**layout(
    height=max(250, len(bank_df)*45),
    xaxis=dict(visible=False),
))
st.plotly_chart(fig_bank, use_container_width=True)

interp_bank = interpret_bank(bank_df)
st.markdown(f'<div class="interp-box"><div class="interp-title">Interpretasi</div><div class="interp-text">{interp_bank}</div></div>', unsafe_allow_html=True)

# --- CHART 5: WEEKEND VS WEEKDAY ---
if 'is_weekend' in df_filtered.columns:
    st.markdown('<div class="section-header">POLA HARI KERJA VS AKHIR PEKAN</div>', unsafe_allow_html=True)
    wk_df = df_filtered.groupby(['is_weekend', 'jam_tap_in']).size().reset_index(name='volume')
    wk_df['kategori'] = wk_df['is_weekend'].map({0: 'Hari Kerja', 1: 'Akhir Pekan'})

    fig_wk = px.line(
        wk_df, x='jam_tap_in', y='volume', color='kategori',
        color_discrete_map={'Hari Kerja': C_BLUE, 'Akhir Pekan': C_GREEN},
        markers=True,
    )
    fig_wk.update_traces(line_width=2.5, marker_size=5)
    fig_wk.update_layout(**layout(
        height=280,
        xaxis=dict(title='Jam', tickmode='linear', dtick=2),
        yaxis=dict(title='Volume'),
        legend=dict(bgcolor='rgba(0,0,0,0)', font=dict(color=C_WHITE), orientation='h', y=1.1, x=0),
    ))
    st.plotly_chart(fig_wk, use_container_width=True)

# ============================================================
# 11. GENERATE & UNDUH PDF
# ============================================================
st.markdown('<hr style="border-color:#0083b333; margin: 2rem 0 1rem;">', unsafe_allow_html=True)
st.markdown('<div class="section-header">EKSPOR LAPORAN</div>', unsafe_allow_html=True)

col_pdf1, col_pdf2, col_pdf3 = st.columns([2, 1, 1])
with col_pdf1:
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #0f3555, #0a2940);
                border: 1px solid {C_GREEN}44; border-radius: 10px; padding: 1rem 1.4rem;">
        <div style="font-size:0.8rem; font-weight:600; color:{C_GREEN}; margin-bottom:0.4rem;">
            UNDUH LAPORAN PDF EKSEKUTIF
        </div>
        <div style="font-size:0.78rem; color:#c5dde8; line-height:1.55;">
            Laporan akan memuat ringkasan KPI, tabel data, analisis tren, distribusi jam,
            komposisi segmen, preferensi bank, dan rekomendasi strategis berbasis data aktual.
        </div>
    </div>
    """, unsafe_allow_html=True)

with col_pdf2:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Generate PDF", type="primary", use_container_width=True):
        with st.spinner("Menyusun laporan PDF..."):
            interpretations = {
                'tren'   : interp_tren,
                'rush'   : interp_rush,
                'segment': interp_seg,
                'bank'   : interp_bank,
            }
            pdf_bytes = generate_pdf_report(df_filtered, metrics_dict, interpretations)
            st.session_state['pdf_bytes'] = pdf_bytes
            st.session_state['pdf_ready'] = True
        st.success("Laporan siap diunduh.")

with col_pdf3:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.session_state.get('pdf_ready'):
        filename = f"laporan_jaklingko_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
        st.download_button(
            label="Unduh PDF",
            data=st.session_state['pdf_bytes'],
            file_name=filename,
            mime="application/pdf",
            use_container_width=True,
        )

# ============================================================
# 12. AUTO REFRESH
# ============================================================
if auto_refresh:
    time.sleep(refresh_interval)
    st.cache_data.clear()
    st.rerun()

# Footer
st.markdown('<hr style="border-color:#0083b333; margin-top:2rem;">', unsafe_allow_html=True)
st.markdown(f"""
<div style="text-align:center; font-size:0.72rem; color:{C_GRAY}; padding-bottom: 1rem;">
    JakLingko Analytics Command Center &mdash; Dibangun menggunakan Python, Streamlit, Plotly, dan ReportLab
    &nbsp;|&nbsp; Arsitektur Data Warehouse UTS
</div>
""", unsafe_allow_html=True)
