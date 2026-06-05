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

st.set_page_config(
    page_title="SIGAP-ID | Sistem Intelijen Geospasial Adaptif Perkotaan Indonesia",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.metric-card {
    background: #1e1e2e; border-radius: 10px; padding: 16px; margin: 6px 0;
    border-left: 4px solid #3498db;
}
.alert-red   { border-left-color: #e74c3c !important; }
.alert-orange{ border-left-color: #f39c12 !important; }
.alert-green { border-left-color: #2ecc71 !important; }
</style>
""", unsafe_allow_html=True)

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
            station = data.get('lokasi', 'Jakarta Pusat')
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
    st.image(
        "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6e/Jakarta_coat_of_arms.svg/200px-Jakarta_coat_of_arms.svg.png",
        width=60,
    )
    st.title("SIGAP-ID")
    st.caption("Sistem Intelijen Geospasial Adaptif Perkotaan Indonesia")
    st.divider()

    user_mode = st.radio("Mode Pengguna", ["Operator Logistik", "Dishub / BPBD"], index=0)
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
    st.title("🚦 SIGAP-ID — Real-Time Risk Dashboard")
    data_src = "🟢 BMKG Live" if bmkg_live else "⚪ Simulasi Manual"
    st.caption(f"Mode: **{user_mode}** | Sumber cuaca: **{data_src}** | Update setiap 15 menit")
with col_h2:
    rain_cat = ("Ekstrem 🔴" if rainfall_sim > 50 else
                "Lebat 🟠"  if rainfall_sim > 30 else
                "Sedang 🟡" if rainfall_sim > 10 else
                "Ringan 🟢" if rainfall_sim > 0  else "Tidak Hujan ⚪")
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
        fig, ax = plt.subplots(figsize=(8, 7), facecolor='#1e1e2e')
        ax.set_facecolor('#1e1e2e')
        for _, row in df_display.iterrows():
            c = color_map[row['live_level']]
            ax.scatter(row['lon'], row['lat'], c=c, s=row['prob_macet']*300+50,
                       alpha=0.85, edgecolors='white', linewidth=0.5, zorder=3)
            ax.annotate(row['corridor'][:10], (row['lon'], row['lat']),
                        fontsize=5, color='white', ha='center', va='bottom',
                        xytext=(0, 5), textcoords='offset points')
        ax.set_xlabel('Longitude', color='white')
        ax.set_ylabel('Latitude', color='white')
        ax.tick_params(colors='white')
        for spine in ax.spines.values():
            spine.set_edgecolor('#444')
        ax.legend(handles=[
            mpatches.Patch(color='#e74c3c', label=f'Macet ({n_macet})'),
            mpatches.Patch(color='#f39c12', label=f'Sedang ({n_sedang})'),
            mpatches.Patch(color='#2ecc71', label=f'Lancar ({n_lancar})'),
        ], loc='upper left', facecolor='#2e2e3e', labelcolor='white', edgecolor='#555')
        ax.set_title(f'Risiko per Koridor — {hour_sim:02d}:00 WIB | {rainfall_sim}mm/hr',
                     color='white', fontsize=11, fontweight='bold')
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
    st.caption("Pilih zona asal dan tujuan untuk melihat kondisi koridor dan rekomendasi rute aman.")

    col_orig, col_dest = st.columns(2)
    with col_orig:
        origin_zone = st.selectbox("📍 Zona Asal", ZONES, index=1,
                                   key="origin_zone")
    with col_dest:
        dest_zone = st.selectbox("🏁 Zona Tujuan", ZONES, index=0,
                                 key="dest_zone")

    st.divider()

    # Corridors in each zone
    df_orig = df_all[df_all['zone'] == origin_zone].copy().sort_values('prob_macet', ascending=False)
    df_dest = df_all[df_all['zone'] == dest_zone].copy().sort_values('prob_macet', ascending=False)

    def zone_risk_table(df_zone):
        t = df_zone[['corridor','live_speed','live_level','prob_macet','flood_risk']].copy()
        t['Status']       = t['live_level'].map(emoji_map) + ' ' + t['live_level']
        t['Speed (km/h)'] = t['live_speed'].round(1)
        t['P(Macet)']     = (t['prob_macet']*100).round(0).astype(int).astype(str) + '%'
        t['Flood Risk']   = t['flood_risk'].round(2)
        return t[['corridor','Status','Speed (km/h)','P(Macet)','Flood Risk']]

    if origin_zone == dest_zone:
        st.info("ℹ️ Zona asal dan tujuan sama — menampilkan kondisi seluruh koridor dalam zona.")
        st.dataframe(zone_risk_table(df_orig), hide_index=True, use_container_width=True)
    else:
        c_orig, c_dest = st.columns(2)
        with c_orig:
            st.markdown(f"**📍 {origin_zone}** — {len(df_orig)} koridor")
            st.dataframe(zone_risk_table(df_orig), hide_index=True,
                         height=250, use_container_width=True)
        with c_dest:
            st.markdown(f"**🏁 {dest_zone}** — {len(df_dest)} koridor")
            st.dataframe(zone_risk_table(df_dest), hide_index=True,
                         height=250, use_container_width=True)

    st.divider()
    st.subheader("📋 Rekomendasi SIGAP-ID")

    # Combine origin + destination corridors for analysis
    df_route = pd.concat([df_orig, df_dest]).drop_duplicates('corridor')
    macet_corridors  = df_route[df_route['live_level'] == 'Macet']
    safe_corridors   = df_route[df_route['live_level'] == 'Lancar'].sort_values('prob_macet')
    sedang_corridors = df_route[df_route['live_level'] == 'Sedang']

    # Time estimate: assume avg 4km per corridor segment
    SEGMENT_KM = 4.0
    avg_macet_spd = macet_corridors['live_speed'].mean() if len(macet_corridors) > 0 else 7.0
    avg_safe_spd  = safe_corridors['live_speed'].mean()  if len(safe_corridors)  > 0 else 35.0
    time_macet    = SEGMENT_KM / avg_macet_spd * 60
    time_safe     = SEGMENT_KM / avg_safe_spd  * 60
    savings_per   = max(0, time_macet - time_safe)
    total_savings = len(macet_corridors) * savings_per

    col_avoid, col_use = st.columns(2)

    with col_avoid:
        if len(macet_corridors) > 0:
            st.error(f"🚫 **Hindari {len(macet_corridors)} Koridor Macet**")
            for _, r in macet_corridors.iterrows():
                st.markdown(f"- **{r['corridor']}** — {r['live_speed']:.0f} km/h | "
                            f"P(Macet): {r['prob_macet']*100:.0f}%")
        else:
            st.success("✅ Tidak ada koridor macet di rute ini saat ini.")

    with col_use:
        if len(safe_corridors) > 0:
            st.success(f"✅ **Gunakan {len(safe_corridors)} Koridor Aman**")
            for _, r in safe_corridors.head(5).iterrows():
                st.markdown(f"- **{r['corridor']}** — {r['live_speed']:.0f} km/h | "
                            f"P(Macet): {r['prob_macet']*100:.0f}%")
        elif len(sedang_corridors) > 0:
            st.warning(f"⚠️ **Koridor Tersedia (Sedang)**")
            for _, r in sedang_corridors.head(5).iterrows():
                st.markdown(f"- **{r['corridor']}** — {r['live_speed']:.0f} km/h | "
                            f"P(Macet): {r['prob_macet']*100:.0f}%")
        else:
            st.warning("⚠️ Tidak ada koridor lancar yang tersedia di zona ini.")

    # Summary metrics
    st.divider()
    ms1, ms2, ms3 = st.columns(3)
    ms1.metric("🚫 Koridor Harus Dihindari", len(macet_corridors))
    ms2.metric("✅ Koridor Alternatif Aman",  len(safe_corridors))
    if total_savings > 1:
        ms3.metric("⏱️ Estimasi Penghematan Waktu",
                   f"~{total_savings:.0f} menit",
                   f"vs rute via koridor macet")
    else:
        ms3.metric("⏱️ Estimasi Waktu Tempuh", "Normal", "Tidak ada kemacetan")

    st.caption(
        "ℹ️ Estimasi berdasarkan kecepatan rata-rata per koridor dan asumsi segmen 4 km. "
        "Untuk navigasi turn-by-turn, gunakan Azure Maps Route API (roadmap Phase 1)."
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

        fig2, axes2 = plt.subplots(1, 2, figsize=(12, 4), facecolor='#1e1e2e')
        fig2.patch.set_facecolor('#1e1e2e')
        hour_labels = [f'{h%24:02d}:00' for h in hours_ahead]

        for ax in axes2:
            ax.set_facecolor('#2e2e3e')
            ax.tick_params(colors='white')
            ax.xaxis.label.set_color('white')
            ax.yaxis.label.set_color('white')
            ax.title.set_color('white')
            for spine in ax.spines.values():
                spine.set_edgecolor('#444')

        axes2[0].fill_between(range(len(hours_ahead)), rain_profile, alpha=0.4, color='steelblue')
        axes2[0].plot(range(len(hours_ahead)), rain_profile, 'o-', color='steelblue', markersize=6)
        axes2[0].set_xticks(range(len(hours_ahead)))
        axes2[0].set_xticklabels(hour_labels, rotation=30, color='white')
        axes2[0].set_ylabel('Rainfall (mm/hr)', color='white')
        src_label = "BMKG Live (Decay Forecast)" if bmkg_live else "Simulasi Manual (Decay)"
        axes2[0].set_title(f'Input: {src_label}', fontweight='bold')

        axes2[1].bar(range(len(hours_ahead)), [p*100 for p in prbs],
                     color=[color_map[l] for l in lvls], edgecolor='white', alpha=0.85)
        axes2[1].axhline(60, color='red', linestyle='--', alpha=0.7, linewidth=1.5)
        axes2[1].set_xticks(range(len(hours_ahead)))
        axes2[1].set_xticklabels(hour_labels, rotation=30, color='white')
        axes2[1].set_ylabel('P(Macet) %', color='white')
        axes2[1].set_ylim(0, 105)
        axes2[1].set_title(f'Output: Prediksi Risiko — {selected_corridor}', fontweight='bold')
        for i, (p, s) in enumerate(zip(prbs, spds)):
            axes2[1].text(i, p*100 + 2, f'{s:.0f} km/h', ha='center', fontsize=8, color='white')

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
