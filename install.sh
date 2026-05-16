#!/bin/bash
echo "=== SenSecure AI — Installation ==="

# Mise à jour système
sudo apt update -y && sudo apt upgrade -y

# Dépendances système
sudo apt install -y python3-pip python3-venv libpcap-dev net-tools curl git

# Environnement Python isolé
cd ~/SenSecureAI
python3 -m venv venv
source venv/bin/activate

# Librairies Python — Phase 1 (capture) + Phase 2 (ML) + Phase 3 (API)
pip install --upgrade pip
pip install \
  scapy \
  pandas numpy scikit-learn \
  fastapi uvicorn[standard] \
  websockets aiofiles \
  sqlalchemy \
  python-dotenv \
  joblib \
  requests \
  rich

# Vérification Docker
if ! command -v docker &> /dev/null; then
  echo "Installation Docker..."
  curl -fsSL https://get.docker.com | sh
  sudo usermod -aG docker $USER
fi

echo ""
echo "=== Installation terminée ==="
echo "Active le venv : source ~/SenSecureAI/venv/bin/activate"
