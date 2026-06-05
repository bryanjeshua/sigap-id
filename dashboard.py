"""
SIGAP-ID Dashboard — Streamlit Prototype
Run: streamlit run dashboard.py
"""
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import requests
import os
from pathlib import Path
from datetime import datetime

# ── Dicoding meta injection ────────────────────────────────────────────────────
def _inject_dicoding_meta():
    try:
        index = Path(st.__file__).parent / "static" / "index.html"
        if not index.exists():
            return
        html = index.read_text(encoding="utf-8")
        meta = '<meta name="dicoding:email" content="salmakurniadewi@gmail.com"/>'
        if 'dicoding:email' not in html:
            html = html.replace('<head>', f'<head>{meta}', 1)
            index.write_text(html, encoding="utf-8")
    except Exception:
        pass

_inject_dicoding_meta()

# ── Theme ──────────────────────────────────────────────────────────────────────
if 'light_mode' not in st.session_state:
    st.session_state.light_mode = False

if st.session_state.light_mode:
    T = dict(
        bg0='#f8fafc', bg1='#f1f5f9', bg2='#ffffff', bg3='#e2e8f0',
        accent='#d97706', accent_dim='rgba(217,119,6,0.08)',
        accent_border='rgba(217,119,6,0.25)',
        text0='#0f172a', text1='#475569', text2='#94a3b8',
        border='#e2e8f0',
        fig_bg='#f1f5f9', ax_bg='#ffffff',
        legend_fg='#334155', legend_bg='#f8fafc',
        label='#64748b', title='#0f172a',
        tick='#475569',
    )
else:
    T = dict(
        bg0='#07090f', bg1='#0c1120', bg2='#111827', bg3='#1a2540',
        accent='#f59e0b', accent_dim='rgba(245,158,11,0.08)',
        accent_border='rgba(245,158,11,0.25)',
        text0='#f1f5f9', text1='#94a3b8', text2='#475569',
        border='#1e2d3d',
        fig_bg='#0c1120', ax_bg='#0c1120',
        legend_fg='#94a3b8', legend_bg='#111827',
        label='#64748b', title='#e2e8f0',
        tick='#94a3b8',
    )

