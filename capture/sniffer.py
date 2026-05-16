#!/usr/bin/env python3
"""
SenSecure AI — Sniffer réseau (mode Docker)
Lit l'interface depuis la variable d'environnement IFACE
"""
from scapy.all import sniff, IP, TCP, UDP
from datetime import datetime
from collections import defaultdict
import json, time, os

DATA_DIR = os.environ.get("DATA_DIR", os.path.expanduser("~/SenSecureAI/data"))
LOG_FILE = f"{DATA_DIR}/traffic.jsonl"
IFACE    = os.environ.get("IFACE", "eth0")

os.makedirs(DATA_DIR, exist_ok=True)

ip_counter = defaultdict(lambda: {"count": 0, "ports": set(), "last": 0})

def extract_features(pkt):
    if not pkt.haslayer(IP):
        return None
    ip      = pkt[IP]
    src     = ip.src
    dst     = ip.dst
    proto   = ip.proto
    size    = len(pkt)
    ttl     = ip.ttl
    port_dst= 0
    flags   = ""

    if pkt.haslayer(TCP):
        port_dst = pkt[TCP].dport
        flags    = str(pkt[TCP].flags)
    elif pkt.haslayer(UDP):
        port_dst = pkt[UDP].dport

    c = ip_counter[src]
    c["count"] += 1
    c["ports"].add(port_dst)
    c["last"] = time.time()

    freq    = c["count"]
    n_ports = len(c["ports"])

    suspicion = 0
    if n_ports > 20:  suspicion += 3
    if freq    > 100: suspicion += 2
    if ttl     < 10:  suspicion += 1
    if port_dst in [22,23,3389,445,1433]: suspicion += 2

    return {
        "ts":        datetime.now().isoformat(),
        "src":       src, "dst": dst,
        "proto":     proto, "port_dst": port_dst,
        "size":      size,  "ttl": ttl,
        "flags":     flags, "freq": freq,
        "n_ports":   n_ports, "suspicion": suspicion,
    }

def packet_callback(pkt):
    rec = extract_features(pkt)
    if not rec:
        return
    color = "\033[91m" if rec["suspicion"] >= 3 else \
            "\033[93m" if rec["suspicion"] >= 1 else "\033[0m"
    print(f"{color}[{rec['ts'][11:19]}] {rec['src']:>15} → {rec['dst']:<15}"
          f"  port={rec['port_dst']:<5}  score={rec['suspicion']}\033[0m")
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(rec) + "\n")

if __name__ == "__main__":
    print(f"[SenSecure AI] Capture sur {IFACE} — Ctrl+C pour arrêter\n")
    sniff(iface=IFACE, prn=packet_callback, store=False)
