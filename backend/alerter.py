#!/usr/bin/env python3
"""
SenSecure AI — Alertes automatiques (mode Docker · logs uniquement)
"""
import os, json, time, joblib, logging
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

load_dotenv("/app/.env")

BASE     = os.environ.get("BASE_DIR", "/app")
DATA     = f"{BASE}/data/traffic.jsonl"
MODEL    = f"{BASE}/ml/models/isolation_forest.pkl"
SCALER   = f"{BASE}/ml/models/scaler.pkl"
LOG_FILE = f"{BASE}/logs/alertes.log"
FEATURES = ["proto","port_dst","size","ttl","freq","n_ports"]

os.makedirs(f"{BASE}/logs", exist_ok=True)
os.makedirs(f"{BASE}/data", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

SEUIL_C = float(os.getenv("SEUIL_CRITIQUE", "-0.70"))
SEUIL_E = float(os.getenv("SEUIL_ELEVE",    "-0.60"))
COOLDOWN= int(os.getenv("COOLDOWN_MINUTES",  "5")) * 60

derniere_alerte: dict = {}

def niveau(score):
    if score < SEUIL_C: return "CRITIQUE", "🔴"
    if score < SEUIL_E: return "ÉLEVÉ",    "🟠"
    return "MOYEN", "🟡"

def alerter(record: dict, score: float):
    niv, emoji = niveau(score)
    proto_nom  = {6:"TCP", 17:"UDP", 1:"ICMP", 2:"IGMP"}.get(
                  record.get("proto"), str(record.get("proto","?")))
    now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    # Log structuré visible dans docker logs
    print(f"""
╔══════════════════════════════════════════╗
║  {emoji}  ALERTE SENSECURE AI — {niv:<10}    ║
╠══════════════════════════════════════════╣
║  Heure    : {now}           ║
║  Source   : {record.get('src','?'):<30} ║
║  Dest     : {record.get('dst','?'):<30} ║
║  Port     : {str(record.get('port_dst','?')):<30} ║
║  Proto    : {proto_nom:<30} ║
║  Score ML : {score:<30.4f} ║
╚══════════════════════════════════════════╝
""", flush=True)

    # Sauvegarder dans le fichier d'alertes
    alerte = {
        "ts":      now,
        "niveau":  niv,
        "src":     record.get("src"),
        "dst":     record.get("dst"),
        "port":    record.get("port_dst"),
        "proto":   proto_nom,
        "score":   round(score, 4)
    }
    with open(f"{BASE}/logs/alertes.jsonl", "a") as f:
        f.write(json.dumps(alerte) + "\n")

    logging.warning(f"{emoji} ALERTE {niv} | {record.get('src')} → "
                   f"{record.get('dst')} port={record.get('port_dst')} score={score:.4f}")

def analyser_flux(record: dict, model, scaler):
    try:
        row = pd.DataFrame([{
            "proto":    record.get("proto", 17),
            "port_dst": record.get("port_dst", 0),
            "size":     record.get("size", 100),
            "ttl":      record.get("ttl", 64),
            "freq":     record.get("freq", 1),
            "n_ports":  record.get("n_ports", 1),
        }])
        Xs    = scaler.transform(row[FEATURES])
        label = model.predict(Xs)[0]
        score = model.score_samples(Xs)[0]
        return float(score) if label == -1 else None
    except:
        return None

def doit_alerter(src: str) -> bool:
    now = time.time()
    if src in derniere_alerte:
        if now - derniere_alerte[src] < COOLDOWN:
            return False
    derniere_alerte[src] = now
    return True

def surveiller():
    logging.info("🛡️  SenSecure AI — Alertes démarrées (mode Docker)")
    logging.info(f"   Modèle    : {MODEL}")
    logging.info(f"   Données   : {DATA}")
    logging.info(f"   Seuils    : critique={SEUIL_C} | élevé={SEUIL_E}")

    # Attendre que le modèle soit disponible
    while not os.path.exists(MODEL):
        logging.warning(f"⏳ Attente du modèle ML : {MODEL}")
        time.sleep(5)

    model  = joblib.load(MODEL)
    scaler = joblib.load(SCALER)
    logging.info("✅ Modèle ML chargé")

    last_size = 0
    while True:
        time.sleep(5)
        try:
            if not os.path.exists(DATA):
                continue
            with open(DATA) as f:
                lines = f.readlines()
            if len(lines) <= last_size:
                continue
            new_lines = lines[last_size:]
            last_size = len(lines)

            for line in new_lines:
                line = line.strip()
                if not line:
                    continue
                record = json.loads(line)
                score  = analyser_flux(record, model, scaler)
                if score is None:
                    continue
                niv, emoji = niveau(score)
                logging.info(f"{emoji} {record.get('src')} → {record.get('dst')} "
                            f"port={record.get('port_dst')} score={score:.4f} [{niv}]")
                if score < SEUIL_E and doit_alerter(record.get("src","?")):
                    alerter(record, score)

        except KeyboardInterrupt:
            logging.info("Arrêt alertes.")
            break
        except Exception as e:
            logging.error(f"Erreur : {e}")

if __name__ == "__main__":
    surveiller()