st.set_page_config(
    page_title="SIGAP-ID | Sistem Intelijen Geospasial Adaptif Perkotaan Indonesia",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@600;700;800&family=IBM+Plex+Mono:wght@300;400;500&family=DM+Sans:opsz,wght@9..40,300;9..40,400;9..40,500&display=swap');

:root {
    --bg-0: #07090f;
    --bg-1: #0c1120;
    --bg-2: #111827;
    --bg-3: #1a2540;
    --accent: #f59e0b;
    --accent-dim: rgba(245,158,11,0.08);
    --accent-border: rgba(245,158,11,0.25);
    --danger: #ef4444;
    --warn: #f97316;
    --safe: #22c55e;
    --text-0: #f1f5f9;
    --text-1: #94a3b8;
    --text-2: #475569;
    --border: #1e2d3d;
    --radius: 3px;
}

/* ── hide streamlit chrome ── */
#MainMenu, footer { visibility: hidden; }
.stDeployButton,
[data-testid="stToolbarActions"],
[data-testid="stMainMenu"],
[data-testid="stStatusWidget"],
[data-testid="stHeaderActionElements"] { display: none !important; }

/* ── sidebar toggle button ── */
[data-testid="stSidebarCollapseButton"],
[data-testid="collapsedControl"] {
    visibility: visible !important;
    display: flex !important;
    background: var(--bg-2) !important;
    border: 1px solid var(--border) !important;
    border-radius: 0 var(--radius) var(--radius) 0 !important;
}
[data-testid="stExpandSidebarButton"] {
    visibility: visible !important;
    display: flex !important;
}

/* ── global ── */
html, body, .stApp {
    background-color: var(--bg-0) !important;
    font-family: 'DM Sans', sans-serif !important;
    color: var(--text-1) !important;
}

/* ── sidebar ── */
[data-testid="stSidebar"] {
    background-color: var(--bg-1) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] * { font-family: 'DM Sans', sans-serif !important; }
[data-testid="stSidebar"] h1 {
    font-family: 'Syne', sans-serif !important;
    font-weight: 800 !important;
    font-size: 1.4rem !important;
    letter-spacing: -0.03em !important;
    color: var(--text-0) !important;
}
[data-testid="stSidebar"] .stCaption p {
    color: var(--text-2) !important;
    font-size: 0.72rem !important;
    letter-spacing: 0.01em !important;
}
[data-testid="stSidebar"] hr { border-color: var(--border) !important; }

/* ── headings ── */
h1, h2, h3 {
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    letter-spacing: -0.025em !important;
    color: var(--text-0) !important;
}
h1 { font-weight: 800 !important; }
p, li { color: var(--text-1) !important; }

/* ── metrics ── */
[data-testid="metric-container"] {
    background: var(--bg-2) !important;
    border: 1px solid var(--border) !important;
    border-top: 2px solid var(--accent) !important;
    border-radius: var(--radius) !important;
    padding: 1rem 1.1rem !important;
}
[data-testid="stMetricValue"] {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 1.9rem !important;
    font-weight: 500 !important;
    color: var(--text-0) !important;
    letter-spacing: -0.03em !important;
}
[data-testid="stMetricLabel"] > div {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.68rem !important;
    font-weight: 500 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.1em !important;
    color: var(--text-2) !important;
}
[data-testid="stMetricDelta"] svg { display: none !important; }
[data-testid="stMetricDelta"] > div {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.72rem !important;
    color: var(--text-2) !important;
}

/* ── tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: var(--bg-1) !important;
    border-bottom: 1px solid var(--border) !important;
    gap: 0 !important;
    padding: 0 !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: var(--text-2) !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.73rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    padding: 0.7rem 1.4rem !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
    border-radius: 0 !important;
    transition: color 0.15s ease !important;
}
.stTabs [aria-selected="true"] {
    color: var(--accent) !important;
    border-bottom: 2px solid var(--accent) !important;
    background: var(--accent-dim) !important;
}
.stTabs [data-baseweb="tab-highlight"] { display: none !important; }
.stTabs [data-baseweb="tab-panel"] {
    background: transparent !important;
    padding-top: 1.5rem !important;
}

/* ── dataframe ── */
[data-testid="stDataFrame"] {
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
}
[data-testid="stDataFrame"] thead tr th {
    background: var(--bg-3) !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.7rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
    color: var(--text-2) !important;
}

/* ── alerts ── */
[data-baseweb="notification"] {
    background: var(--bg-2) !important;
    border-radius: var(--radius) !important;
}
.stSuccess > div { border-left: 3px solid var(--safe) !important; }
.stWarning > div { border-left: 3px solid var(--warn) !important; }
.stError   > div { border-left: 3px solid var(--danger) !important; }
.stInfo    > div { border-left: 3px solid var(--accent) !important; }

/* ── sliders ── */
[data-testid="stSlider"] [data-baseweb="thumb"] {
    background: var(--accent) !important;
    border-color: var(--accent) !important;
    width: 14px !important; height: 14px !important;
}
[data-testid="stSlider"] [data-baseweb="track-fill"] {
    background: var(--accent) !important;
}
[data-testid="stSlider"] [data-baseweb="track"] {
    background: var(--bg-3) !important;
}

/* ── radio + checkbox ── */
[data-testid="stRadio"] label, [data-testid="stCheckbox"] label {
    font-size: 0.85rem !important;
    color: var(--text-1) !important;
}
[data-testid="stRadio"] [data-testid="stMarkdownContainer"] p {
    font-size: 0.85rem !important;
    color: var(--text-1) !important;
}

/* ── selectbox ── */
[data-baseweb="select"] > div {
    background: var(--bg-2) !important;
    border-color: var(--border) !important;
    color: var(--text-0) !important;
    font-size: 0.85rem !important;
}

/* ── divider ── */
hr { border-color: var(--border) !important; margin: 1.25rem 0 !important; }

/* ── captions ── */
.stCaption p {
    font-size: 0.72rem !important;
    color: var(--text-2) !important;
    letter-spacing: 0.01em !important;
}

/* ── live pulse ── */
@keyframes live-pulse {
    0%, 100% { opacity: 1; }
    50%       { opacity: 0.35; }
}
.live-indicator {
    display: inline-block;
    width: 7px; height: 7px;
    background: var(--safe);
    border-radius: 50%;
    animation: live-pulse 1.8s ease-in-out infinite;
    margin-right: 5px;
    vertical-align: middle;
    position: relative; top: -1px;
}
</style>
""", unsafe_allow_html=True)

# ── Dynamic theme CSS override ─────────────────────────────────────────────────
_light_extra = """
    [data-baseweb="input"] input,
    [data-baseweb="textarea"] textarea { color: #0f172a !important; background: #fff !important; }
    [data-baseweb="select"] [data-testid="stSelectboxValue"] { color: #0f172a !important; }
    [data-testid="stDataFrame"] td, [data-testid="stDataFrame"] th { color: #334155 !important; }
    [data-testid="stMarkdownContainer"] p { color: #475569 !important; }
    [data-testid="stRadio"] label span, [data-testid="stCheckbox"] label span { color: #334155 !important; }
    .stAlert > div { color: #0f172a !important; }
""" if st.session_state.light_mode else ""

st.markdown(f"""<style>
:root {{
    --bg-0: {T['bg0']};
    --bg-1: {T['bg1']};
    --bg-2: {T['bg2']};
    --bg-3: {T['bg3']};
    --accent: {T['accent']};
    --accent-dim: {T['accent_dim']};
    --accent-border: {T['accent_border']};
    --text-0: {T['text0']};
    --text-1: {T['text1']};
    --text-2: {T['text2']};
    --border: {T['border']};
}}
{_light_extra}
</style>""", unsafe_allow_html=True)

ZONES = ['Jakarta Pusat', 'Jakarta Barat', 'Jakarta Selatan', 'Jakarta Timur', 'Jakarta Utara']

# ── BMKG Live API ──────────────────────────────────────────────────────────────
@st.cache_data(ttl=900)
def fetch_bmkg_rainfall():
    """Fetch current rainfall forecast from BMKG API (Gambir, Jakarta Pusat).
    Returns: (mm_per_hr, weather_desc, station_name, error_message)
    """
    try:
        url = "https://api.bmkg.go.id/publik/prakiraan-cuaca?adm4=31.71.05.1003"
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        data = r.json()

        forecasts = []
        for day_list in data['data'][0]['cuaca']:
            forecasts.extend(day_list)

        now = datetime.now()
        best, best_diff = None, float('inf')
        for f in forecasts:
            try:
                ft = datetime.strptime(f['local_datetime'], '%Y-%m-%d %H:%M:%S')
                diff = abs((ft - now).total_seconds())
                if diff < best_diff:
                    best_diff = diff
                    best = f
            except Exception:
                continue

        if best:
            mm_hr = round(float(best.get('tp', 0)) / 3, 1)
            desc  = best.get('weather_desc', '-')

            # BMKG API returns lokasi as dict or string depending on version
            lokasi_raw = data.get('lokasi', {})
            if isinstance(lokasi_raw, dict):
                kec   = lokasi_raw.get('kecamatan', '')
                kota  = (lokasi_raw.get('kotkab', 'Jakarta')
                         .replace('Kota Adm. ', '').replace('Kota ', ''))
                station = f"{kec}, {kota}" if kec else kota
            else:
                station = str(lokasi_raw) if lokasi_raw else 'Jakarta Pusat'

            return mm_hr, desc, station, None

        return None, None, None, "Data prakiraan tidak ditemukan dalam respons BMKG."

    except requests.exceptions.Timeout:
        return None, None, None, "Timeout: BMKG API tidak merespons (>5 detik)."
    except requests.exceptions.ConnectionError:
        return None, None, None, "Tidak dapat terhubung ke BMKG API."
    except Exception as e:
        return None, None, None, f"Error BMKG API: {str(e)[:80]}"

# ── Data Loading ───────────────────────────────────────────────────────────────
@st.cache_data
def load_corridor_meta():
    return pd.read_pickle("data/processed/corridor_meta.pkl")

@st.cache_data
def load_lookup():
    path = "data/processed/lookup_table.pkl"
    if not os.path.exists(path):
        return None
    return pd.read_pickle(path)

def lookup_corridor(lookup_df, corridor, hour, is_weekend, rainfall_mm):
    rain_key = int(min(round(rainfall_mm / 5) * 5, 100))
    try:
        row = lookup_df.loc[(corridor, hour, int(is_weekend), rain_key)]
        return float(row['live_speed']), str(row['live_level']), float(row['prob_macet'])
    except KeyError:
        return 20.0, 'Sedang', 0.3

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("SIGAP-ID")
    st.caption("Sistem Intelijen Geospasial Adaptif Perkotaan Indonesia")
    st.divider()

    user_mode = st.radio("Mode Pengguna", ["Operator Logistik", "Dishub / BPBD"], index=0)
    st.toggle("☀️ Light Mode", key="light_mode")
    st.divider()

    # ── Sumber Data Cuaca ──────────────────────────────────────────────────────
    st.subheader("☁️ Data Cuaca")
    bmkg_rain, bmkg_desc, bmkg_station, bmkg_error = fetch_bmkg_rainfall()
    bmkg_available = bmkg_error is None

    if bmkg_available:
        data_mode = st.radio(
            "Sumber Data",
            ["🟢 BMKG Live", "⚙️ Simulasi Manual"],
            index=0,
            help="BMKG Live menggunakan prakiraan cuaca terkini dari BMKG API. "
                 "Simulasi Manual memungkinkan Anda mengatur nilai secara bebas."
        )
    else:
        st.warning(f"⚠️ **BMKG tidak tersedia**\n\n_{bmkg_error}_")
        st.caption("Mode otomatis beralih ke Simulasi Manual.")
        data_mode = "⚙️ Simulasi Manual"

    st.divider()

    if data_mode == "🟢 BMKG Live":
        # All values auto-set from live data — no sliders shown
        rainfall_sim = int(min(round(bmkg_rain / 5) * 5, 100))
        hour_sim     = datetime.now().hour
        is_weekend   = datetime.now().weekday() >= 5
        bmkg_live    = True

        st.success(f"🟢 **LIVE** — {bmkg_station}")
        st.caption(f"Kondisi: **{bmkg_desc}**")
        mc1, mc2 = st.columns(2)
        mc1.metric("Curah Hujan", f"{rainfall_sim} mm/hr")
        mc2.metric("Jam (WIB)",   f"{hour_sim:02d}:00")
        st.caption(f"{'🏖️ Weekend' if is_weekend else '💼 Hari Kerja'} · "
                   f"Diperbarui tiap 15 menit")
        st.caption("💡 Pilih **Simulasi Manual** untuk mengubah nilai.")
    else:
        # Full manual control
        bmkg_live    = False
        rainfall_sim = st.slider(
            "Curah Hujan (mm/hr)", 0, 100, 25, step=5,
            help="Atur nilai curah hujan untuk simulasi skenario risiko."
        )
        hour_sim     = st.slider("Jam Prediksi (WIB)", 0, 23, datetime.now().hour)
        is_weekend   = st.checkbox("Hari Weekend/Libur",
                                   value=datetime.now().weekday() >= 5)

    st.divider()

    selected_zone = st.multiselect(
        "Filter Zona (Dashboard)",
        ZONES,
        default=['Jakarta Barat', 'Jakarta Utara'],
    )

# ── Header ─────────────────────────────────────────────────────────────────────
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    live_dot = '<span class="live-indicator"></span>' if bmkg_live else ''
    data_src = f"{live_dot}BMKG Live" if bmkg_live else "Simulasi Manual"
    rain_label = ("EKSTREM" if rainfall_sim > 50 else "LEBAT" if rainfall_sim > 30
                  else "SEDANG" if rainfall_sim > 10 else "RINGAN" if rainfall_sim > 0
                  else "TIDAK HUJAN")
    st.markdown(f"""
    <div style="margin-bottom: 0.25rem;">
        <span style="font-family:'Syne',sans-serif;font-size:1.9rem;font-weight:800;
                     color:{T['text0']};letter-spacing:-0.04em;line-height:1;">SIGAP-ID</span>
        <span style="font-family:'IBM Plex Mono',monospace;font-size:0.65rem;color:{T['accent']};
                     letter-spacing:0.15em;text-transform:uppercase;border:1px solid {T['accent_border']};
                     padding:2px 7px;border-radius:2px;margin-left:10px;vertical-align:middle;">
            {data_src}
        </span>
    </div>
    <p style="font-family:'DM Sans',sans-serif;color:{T['text2']};font-size:0.8rem;
              letter-spacing:0.02em;margin:0;">
        Sistem Intelijen Geospasial Adaptif Perkotaan &nbsp;·&nbsp;
        Jabodetabek Risk Monitor &nbsp;·&nbsp; Mode: {user_mode}
    </p>
    """, unsafe_allow_html=True)
with col_h2:
    rain_cat = ("Ekstrem" if rainfall_sim > 50 else "Lebat" if rainfall_sim > 30
                else "Sedang" if rainfall_sim > 10 else "Ringan" if rainfall_sim > 0
                else "Tidak Hujan")
    st.metric("Curah Hujan", f"{rainfall_sim} mm/hr", rain_cat)
    st.metric("Jam Prediksi", f"{hour_sim:02d}:00 WIB",
              "Peak Morning" if 6 <= hour_sim <= 9 else
              "Peak Evening" if 16 <= hour_sim <= 20 else "Off-Peak")

st.divider()

# ── Load Data ──────────────────────────────────────────────────────────────────
try:
    df_meta  = load_corridor_meta()
    lookup   = load_lookup()
    has_data = True
except Exception as e:
    st.error(f"Data tidak ditemukan. Jalankan generate_lookup.py terlebih dahulu. Error: {e}")
    has_data = False

if not has_data:
    st.stop()

use_lookup = lookup is not None
if not use_lookup:
    st.warning("Lookup table tidak ditemukan — menggunakan rule-based fallback.")

# ── Compute predictions for ALL 41 corridors ──────────────────────────────────
def compute_all_predictions(df_meta, lookup, rainfall_mm, hour, is_weekend):
    rows = []
    for _, row in df_meta.iterrows():
        if use_lookup:
            spd, lvl, prob = lookup_corridor(lookup, row['corridor'], hour, is_weekend, rainfall_mm)
        else:
            ws, fr = row['weather_sensitivity'], row['flood_risk']
            rf = (0.0 if rainfall_mm < 5 else 0.10 if rainfall_mm < 10 else
                  0.30 if rainfall_mm < 30 else 0.50 if rainfall_mm < 50 else 0.70)
            pf = (0.50 if (6 <= hour <= 9  and not is_weekend) else
                  0.45 if (16 <= hour <= 20 and not is_weekend) else
                  1.35 if (hour < 5 or hour >= 22) else
                  1.20 if is_weekend else 1.0)
            spd = max(3, 35 * pf - 35 * ws * rf)
            if fr > 0.6 and rainfall_mm > 30:
                spd -= 35 * 0.30 * (fr - 0.6)
            spd = max(3, spd)
            lvl  = "Macet" if spd < 10 else "Sedang" if spd < 25 else "Lancar"
            prob = max(0, min(1, (25 - spd) / 22))
        rows.append({'corridor': row['corridor'], 'zone': row['zone'],
                     'lat': row['lat'], 'lon': row['lon'],
                     'flood_risk': row['flood_risk'],
                     'weather_sensitivity': row['weather_sensitivity'],
                     'live_speed': spd, 'live_level': lvl, 'prob_macet': prob})
    return pd.DataFrame(rows)

df_all = compute_all_predictions(df_meta, lookup, rainfall_sim, hour_sim, is_weekend)

# Zone-filtered view for Dashboard tab
if selected_zone:
    df_display = df_all[df_all['zone'].isin(selected_zone)].copy()
else:
    df_display = df_all.copy()

color_map = {'Macet': '#e74c3c', 'Sedang': '#f39c12', 'Lancar': '#2ecc71'}
emoji_map  = {'Macet': '🔴', 'Sedang': '🟡', 'Lancar': '🟢'}

# ── Tabs ───────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📊 Risk Dashboard", "🚗 Rekomendasi Rute", "📈 Prediksi & Analisis"])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — Risk Dashboard
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    n_macet  = (df_display['live_level'] == 'Macet').sum()
    n_sedang = (df_display['live_level'] == 'Sedang').sum()
    n_lancar = (df_display['live_level'] == 'Lancar').sum()
    n        = len(df_display)

    model_badge = "🤖 XGBoost" if use_lookup else "📐 Rule-based"
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🔴 Koridor MACET",  f"{n_macet}",  f"{n_macet/n*100:.0f}% dari {n} koridor")
    c2.metric("🟡 Koridor SEDANG", f"{n_sedang}", f"{n_sedang/n*100:.0f}%")
    c3.metric("🟢 Koridor LANCAR", f"{n_lancar}", f"{n_lancar/n*100:.0f}%")
    c4.metric("⚠️ Zona High-Risk",
              f"{(df_display['flood_risk'] > 0.7).sum()}",
              f"flood risk > 0.7 | {model_badge}")

    st.divider()
    col_map, col_table = st.columns([1.3, 1])

    with col_map:
        st.subheader("Peta Risiko Real-Time")
        fig, ax = plt.subplots(figsize=(8, 7), facecolor=T['fig_bg'])
        ax.set_facecolor(T['ax_bg'])
        for _, row in df_display.iterrows():
            c = color_map[row['live_level']]
            ax.scatter(row['lon'], row['lat'], c=c, s=row['prob_macet']*300+50,
                       alpha=0.85, edgecolors=T['bg0'], linewidth=0.5, zorder=3)
            ax.annotate(row['corridor'][:10], (row['lon'], row['lat']),
                        fontsize=5, color=T['label'], ha='center', va='bottom',
                        xytext=(0, 5), textcoords='offset points')
        ax.set_xlabel('Longitude', color=T['label'], fontsize=7)
        ax.set_ylabel('Latitude', color=T['label'], fontsize=7)
        ax.tick_params(colors=T['label'], labelsize=7)
        for spine in ax.spines.values():
            spine.set_edgecolor(T['border'])
        ax.legend(handles=[
            mpatches.Patch(color='#e74c3c', label=f'Macet ({n_macet})'),
            mpatches.Patch(color='#f39c12', label=f'Sedang ({n_sedang})'),
            mpatches.Patch(color='#2ecc71', label=f'Lancar ({n_lancar})'),
        ], loc='upper left', facecolor=T['legend_bg'], labelcolor=T['legend_fg'], edgecolor=T['border'])
        ax.set_title(f'Risiko per Koridor — {hour_sim:02d}:00 WIB | {rainfall_sim}mm/hr',
                     color=T['title'], fontsize=9, fontweight='600')
        st.pyplot(fig, use_container_width=True)
        plt.close()

    with col_table:
        st.subheader("Prediksi per Koridor")
        tbl = df_display[['corridor','zone','live_speed','live_level','prob_macet','flood_risk']].copy()
        tbl['Status']       = tbl['live_level'].map(emoji_map) + ' ' + tbl['live_level']
        tbl['Speed (km/h)'] = tbl['live_speed'].round(1)
        tbl['P(Macet)']     = (tbl['prob_macet']*100).round(0).astype(int).astype(str) + '%'
        tbl['Flood Risk']   = tbl['flood_risk'].round(2)
        tbl = tbl.sort_values('prob_macet', ascending=False)
        st.dataframe(tbl[['corridor','zone','Status','Speed (km/h)','P(Macet)','Flood Risk']],
                     hide_index=True, height=400, use_container_width=True)

        high_risk = tbl[tbl['prob_macet'] > 0.6]
        if len(high_risk) > 0:
            st.error(f"⚠️ **ALERT**: {len(high_risk)} koridor berisiko tinggi macet parah!")
            for _, r in high_risk.head(3).iterrows():
                st.warning(f"🔴 **{r['corridor']}** — P(Macet)={r['P(Macet)']} | Flood Risk={r['Flood Risk']:.2f}")
        else:
            st.success("✅ Semua koridor dalam batas aman saat ini.")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — Rekomendasi Rute
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.subheader("🚗 Rekomendasi Rute Logistik")
    st.caption("Pilih koridor asal dan tujuan — sistem mendeteksi koridor di sepanjang rute secara geografis.")

    all_corridors = sorted(df_all['corridor'].tolist())
    default_orig  = all_corridors.index('Pluit-Muara Baru') if 'Pluit-Muara Baru' in all_corridors else 0
    default_dest  = all_corridors.index('TB Simatupang')    if 'TB Simatupang'    in all_corridors else 5

    col_orig, col_dest = st.columns(2)
    with col_orig:
        origin_corr = st.selectbox("📍 Koridor Asal", all_corridors,
                                   index=default_orig, key="origin_corr")
    with col_dest:
        dest_corr = st.selectbox("🏁 Koridor Tujuan", all_corridors,
                                 index=default_dest, key="dest_corr")

    st.divider()

    if origin_corr == dest_corr:
        st.warning("⚠️ Pilih koridor yang berbeda untuk asal dan tujuan.")
    else:
        orig = df_all[df_all['corridor'] == origin_corr].iloc[0]
        dest = df_all[df_all['corridor'] == dest_corr].iloc[0]

        # ── Find corridors along the route ───────────────────────────────────────
        dx   = dest['lon'] - orig['lon']
        dy   = dest['lat'] - orig['lat']
        dist = (dx**2 + dy**2) ** 0.5

        # Adaptive buffer: scales with route length (min ~2.2 km)
        BUFFER   = max(0.020, dist * 0.40)
        MAX_PERP = max(0.018, dist * 0.28)  # perpendicular tolerance

        min_lat = min(orig['lat'], dest['lat']) - BUFFER
        max_lat = max(orig['lat'], dest['lat']) + BUFFER
        min_lon = min(orig['lon'], dest['lon']) - BUFFER
        max_lon = max(orig['lon'], dest['lon']) + BUFFER

        route_df = df_all[
            (df_all['lat'] >= min_lat) & (df_all['lat'] <= max_lat) &
            (df_all['lon'] >= min_lon) & (df_all['lon'] <= max_lon)
        ].copy()

        if dist > 0:
            # Perpendicular distance from each corridor to the origin→dest line
            def _perp(row):
                t = max(0.0, min(1.0,
                    ((row['lon'] - orig['lon']) * dx +
                     (row['lat'] - orig['lat']) * dy) / dist**2
                ))
                return (((row['lon'] - orig['lon'] - t * dx)**2 +
                         (row['lat'] - orig['lat'] - t * dy)**2) ** 0.5)

            route_df['_perp'] = route_df.apply(_perp, axis=1)
            route_df['_proj'] = (
                (route_df['lon'] - orig['lon']) * dx +
                (route_df['lat'] - orig['lat']) * dy
            ) / dist

            # Keep only corridors close to the route line, sorted by position
            route_df = (route_df[route_df['_perp'] <= MAX_PERP]
                        .sort_values('_proj')
                        .drop(columns=['_perp', '_proj']))

        macet_rt  = route_df[route_df['live_level'] == 'Macet']
        safe_rt   = route_df[route_df['live_level'] == 'Lancar'].sort_values('prob_macet')
        sedang_rt = route_df[route_df['live_level'] == 'Sedang']

        # ── Map + Table ──────────────────────────────────────────────────────────
        col_map2, col_tbl2 = st.columns([1.2, 1])

        with col_map2:
            st.markdown("**Peta Rute**")
            fig_r, ax_r = plt.subplots(figsize=(7, 6), facecolor=T['fig_bg'])
            ax_r.set_facecolor(T['ax_bg'])

            # Dashed line origin → destination
            ax_r.plot([orig['lon'], dest['lon']], [orig['lat'], dest['lat']],
                      '--', color=T['label'], alpha=0.45, linewidth=1.5, zorder=1)

            # Intermediate corridors
            for _, row in route_df.iterrows():
                if row['corridor'] in (origin_corr, dest_corr):
                    continue
                ax_r.scatter(row['lon'], row['lat'],
                             c=color_map[row['live_level']], s=110, alpha=0.85,
                             edgecolors=T['bg0'], linewidth=0.5, zorder=3)
                ax_r.annotate(row['corridor'][:10], (row['lon'], row['lat']),
                              fontsize=5, color=T['label'], ha='center', va='bottom',
                              xytext=(0, 5), textcoords='offset points')

            # Origin (blue star) and destination (green star)
            ax_r.scatter(orig['lon'], orig['lat'], c='#3498db', s=220,
                         marker='*', zorder=5, edgecolors=T['bg0'], linewidth=0.5)
            ax_r.scatter(dest['lon'], dest['lat'], c='#2ecc71', s=220,
                         marker='*', zorder=5, edgecolors=T['bg0'], linewidth=0.5)
            ax_r.annotate(f"ASAL\n{origin_corr[:12]}", (orig['lon'], orig['lat']),
                          fontsize=6, color='#3498db', ha='center', va='top',
                          xytext=(0, -8), textcoords='offset points', fontweight='bold')
            ax_r.annotate(f"TUJUAN\n{dest_corr[:12]}", (dest['lon'], dest['lat']),
                          fontsize=6, color='#2ecc71', ha='center', va='top',
                          xytext=(0, -8), textcoords='offset points', fontweight='bold')

            ax_r.set_xlabel('Longitude', color=T['label'], fontsize=7)
            ax_r.set_ylabel('Latitude', color=T['label'], fontsize=7)
            ax_r.tick_params(colors=T['tick'])
            for spine in ax_r.spines.values():
                spine.set_edgecolor(T['border'])
            ax_r.legend(handles=[
                mpatches.Patch(color='#e74c3c', label=f'Macet ({len(macet_rt)})'),
                mpatches.Patch(color='#f39c12', label=f'Sedang ({len(sedang_rt)})'),
                mpatches.Patch(color='#2ecc71', label=f'Lancar ({len(safe_rt)})'),
            ], loc='upper left', facecolor=T['legend_bg'], labelcolor=T['legend_fg'],
               edgecolor=T['border'], fontsize=7)
            ax_r.set_title(f'{origin_corr[:14]} → {dest_corr[:14]}',
                           color=T['title'], fontsize=9, fontweight='600')
            st.pyplot(fig_r, use_container_width=True)
            plt.close()

        with col_tbl2:
            st.markdown(f"**Koridor di Sepanjang Rute** ({len(route_df)} terdeteksi)")
            tbl_r = route_df[['corridor','zone','live_level','live_speed','prob_macet']].copy()
            tbl_r['Status']   = tbl_r['live_level'].map(emoji_map) + ' ' + tbl_r['live_level']
            tbl_r['km/h']     = tbl_r['live_speed'].round(1)
            tbl_r['P(Macet)'] = (tbl_r['prob_macet']*100).round(0).astype(int).astype(str) + '%'
            # Mark origin/destination
            tbl_r['Koridor'] = tbl_r['corridor'].apply(
                lambda c: f"📍 {c}" if c == origin_corr else (f"🏁 {c}" if c == dest_corr else c)
            )
            st.dataframe(tbl_r[['Koridor','zone','Status','km/h','P(Macet)']],
                         hide_index=True, height=320, use_container_width=True)

        # ── Recommendation ───────────────────────────────────────────────────────
        st.divider()
        st.subheader("📋 Rekomendasi SIGAP-ID")

        col_av, col_us = st.columns(2)
        with col_av:
            if len(macet_rt) > 0:
                st.error(f"🚫 **Hindari {len(macet_rt)} Koridor Macet**")
                for _, r in macet_rt.iterrows():
                    st.markdown(f"- **{r['corridor']}** ({r['zone']}) — "
                                f"{r['live_speed']:.0f} km/h | P(Macet): {r['prob_macet']*100:.0f}%")
            else:
                st.success("✅ Tidak ada koridor macet di rute ini.")

        with col_us:
            if len(safe_rt) > 0:
                st.success(f"✅ **Gunakan {len(safe_rt)} Koridor Aman**")
                for _, r in safe_rt.head(5).iterrows():
                    st.markdown(f"- **{r['corridor']}** ({r['zone']}) — "
                                f"{r['live_speed']:.0f} km/h | P(Macet): {r['prob_macet']*100:.0f}%")
            elif len(sedang_rt) > 0:
                st.warning(f"⚠️ **Koridor Tersedia (Sedang)**")
                for _, r in sedang_rt.head(5).iterrows():
                    st.markdown(f"- **{r['corridor']}** ({r['zone']}) — "
                                f"{r['live_speed']:.0f} km/h")
            else:
                st.warning("⚠️ Tidak ada koridor lancar di area ini saat ini.")

        # Time savings estimate
        SEGMENT_KM  = 4.0
        avg_m_spd   = macet_rt['live_speed'].mean()  if len(macet_rt)  > 0 else 7.0
        avg_s_spd   = safe_rt['live_speed'].mean()   if len(safe_rt)   > 0 else 35.0
        savings     = len(macet_rt) * max(0, SEGMENT_KM/avg_m_spd*60 - SEGMENT_KM/avg_s_spd*60)

        st.divider()
        ms1, ms2, ms3 = st.columns(3)
        ms1.metric("🗺️ Koridor di Rute",      len(route_df))
        ms2.metric("🚫 Harus Dihindari",       len(macet_rt))
        ms3.metric("⏱️ Estimasi Penghematan",
                   f"~{savings:.0f} menit" if savings > 1 else "Rute Normal",
                   "vs lewat koridor macet"  if savings > 1 else "")
        st.caption(
            "ℹ️ Koridor dideteksi secara geografis (bounding box asal→tujuan + buffer 5km). "
            "Estimasi waktu: asumsi segmen 4 km per koridor. "
            "Navigasi turn-by-turn via Azure Maps tersedia di roadmap Phase 1."
        )

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — Prediksi 6 Jam & Analisis
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.subheader("📈 Prediksi 6 Jam Ke Depan — Simulasi Koridor Terpilih")

    selected_corridor = st.selectbox(
        "Pilih koridor:",
        df_all.sort_values('prob_macet', ascending=False)['corridor'].tolist(),
        index=0,
    )

    if selected_corridor:
        hours_ahead  = list(range(hour_sim, hour_sim + 7))
        rain_profile = [max(0, rainfall_sim * (1 - 0.08 * i)) for i in range(7)]

        spds, lvls, prbs = [], [], []
        for h, r in zip(hours_ahead, rain_profile):
            s, l, p = lookup_corridor(lookup, selected_corridor, h % 24, is_weekend, r) \
                      if use_lookup else (20.0, 'Sedang', 0.3)
            spds.append(s); lvls.append(l); prbs.append(p)

        fig2, axes2 = plt.subplots(1, 2, figsize=(12, 4), facecolor=T['fig_bg'])
        fig2.patch.set_facecolor(T['bg1'])
        hour_labels = [f'{h%24:02d}:00' for h in hours_ahead]

        for ax in axes2:
            ax.set_facecolor(T['ax_bg'])
            ax.tick_params(colors=T['label'], labelsize=7)
            ax.xaxis.label.set_color(T['title'])
            ax.yaxis.label.set_color(T['title'])
            ax.title.set_color(T['title'])
            for spine in ax.spines.values():
                spine.set_edgecolor(T['border'])

        axes2[0].fill_between(range(len(hours_ahead)), rain_profile, alpha=0.4, color='steelblue')
        axes2[0].plot(range(len(hours_ahead)), rain_profile, 'o-', color='steelblue', markersize=6)
        axes2[0].set_xticks(range(len(hours_ahead)))
        axes2[0].set_xticklabels(hour_labels, rotation=30, color=T['label'])
        axes2[0].set_ylabel('Rainfall (mm/hr)', color=T['label'], fontsize=8)
        src_label = "BMKG Live (Decay Forecast)" if bmkg_live else "Simulasi Manual (Decay)"
        axes2[0].set_title(f'Input: {src_label}', fontweight='bold')

        axes2[1].bar(range(len(hours_ahead)), [p*100 for p in prbs],
                     color=[color_map[l] for l in lvls], edgecolor=T['bg0'], alpha=0.85)
        axes2[1].axhline(60, color='red', linestyle='--', alpha=0.7, linewidth=1.5)
        axes2[1].set_xticks(range(len(hours_ahead)))
        axes2[1].set_xticklabels(hour_labels, rotation=30, color=T['label'])
        axes2[1].set_ylabel('P(Macet) %', color=T['label'], fontsize=8)
        axes2[1].set_ylim(0, 105)
        axes2[1].set_title(f'Output: Prediksi Risiko — {selected_corridor}', fontweight='bold')
        for i, (p, s) in enumerate(zip(prbs, spds)):
            axes2[1].text(i, p*100 + 2, f'{s:.0f} km/h', ha='center', fontsize=7, color=T['legend_fg'])

        plt.tight_layout()
        st.pyplot(fig2, use_container_width=True)
        plt.close()

    # Explainability (Dishub/BPBD only)
    if user_mode == "Dishub / BPBD":
        st.divider()
        st.subheader("🔍 Feature Explainability")
        exp_path = "data/processed/plot_08_explainability.png"
        if os.path.exists(exp_path):
            st.image(exp_path, caption="Feature importance & partial dependence P(Macet) vs rainfall")
        else:
            st.info("Jalankan notebook untuk menghasilkan explainability plot.")
        st.caption("""
        **Interpretasi:**
        - `speed_lag_1h` tinggi → risiko macet turun (kecepatan sebelumnya tinggi)
        - `rain_roll_3h` tinggi → risiko macet naik (akumulasi hujan)
        - `flood_risk` tinggi + `rain_roll_3h` → kombinasi paling berbahaya
        """)

# ── Footer ─────────────────────────────────────────────────────────────────────
st.divider()
st.caption("""
**SIGAP-ID** | AI Impact Challenge Datathon 2026 | Urban Resilience & Smart City
Data: BMKG API (Live) · Open Data Jakarta · BNPB DIBI · Pantau Banjir Jakarta
Model: XGBoost (F1=0.9549) + K-Means k=5 | Azure App Service B1 — Southeast Asia
GitHub: github.com/bryanjeshua/sigap-id
""")
