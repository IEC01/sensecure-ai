#!/usr/bin/env python3
"""
SenSecure AI — Entraînement sur NSL-KDD
Dataset de référence mondiale en cybersécurité
125 973 flux d'entraînement avec attaques réelles
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import classification_report, confusion_matrix
import joblib, os

BASE      = os.path.expanduser("~/SenSecureAI")
TRAIN     = f"{BASE}/data/datasets/KDDTrain+.txt"
TEST      = f"{BASE}/data/datasets/KDDTest+.txt"
MODEL_DIR = f"{BASE}/ml/models"
os.makedirs(MODEL_DIR, exist_ok=True)

# Colonnes du dataset NSL-KDD
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

# Features numériques utilisables
FEATURES = [
    "duration","src_bytes","dst_bytes","wrong_fragment","urgent","hot",
    "num_failed_logins","logged_in","num_compromised","root_shell",
    "num_root","num_file_creations","num_shells","num_access_files",
    "count","srv_count","serror_rate","srv_serror_rate","rerror_rate",
    "srv_rerror_rate","same_srv_rate","diff_srv_rate","srv_diff_host_rate",
    "dst_host_count","dst_host_srv_count","dst_host_same_srv_rate",
    "dst_host_diff_srv_rate","dst_host_same_src_port_rate",
    "dst_host_serror_rate","dst_host_rerror_rate",
]

def load_dataset(path):
    df = pd.read_csv(path, names=COLUMNS)
    # Encoder les colonnes catégorielles
    for col in ["protocol_type","service","flag"]:
        df[col] = LabelEncoder().fit_transform(df[col])
    # Labelliser : normal=0, attaque=1
    df["is_attack"] = (df["label"] != "normal").astype(int)
    return df

def get_attack_types(df):
    attacks = df[df["is_attack"]==1]["label"].value_counts()
    print("\n[NSL-KDD] Types d'attaques dans le dataset :")
    for atk, count in attacks.head(10).items():
        print(f"  {atk:<25} → {count:>6} flux")
    return attacks

print("=" * 55)
print("  SenSecure AI — Entraînement NSL-KDD")
print("=" * 55)

# Chargement
print("\n[1/5] Chargement des données...")
train_df = load_dataset(TRAIN)
test_df  = load_dataset(TEST)
print(f"  Train : {len(train_df):,} flux")
print(f"  Test  : {len(test_df):,} flux")
print(f"  Attaques train : {train_df['is_attack'].sum():,} ({train_df['is_attack'].mean()*100:.1f}%)")
print(f"  Attaques test  : {test_df['is_attack'].sum():,} ({test_df['is_attack'].mean()*100:.1f}%)")

get_attack_types(train_df)

# Préparation
print("\n[2/5] Préparation des features...")
X_train = train_df[FEATURES].fillna(0)
y_train = train_df["is_attack"]
X_test  = test_df[FEATURES].fillna(0)
y_test  = test_df["is_attack"]

scaler  = StandardScaler()
X_train_s = scaler.fit_transform(X_train)
X_test_s  = scaler.transform(X_test)

# Isolation Forest (détection d'anomalies)
print("\n[3/5] Entraînement Isolation Forest...")
contamination = train_df["is_attack"].mean()
iso_forest = IsolationForest(
    n_estimators=300,
    contamination=float(contamination),
    random_state=42,
    n_jobs=-1
)
iso_forest.fit(X_train_s)

# Random Forest (classification supervisée)
print("\n[4/5] Entraînement Random Forest (supervisé)...")
rf = RandomForestClassifier(
    n_estimators=200,
    max_depth=15,
    random_state=42,
    n_jobs=-1,
    class_weight="balanced"
)
rf.fit(X_train_s, y_train)

# Évaluation
print("\n[5/5] Évaluation sur les données de test...")

# Random Forest
rf_preds = rf.predict(X_test_s)
print("\n--- Random Forest ---")
print(classification_report(y_test, rf_preds, target_names=["Normal","Attaque"]))

# Isolation Forest
iso_preds = iso_forest.predict(X_test_s)
iso_preds = (iso_preds == -1).astype(int)  # -1=anomalie → 1=attaque
print("\n--- Isolation Forest ---")
print(classification_report(y_test, iso_preds, target_names=["Normal","Attaque"]))

# Sauvegarde
print("\n[OK] Sauvegarde des modèles...")
joblib.dump(iso_forest, f"{MODEL_DIR}/isolation_forest.pkl")
joblib.dump(scaler,     f"{MODEL_DIR}/scaler.pkl")
joblib.dump(rf,         f"{MODEL_DIR}/random_forest.pkl")
joblib.dump(FEATURES,   f"{MODEL_DIR}/features.pkl")

print(f"  isolation_forest.pkl → sauvegardé")
print(f"  random_forest.pkl    → sauvegardé")
print(f"  scaler.pkl           → sauvegardé")
print(f"  features.pkl         → sauvegardé")
print("\n✅ Entraînement terminé — SenSecure AI v2.0 ML ready !")
