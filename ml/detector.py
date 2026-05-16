#!/usr/bin/env python3
"""
SenSecure AI — Détecteur d'anomalies (Isolation Forest)
Entraîne un modèle sur le trafic capturé et classe les flux suspects
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import joblib, json, os

DATA_FILE  = os.path.expanduser("~/SenSecureAI/data/traffic.jsonl")
MODEL_DIR  = os.path.expanduser("~/SenSecureAI/ml/models")
os.makedirs(MODEL_DIR, exist_ok=True)

FEATURES = ["proto", "port_dst", "size", "ttl", "freq", "n_ports"]

def load_data():
    records = []
    with open(DATA_FILE) as f:
        for line in f:
            records.append(json.loads(line))
    return pd.DataFrame(records)

def train(contamination=0.05):
    print("[ML] Chargement des données...")
    df = load_data()
    X  = df[FEATURES].fillna(0)

    scaler = StandardScaler()
    Xs     = scaler.fit_transform(X)

    print(f"[ML] Entraînement Isolation Forest sur {len(df)} flux...")
    model = IsolationForest(
        n_estimators=200,
        contamination=contamination,
        random_state=42,
        n_jobs=-1
    )
    model.fit(Xs)

    joblib.dump(model,  f"{MODEL_DIR}/isolation_forest.pkl")
    joblib.dump(scaler, f"{MODEL_DIR}/scaler.pkl")
    print("[ML] Modèle sauvegardé.")
    return model, scaler, df

def predict(model, scaler, df):
    X      = df[FEATURES].fillna(0)
    Xs     = scaler.transform(X)
    labels = model.predict(Xs)       # -1 = anomalie, 1 = normal
    scores = model.score_samples(Xs) # plus négatif = plus anormal

    df["anomaly"] = labels
    df["score"]   = scores
    anomalies      = df[df["anomaly"] == -1].sort_values("score")

    print(f"\n[ML] Anomalies détectées : {len(anomalies)} / {len(df)} flux\n")
    print(anomalies[["ts","src","dst","port_dst","n_ports","suspicion","score"]].head(20).to_string())
    return anomalies

if __name__ == "__main__":
    model, scaler, df = train()
    anomalies = predict(model, scaler, df)
    anomalies.to_csv(os.path.expanduser("~/SenSecureAI/data/anomalies.csv"), index=False)
    print("\n[ML] Résultats exportés dans data/anomalies.csv")
