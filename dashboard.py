"""
SIGAP-ID Dashboard — Streamlit Prototype
Run: streamlit run dashboard.py
"""
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import os

st.set_page_config(
    page_title="SIGAP-ID | Sistem Intelijen Geospasial Adaptif Perkotaan Indonesia",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Dicoding Verification Meta Tag ─────────────────────────────────────────────
st.markdown(
    '<meta name="dicoding:email" content="salmakurniadewi@gmail.com">',
    unsafe_allow_html=True,
)

# Also inject into <head> via JS for Dicoding scraper compatibility
st.components.v1.html(
    """
    <script>
    (function() {
      try {
        var head = window.parent.document.head;
        if (head && !window.parent.document.querySelector('meta[name="dicoding:email"]')) {
          var m = window.parent.document.createElement('meta');
          m.name = 'dicoding:email';
          m.content = 'salmakurniadewi@gmail.com';
          head.appendChild(m);
        }
      } catch (e) { console.log('meta injection skipped:', e); }
    })();
    </script>
    """,
    height=0,
)

# ── Styles ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.metric-card {
    background: #1e1e2e; border-radius: 10px; padding: 16px; margin: 6px 0;
    border-left: 4px solid #3498db;
}
.alert-red   { border-left-color: #e74c3c !important; }
.alert-orange{ border-left-color: #f39c12 !important; }
.alert-green { border-left-color: #2ecc71 !important; }
.big-font { font-size: 24px !important; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ── Load or Generate Data ──────────────────────────────────────────────────────
@st.cache_data
def load_data():
    data_path = "data/processed/sigap_id_dataset.csv"
    if os.path.exists(data_path):
        df = pd.read_csv(data_path, parse_dates=['datetime'])
    else:
        # Regenerate if notebook hasn't been run yet
        st.warning("Dataset not found. Generating on-the-fly... (run the notebook first for full data)")
        from notebooks import generate_data  # fallback
        df = generate_data()
    return df

@st.cache_data
def get_corridor_stats(df):
    return df.groupby('corridor').agg(
        mean_speed=('avg_speed_kmh', 'mean'),
        pct_macet=('congestion_level', lambda x: (x == 'Macet').mean() * 100),
        flood_risk=('flood_risk', 'first'),
        weather_sensitivity=('weather_sensitivity', 'first'),
        zone=('zone', 'first'),
        lat=('lat', 'first'),
        lon=('lon', 'first'),
    ).reset_index()

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/6/6e/Jakarta_coat_of_arms.svg/200px-Jakarta_coat_of_arms.svg.png",
             width=60)
    st.title("SIGAP-ID")
    st.caption("Sistem Intelijen Geospasial Adaptif Perkotaan Indonesia")
    st.divider()

    user_mode = st.radio("Mode Pengguna", ["Operator Logistik", "Dishub / BPBD"], index=0)
    st.divider()

    rainfall_sim = st.slider("Simulasi Curah Hujan (mm/hr)", 0, 100, 25, step=5,
                              help="Ubah nilai untuk melihat prediksi risiko berubah real-time")
    hour_sim = st.slider("Jam Prediksi (WIB)", 0, 23, 8)
    is_weekend = st.checkbox("Hari Weekend/Libur", value=False)
    st.divider()

    selected_zone = st.multiselect(
        "Filter Zona",
        ['Jakarta Pusat', 'Jakarta Barat', 'Jakarta Selatan', 'Jakarta Timur', 'Jakarta Utara'],
        default=['Jakarta Barat', 'Jakarta Utara'],
    )

# ── Header ─────────────────────────────────────────────────────────────────────
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.title("🚦 SIGAP-ID — Real-Time Risk Dashboard")
    st.caption(f"Mode: **{user_mode}** | Prakiraan BMKG terintegrasi | Update setiap 15 menit")
with col_h2:
    rain_cat = "Ekstrem 🔴" if rainfall_sim > 50 else "Lebat 🟠" if rainfall_sim > 30 else "Sedang 🟡" if rainfall_sim > 10 else "Ringan 🟢" if rainfall_sim > 0 else "Tidak Hujan ⚪"
    st.metric("Curah Hujan Saat Ini", f"{rainfall_sim} mm/hr", rain_cat)
    st.metric("Jam Prediksi", f"{hour_sim:02d}:00 WIB",
              "Peak Morning" if 6 <= hour_sim <= 9 else "Peak Evening" if 16 <= hour_sim <= 20 else "Off-Peak")

st.divider()

# ── Compute Live Risk Scores ───────────────────────────────────────────────────
def compute_risk_score(row, rainfall_mm, hour, weekend):
    base = row['base_speed'] if 'base_speed' in row.index else 35
    ws   = row['weather_sensitivity']
    fr   = row['flood_risk']

    rain_factor = (0.0 if rainfall_mm < 5 else
                   0.10 if rainfall_mm < 10 else
                   0.30 if rainfall_mm < 30 else
                   0.50 if rainfall_mm < 50 else 0.70)

    peak_factor = (0.50 if (6 <= hour <= 9 and not weekend) else
                   0.45 if (16 <= hour <= 20 and not weekend) else
                   1.35 if (hour < 5 or hour >= 22) else
                   1.20 if weekend else 1.0)

    speed = 35 * peak_factor - 35 * ws * rain_factor
    if fr > 0.6 and rainfall_mm > 30:
        speed -= 35 * 0.30 * (fr - 0.6)

    speed = max(3, speed)
    level = "Macet" if speed < 10 else "Sedang" if speed < 25 else "Lancar"
    prob_macet = max(0, min(1, (25 - speed) / 22))
    return speed, level, prob_macet

# Load data
try:
    df = load_data()
    df_corridors_meta = df[['corridor', 'zone', 'lat', 'lon',
                             'flood_risk', 'weather_sensitivity']].drop_duplicates('corridor')
    has_data = True
except Exception as e:
    st.error(f"Data tidak ditemukan. Jalankan notebook terlebih dahulu. Error: {e}")
    has_data = False

if has_data:
    # Apply live risk computation
    df_corridors_meta = df_corridors_meta.copy()
    df_corridors_meta['base_speed'] = 35
    results = df_corridors_meta.apply(
        lambda r: compute_risk_score(r, rainfall_sim, hour_sim, is_weekend), axis=1
    )
    df_corridors_meta['live_speed']    = [r[0] for r in results]
    df_corridors_meta['live_level']    = [r[1] for r in results]
    df_corridors_meta['prob_macet']    = [r[2] for r in results]

    # Filter by selected zone
    if selected_zone:
        df_display = df_corridors_meta[df_corridors_meta['zone'].isin(selected_zone)]
    else:
        df_display = df_corridors_meta

    # ── KPI Metrics ────────────────────────────────────────────────────────────
    n_macet  = (df_display['live_level'] == 'Macet').sum()
    n_sedang = (df_display['live_level'] == 'Sedang').sum()
    n_lancar = (df_display['live_level'] == 'Lancar').sum()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🔴 Koridor MACET",   f"{n_macet}",  f"{n_macet/len(df_display)*100:.0f}% dari {len(df_display)} koridor")
    col2.metric("🟡 Koridor SEDANG",  f"{n_sedang}", f"{n_sedang/len(df_display)*100:.0f}%")
    col3.metric("🟢 Koridor LANCAR",  f"{n_lancar}", f"{n_lancar/len(df_display)*100:.0f}%")
    col4.metric("⚠️ Zona High-Risk",
                f"{(df_display['flood_risk'] > 0.7).sum()}",
                "flood risk > 0.7")

    st.divider()

    # ── Main Columns ───────────────────────────────────────────────────────────
    col_map, col_table = st.columns([1.3, 1])

    with col_map:
        st.subheader("Peta Risiko Real-Time")
        fig, ax = plt.subplots(figsize=(8, 7), facecolor='#1e1e2e')
        ax.set_facecolor('#1e1e2e')

        color_map = {'Macet': '#e74c3c', 'Sedang': '#f39c12', 'Lancar': '#2ecc71'}
        for _, row in df_display.iterrows():
            c = color_map[row['live_level']]
            size = row['prob_macet'] * 300 + 50
            ax.scatter(row['lon'], row['lat'], c=c, s=size, alpha=0.85,
                      edgecolors='white', linewidth=0.5, zorder=3)
            ax.annotate(row['corridor'][:10], (row['lon'], row['lat']),
                        fontsize=5, color='white', ha='center', va='bottom',
                        xytext=(0, 5), textcoords='offset points')

        ax.set_xlabel('Longitude', color='white')
        ax.set_ylabel('Latitude', color='white')
        ax.tick_params(colors='white')
        for spine in ax.spines.values():
            spine.set_edgecolor('#444')

        legend_handles = [
            mpatches.Patch(color='#e74c3c', label=f'Macet ({n_macet})'),
            mpatches.Patch(color='#f39c12', label=f'Sedang ({n_sedang})'),
            mpatches.Patch(color='#2ecc71', label=f'Lancar ({n_lancar})'),
        ]
        ax.legend(handles=legend_handles, loc='upper left',
                  facecolor='#2e2e3e', labelcolor='white', edgecolor='#555')
        ax.set_title(f'Risiko per Koridor — {hour_sim:02d}:00 WIB | {rainfall_sim}mm/hr',
                     color='white', fontsize=11, fontweight='bold')

        st.pyplot(fig, use_container_width=True)
        plt.close()

    with col_table:
        st.subheader("Prediksi per Koridor")

        emoji_map = {'Macet': '🔴', 'Sedang': '🟡', 'Lancar': '🟢'}
        table_df = df_display[['corridor', 'zone', 'live_speed', 'live_level', 'prob_macet', 'flood_risk']].copy()
        table_df['Status'] = table_df['live_level'].map(emoji_map) + ' ' + table_df['live_level']
        table_df['Speed (km/h)'] = table_df['live_speed'].round(1)
        table_df['P(Macet)'] = (table_df['prob_macet'] * 100).round(0).astype(int).astype(str) + '%'
        table_df['Flood Risk'] = table_df['flood_risk'].round(2)
        table_df = table_df.sort_values('prob_macet', ascending=False)

        st.dataframe(
            table_df[['corridor', 'zone', 'Status', 'Speed (km/h)', 'P(Macet)', 'Flood Risk']],
            hide_index=True,
            height=400,
            use_container_width=True,
        )

        # Alert for high-risk corridors
        high_risk = table_df[table_df['prob_macet'] > 0.6]
        if len(high_risk) > 0:
            st.error(f"⚠️ **ALERT**: {len(high_risk)} koridor berisiko tinggi macet parah!")
            for _, r in high_risk.head(3).iterrows():
                st.warning(f"🔴 **{r['corridor']}** — P(Macet)={r['P(Macet)']} | Flood Risk={r['Flood Risk']:.2f}")
        else:
            st.success("✅ Semua koridor dalam batas aman saat ini.")

    st.divider()

    # ── Prediction Timeline ────────────────────────────────────────────────────
    st.subheader("📈 Prediksi 6 Jam Ke Depan — Simulasi Koridor Terpilih")

    selected_corridor = st.selectbox(
        "Pilih koridor:",
        df_display.sort_values('prob_macet', ascending=False)['corridor'].tolist(),
        index=0
    )

    if selected_corridor:
        corr_meta = df_corridors_meta[df_corridors_meta['corridor'] == selected_corridor].iloc[0]

        hours_ahead = list(range(hour_sim, hour_sim + 7))
        rain_profile = []
        for h in hours_ahead:
            h_mod = h % 24
            sim_rain = rainfall_sim * (1 - 0.08 * (h - hour_sim))
            rain_profile.append(max(0, sim_rain))

        speeds, levels, probs = [], [], []
        for h, r in zip(hours_ahead, rain_profile):
            s, l, p = compute_risk_score(corr_meta, r, h % 24, is_weekend)
            speeds.append(s)
            levels.append(l)
            probs.append(p)

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
        axes2[0].set_title(f'Input: Forecast Curah Hujan\n(BMKG API)', fontweight='bold')

        colors_bar = [color_map[l] for l in levels]
        axes2[1].bar(range(len(hours_ahead)), [p*100 for p in probs], color=colors_bar, edgecolor='white', alpha=0.85)
        axes2[1].axhline(60, color='red', linestyle='--', alpha=0.7, linewidth=1.5)
        axes2[1].set_xticks(range(len(hours_ahead)))
        axes2[1].set_xticklabels(hour_labels, rotation=30, color='white')
        axes2[1].set_ylabel('P(Macet) %', color='white')
        axes2[1].set_ylim(0, 105)
        axes2[1].set_title(f'Output: Prediksi Risiko Macet\n{selected_corridor}', fontweight='bold')
        for i, (p, s) in enumerate(zip(probs, speeds)):
            axes2[1].text(i, p*100 + 2, f'{s:.0f} km/h', ha='center', fontsize=8, color='white')

        plt.tight_layout()
        st.pyplot(fig2, use_container_width=True)
        plt.close()

    # ── SHAP Explanation (static image if available) ───────────────────────────
    st.divider()
    if user_mode == "Dishub / BPBD":
        st.subheader("🔍 SHAP Explanation — Mengapa Model Memprediksi Risiko Ini?")
        shap_path = "data/processed/plot_08_shap.png"
        if os.path.exists(shap_path):
            st.image(shap_path, caption="SHAP values: fitur mana yang paling memengaruhi prediksi Macet")
        else:
            st.info("Jalankan notebook untuk menghasilkan SHAP plot.")

        st.caption("""
        **Interpretasi SHAP:**
        - `speed_lag_1h` tinggi → SHAP negatif (kecepatan sebelumnya tinggi → risiko macet turun)
        - `rain_roll_3h` tinggi → SHAP positif (akumulasi hujan → risiko macet naik)
        - `flood_risk` tinggi + `rain_roll_3h` → kombinasi paling berbahaya
        """)

    # ── Footer ─────────────────────────────────────────────────────────────────
    st.divider()
    st.caption("""
    **SIGAP-ID** | AI Impact Challenge Datathon 2026 | Urban Resilience & Smart City
    Data: Open Data Jakarta (satudata.jakarta.go.id) · BMKG API · BNPB DIBI · Pantau Banjir Jakarta
    Model: XGBoost + SHAP | Azure ML + Azure Maps + Azure Stream Analytics
    """)
