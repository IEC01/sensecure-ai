#!/usr/bin/env python3
import requests, time, json, os
import pandas as pd

CACHE_FILE = os.path.expanduser("~/SenSecureAI/data/geo_cache.json")
ANOMALIES  = os.path.expanduser("~/SenSecureAI/data/anomalies.csv")
OUTPUT     = os.path.expanduser("~/SenSecureAI/data/geo_anomalies.json")
PRIVATE    = ["192.168.","10.","172.","127.","0.0.0.0","255.255"]

def is_private(ip):
    return any(ip.startswith(p) for p in PRIVATE)

def load_cache():
    try:
        with open(CACHE_FILE) as f:
            return json.load(f)
    except:
        return {}

cache = load_cache()

def geolocate(ip):
    if is_private(ip):
        return None
    if ip in cache:
        return cache[ip]
    try:
        r = requests.get(
            f"http://ip-api.com/json/{ip}?fields=status,country,countryCode,city,lat,lon,isp",
            timeout=5
        ).json()
        if r.get("status") == "success":
            result = {
                "ip":      ip,
                "country": r.get("country", "?"),
                "code":    r.get("countryCode", "?"),
                "city":    r.get("city", "?"),
                "lat":     r.get("lat", 0),
                "lon":     r.get("lon", 0),
                "isp":     r.get("isp", "?"),
            }
            cache[ip] = result
            with open(CACHE_FILE, "w") as f:
                json.dump(cache, f)
            time.sleep(1.5)
            return result
    except Exception as e:
        print(f"Erreur {ip}: {e}")
    return None

if __name__ == "__main__":
    print("[GEO] Chargement anomalies...")
    df = pd.read_csv(ANOMALIES)
    df["flags"] = df["flags"].fillna("")
    df = df.fillna(0)
    results = []
    ips_vues = set()
    for _, row in df.iterrows():
        src = str(row.get("src", ""))
        if not src or is_private(src) or src in ips_vues:
            continue
        ips_vues.add(src)
        print(f"  {src}...", end=" ", flush=True)
        geo = geolocate(src)
        if geo:
            results.append({
                **geo,
                "score":     round(float(row.get("score", 0)), 4),
                "port":      int(row.get("port_dst", 0)),
                "suspicion": int(row.get("suspicion", 0)),
            })
            print(f"-> {geo['city']}, {geo['country']}")
        else:
            print("-> ignoree")
    with open(OUTPUT, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n[GEO] {len(results)} IPs geolocalisees")
    for r in results:
        print(f"  {r['ip']:20} {r['city']:<15} {r['country']}")
