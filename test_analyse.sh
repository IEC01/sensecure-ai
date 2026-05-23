#!/bin/bash
# Obtenir un token frais
TOKEN=$(curl -s -X POST http://localhost:8000/token \
  -d "username=admin&password=sensecure2026" \
  | python3 -c "import sys,json; print(json.loads(sys.stdin.read())['access_token'])")

echo "=== Test Normal ==="
curl -s -X POST http://localhost:8000/analyse \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"duration":0,"src_bytes":100,"dst_bytes":200,"count":1,"serror_rate":0.0}' 

echo ""
echo "=== Test Neptune (DoS) ==="
curl -s -X POST http://localhost:8000/analyse \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"duration":0,"src_bytes":0,"dst_bytes":0,"count":511,"serror_rate":1.0,"srv_serror_rate":1.0,"dst_host_count":255,"dst_host_serror_rate":1.0}'

echo ""
echo "=== Test nmap (Scan) ==="
curl -s -X POST http://localhost:8000/analyse \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"duration":0,"src_bytes":0,"dst_bytes":0,"count":0,"serror_rate":0.0,"diff_srv_rate":1.0,"dst_host_diff_srv_rate":1.0}'

echo ""
