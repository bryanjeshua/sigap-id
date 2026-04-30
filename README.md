# SIGAP-ID

### Sistem Intelijen Geospasial Adaptif Perkotaan Indonesia
**Prediksi Kemacetan Berbasis Risiko Banjir & Cuaca untuk Optimasi Mobilitas Urban di Jabodetabek**

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org)
[![XGBoost](https://img.shields.io/badge/XGBoost-3.2-orange.svg)](https://xgboost.readthedocs.io)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28-red.svg)](https://streamlit.io)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> **AI Impact Challenge — Datathon 2026** · Topic: *Urban Resilience & Smart City*

---

## Problem

Jakarta dan kawasan Jabodetabek mengalami kerugian **Rp65–100 triliun per tahun** akibat kemacetan ([Kemenhub 2023](https://news.detik.com/berita/d-6795414/), [BMKG 2024](https://katadata.co.id/ekonomi-hijau/ekonomi-sirkular/670e27cecd2dc/)). Pemicu yang konsisten dan sering diabaikan: **banjir dan hujan deras**. Saat banjir menerjang titik strategis, pengemudi beralih rute massal tanpa panduan, memicu kemacetan kaskade.

**Belum ada sistem operasional yang mengintegrasikan prediksi cuaca + risiko banjir + pola lalu lintas untuk menghasilkan rekomendasi rute yang langsung executable.**

SIGAP-ID mengisi gap ini.

---

## Key Results

| Metric | Result | Target |
|---|---|---|
| **F1-Score (Weighted)** | **0.9543** | > 0.82 |
| **Weather-Sensitive Corridors** (r < -0.65) | **35 / 41** | identifikasi |
| **K-Means Silhouette** (k=5 zones) | 0.358 | > 0.30 |
| **Macet Class Recall** | 0.88 | > 0.70 |
| **Dataset Size** | 178,104 records | — |
| **Time Coverage** | Nov 2024 – Apr 2025 (rainy season) | — |
| **Corridors** | 41 jalan utama Jabodetabek | dokumentasi |

### Top 5 Most Weather-Sensitive Corridors

| Corridor | Zone | Pearson r |
|---|---|---|
| Pluit-Muara Baru | Jakarta Utara | < -0.65 |
| Tanah Abang | Jakarta Pusat | < -0.65 |
| Kalideres-Cengkareng | Jakarta Barat | < -0.65 |
| Sudirman-Thamrin | Jakarta Pusat | < -0.65 |
| MT Haryono | Jakarta Timur | < -0.65 |

*Konsisten dengan temuan [Yang et al. (2021), Sensors MDPI](https://www.mdpi.com/1424-8220/21/7/2405) tentang weather-sensitive roads di Jakarta.*

---

## Pipeline Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌──────────────┐    ┌──────────────┐
│  Data Sources   │ →  │  Feature Eng.    │ →  │  ML Models   │ →  │  Dashboard   │
├─────────────────┤    ├──────────────────┤    ├──────────────┤    ├──────────────┤
│ BMKG API        │    │ Lag features     │    │ XGBoost      │    │ Risk map     │
│ Open Data Jkt   │    │ Cyclical time    │    │ K-Means k=5  │    │ Predictions  │
│ BNPB DIBI       │    │ Flood proximity  │    │ Feature imp. │    │ Routing      │
│ Pantau Banjir   │    │ Rolling rainfall │    │              │    │ Alerts       │
└─────────────────┘    └──────────────────┘    └──────────────┘    └──────────────┘
        ↓                       ↓                      ↓                    ↓
   Azure Blob          Azure Stream Analytics   Azure ML Studio      Azure Maps SDK
```

---

## Quickstart

### Prerequisites
- Python 3.10+ (tested on 3.12)
- 4GB RAM minimum

### Installation
```bash
git clone https://github.com/bryanjeshua/sigap-id.git
cd sigap-id
pip install -r requirements.txt
```

### Run Analysis Notebook
```bash
jupyter notebook notebooks/SIGAP_ID_Analysis.ipynb
```
Generates: `data/processed/sigap_id_dataset.csv` + 9 visualization PNGs.

### Launch Dashboard
```bash
streamlit run dashboard.py
```
Opens at `http://localhost:8501` — interactive risk map with rainfall slider.

---

## Project Structure

```
sigap-id/
├── README.md                              ← this file
├── requirements.txt                       ← Python dependencies
├── dashboard.py                           ← Streamlit prototype
│
├── notebooks/
│   └── SIGAP_ID_Analysis.ipynb            ← Main analysis (17 cells)
│
└── data/
    └── processed/
        ├── sigap_id_dataset.csv           ← 178k records
        ├── plot_01_overview.png           ← Dataset overview
        ├── plot_02_rainfall.png           ← Rainfall patterns
        ├── plot_03_weather_sensitivity.png ← KEY: correlation analysis
        ├── plot_04_temporal.png           ← Peak hour + flood lead time
        ├── plot_05_elbow.png              ← K-Means elbow curve
        ├── plot_06_clustering.png         ← 5 risk zones geomap
        ├── plot_07_model_eval.png         ← Confusion matrix + importance
        ├── plot_08_explainability.png     ← Partial dependence
        └── plot_09_prediction_demo.png    ← 6-hour prediction demo
```

---

## Methodology

### Data Strategy
| Dataset | Source | Type |
|---|---|---|
| Kecepatan 41 Koridor | [Open Data Jakarta](https://satudata.jakarta.go.id) | Time-series + Geospasial |
| Prakiraan Cuaca BMKG | [api.bmkg.go.id](https://data.bmkg.go.id/prakiraan-cuaca/) | Real-time JSON API |
| Curah Hujan Historis | [BMKG Data Online](https://dataonline.bmkg.go.id) | Time-series per stasiun |
| Banjir Historis | [BNPB DIBI](https://dibi.bnpb.go.id) | Tabular + temporal |
| Pantau Banjir Jakarta | [pantaubanjir.jakarta.go.id](https://pantaubanjir.jakarta.go.id) | Real-time geospasial |
| Statistik Transportasi | [BPS DKI Jakarta](https://jakarta.bps.go.id) | Tabular tahunan |

> **Note:** Open Data Jakarta migrated to satudata.jakarta.go.id during development. Dataset schema (waktu, koridor, arah, kecepatan_target, capaian_kecepatan) confirmed from official resource. Synthetic data generated for this MVP is **calibrated against documented Jakarta patterns** from Yang et al. (2021) and TomTom Traffic Index 2024 for reproducibility.

### Feature Engineering
- **Cyclical time encoding** (sin/cos for hour, day, month) — captures periodic patterns
- **Lag features** (1h, 2h, 3h, 6h) for both rainfall and speed
- **Rolling means** (3h, 6h rainfall accumulation) — proxy for flood risk
- **Flood alert flag**: `flood_risk > 0.6 AND rain_roll_3h > 20mm`
- **Rainfall intensity bins**: Low / Medium / Heavy / Extreme (BMKG thresholds)

### Models
| Model | Purpose | Output |
|---|---|---|
| **XGBoost Classifier** | Klasifikasi 3-kelas | Lancar / Sedang / Macet per koridor per jam |
| **K-Means (k=5)** | Segmentasi zona risiko | 5 zona Jabodetabek |
| **Partial Dependence** | Explainability | P(Macet) vs rainfall per corridor |

### Evaluation
- **Time-based split**: Train Nov 2024–Mar 2025 / Test Apr 2025 (1 month holdout)
- **Class imbalance handled**: balanced sample weights via `sklearn.utils.class_weight`
- **27 input features** spanning rainfall, time, lag, geospatial dimensions

---

## Tech Stack

| Layer | Technology |
|---|---|
| Data Processing | `pandas`, `numpy`, `geopandas` |
| Machine Learning | `xgboost`, `scikit-learn` |
| Visualization | `matplotlib`, `seaborn` |
| Dashboard | `streamlit`, `plotly` |
| Geospatial | `folium`, `shapely` |
| **Production (proposal)** | Azure ML, Azure Maps, Azure Stream Analytics, Azure Anomaly Detector, Azure Blob |

---

## Use Case — Skenario Banjir Jakarta Barat

**Tanpa SIGAP-ID:** Operator logistik bergerak setelah macet terjadi → keterlambatan 3.5 jam, BBM boros 25%.

**Dengan SIGAP-ID:**
1. Pukul 03:00 WIB — BMKG forecast intensitas hujan >80mm/jam
2. Pukul 04:00 WIB — Model predict P(Macet)=91% di JORR Barat pukul 06:00
3. Pukul 04:30 WIB — Dashboard generate rute alternatif via Tol Cikampek
4. Pukul 06:00 WIB — Kemacetan parah seperti diprediksi, **rute alternatif menghemat 2.1 jam**

### Estimated Impact
- Pengurangan 30% durasi kemacetan parah di 14+ koridor weather-sensitive
- 45 hari hujan ekstrem per tahun → **estimasi penghematan Rp8–12 triliun/tahun**
- Belum termasuk dampak tidak langsung: kesehatan, produktivitas, efisiensi rantai pasok

---

## Future Roadmap

| Phase | Timeline | Goals |
|---|---|---|
| **Phase 1** | 0–3 bln | MVP: pipeline + dashboard + integrasi Azure ML & Azure Maps |
| **Phase 2** | 3–6 bln | Ekspansi Jawa Barat (Bandung, Depok, Bekasi) |
| **Phase 3** | 6–12 bln | Integrasi real-time ATCS Dishub DKI + API publik |
| **Phase 4** | 12+ bln | SaaS urban intelligence: Surabaya, Medan, Makassar |

---

## References

1. BMKG & Katadata (2024). *Kerugian Kemacetan Jakarta Tembus Rp100 Triliun per Tahun*. [link](https://katadata.co.id/ekonomi-hijau/ekonomi-sirkular/670e27cecd2dc/)
2. BPTJ Kemenhub (2021). *Kerugian Ekonomi Akibat Kemacetan Jabodetabek Rp71,4 Triliun*. [link](https://www.cnnindonesia.com/ekonomi/20210428120006-92-635840/)
3. TomTom (2025). *TomTom Traffic Index 2024 — Indonesia*. [link](https://www.tomtom.com/traffic-index/country/indonesia)
4. Yang, C.-L. et al. (2021). *Identification and Analysis of Weather-Sensitive Roads Based on Smartphone Sensor Data: A Case Study in Jakarta*. Sensors MDPI, 21(7), 2405. [link](https://www.mdpi.com/1424-8220/21/7/2405)
5. Open Data Jakarta — Dinas Perhubungan DKI. [satudata.jakarta.go.id](https://satudata.jakarta.go.id)
6. BMKG Open Data API. [data.bmkg.go.id](https://data.bmkg.go.id/prakiraan-cuaca/)
7. BNPB DIBI. [dibi.bnpb.go.id](https://dibi.bnpb.go.id)
8. Pantau Banjir Jakarta. [pantaubanjir.jakarta.go.id](https://pantaubanjir.jakarta.go.id)

---

## Team

| Nama | Role | Email Dicoding |
|---|---|---|
| [Anggota 1] | ML Engineer | [email] |
| [Anggota 2] | Data Scientist | [email] |
| [Anggota 3] | Backend / Dashboard | [email] |

---

## License

MIT License — bebas digunakan untuk kepentingan riset, edukasi, dan pengembangan smart city Indonesia.

---

<p align="center">
  <strong>SIGAP-ID</strong> · AI Impact Challenge Datathon 2026 · Urban Resilience & Smart City
</p>
