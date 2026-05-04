"""
============================================================
 JAKLINGKO INTERACTIVE DASHBOARD - ENHANCED VERSION
 FILE  : dashboard_app.py
 DESC  : Dashboard interaktif dengan fitur:
         - Real-time monitoring (auto-refresh)
         - Interpretasi otomatis berbasis data
         - Generate & unduh laporan PDF
         - Palet warna brand JakLingko
 STACK : Streamlit + Plotly + ReportLab (CSV Based)
============================================================
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time
import io
import random
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
    HRFlowable, Image as RLImage, PageBreak
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY


# ============================================================
# BRAND COLORS & CONSTANTS
# ============================================================
C_GREEN  = "#b0de38"   # Lime green - accent utama
C_BLUE   = "#0083b3"   # Ocean blue - warna primer
C_WHITE  = "#FFFFFF"   # Putih
C_DARK   = "#0a2940"   # Dark navy - teks utama
C_LIGHT  = "#e8f4f8"   # Light blue tint - background card
C_GRAY   = "#1f3e55"   # Abu-abu medium - teks sekunder
C_GREEN2 = "#8cb82e"   # Green gelap untuk kontras

PLOTLY_COLORS = [C_BLUE, C_GREEN, "#00a8e8", "#7ec832", "#004d6e", "#d4f56a"]


# ============================================================
# 1. KONFIGURASI HALAMAN
# ============================================================
st.set_page_config(
    page_title="JakLingko Analytics Command Center",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown(f"""
