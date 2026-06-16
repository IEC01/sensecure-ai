#!/usr/bin/env python3
"""
SenSecure AI — API Backend FastAPI v2.0
Avec authentification JWT + Whitelist + Seuils calibrés NSL-KDD
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from contextlib import asynccontextmanager
from datetime import timedelta
import asyncio, json, os, joblib
import pandas as pd
from datetime import datetime

from backend.auth import (
    authenticate_user, create_access_token, get_current_active_user,
    Token, ACCESS_TOKEN_EXPIRE_MINUTES
)

BASE      = os.environ.get("BASE", os.path.expanduser("~/SenSecureAI"))
DATA      = f"{BASE}/data/traffic.jsonl"
ANOMALIES = f"{BASE}/data/anomalies.csv"
MODEL     = f"{BASE}/ml/models/isolation_forest.pkl"
SCALER    = f"{BASE}/ml/models/scaler.pkl"
FEAT_FILE = f"{BASE}/ml/models/features.pkl"

# Charger les features NSL-KDD
try:
    FEATURES = joblib.load(FEAT_FILE)
except:
    FEATURES = ["proto","port_dst","size","ttl","freq","n_ports"]

# Seuils calibrés sur NSL-KDD
SEUIL_CRITIQUE = -0.5067
SEUIL_ELEVE    = -0.4624
SEUIL_MOYEN    = -0.3559

# Whitelist IPs légitimes
WHITELIST = [
    "151.101.", "172.217.", "142.251.", "216.58.",
    "140.82.",  "8.8.8.8",  "8.8.4.4",  "1.1.1.1",
    "196.10.",  "192.168.", "10.",       "172.16.",
    "172.17.",  "172.18.",  "172.19.",   "172.20.",
    "127.",     "0.0.0.0",
]

def is_whitelisted(ip: str) -> bool:
    return any(str(ip).startswith(w) for w in WHITELIST)

def get_niveau(score: float) -> str:
    if score < SEUIL_CRITIQUE: return "CRITIQUE"
    if score < SEUIL_ELEVE:    return "ÉLEVÉ"
    if score < SEUIL_MOYEN:    return "MOYEN"
    return "NORMAL"

clients: list[WebSocket] = []

@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(broadcast_loop())
    yield

app = FastAPI(title="SenSecure AI API", version="2.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

def load_model():
    try:
        iso    = joblib.load(MODEL)
        scaler = joblib.load(SCALER)
        rf     = joblib.load(f"{BASE}/ml/models/random_forest.pkl")
        return iso, scaler, rf
    except:
        return None, None, None
# ─── Routes publiques ─────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"status": "SenSecure AI actif", "version": "2.0"}

@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiants incorrects",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"sub": user["username"]},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {
        "access_token": access_token,
        "token_type":   "bearer",
        "username":     user["username"],
        "role":         user["role"],
    }

# ─── Routes protégées ─────────────────────────────────────────────────────────

@app.get("/stats")
def stats(current_user: dict = Depends(get_current_active_user)):
    try:
        df = pd.read_json(DATA, lines=True)
        return {
            "total_flux":    int(len(df)),
            "ips_uniques":   int(df["src"].nunique()),
            "ports_uniques": int(df["port_dst"].nunique()),
            "score_moyen":   round(float(df["suspicion"].mean()), 2),
            "derniere_maj":  datetime.now().isoformat(),
            "user":          current_user["username"],
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/anomalies")
def get_anomalies(current_user: dict = Depends(get_current_active_user)):
    try:
        df = pd.read_csv(ANOMALIES)
        df["flags"] = df["flags"].fillna("")
        df = df.fillna(0)
        df = df[~df["src"].astype(str).apply(is_whitelisted)]
        records = df.sort_values("score").head(20).to_dict(orient="records")
        return [clean_record(r) for r in records]
    except Exception as e:
        return {"error": str(e)}

@app.get("/flux")
def get_flux(limit: int = 50, current_user: dict = Depends(get_current_active_user)):
    try:
        if not os.path.exists(DATA):
            return []
        records = []
        with open(DATA) as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
        return [clean_record(r) for r in records[-limit:]]
    except Exception as e:
        return {"error": str(e)}

@app.get("/geo")
def get_geo(current_user: dict = Depends(get_current_active_user)):
    geo_file = f"{BASE}/data/geo_anomalies.json"
    try:
        with open(geo_file) as f:
            return json.load(f)
    except Exception as e:
        return {"error": str(e)}

@app.post("/analyse")
async def analyse(payload: dict, current_user: dict = Depends(get_current_active_user)):
    iso, scaler, rf = load_model()
    if not iso:
        return {"error": "Modèle non chargé"}
    try:
        row  = pd.DataFrame([{f: payload.get(f, 0) for f in FEATURES}])
        Xs   = scaler.transform(row[FEATURES])

        # Isolation Forest — score d'anomalie
        iso_label = iso.predict(Xs)[0]
        iso_score = iso.score_samples(Xs)[0]

        # Random Forest — classification supervisée
        rf_pred  = rf.predict(Xs)[0]
        rf_proba = rf.predict_proba(Xs)[0][1]  # Probabilité d'attaque

        # Décision combinée
        est_attaque = bool(rf_pred == 1 or iso_label == -1)
        niveau = "NORMAL"
        if rf_proba > 0.90: niveau = "CRITIQUE"
        elif rf_proba > 0.70: niveau = "ÉLEVÉ"
        elif rf_proba > 0.40 or iso_label == -1: niveau = "MOYEN"

        return {
            "anomalie":    est_attaque,
            "score_iso":   round(float(iso_score), 4),
            "proba_rf":    round(float(rf_proba), 4),
            "niveau":      niveau,
            "rf_decision": "ATTAQUE" if rf_pred == 1 else "NORMAL",
        }
    except Exception as e:
        return {"error": str(e)}
@app.get("/me")
def me(current_user: dict = Depends(get_current_active_user)):
    return {
        "username":  current_user["username"],
        "full_name": current_user["full_name"],
        "role":      current_user["role"],
        "email":     current_user["email"],
    }

@app.get("/seuils")
def seuils(current_user: dict = Depends(get_current_active_user)):
    return {
        "critique": SEUIL_CRITIQUE,
        "eleve":    SEUIL_ELEVE,
        "moyen":    SEUIL_MOYEN,
        "source":   "Calibré sur NSL-KDD 2024 — 22 544 flux test",
    }

# ─── WebSocket ────────────────────────────────────────────────────────────────

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    clients.append(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        if ws in clients:
            clients.remove(ws)

async def broadcast_loop():
    last_size = 0
    while True:
        await asyncio.sleep(3)
        try:
            if not os.path.exists(DATA):
                continue
            with open(DATA) as f:
                lines = f.readlines()
            if len(lines) > last_size:
                new_lines = lines[last_size:]
                last_size = len(lines)
                dead = []
                for line in new_lines:
                    rec = clean_record(json.loads(line))
                    msg = json.dumps(rec)
                    for ws in clients:
                        try:
                            await ws.send_text(msg)
                        except:
                            dead.append(ws)
                for ws in dead:
                    if ws in clients:
                        clients.remove(ws)
        except:
            pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.api:app", host="0.0.0.0", port=8000,
                reload=False, log_level="info")
