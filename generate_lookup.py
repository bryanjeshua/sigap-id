"""
generate_lookup.py — SIGAP-ID
Trains XGBoost (mirrors notebook pipeline exactly) and pre-computes
predictions for all dashboard slider combinations into a lookup table.

Run: py -3.11 generate_lookup.py   (~3-5 min)

Outputs:
  data/processed/xgb_model.pkl
  data/processed/le_target.pkl
  data/processed/le_zone.pkl
  data/processed/lookup_table.pkl
"""

import numpy as np
import pandas as pd
import joblib
import warnings
from sklearn.preprocessing import LabelEncoder
from sklearn.utils.class_weight import compute_sample_weight
from sklearn.metrics import f1_score, classification_report
import xgboost as xgb

warnings.filterwarnings('ignore')
np.random.seed(42)

FEATURE_COLS = [
    'rainfall_mm', 'rainfall_bin', 'temperature_c', 'humidity_pct',
    'hour_sin', 'hour_cos', 'dow_sin', 'dow_cos', 'month_sin', 'month_cos',
    'is_weekend', 'is_peak_morning', 'is_peak_evening',
    'weather_sensitivity', 'flood_risk', 'flood_alert', 'zone_enc',
    'rain_lag_1h', 'rain_lag_2h', 'rain_lag_3h', 'rain_lag_6h',
    'speed_lag_1h', 'speed_lag_3h', 'speed_lag_6h',
    'rain_roll_3h', 'rain_roll_6h', 'speed_roll_3h',
]

# base_speed not in CSV — sourced from notebook CORRIDORS list
BASE_SPEEDS = {
    'Sudirman-Thamrin': 35, 'Gatot Subroto': 32, 'Rasuna Said HR': 28,
    'MT Haryono': 30, 'TB Simatupang': 40, 'S. Parman': 35,
    'Tomang Raya': 25, 'Daan Mogot': 45, 'Kalideres-Cengkareng': 40,
    'Pluit-Muara Baru': 30, 'Pantai Indah Kapuk': 50, 'Gunung Sahari': 30,
    'Perintis Kemerdekaan': 40, 'Ahmad Yani': 45, 'Bekasi Raya': 50,
    'Kalimalang': 40, 'DI Panjaitan': 35, 'Casablanca': 30,
    'Fatmawati': 35, 'Pondok Indah': 40, 'JORR Barat': 60,
    'JORR Selatan': 60, 'JORR Timur': 60, 'Cilincing': 40,
    'Yos Sudarso': 45, 'Cempaka Putih': 30, 'Matraman': 25,
    'Salemba': 25, 'Kramat Raya': 30, 'Senen Raya': 25,
    'Kyai Tapa': 35, 'Puri Kembangan': 40, 'Kelapa Gading': 40,
    'Ancol-Enggano': 45, 'Cakung': 40, 'Ciracas': 45,
    'Ragunan': 35, 'Lebak Bulus': 40, 'Cinere': 50,
    'Mangga Dua': 30, 'Tanah Abang': 20,
}

# ── 1. Load data ───────────────────────────────────────────────────────────────
print('Loading dataset...')
df = pd.read_csv('data/processed/sigap_id_dataset.csv', parse_dates=['datetime'])
print(f'  Shape: {df.shape}')

# ── 2. Feature engineering (mirrors notebook cell-16 exactly) ─────────────────
print('Feature engineering...')
df_feat = df.sort_values(['corridor', 'datetime']).copy()

df_feat['hour_sin']  = np.sin(2 * np.pi * df_feat['hour'] / 24)
df_feat['hour_cos']  = np.cos(2 * np.pi * df_feat['hour'] / 24)
df_feat['dow_sin']   = np.sin(2 * np.pi * df_feat['day_of_week'] / 7)
df_feat['dow_cos']   = np.cos(2 * np.pi * df_feat['day_of_week'] / 7)
df_feat['month_sin'] = np.sin(2 * np.pi * df_feat['month'] / 12)
df_feat['month_cos'] = np.cos(2 * np.pi * df_feat['month'] / 12)

df_feat['rainfall_bin'] = pd.cut(
    df_feat['rainfall_mm'],
    bins=[-0.01, 5, 10, 30, 50, 200],
    labels=[0, 1, 2, 3, 4]
).astype(int)

for lag in [1, 2, 3, 6]:
    df_feat[f'rain_lag_{lag}h']  = df_feat.groupby('corridor')['rainfall_mm'].shift(lag)
    df_feat[f'speed_lag_{lag}h'] = df_feat.groupby('corridor')['avg_speed_kmh'].shift(lag)

