#!/bin/bash
echo "╔══════════════════════════════════════╗"
echo "║     🛡️  SenSecure AI — Démarrage     ║"
echo "╚══════════════════════════════════════╝"

cd ~/SenSecureAI

# Copier les données et modèles dans les volumes Docker
echo "[1/4] Préparation des données..."
sudo cp /root/SenSecureAI/data/traffic.jsonl data/ 2>/dev/null || true
sudo chown -R iec:iec data/ logs/ 2>/dev/null || true

echo "[2/4] Construction des images Docker..."
docker-compose build

echo "[3/4] Démarrage des services..."
docker-compose up -d

echo "[4/4] Vérification..."
sleep 5
docker-compose ps

echo ""
echo "✅ SenSecure AI opérationnel !"
echo "   Dashboard  → http://localhost:3000"
echo "   API        → http://localhost:8000"
echo "   Logs       → docker-compose logs -f"
