#!/usr/bin/env python3
"""
SenSecure AI — Calibration des seuils de détection
"""
import pandas as pd
import numpy as np
import joblib, os

BASE     = os.path.expanduser("~/SenSecureAI")
TEST     = f"{BASE}/data/datasets/KDDTest+.txt"
MODEL    = f"{BASE}/ml/models/isolation_forest.pkl"
SCALER   = f"{BASE}/ml/models/scaler.pkl"
FEATURES = joblib.load(f"{BASE}/ml/models/features.pkl")

COLUMNS = [
    "duration","protocol_type","service","flag","src_bytes","dst_bytes",
    "land","wrong_fragment","urgent","hot","num_failed_logins","logged_in",
    "num_compromised","root_shell","su_attempted","num_root","num_file_creations",
    "num_shells","num_access_files","num_outbound_cmds","is_host_login",
    "is_guest_login","count","srv_count","serror_rate","srv_serror_rate",
    "rerror_rate","srv_rerror_rate","same_srv_rate","diff_srv_rate",
    "srv_diff_host_rate","dst_host_count","dst_host_srv_count",
    "dst_host_same_srv_rate","dst_host_diff_srv_rate","dst_host_same_src_port_rate",
    "dst_host_srv_diff_host_rate","dst_host_serror_rate","dst_host_srv_serror_rate",
    "dst_host_rerror_rate","dst_host_srv_rerror_rate","label","difficulty"
]

from sklearn.preprocessing import LabelEncoder
df = pd.read_csv(TEST, names=COLUMNS)
for col in ["protocol_type","service","flag"]:
    df[col] = LabelEncoder().fit_transform(df[col])
df["is_attack"] = (df["label"] != "normal").astype(int)

model  = joblib.load(MODEL)
scaler = joblib.load(SCALER)
X      = scaler.transform(df[FEATURES].fillna(0))
scores = model.score_samples(X)
df["score"] = scores

print("=== Distribution des scores par type ===\n")
print(f"NORMAL  — mean={df[df['is_attack']==0]['score'].mean():.4f}  "
      f"min={df[df['is_attack']==0]['score'].min():.4f}  "
      f"max={df[df['is_attack']==0]['score'].max():.4f}")
print(f"ATTAQUE — mean={df[df['is_attack']==1]['score'].mean():.4f}  "
      f"min={df[df['is_attack']==1]['score'].min():.4f}  "
      f"max={df[df['is_attack']==1]['score'].max():.4f}")

print("\n=== Percentiles scores normaux ===")
for p in [10,25,50,75,90]:
    print(f"  P{p:2d} : {np.percentile(df[df['is_attack']==0]['score'], p):.4f}")

print("\n=== Percentiles scores attaques ===")
for p in [10,25,50,75,90]:
    print(f"  P{p:2d} : {np.percentile(df[df['is_attack']==1]['score'], p):.4f}")

print("\n=== Seuils recommandés ===")
p25_attack = np.percentile(df[df['is_attack']==1]['score'], 25)
p50_attack = np.percentile(df[df['is_attack']==1]['score'], 50)
p75_normal = np.percentile(df[df['is_attack']==0]['score'], 75)
print(f"  CRITIQUE : score < {p25_attack:.4f}")
print(f"  ÉLEVÉ    : score < {p50_attack:.4f}")
print(f"  MOYEN    : score < {p75_normal:.4f}")