<style>
    /* ---- IMPORT FONT ---- */
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@300;400;500;600;700&display=swap');

    /* ---- GLOBAL ---- */
    html, body, [class*="css"] {{
        font-family: 'Inter', 'DM Sans', sans-serif;
        background-color: {C_DARK};
        color: {C_WHITE};
    }}
    .main {{
        background-color: {C_DARK};
        background: linear-gradient(180deg, {C_DARK} 0%, #050f1a 50%, {C_DARK} 100%);
    }}
    .block-container {{
        padding: 2rem 2.5rem 3rem 2.5rem;
        max-width: 1500px;
        margin: 0 auto;
    }}

    /* ---- HEADER ---- */
    .dash-header {{
        background: linear-gradient(135deg, {C_BLUE}dd 0%, #004580 50%, {C_DARK} 100%);
        border-radius: 20px;
        padding: 2.5rem 3rem;
        margin-bottom: 2rem;
        border-left: 6px solid {C_GREEN};
        position: relative;
        overflow: hidden;
        box-shadow: 0 12px 40px rgba(0, 131, 179, 0.15);
        backdrop-filter: blur(10px);
    }}
    .dash-header::before {{
        content: '';
        position: absolute;
        top: -60px; right: -60px;
        width: 300px; height: 300px;
        background: radial-gradient(circle, {C_GREEN}44 0%, transparent 70%);
    }}
    .dash-header h1 {{
        font-family: 'Space Grotesk', sans-serif;
        font-size: 2.2rem;
        font-weight: 700;
        color: {C_WHITE};
        margin: 0;
        letter-spacing: -1px;
        text-transform: uppercase;
    }}
    .dash-header p {{
        color: {C_GREEN};
        font-size: 0.9rem;
        font-weight: 500;
        margin: 0.6rem 0 0 0;
        letter-spacing: 1px;
        text-transform: uppercase;
    }}

    /* ---- KPI CARDS ---- */
    .kpi-card {{
        background: linear-gradient(145deg, #0f3555 0%, #0a2940 100%);
        border: 1px solid {C_BLUE}44;
        border-radius: 12px;
        padding: 1.2rem 1rem;
        position: relative;
        overflow: hidden;
        transition: transform 0.2s, box-shadow 0.2s;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
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
        font-size: clamp(1.2rem, 1.8vw, 1.8rem);
        font-weight: 700;
        color: {C_WHITE};
        line-height: 1.2;
        letter-spacing: -0.5px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }}
    .kpi-delta {{
        font-size: 0.78rem;
        margin-top: 0.5rem;
        color: {C_GREEN};
        font-weight: 500;
        opacity: 0.9;
    }}

    /* ---- SECTION HEADERS ---- */
    .section-header {{
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1.1rem;
        font-weight: 700;
        color: {C_DARK};
        text-transform: uppercase;
        letter-spacing: 2px;
        border-left: 4px solid {C_GREEN};
        padding-left: 1rem;
        margin: 2.5rem 0 1.5rem 0;
        position: relative;
    }}
    .section-header::after {{
        content: '';
        position: absolute;
        bottom: -8px;
        left: 0;
        width: 60px;
        height: 2px;
        background: linear-gradient(90deg, {C_GREEN}, transparent);
    }}

    /* ---- CHART CONTAINER ---- */
    [data-testid="stPlotlyChart"] {{
        background: #ffffff;
        border: 1px solid #e8f4f8;
        border-radius: 16px;
        padding: 1.2rem !important;
        margin-top: 0.8rem;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
        transition: all 0.3s ease;
        overflow: hidden !important; 
    }}
    [data-testid="stPlotlyChart"]:hover {{
        border-color: {C_BLUE}88;
        box-shadow: 0 8px 25px rgba(0, 131, 179, 0.15);
    }}
    [data-testid="stPlotlyChart"] iframe {{
        overflow: hidden !important; 
    }}

    /* ---- INTERPRETATION BOX ---- */
    .interp-box {{
        background: linear-gradient(135deg, #0a3a52 0%, #06202f 100%);
        border: 1.2px solid {C_GREEN}66;
        border-left: 4px solid {C_GREEN};
        border-radius: 12px;
        padding: 1.3rem 1.6rem;
        margin-top: 1rem;
        height: auto;
        min-height: 120px;
        box-shadow: 0 8px 24px rgba(176, 222, 56, 0.08);
        transition: all 0.3s ease;
    }}
    .interp-box:hover {{
        box-shadow: 0 12px 32px rgba(176, 222, 56, 0.12);
        border-color: {C_GREEN}88;
    }}
    .interp-title {{
        font-size: 0.75rem;
        font-weight: 700;
        color: {C_GREEN};
        text-transform: uppercase;
        letter-spacing: 1.2px;
        margin-bottom: 0.7rem;
    }}
    .interp-text {{
        font-size: 0.87rem;
        color: #d5e8f2;
        line-height: 1.7;
        font-weight: 400;
    }}
    .interp-text strong {{
        color: {C_WHITE};
        font-weight: 600;
    }}

    /* ---- SIDEBAR ---- */
    [data-testid="stSidebar"] {{
        background: linear-gradient(180deg, #07202e 0%, #051820 100%);
        border-right: 1px solid {C_BLUE}44;
    }}
    [data-testid="stSidebar"] .stSelectbox label,
    [data-testid="stSidebar"] .stSlider label,
    [data-testid="stSidebar"] .stCheckbox label {{
        color: {C_WHITE} !important;
        font-size: 0.85rem;
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
        gap: 8px;
        background: {C_GREEN}22;
        border: 1.5px solid {C_GREEN}88;
        border-radius: 25px;
        padding: 5px 14px;
        font-size: 0.72rem;
        font-weight: 700;
        color: {C_GREEN};
        text-transform: uppercase;
        letter-spacing: 0.8px;
    }}
    .status-dot {{
        width: 8px; height: 8px;
        background: {C_GREEN};
        border-radius: 50%;
        animation: pulse 1.5s ease-in-out infinite;
    }}
    @keyframes pulse {{
        0%, 100% {{ opacity: 1; transform: scale(1); }}
        50% {{ opacity: 0.4; transform: scale(0.85); }}
    }}

    /* ---- STREAMLIT OVERRIDES ---- */
    .stMetric {{ display: none; }}
    div[data-testid="stHorizontalBlock"] > div {{ padding: 0 0.4rem; }}
    button[kind="primary"] {{
        background: linear-gradient(135deg, {C_GREEN} 0%, {C_GREEN2} 100%) !important;
        color: {C_DARK} !important;
        font-weight: 700 !important;
        border: none !important;
        border-radius: 10px !important;
        box-shadow: 0 8px 20px rgba(176, 222, 56, 0.2) !important;
    }}
    .stDownloadButton button {{
        background: linear-gradient(135deg, {C_GREEN} 0%, {C_GREEN2} 100%) !important;
        color: {C_DARK} !important;
        font-weight: 700 !important;
        border: none !important;
        border-radius: 10px !important;
        width: 100%;
        padding: 0.7rem;
        font-size: 0.9rem;
    }}
    h1, h2, h3, h4 {{ color: {C_WHITE} !important; }}
</style>
""", unsafe_allow_html=True)


# ============================================================
# 2. DATA LOADING (Membaca file jaklingko_dwh.csv)
# ============================================================
def generate_mock_data():
    """Fungsi cadangan untuk menghasilkan data simulasi jika CSV salah/tidak ada"""
    from datetime import timedelta
    data = []
    base_date = datetime(2024, 4, 1)
    segments, seg_weights = ['Pekerja', 'Pelajar', 'Mahasiswa', 'Lansia'], [0.65, 0.15, 0.15, 0.05]
    genders = ['Pria', 'Wanita']
    banks, bank_weights = ['Bank DKI', 'BCA', 'Mandiri', 'BNI', 'BRI'], [0.4, 0.25, 0.15, 0.1, 0.1]
    corridors = ['Koridor 1', 'Koridor 2', 'Koridor 3', 'Koridor 4', 'Koridor 5']
    
    for i in range(2500):
        date_val = base_date + timedelta(days=random.randint(0, 30))
        is_wknd = 1 if date_val.weekday() >= 5 else 0
        jam = random.choices(range(6, 22), weights=[1]*16, k=1)[0] if is_wknd else random.choices(range(5, 23), weights=[1,5,8,7,4,2,2,2,2,2,3,6,8,5,2,1,1,1], k=1)[0]
        data.append({
            'tanggal': date_val, 'nama_hari': date_val.strftime('%A'), 'is_weekend': is_wknd,
            'jam_tap_in': jam, 'total_bayar': random.choice([3500, 3500, 3500, 0, 10000]),
            'transaksi_id': f"TRX{i:05d}", 'segment_pengguna': random.choices(segments, weights=seg_weights, k=1)[0],
            'gender': random.choice(genders), 'bank_kartu': random.choices(banks, weights=bank_weights, k=1)[0],
            'jenis_koridor': random.choice(corridors)
        })
    return pd.DataFrame(data)

@st.cache_data(ttl=60)   # Cache 60 detik untuk simulasi auto-refresh
def load_data():
    try:
        # Membaca data dengan auto-detect delimiter
        df = pd.read_csv("jaklingko_dwh.csv", sep=None, engine='python')
        df.columns = df.columns.str.strip().str.lower()
        
        # Validasi apakah kolom yang diekspor sudah benar hasil JOIN
        req_cols = ['tanggal', 'jam_tap_in', 'total_bayar', 'segment_pengguna']
        if not all(col in df.columns for col in req_cols):
            st.warning("File CSV terbaca, tetapi ini sepertinya tabel dimensi (bukan hasil JOIN seluruh data). Sistem otomatis beralih menggunakan Data Simulasi agar dashboard tetap dapat dipresentasikan.")
            return generate_mock_data()
        
        # Jika CSV benar, proses secara normal
        df['tanggal']    = pd.to_datetime(df['tanggal'])
        df['jam_tap_in'] = pd.to_numeric(df['jam_tap_in'], errors='coerce')
        df['total_bayar']= pd.to_numeric(df['total_bayar'], errors='coerce')
        
        # Bersihkan string dari spasi ekstra (jika ada dari hasil ekspor DB)
        cols_to_strip = ['nama_hari', 'segment_pengguna', 'gender', 'bank_kartu', 'jenis_koridor']
        for col in cols_to_strip:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()
                
        # Penyesuaian bahasa untuk kolom gender agar tampil rapi di grafik
        if 'gender' in df.columns:
            df['gender'] = df['gender'].replace({'M': 'Pria', 'F': 'Wanita', 'L': 'Pria', 'P': 'Wanita'})
                
        return df
    except FileNotFoundError:
        st.warning("File 'jaklingko_dwh.csv' tidak ditemukan di repositori GitHub. Sistem otomatis beralih menggunakan Data Simulasi agar dashboard tetap berjalan.")
        return generate_mock_data()


# ============================================================
# 3. HELPER: PLOTLY THEME
# ============================================================
PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor ="rgba(0,0,0,0)",
    font         =dict(family="DM Sans", color=C_DARK, size=12),  
    title_font   =dict(family="Space Grotesk", color=C_DARK, size=14),
    xaxis        =dict(gridcolor="#e8f4f8", zeroline=False, tickfont=dict(size=11)),
    yaxis        =dict(gridcolor="#e8f4f8", zeroline=False, tickfont=dict(size=11)),
    margin       =dict(l=15, r=15, t=50, b=40), 
    colorway     =PLOTLY_COLORS,
    hoverlabel   =dict(bgcolor=C_WHITE, font_color=C_DARK, bordercolor=C_BLUE),
)

_LEGEND_DEFAULT = dict(bgcolor="rgba(255,255,255,0.7)", font=dict(color=C_DARK))

def layout(**overrides):
    base = {**PLOTLY_LAYOUT, "legend": _LEGEND_DEFAULT}
    base.update(overrides)
    return base


# ============================================================
# 4. HELPER: INTERPRETASI & FORMATTING OTOMATIS
# ============================================================
def format_metric(val):
    if pd.isna(val): return "Rp 0"
    if val >= 1e9: return f"Rp {val/1e9:.2f} Miliar"
    elif val >= 1e6: return f"Rp {val/1e6:.2f} Juta"
    else: return f"Rp {val:,.0f}"

def interpret_trend(tren_df):
    if len(tren_df) < 3: return "Data tren belum cukup untuk dianalisis."
    recent_7  = tren_df.tail(7)['volume'].mean()
    before_7  = tren_df.iloc[-14:-7]['volume'].mean() if len(tren_df) >= 14 else tren_df.head(7)['volume'].mean()
    delta_pct = ((recent_7 - before_7) / before_7 * 100) if before_7 > 0 else 0
    peak_day  = tren_df.loc[tren_df['volume'].idxmax(), 'tanggal'].strftime('%d %b %Y')
    peak_vol  = int(tren_df['volume'].max())

    if delta_pct >= 5: trend_text = f"tumbuh positif sebesar <strong>{delta_pct:.1f}%</strong> dibandingkan 7 hari sebelumnya"
    elif delta_pct <= -5: trend_text = f"mengalami penurunan <strong>{abs(delta_pct):.1f}%</strong> dibandingkan 7 hari sebelumnya"
    else: trend_text = "relatif stabil tanpa fluktuasi signifikan"

    return (f"Volume perjalanan harian {trend_text}. Puncak aktivitas tertinggi terjadi pada <strong>{peak_day}</strong> "
            f"dengan <strong>{peak_vol:,} transaksi</strong>. Rata-rata 7 hari terakhir: <strong>{recent_7:.0f} transaksi/hari</strong>.")

def interpret_rush_hour(rush_df):
    if rush_df.empty: return "Data jam tidak tersedia."
    top3     = rush_df.nlargest(3, 'volume')['jam_tap_in'].tolist()
    morning  = rush_df[rush_df['jam_tap_in'].between(6, 9)]['volume'].sum()
    evening  = rush_df[rush_df['jam_tap_in'].between(16, 19)]['volume'].sum()
    dominant = "pagi" if morning >= evening else "sore"
    top3_str = ", ".join([f"pukul {int(h):02d}.00" for h in top3])

    return (f"Pola distribusi jam menunjukkan jam sibuk dominan pada <strong>{top3_str}</strong>. "
            f"Lonjakan utama terjadi di periode <strong>{dominant} hari</strong>, "
            f"sehingga penambahan armada di jam tersebut akan berdampak signifikan terhadap kepuasan penumpang.")

def interpret_segment(demo_df):
    if demo_df.empty: return "Data segmen tidak tersedia."
    total    = demo_df['total'].sum()
    top_seg  = demo_df.loc[demo_df['total'].idxmax()]
    top_pct  = top_seg['total'] / total * 100
    n_seg    = len(demo_df)

    if top_pct > 60: concentration = f"terkonsentrasi kuat pada segmen <strong>{top_seg['segment_pengguna']}</strong> ({top_pct:.1f}%)"
    elif top_pct > 40: concentration = f"didominasi oleh segmen <strong>{top_seg['segment_pengguna']}</strong> ({top_pct:.1f}%)"
    else: concentration = f"tersebar merata di antara <strong>{n_seg} segmen</strong>"

    return (f"Basis penumpang {concentration}. Program loyalitas dan tarif diferensiasi dapat dioptimalkan berdasarkan "
            f"proporsi segmen ini untuk meningkatkan retensi dan daya beli.")

def interpret_bank(bank_df):
    if bank_df.empty: return "Data kartu tidak tersedia."
    total   = bank_df['total'].sum()
    top_bank = bank_df.loc[bank_df['total'].idxmax()]
    top_pct  = top_bank['total'] / total * 100
    bottom   = bank_df.loc[bank_df['total'].idxmin()]['bank_kartu']

    return (f"<strong>{top_bank['bank_kartu']}</strong> mendominasi penggunaan kartu dengan pangsa <strong>{top_pct:.1f}%</strong>. "
            f"Kerjasama co-branding berpotensi meningkatkan loyalitas. Sebaliknya, adopsi kartu <strong>{bottom}</strong> "
            f"masih rendah dan perlu strategi edukasi.")

def interpret_corridor(corridor_df):
    if corridor_df.empty: return "Data koridor tidak tersedia."
    top_corridor = corridor_df.loc[corridor_df['total'].idxmax()]
    top_pct = top_corridor['total'] / corridor_df['total'].sum() * 100
    return (f"Koridor <strong>{top_corridor['jenis_koridor']}</strong> merupakan jalur terpadat "
            f"dengan proporsi <strong>{top_pct:.1f}%</strong> dari total perjalanan. "
            f"Fokus operasional dan penambahan armada sebaiknya diprioritaskan pada koridor ini.")

def interpret_gender(gender_df):
    if gender_df.empty: return "Data gender tidak tersedia."
    top_gender = gender_df.loc[gender_df['total'].idxmax()]
    top_pct = top_gender['total'] / gender_df['total'].sum() * 100
    return (f"Profil penumpang didominasi oleh kelompok <strong>{top_gender['gender']}</strong> "
            f"({top_pct:.1f}%). Insight ini sangat berguna untuk menyesuaikan kampanye pemasaran.")

def interpret_weekend(wk_df):
    if wk_df.empty: return "Data akhir pekan tidak tersedia."
    weekday_vol = wk_df[wk_df['is_weekend'] == 0]['volume'].sum()
    weekend_vol = wk_df[wk_df['is_weekend'] == 1]['volume'].sum()
    total = weekday_vol + weekend_vol
    
    if total == 0: return "Tidak ada transaksi tercatat."
    wd_pct = weekday_vol / total * 100
    we_pct = weekend_vol / total * 100
    
    if wd_pct > we_pct: dominance = f"didominasi aktivitas <strong>Hari Kerja ({wd_pct:.1f}%)</strong>"
    else: dominance = f"didominasi aktivitas <strong>Akhir Pekan ({we_pct:.1f}%)</strong>"
        
    return (f"Pola transaksi secara keseluruhan {dominance}. Perbedaan ini mencerminkan kepadatan komuter "
            f"di hari kerja (puncak tajam), sementara akhir pekan lebih merata sepanjang siang.")


# ============================================================
# 5A. MATPLOTLIB CHARTS UNTUK PDF
# ============================================================
MPL_BLUE  = (0/255, 131/255, 179/255)
MPL_GREEN = (176/255, 222/255, 56/255)

def _mpl_style(ax, fig):
    fig.patch.set_facecolor("white")
    ax.set_facecolor("#f5fafc")
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color("#ccddee")
    ax.spines['bottom'].set_color("#ccddee")
    ax.tick_params(colors="#444444", labelsize=8)
    ax.grid(axis='y', color="#ccddee", linewidth=0.6, linestyle='--')
    ax.set_axisbelow(True)

def _fig_to_rl_image(fig, width_cm=17, height_cm=7):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    buf.seek(0)
    return RLImage(buf, width=width_cm * cm, height=height_cm * cm)

def _chart_tren(tren_df) -> RLImage:
    fig, ax = plt.subplots(figsize=(10, 3.8))
    _mpl_style(ax, fig)
    ax.fill_between(tren_df['tanggal'], tren_df['volume'], alpha=0.15, color=MPL_BLUE)
    ax.plot(tren_df['tanggal'], tren_df['volume'], color=MPL_BLUE, linewidth=2, label='Volume')
    ax.scatter(tren_df['tanggal'], tren_df['volume'], color=MPL_GREEN, s=20)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{int(x):,}"))
    fig.autofmt_xdate(rotation=30)
    fig.tight_layout()
    return _fig_to_rl_image(fig, width_cm=17, height_cm=5)

def _chart_rush(df_f) -> RLImage:
    rush = df_f.groupby('jam_tap_in').size().reset_index(name='volume').sort_values('jam_tap_in')
    fig, ax = plt.subplots(figsize=(10, 3.5))
    _mpl_style(ax, fig)
    bar_colors = [MPL_GREEN if v == rush['volume'].max() else MPL_BLUE for v in rush['volume']]
    ax.bar(rush['jam_tap_in'].astype(int), rush['volume'], color=bar_colors, width=0.7)
    ax.set_xticks(rush['jam_tap_in'].astype(int))
    ax.set_xticklabels([f"{int(h):02d}:00" for h in rush['jam_tap_in']], rotation=45, fontsize=7.5)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{int(x):,}"))
    fig.tight_layout()
    return _fig_to_rl_image(fig, width_cm=17, height_cm=5)

def _chart_segmen(df_f) -> RLImage:
    seg = df_f.groupby('segment_pengguna').size().reset_index(name='total').sort_values('total', ascending=False)
    seg['pct'] = seg['total'] / seg['total'].sum() * 100
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
    fig.patch.set_facecolor("white")
    palette = [MPL_BLUE, MPL_GREEN, (0/255,168/255,232/255), (126/255,200/255,50/255), (0/255,77/255,110/255)]
    ax1.pie(seg['total'], labels=seg['segment_pengguna'], colors=palette, autopct='%1.1f%%', startangle=90, wedgeprops=dict(width=0.5, edgecolor='white'))
    _mpl_style(ax2, fig)
    bars = ax2.barh(seg['segment_pengguna'], seg['pct'], color=palette, height=0.55)
    for bar, pct in zip(bars, seg['pct']): ax2.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height()/2, f"{pct:.1f}%", va='center', fontsize=8)
    ax2.invert_yaxis()
    fig.tight_layout()
    return _fig_to_rl_image(fig, width_cm=17, height_cm=5.5)

def _chart_bank(df_f) -> RLImage:
    bank = df_f.groupby('bank_kartu').size().reset_index(name='total').sort_values('total', ascending=True)
    n = len(bank)
    fig, ax1 = plt.subplots(figsize=(10, max(3.5, n*0.5)))
    fig.patch.set_facecolor("white")
    _mpl_style(ax1, fig)
    bars = ax1.barh(bank['bank_kartu'], bank['total'], color=MPL_BLUE, height=0.6)
    for bar, v in zip(bars, bank['total']): ax1.text(bar.get_width() + bank['total'].max()*0.01, bar.get_y() + bar.get_height()/2, f"{v:,}", va='center', fontsize=8)
    ax1.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{int(x):,}"))
    fig.tight_layout()
    return _fig_to_rl_image(fig, width_cm=15, height_cm=max(4, n*0.6))

def _chart_corridor(df_f) -> RLImage:
    corridor = df_f.groupby('jenis_koridor').size().reset_index(name='total').sort_values('total', ascending=True)
    fig, ax = plt.subplots(figsize=(10, max(3.5, len(corridor)*0.5)))
    fig.patch.set_facecolor("white")
    _mpl_style(ax, fig)
    bars = ax.barh(corridor['jenis_koridor'], corridor['total'], color=MPL_BLUE, height=0.6)
    for bar, v in zip(bars, corridor['total']): 
        ax.text(bar.get_width() + corridor['total'].max()*0.01, bar.get_y() + bar.get_height()/2, f"{v:,}", va='center', fontsize=8)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{int(x):,}"))
    fig.tight_layout()
    return _fig_to_rl_image(fig, width_cm=15, height_cm=max(4.5, len(corridor)*0.6))

def _chart_gender(df_f) -> RLImage:
    if 'gender' not in df_f.columns: return None
    gender = df_f.groupby('gender').size().reset_index(name='total')
    fig, ax = plt.subplots(figsize=(6, 4))
    fig.patch.set_facecolor("white")
    ax.pie(gender['total'], labels=gender['gender'], colors=[MPL_GREEN, MPL_BLUE, "#00a8e8"], autopct='%1.1f%%', startangle=90, wedgeprops=dict(width=0.5, edgecolor='white'))
    fig.tight_layout()
    return _fig_to_rl_image(fig, width_cm=10, height_cm=5.5)

def _chart_weekend(df_f) -> RLImage:
    if 'is_weekend' not in df_f.columns: return None
    wk = df_f.groupby(['is_weekend', 'jam_tap_in']).size().reset_index(name='volume')
    weekday = wk[wk['is_weekend']==0].sort_values('jam_tap_in')
    weekend = wk[wk['is_weekend']==1].sort_values('jam_tap_in')
    fig, ax = plt.subplots(figsize=(10, 3.5))
    _mpl_style(ax, fig)
    ax.plot(weekday['jam_tap_in'], weekday['volume'], color=MPL_BLUE, linewidth=2, marker='o', label='Hari Kerja')
    ax.plot(weekend['jam_tap_in'], weekend['volume'], color=MPL_GREEN, linewidth=2, marker='s', label='Akhir Pekan')
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{int(x):,}"))
    ax.set_xticks(range(0, 24, 2))
    ax.legend()
    fig.tight_layout()
    return _fig_to_rl_image(fig, width_cm=17, height_cm=5)


# ============================================================
# 5. GENERATE PDF REPORT
# ============================================================
def generate_pdf_report(df_f, metrics: dict, interpretations: dict) -> bytes:
    buffer = io.BytesIO()
    RL_BLUE, RL_GREEN, RL_DARK, RL_GRAY, RL_LIGHT = [colors.HexColor(c) for c in [C_BLUE, C_GREEN, C_DARK, C_GRAY, "#e8f4f8"]]

    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2.5*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()

    s_section = ParagraphStyle('Sec', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=11, textColor=RL_BLUE, spaceBefore=14, spaceAfter=6)
    s_body = ParagraphStyle('Body', parent=styles['Normal'], fontName='Helvetica', fontSize=9, leading=14, spaceAfter=4, alignment=TA_JUSTIFY)
    s_label = ParagraphStyle('Label', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8, textColor=RL_GRAY)
    s_kpi = ParagraphStyle('KPI', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=16, textColor=RL_BLUE)

    story = []
    
    # Header
    header_tbl = Table([[Paragraph("JAKLINGKO", ParagraphStyle('Logo', fontName='Helvetica-Bold', fontSize=26, textColor=RL_BLUE)), 
                         Paragraph(f"LAPORAN ANALITIK OPERASIONAL<br/><font size='8'>Digenerate: {datetime.now().strftime('%d %B %Y, %H:%M')}</font>", ParagraphStyle('HR', fontName='Helvetica-Bold', fontSize=10, alignment=TA_RIGHT))]], 
                       colWidths=[9*cm, 8*cm])
    header_tbl.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('BOTTOMPADDING', (0,0), (-1,-1), 8)]))
    story.append(header_tbl)
    story.append(HRFlowable(width="100%", thickness=3, color=RL_GREEN, spaceAfter=10))

    # KPI
    story.append(Paragraph("RINGKASAN KINERJA UTAMA", s_section))
    kpi_tbl = Table([[Paragraph("Total Transaksi", s_label), Paragraph("Total Pendapatan", s_label), Paragraph("Rata-Rata Tarif", s_label)], 
                     [Paragraph(f"{metrics['total_trx']:,}", s_kpi), Paragraph(f"Rp {metrics['total_rev']:,.0f}", s_kpi), Paragraph(f"Rp {metrics['avg_rev']:,.0f}", s_kpi)]], 
                    colWidths=[5.5*cm]*3)
    kpi_tbl.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), RL_LIGHT), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#ccddee")), ('BOX', (0,0), (-1,-1), 1.5, RL_BLUE)]))
    story.append(kpi_tbl)
    story.append(Spacer(1, 0.5*cm))

    # Charts
    def add_chart_section(title, interp_key, chart_func, data):
        story.append(Paragraph(title, s_section))
        story.append(Paragraph(_strip_html(interpretations.get(interp_key, '-')), s_body))
        if chart_func and data is not None:
            story.append(chart_func(data))
        story.append(Spacer(1, 0.3*cm))

    add_chart_section("1. ANALISIS TREN VOLUME HARIAN", 'tren', _chart_tren, df_f.groupby('tanggal').size().reset_index(name='volume'))
    add_chart_section("2. ANALISIS JAM OPERASIONAL", 'rush', _chart_rush, df_f)
    
    story.append(PageBreak())
    add_chart_section("3. KOMPOSISI SEGMEN PENUMPANG", 'segment', _chart_segmen, df_f)
    add_chart_section("4. PREFERENSI KARTU BANK", 'bank', _chart_bank, df_f)
    
    story.append(PageBreak())
    add_chart_section("5. KINERJA VOLUME PER KORIDOR", 'corridor', _chart_corridor, df_f)
    if 'gender' in df_f.columns:
        add_chart_section("6. DEMOGRAFI GENDER PENUMPANG", 'gender', _chart_gender, df_f)
    if 'is_weekend' in df_f.columns:
        add_chart_section("7. POLA HARI KERJA VS AKHIR PEKAN", 'weekend', _chart_weekend, df_f)

    doc.build(story)
    return buffer.getvalue()

def _strip_html(text: str) -> str:
    import re
    return re.sub(r'<strong>(.*?)</strong>', r'<b>\1</b>', text)


# ============================================================
# 6. SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown(f"""
    <div style="padding: 1.2rem 0 1.5rem; border-bottom: 1px solid {C_BLUE}44; margin-bottom: 1rem;">
        <div style="font-family:'Space Grotesk',sans-serif; font-size:0.65rem; font-weight:600; color:{C_GRAY}; letter-spacing:3px; text-transform:uppercase; margin-bottom:4px;">TransJakarta</div>
        <div style="font-family:'Space Grotesk',sans-serif; font-size:1.25rem; font-weight:700; color:{C_WHITE}; letter-spacing:1px; line-height:1.2;">OLAP Dashboard</div>
        <div style="font-family:'Space Grotesk',sans-serif; font-size:0.68rem; font-weight:500; color:{C_GREEN}; letter-spacing:1.5px; text-transform:uppercase; margin-top:4px;">JakLingko Analytics</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f'<div style="font-family:Space Grotesk; font-weight:700; font-size:0.9rem; color:{C_GREEN}; margin-bottom:0.5rem;">FILTER DATA</div>', unsafe_allow_html=True)

    with st.spinner("Memuat data dari CSV..."):
        df_raw = load_data()

    koridor_list = ["Semua"] + sorted(df_raw['jenis_koridor'].dropna().unique().tolist())
    segmen_list  = ["Semua"] + sorted(df_raw['segment_pengguna'].dropna().unique().tolist())

    selected_koridor = st.selectbox("Jenis Koridor", koridor_list)
    selected_segmen  = st.selectbox("Segmen Pengguna", segmen_list)

    st.markdown('<hr style="border-color:#0083b333;">', unsafe_allow_html=True)

    st.markdown(f'<div style="font-family:Space Grotesk; font-weight:700; font-size:0.9rem; color:{C_GREEN}; margin-bottom:0.5rem;">MONITORING REALTIME</div>', unsafe_allow_html=True)
    auto_refresh    = st.toggle("Aktifkan Auto-Refresh", value=True)
    refresh_interval= st.slider("Interval Refresh (detik)", 15, 300, 60, step=15, disabled=not auto_refresh)

    if auto_refresh:
        st.markdown(f'<div class="status-live"><div class="status-dot"></div> LIVE</div><div style="font-size:0.7rem; color:{C_GRAY}; margin-top:4px;">Refresh setiap {refresh_interval}s</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div style="font-size:0.7rem; color:{C_GRAY};">Mode statis - data tidak diperbarui otomatis</div>', unsafe_allow_html=True)

    st.markdown('<hr style="border-color:#0083b333;">', unsafe_allow_html=True)
    st.markdown(f'<div style="font-size:0.7rem; color:{C_GRAY}; margin-bottom:0.3rem;">Terakhir dimuat:</div><div style="font-size:0.8rem; color:{C_WHITE}; font-weight:600;">{datetime.now().strftime("%d %b %Y, %H:%M:%S")}</div>', unsafe_allow_html=True)


# ============================================================
# 7. FILTER DATA
# ============================================================
df_filtered = df_raw.copy()
if selected_koridor != "Semua": df_filtered = df_filtered[df_filtered['jenis_koridor'] == selected_koridor]
if selected_segmen != "Semua": df_filtered = df_filtered[df_filtered['segment_pengguna'] == selected_segmen]


# ============================================================
# 8. HEADER UTAMA
# ============================================================
st.markdown(f"""
<div class="dash-header">
    <div style="display:flex; justify-content:space-between; align-items:flex-start;">
        <div>
            <h1>ANALYTICS COMMAND CENTER</h1>
            <p>TransJakarta JakLingko &mdash; Data Warehouse Intelligence Platform (CSV Based)</p>
        </div>
        <div class="status-live" style="margin-top:0.3rem;"><div class="status-dot"></div> LIVE DATA</div>
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

metrics_dict = {'total_trx': total_trx, 'total_rev': total_rev, 'avg_rev': avg_rev, 'active_days': active_days}

st.markdown('<div style="height:0.5rem;"></div>', unsafe_allow_html=True)
col1, col2, col3, col4 = st.columns(4, gap="medium")
kpi_items = [
    (col1, "TOTAL TRANSAKSI",    f"{total_trx:,}",           "Seluruh perjalanan tercatat"),
    (col2, "TOTAL PENDAPATAN",   format_metric(total_rev),     "Kumulatif tarif seluruh periode"),
    (col3, "RATA-RATA TARIF",    f"Rp {avg_rev:,.0f}",       "Per transaksi perjalanan"),
    (col4, "HARI OPERASIONAL",   f"{active_days}",            "Hari dengan aktivitas"),
]
for col, label, value, sub in kpi_items:
    with col:
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">{label}</div><div class="kpi-value">{value}</div><div class="kpi-delta">> {sub}</div></div>', unsafe_allow_html=True)


# ============================================================
# 10. TREN VOLUME HARIAN
# ============================================================
st.markdown('<div style="height:1.2rem;"></div><div class="section-header">Analisis Tren & Perilaku Pengguna</div>', unsafe_allow_html=True)

tren_df = df_filtered.groupby('tanggal').size().reset_index(name='volume')
fig_tren = go.Figure()
fig_tren.add_trace(go.Scatter(x=tren_df['tanggal'], y=tren_df['volume'], fill='tozeroy', fillcolor=f"rgba(0,131,179,0.15)", line=dict(color=C_BLUE, width=3), mode='lines+markers', marker=dict(size=6, color=C_GREEN, line=dict(color=C_BLUE, width=1.5)), hovertemplate='<b>%{x|%d %b %Y}</b><br>Volume: <b>%{y:,} transaksi</b><extra></extra>', name='Volume Harian'))
if len(tren_df) >= 7:
    tren_df['ma7'] = tren_df['volume'].rolling(7).mean()
    fig_tren.add_trace(go.Scatter(x=tren_df['tanggal'], y=tren_df['ma7'], line=dict(color=C_GREEN, width=2.5, dash='dash'), mode='lines', name='Moving Avg (7 hari)', hovertemplate='<b>MA7:</b> %{y:.0f}<extra></extra>'))

fig_tren.update_layout(**layout(height=380, title="", legend=dict(font=dict(color=C_DARK), orientation='h', yanchor='bottom', y=1.02, xanchor='left', x=0), margin=dict(t=50, b=20), hovermode='x unified'))
st.plotly_chart(fig_tren, use_container_width=True, config={'displayModeBar': False})

interp_tren = interpret_trend(tren_df)
st.markdown(f'<div class="interp-box"><div class="interp-title">Insight Tren Volume</div><div class="interp-text">{interp_tren}</div></div>', unsafe_allow_html=True)

# --- CHART 2 & 3: SEGMEN + JAM SIBUK ---
st.markdown('<div style="height:1rem;"></div><div class="section-header">Demografi Penumpang & Jam Operasional</div>', unsafe_allow_html=True)
col_a, col_b = st.columns(2, gap="medium")

with col_a:
    demo_df = df_filtered.groupby('segment_pengguna').size().reset_index(name='total')
    fig_demo = px.pie(demo_df, values='total', names='segment_pengguna', hole=0.55, color_discrete_sequence=PLOTLY_COLORS)
    fig_demo.update_traces(textfont_color=C_WHITE, textposition='inside', textinfo='label+percent', hovertemplate='<b>%{label}</b><br>%{value:,} transaksi (%{percent})<extra></extra>', marker=dict(line=dict(color=C_WHITE, width=2)))
    fig_demo.update_layout(**layout(height=400, title="Komposisi Segmen Pengguna", title_font_size=14, legend=dict(font=dict(color=C_DARK), orientation='h', yanchor='top', y=-0.05, xanchor='center', x=0.5), margin=dict(t=50, b=80, l=10, r=10), annotations=[dict(text='', x=0.5, y=0.5, font_size=12, font_color=C_GRAY, showarrow=False)]))
    st.plotly_chart(fig_demo, use_container_width=True, config={'displayModeBar': False})
    interp_seg = interpret_segment(demo_df)
    st.markdown(f'<div class="interp-box"><div class="interp-title">Insight Segmen</div><div class="interp-text">{interp_seg}</div></div>', unsafe_allow_html=True)

with col_b:
    rush_df = df_filtered.groupby('jam_tap_in').size().reset_index(name='volume').sort_values('jam_tap_in')
    colors_bar = [C_GREEN if v == rush_df['volume'].max() else C_BLUE for v in rush_df['volume']]
    fig_rush = go.Figure(go.Bar(x=rush_df['jam_tap_in'].astype(int), y=rush_df['volume'], marker=dict(color=colors_bar, line=dict(color=C_DARK, width=1)), hovertemplate='<b>%{x}:00 - %{x+1}:00</b><br>Volume: <b>%{y:,} transaksi</b><extra></extra>'))
    fig_rush.update_layout(**layout(height=400, bargap=0.3, title="Distribusi Transaksi per Jam", title_font_size=14, xaxis=dict(tickmode='linear', tick0=0, dtick=2, tickformat='%02d:00', title='Jam'), yaxis=dict(title='Jumlah Transaksi'), margin=dict(t=50, b=40, l=10, r=10)))
    st.plotly_chart(fig_rush, use_container_width=True, config={'displayModeBar': False})
    interp_rush = interpret_rush_hour(rush_df)
    st.markdown(f'<div class="interp-box"><div class="interp-title">Insight Jam Sibuk</div><div class="interp-text">{interp_rush}</div></div>', unsafe_allow_html=True)

# --- CHART 4: BANK ---
st.markdown('<div style="height:1rem;"></div><div class="section-header">Preferensi Pembayaran Kartu Bank</div>', unsafe_allow_html=True)
bank_df = df_filtered.groupby('bank_kartu').size().reset_index(name='total').sort_values('total', ascending=True)
fig_bank = go.Figure(go.Bar(x=bank_df['total'], y=bank_df['bank_kartu'], orientation='h', marker=dict(color=bank_df['total'], colorscale=[[0, C_BLUE], [0.5, "#00a8e8"], [1, C_GREEN]], showscale=False, line=dict(color=C_WHITE, width=1)), text=[f"  {v:,}" for v in bank_df['total']], textposition='outside', textfont=dict(color=C_DARK, size=10), hovertemplate='<b>%{y}</b><br>%{x:,} transaksi (%{customdata:.1f}%)<extra></extra>', customdata=(bank_df['total']/bank_df['total'].sum()*100)))
fig_bank.update_layout(**layout(height=max(400, len(bank_df)*50), title="Volume Transaksi per Bank", title_font_size=14, xaxis=dict(title='Jumlah Transaksi'), margin=dict(t=50, b=40, l=10, r=10)))
st.plotly_chart(fig_bank, use_container_width=True, config={'displayModeBar': False})
interp_bank = interpret_bank(bank_df)
st.markdown(f'<div class="interp-box"><div class="interp-title">Insight Pembayaran</div><div class="interp-text">{interp_bank}</div></div>', unsafe_allow_html=True)

# --- CHART 5 & 6: KORIDOR & GENDER ---
st.markdown('<div style="height:1rem;"></div><div class="section-header">Kinerja Koridor & Demografi Lanjutan</div>', unsafe_allow_html=True)
col_c, col_d = st.columns(2, gap="medium")

with col_c:
    corridor_df = df_filtered.groupby('jenis_koridor').size().reset_index(name='total').sort_values('total', ascending=True)
    fig_corridor = go.Figure(go.Bar(x=corridor_df['total'], y=corridor_df['jenis_koridor'], orientation='h', marker=dict(color=C_BLUE, line=dict(color=C_WHITE, width=1)), text=[f"  {v:,}" for v in corridor_df['total']], textposition='outside', textfont=dict(color=C_DARK, size=10), hovertemplate='<b>%{y}</b><br>Volume: <b>%{x:,}</b> transaksi<extra></extra>'))
    fig_corridor.update_layout(**layout(height=400, title="Volume Transaksi per Koridor", title_font_size=14, xaxis=dict(title='Jumlah Transaksi'), margin=dict(t=50, b=40, l=10, r=10)))
    st.plotly_chart(fig_corridor, use_container_width=True, config={'displayModeBar': False})
    interp_corridor = interpret_corridor(corridor_df)
    st.markdown(f'<div class="interp-box"><div class="interp-title">Insight Koridor</div><div class="interp-text">{interp_corridor}</div></div>', unsafe_allow_html=True)

with col_d:
    interp_gender = "Data gender tidak tersedia."
    if 'gender' in df_filtered.columns:
        gender_df = df_filtered.groupby('gender').size().reset_index(name='total')
        fig_gender = px.pie(gender_df, values='total', names='gender', hole=0.45, color_discrete_sequence=[C_GREEN, C_BLUE, "#00a8e8"])
        fig_gender.update_traces(textfont_color=C_WHITE, textposition='inside', textinfo='label+percent', marker=dict(line=dict(color=C_WHITE, width=2)))
        fig_gender.update_layout(**layout(height=400, title="Proporsi Penumpang Berdasarkan Gender", title_font_size=14, legend=dict(font=dict(color=C_DARK), orientation='h', yanchor='top', y=-0.05, xanchor='center', x=0.5), margin=dict(t=50, b=80, l=10, r=10)))
        st.plotly_chart(fig_gender, use_container_width=True, config={'displayModeBar': False})
        interp_gender = interpret_gender(gender_df)
        st.markdown(f'<div class="interp-box"><div class="interp-title">Insight Gender</div><div class="interp-text">{interp_gender}</div></div>', unsafe_allow_html=True)

# --- CHART 7: WEEKEND VS WEEKDAY ---
interp_weekend = "Data akhir pekan tidak tersedia."
if 'is_weekend' in df_filtered.columns:
    st.markdown('<div style="height:1rem;"></div><div class="section-header">Perbandingan Pola Hari Kerja vs Akhir Pekan</div>', unsafe_allow_html=True)
    wk_df = df_filtered.groupby(['is_weekend', 'jam_tap_in']).size().reset_index(name='volume')
    wk_df['kategori'] = wk_df['is_weekend'].map({0: 'Hari Kerja', 1: 'Akhir Pekan'})
    fig_wk = px.line(wk_df, x='jam_tap_in', y='volume', color='kategori', color_discrete_map={'Hari Kerja': C_BLUE, 'Akhir Pekan': C_GREEN}, markers=True, title="Tren Per Jam: Hari Kerja vs Akhir Pekan")
    fig_wk.update_traces(line_width=3, marker_size=7, hovertemplate='<b>%{fullData.name}</b><br>%{x}:00<br>Volume: <b>%{y:,} transaksi</b><extra></extra>')
    fig_wk.update_layout(**layout(height=400, title_font_size=14, xaxis=dict(title='Jam', tickmode='linear', dtick=2), yaxis=dict(title='Volume Transaksi'), legend=dict(font=dict(color=C_DARK), orientation='h', yanchor='bottom', y=1.02, xanchor='left', x=0), margin=dict(t=60, b=40, l=10, r=10), hovermode='x unified'))
    st.plotly_chart(fig_wk, use_container_width=True, config={'displayModeBar': False})
    interp_weekend = interpret_weekend(wk_df)
    st.markdown(f'<div class="interp-box"><div class="interp-title">Insight Hari Operasional</div><div class="interp-text">{interp_weekend}</div></div>', unsafe_allow_html=True)


# ============================================================
# 12. GENERATE & UNDUH PDF
# ============================================================
st.markdown('<hr style="border: 0; border-top: 2px solid {C_BLUE}44; margin: 2.5rem 0 1.5rem;"></hr><div class="section-header">Ekspor Laporan PDF</div>', unsafe_allow_html=True)

col_pdf1, col_pdf2, col_pdf3 = st.columns([2.5, 1.2, 1.2], gap="medium")
with col_pdf1:
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #0f3555cc, #06202fcc); border: 1.5px solid {C_GREEN}55; border-radius: 14px; padding: 1.3rem 1.6rem; backdrop-filter: blur(10px);">
        <div style="font-size:0.82rem; font-weight:700; color:{C_GREEN}; margin-bottom:0.6rem; letter-spacing:0.5px;">UNDUH LAPORAN EKSEKUTIF PDF</div>
        <div style="font-size:0.8rem; color:#d5e8f2; line-height:1.65;">Dapatkan ringkasan komprehensif yang mencakup KPI utama, analisis tren, distribusi jam operasional, komposisi segmen pengguna, preferensi pembayaran, dan insight strategis berbasis data.</div>
    </div>
    """, unsafe_allow_html=True)

with col_pdf2:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Generate", type="primary", use_container_width=True, key="gen_pdf"):
        with st.spinner("Menyusun laporan PDF..."):
            interpretations = {'tren': interp_tren, 'rush': interp_rush, 'segment': interp_seg, 'bank': interp_bank, 'corridor': interp_corridor, 'gender': interp_gender, 'weekend': interp_weekend}
            pdf_bytes = generate_pdf_report(df_filtered, metrics_dict, interpretations)
            st.session_state['pdf_bytes'] = pdf_bytes
            st.session_state['pdf_ready'] = True
        st.success("Laporan siap diunduh!")

with col_pdf3:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.session_state.get('pdf_ready'):
        st.download_button(label="Unduh PDF", data=st.session_state['pdf_bytes'], file_name=f"laporan_jaklingko_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf", mime="application/pdf", use_container_width=True)

# ============================================================
# 13. AUTO REFRESH & FOOTER
# ============================================================
if auto_refresh:
    time.sleep(refresh_interval)
    st.cache_data.clear()
    st.rerun()

st.markdown('<hr style="border: 0; border-top: 1px solid {C_BLUE}33; margin: 2.5rem 0 0;"></hr>', unsafe_allow_html=True)
st.markdown(f'<div style="text-align:center; font-size:0.78rem; color:{C_GRAY}; padding:1.5rem 0; margin-top:0.5rem;"><div style="margin-bottom:0.5rem; font-weight:500;">JakLingko Analytics Command Center</div><div style="font-size:0.72rem; opacity:0.8;">Powered by Python • Streamlit • Plotly • ReportLab | Data Warehouse Architecture (UTS)</div></div>', unsafe_allow_html=True)