df_feat['rain_roll_3h']  = df_feat.groupby('corridor')['rainfall_mm'].transform(
    lambda x: x.rolling(3, min_periods=1).mean())
df_feat['rain_roll_6h']  = df_feat.groupby('corridor')['rainfall_mm'].transform(
    lambda x: x.rolling(6, min_periods=1).mean())
df_feat['speed_roll_3h'] = df_feat.groupby('corridor')['avg_speed_kmh'].transform(
    lambda x: x.rolling(3, min_periods=1).mean())

df_feat['flood_alert'] = (
    (df_feat['flood_risk'] > 0.6) & (df_feat['rain_roll_3h'] > 20)
).astype(int)

le_zone = LabelEncoder()
df_feat['zone_enc'] = le_zone.fit_transform(df_feat['zone'])

df_model = df_feat.dropna().copy()
print(f'  After feature eng: {df_model.shape}  (dropped {len(df_feat)-len(df_model)} lag warm-up rows)')

# ── 3. Train XGBoost (mirrors notebook cell-17 exactly) ───────────────────────
print('Training XGBoost (this takes ~3 min)...')
le_target = LabelEncoder()
y = le_target.fit_transform(df_model['congestion_level'])
X = df_model[FEATURE_COLS].values

train_mask = df_model['datetime'] < '2025-04-01'
X_train, X_test = X[train_mask], X[~train_mask]
y_train, y_test = y[train_mask], y[~train_mask]
print(f'  Train: {len(X_train):,} | Test: {len(X_test):,}')

sample_weights = compute_sample_weight('balanced', y_train)

model = xgb.XGBClassifier(
    n_estimators=300, max_depth=6, learning_rate=0.05,
    subsample=0.8, colsample_bytree=0.8, min_child_weight=5, gamma=0.1,
    use_label_encoder=False, eval_metric='mlogloss',
    random_state=42, n_jobs=-1, verbosity=0,
)
model.fit(
    X_train, y_train,
    sample_weight=sample_weights,
    eval_set=[(X_test, y_test)],
    verbose=False,
)

y_pred = model.predict(X_test)
f1 = f1_score(y_test, y_pred, average='weighted')
print(f'  F1-Score Weighted: {f1:.4f}')
print(classification_report(y_test, y_pred, target_names=le_target.classes_))

# ── 4. Save model artifacts ────────────────────────────────────────────────────
print('Saving model artifacts...')
joblib.dump(model,     'data/processed/xgb_model.pkl')
joblib.dump(le_target, 'data/processed/le_target.pkl')
joblib.dump(le_zone,   'data/processed/le_zone.pkl')
print('  Saved: xgb_model.pkl, le_target.pkl, le_zone.pkl')

# ── 4b. Save corridor metadata (41 rows) — dashboard loads this instead of the full CSV ──
corridor_meta_df = df.groupby('corridor').agg(
    zone=('zone', 'first'),
    lat=('lat', 'first'),
    lon=('lon', 'first'),
    flood_risk=('flood_risk', 'first'),
    weather_sensitivity=('weather_sensitivity', 'first'),
).reset_index()
corridor_meta_df.to_pickle('data/processed/corridor_meta.pkl')
print(f'  Saved: corridor_meta.pkl ({len(corridor_meta_df)} corridors)')

# ── 5. Speed reference: historical mean per (corridor, hour, is_weekend) ───────
print('Building speed reference table...')
speed_ref = (
    df.groupby(['corridor', 'hour', 'is_weekend'])['avg_speed_kmh']
    .mean()
    .to_dict()
)

# ── 6. Pre-compute lookup table ────────────────────────────────────────────────
print('Pre-computing lookup table...')

corr_meta = df.groupby('corridor').agg(
    weather_sensitivity=('weather_sensitivity', 'first'),
    flood_risk=('flood_risk', 'first'),
    zone=('zone', 'first'),
).reset_index()
corr_meta['zone_enc'] = le_zone.transform(corr_meta['zone'])

MACET_IDX  = list(le_target.classes_).index('Macet')
SEDANG_IDX = list(le_target.classes_).index('Sedang')
LANCAR_IDX = list(le_target.classes_).index('Lancar')

# Slider input space (must match dashboard slider steps exactly)
RAINFALL_VALUES = list(range(0, 105, 5))   # 0, 5, 10, ..., 100  → 21 values
HOUR_VALUES     = list(range(24))           # 0 – 23               → 24 values
WEEKEND_VALUES  = [0, 1]                    # weekday / weekend    →  2 values
# 41 corridors × 21 × 24 × 2 = 41,328 total rows

