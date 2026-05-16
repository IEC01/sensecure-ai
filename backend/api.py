#!/usr/bin/env python3
"""
SenSecure AI — API Backend FastAPI
Expose les alertes et anomalies via HTTP + WebSocket
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio, json, os, joblib
import pandas as pd
from datetime import datetime

BASE      = os.path.expanduser("~/SenSecureAI")
DATA      = f"{BASE}/data/traffic.jsonl"
ANOMALIES = f"{BASE}/data/anomalies.csv"
MODEL     = f"{BASE}/ml/models/isolation_forest.pkl"
SCALER    = f"{BASE}/ml/models/scaler.pkl"
FEATURES  = ["proto","port_dst","size","ttl","freq","n_ports"]

clients: list[WebSocket] = []

@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(broadcast_loop())
    yield

app = FastAPI(title="SenSecure AI API", version="1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

def load_model():
    try:
        return joblib.load(MODEL), joblib.load(SCALER)
    except:
        return None, None

def clean_record(r):
    for k, v in r.items():
        if isinstance(v, float) and v != v:
            r[k] = 0
        elif v is None:
            r[k] = ""
    return r

@app.get("/")
def root():
    return {"status": "SenSecure AI actif", "version": "1.0"}

@app.get("/stats")
def stats():
    try:
        df = pd.read_json(DATA, lines=True)
        return {
            "total_flux":    int(len(df)),
            "ips_uniques":   int(df["src"].nunique()),
            "ports_uniques": int(df["port_dst"].nunique()),
            "score_moyen":   round(float(df["suspicion"].mean()), 2),
            "derniere_maj":  datetime.now().isoformat()
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/anomalies")
def get_anomalies():
    try:
        df = pd.read_csv(ANOMALIES)
        df["flags"] = df["flags"].fillna("")
        df = df.fillna(0)
        records = df.sort_values("score").head(20).to_dict(orient="records")
        return [clean_record(r) for r in records]
    except Exception as e:
        return {"error": str(e)}

@app.get("/flux")
def get_flux(limit: int = 50):
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

@app.post("/analyse")
async def analyse(payload: dict):
    model, scaler = load_model()
    if not model:
        return {"error": "Modèle non chargé"}
    try:
        row = pd.DataFrame([{
            "proto":    payload.get("proto", 17),
            "port_dst": payload.get("port_dst", 0),
            "size":     payload.get("size", 100),
            "ttl":      payload.get("ttl", 64),
            "freq":     payload.get("freq", 1),
            "n_ports":  payload.get("n_ports", 1),
        }])
        Xs    = scaler.transform(row[FEATURES])
        label = model.predict(Xs)[0]
        score = model.score_samples(Xs)[0]
        return {
            "anomalie": bool(label == -1),
            "score":    round(float(score), 4),
            "niveau":   "CRITIQUE" if score < -0.7 else
                        "ÉLEVÉ"    if score < -0.6 else
                        "MOYEN"    if score < -0.5 else "NORMAL"
        }
    except Exception as e:
        return {"error": str(e)}

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
    uvicorn.run("api:app", host="0.0.0.0", port=8000,
                reload=False, log_level="info")