MONTH = 1  # January — peak rainy season, most representative for flood-risk demo

rows_meta = []
X_lookup  = []

for _, corr in corr_meta.iterrows():
    name   = corr['corridor']
    ws     = float(corr['weather_sensitivity'])
    fr     = float(corr['flood_risk'])
    zenc   = int(corr['zone_enc'])
    bspeed = BASE_SPEEDS.get(name, 35)

    for hour in HOUR_VALUES:
        for is_wknd in WEEKEND_VALUES:
            # Historical mean speed for this slot — used as speed lag estimate
            spd = speed_ref.get((name, hour, is_wknd), float(bspeed))

            for rain in RAINFALL_VALUES:
                dow = 6 if is_wknd else 1

                hour_sin  = np.sin(2 * np.pi * hour  / 24)
                hour_cos  = np.cos(2 * np.pi * hour  / 24)
                dow_sin   = np.sin(2 * np.pi * dow   / 7)
                dow_cos   = np.cos(2 * np.pi * dow   / 7)
                month_sin = np.sin(2 * np.pi * MONTH / 12)
                month_cos = np.cos(2 * np.pi * MONTH / 12)

                is_pk_m = 1 if (6 <= hour <= 9  and not is_wknd) else 0
                is_pk_e = 1 if (16 <= hour <= 20 and not is_wknd) else 0

                # Match pd.cut bins=[-0.01, 5, 10, 30, 50, 200]
                if   rain <= 5:  rbin = 0
                elif rain <= 10: rbin = 1
                elif rain <= 30: rbin = 2
                elif rain <= 50: rbin = 3
                else:            rbin = 4

                temp_c   = float(np.clip(29 - rain * 0.06, 22, 36))
                hum_pct  = float(np.clip(72 + rain * 0.25, 55, 99))
                flood_al = 1 if (fr > 0.6 and rain > 20) else 0

                feat = [
                    rain, rbin, temp_c, hum_pct,                    # rainfall features
                    hour_sin, hour_cos, dow_sin, dow_cos,            # time cyclical
                    month_sin, month_cos,                            # month cyclical
                    is_wknd, is_pk_m, is_pk_e,                      # time categorical
                    ws, fr, flood_al, zenc,                          # corridor features
                    rain, rain, rain, rain,                          # rain_lag_1h/2h/3h/6h (steady-state)
                    spd,  spd,  spd,                                 # speed_lag_1h/3h/6h
                    rain, rain, spd,                                 # rain_roll_3h/6h, speed_roll_3h
                ]

                rows_meta.append((name, hour, is_wknd, rain, bspeed))
                X_lookup.append(feat)

print(f'  Total rows: {len(X_lookup):,}')

# Single batch predict — fast
X_arr  = np.array(X_lookup, dtype=np.float32)
probas = model.predict_proba(X_arr)
print('  Inference done.')

# ── 7. Build lookup dataframe with MultiIndex ──────────────────────────────────
print('Building lookup dataframe...')
records = []
for i, (corridor, hour, is_weekend, rainfall_mm, bspeed) in enumerate(rows_meta):
    p_macet  = float(probas[i, MACET_IDX])
    p_sedang = float(probas[i, SEDANG_IDX])
    p_lancar = float(probas[i, LANCAR_IDX])
    pred_cls = le_target.classes_[int(np.argmax(probas[i]))]

    # Speed estimate weighted by class probabilities
    live_speed = round(bspeed * (0.20*p_macet + 0.55*p_sedang + 1.00*p_lancar), 1)

    records.append({
        'corridor':    corridor,
        'hour':        hour,
        'is_weekend':  is_weekend,
        'rainfall_mm': rainfall_mm,
        'live_level':  pred_cls,
        'prob_macet':  round(p_macet, 4),
        'live_speed':  live_speed,
    })

lookup_df = (
    pd.DataFrame(records)
    .set_index(['corridor', 'hour', 'is_weekend', 'rainfall_mm'])
)

lookup_df.to_pickle('data/processed/lookup_table.pkl')

print(f'  Shape: {lookup_df.shape}')
print(f'  Saved: data/processed/lookup_table.pkl')
print(f'\nLevel distribution in lookup table:')
print(lookup_df['live_level'].value_counts(normalize=True).mul(100).round(1).to_string())
print('\nAll done.')
