import { useState, useEffect, useRef } from "react";
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import axios from "axios";

const API = "https://sensecure-ai.onrender.com";

const css = `
  @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Orbitron:wght@400;700;900&family=Rajdhani:wght@300;400;600&display=swap');
  *,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
  body{background:#010a06;color:#00ff88;font-family:'Rajdhani',sans-serif;min-height:100vh}
  .scanline{position:fixed;top:0;left:0;width:100%;height:100%;background:repeating-linear-gradient(0deg,transparent,transparent 2px,rgba(0,255,100,0.015) 2px,rgba(0,255,100,0.015) 4px);pointer-events:none;z-index:9999}
  .grid-bg{position:fixed;top:0;left:0;width:100%;height:100%;background-image:linear-gradient(rgba(0,255,100,0.04) 1px,transparent 1px),linear-gradient(90deg,rgba(0,255,100,0.04) 1px,transparent 1px);background-size:40px 40px;pointer-events:none;z-index:0}
  .app{position:relative;z-index:1;padding:1.5rem;max-width:1100px;margin:0 auto}
  .header{display:flex;align-items:center;justify-content:space-between;margin-bottom:2rem;padding-bottom:1rem;border-bottom:1px solid rgba(0,255,100,0.2)}
  .logo-title{font-family:'Orbitron',monospace;font-size:22px;font-weight:900;color:#00ff88;letter-spacing:3px;text-shadow:0 0 20px rgba(0,255,100,0.6)}
  .logo-sub{font-family:'Share Tech Mono',monospace;font-size:11px;color:#00aa55;letter-spacing:2px;margin-top:4px}
  .status-live{display:flex;align-items:center;gap:8px;font-family:'Share Tech Mono',monospace;font-size:12px;color:#00ff88;border:1px solid rgba(0,255,100,0.3);padding:6px 14px;background:rgba(0,255,100,0.05)}
  .dot{width:8px;height:8px;border-radius:50%;background:#00ff88;animation:blink 1.2s infinite}
  @keyframes blink{0%,100%{opacity:1}50%{opacity:0.2}}
  .stats{display:grid;grid-template-columns:repeat(5,1fr);gap:10px;margin-bottom:1.5rem}
  .stat-card{border:1px solid rgba(0,255,100,0.2);padding:1rem;background:rgba(0,255,100,0.03);position:relative;overflow:hidden;transition:all .3s}
  .stat-card:hover{border-color:rgba(0,255,100,0.6);background:rgba(0,255,100,0.07)}
  .stat-card::before{content:'';position:absolute;top:0;left:0;width:3px;height:100%;background:#00ff88}
  .stat-label{font-family:'Share Tech Mono',monospace;font-size:10px;color:#00aa55;letter-spacing:2px;margin-bottom:6px}
  .stat-value{font-family:'Orbitron',monospace;font-size:26px;font-weight:700;color:#00ff88;text-shadow:0 0 10px rgba(0,255,100,0.4)}
  .stat-value.warn{color:#ffaa00;text-shadow:0 0 10px rgba(255,170,0,0.5)}
  .stat-value.danger{color:#ff3344;text-shadow:0 0 10px rgba(255,51,68,0.5)}
  .panels{display:grid;grid-template-columns:1fr 1fr;gap:1rem;margin-bottom:1rem}
  .panel{border:1px solid rgba(0,255,100,0.2);background:rgba(0,8,4,0.9);padding:1.25rem}
  .panel-title{font-family:'Orbitron',monospace;font-size:11px;font-weight:700;color:#00ff88;letter-spacing:3px;margin-bottom:1rem;padding-bottom:.6rem;border-bottom:1px solid rgba(0,255,100,0.15)}
  .alert-row{display:flex;align-items:center;gap:10px;padding:7px 0;border-bottom:1px solid rgba(0,255,100,0.08);font-family:'Share Tech Mono',monospace;font-size:12px}
  .badge{font-size:10px;padding:2px 8px;letter-spacing:1px;font-family:'Orbitron',monospace;font-weight:700}
  .badge.critique{background:rgba(255,51,68,0.15);color:#ff3344;border:1px solid #ff3344}
  .badge.eleve{background:rgba(255,170,0,0.15);color:#ffaa00;border:1px solid #ffaa00}
  .badge.moyen{background:rgba(0,170,255,0.15);color:#00aaff;border:1px solid #00aaff}
  .badge.normal{background:rgba(0,255,100,0.1);color:#00ff88;border:1px solid #00ff88}
  .full-panel{border:1px solid rgba(0,255,100,0.2);background:rgba(0,8,4,0.9);padding:1.25rem;margin-bottom:1rem}
  .analyse-row{display:flex;gap:8px;flex-wrap:wrap;align-items:flex-end;margin-bottom:12px}
  .field-label{font-family:'Share Tech Mono',monospace;font-size:10px;color:#00aa55;letter-spacing:1px;margin-bottom:4px}
  .field-input{background:rgba(0,255,100,0.05);border:1px solid rgba(0,255,100,0.3);color:#00ff88;font-family:'Share Tech Mono',monospace;font-size:13px;padding:6px 10px;outline:none;width:90px}
  .field-input:focus{border-color:#00ff88}
  .scan-btn{background:rgba(0,255,100,0.1);border:1px solid #00ff88;color:#00ff88;font-family:'Orbitron',monospace;font-size:11px;letter-spacing:2px;padding:8px 18px;cursor:pointer;transition:all .2s}
  .scan-btn:hover{background:rgba(0,255,100,0.25);box-shadow:0 0 16px rgba(0,255,100,0.4)}
  .result-bar{display:flex;align-items:center;gap:14px;background:rgba(0,255,100,0.04);border:1px solid rgba(0,255,100,0.2);padding:10px 16px;font-family:'Share Tech Mono',monospace;font-size:13px}
  .terminal{background:#000;border:1px solid rgba(0,255,100,0.2);padding:1rem;font-family:'Share Tech Mono',monospace;font-size:12px;max-height:160px;overflow-y:auto;line-height:1.7}
  .terminal::-webkit-scrollbar{width:4px}
  .terminal::-webkit-scrollbar-thumb{background:rgba(0,255,100,0.3)}
  .t-normal{color:#00aa55}
  .t-warn{color:#ffaa00}
  .t-danger{color:#ff3344}
  .footer{text-align:center;font-family:'Share Tech Mono',monospace;font-size:10px;color:rgba(0,255,100,0.3);margin-top:1rem;letter-spacing:2px}
  .error-bar{background:rgba(255,51,68,0.08);border:1px solid rgba(255,51,68,0.4);color:#ff3344;padding:10px 16px;font-family:'Share Tech Mono',monospace;font-size:12px;margin-bottom:1rem}
  .tooltip-box{background:#010a06;border:1px solid rgba(0,255,100,0.4);padding:8px 12px;font-family:'Share Tech Mono',monospace;font-size:12px;color:#00ff88}
  .map-wrap{position:relative;width:100%;height:280px;background:#000510;overflow:hidden}
  .map-tip{position:absolute;background:#010a06;border:1px solid #00ff88;padding:8px 12px;font-family:'Share Tech Mono',monospace;font-size:11px;color:#00ff88;pointer-events:none;z-index:50;white-space:nowrap;transform:translate(-50%,-120%)}
  @keyframes ping{0%{r:6;opacity:1}100%{r:18;opacity:0}}
  .pulse{animation:ping 2s ease-out infinite}
`;

function getNiveau(score) {
  if (score < -0.70) return { label:"CRITIQUE", cls:"critique" };
  if (score < -0.60) return { label:"ELEVE",    cls:"eleve" };
  if (score < -0.50) return { label:"MOYEN",    cls:"moyen" };
  return { label:"NORMAL", cls:"normal" };
}

function CustomTooltip({ active, payload }) {
  if (active && payload && payload.length)
    return <div className="tooltip-box">SCORE: {payload[0].value}<br/>SRC: {payload[0].payload?.src}</div>;
  return null;
}

// Projection lat/lon → x,y sur une viewBox 800x400
function latLonToXY(lat, lon, w=800, h=400) {
  const x = ((lon + 180) / 360) * w;
  const y = ((90 - lat) / 180) * h;
  return { x, y };
}

function WorldMap({ geoData }) {
  const [tooltip, setTooltip] = useState(null);

  return (
    <div className="map-wrap">
      <svg viewBox="0 0 800 400" style={{width:"100%",height:"100%"}}>
        {/* Fond océan */}
        <rect width="800" height="400" fill="#000510"/>
        {/* Continents simplifiés */}
        <g fill="rgba(0,255,100,0.08)" stroke="rgba(0,255,100,0.2)" strokeWidth="0.5">
          {/* Amérique du Nord */}
          <path d="M80,60 L180,60 L200,80 L210,120 L190,160 L160,180 L130,200 L100,180 L80,150 L60,120 L70,80 Z"/>
          {/* Amérique du Sud */}
          <path d="M130,210 L180,210 L200,240 L190,300 L160,340 L130,320 L110,280 L115,240 Z"/>
          {/* Europe */}
          <path d="M340,60 L400,55 L420,70 L410,100 L380,110 L350,100 L330,80 Z"/>
          {/* Afrique */}
          <path d="M340,115 L400,110 L420,140 L410,220 L380,260 L340,250 L320,220 L320,150 Z"/>
          {/* Asie */}
          <path d="M420,50 L600,45 L640,80 L630,140 L580,160 L500,150 L450,130 L420,100 Z"/>
          {/* Océanie */}
          <path d="M580,200 L650,195 L670,220 L650,250 L600,245 L575,225 Z"/>
        </g>
        {/* Grille */}
        {[-60,-30,0,30,60].map(lat => {
          const {y} = latLonToXY(lat,0);
          return <line key={lat} x1="0" y1={y} x2="800" y2={y} stroke="rgba(0,255,100,0.06)" strokeWidth="0.5"/>;
        })}
        {[-120,-60,0,60,120].map(lon => {
          const {x} = latLonToXY(0,lon);
          return <line key={lon} x1={x} y1="0" x2={x} y2="400" stroke="rgba(0,255,100,0.06)" strokeWidth="0.5"/>;
        })}
        {/* Points géolocalisés */}
        {geoData.map((d, i) => {
          const {x, y} = latLonToXY(d.lat, d.lon);
          const col = d.score < -0.70 ? "#ff3344" : d.score < -0.60 ? "#ffaa00" : "#00ff88";
          return (
            <g key={i} className="map-point"
              onMouseEnter={() => setTooltip({...d, x, y})}
              onMouseLeave={() => setTooltip(null)}>
              <circle cx={x} cy={y} r="12" fill={col} opacity="0.15" className="pulse"/>
              <circle cx={x} cy={y} r="5"  fill={col} opacity="0.8"/>
              <circle cx={x} cy={y} r="2"  fill="white"/>
            </g>
          );
        })}
        {/* Ligne Sénégal → chaque IP */}
        {geoData.map((d, i) => {
          const src  = latLonToXY(14.6928, -17.4467); // Dakar
          const dest = latLonToXY(d.lat, d.lon);
          return (
            <line key={i} x1={src.x} y1={src.y} x2={dest.x} y2={dest.y}
              stroke="rgba(0,255,100,0.25)" strokeWidth="0.8" strokeDasharray="4,4"/>
          );
        })}
        {/* Point Dakar */}
        <circle cx={latLonToXY(14.6928,-17.4467).x} cy={latLonToXY(14.6928,-17.4467).y}
          r="6" fill="#00ff88" opacity="0.9"/>
        <text x={latLonToXY(14.6928,-17.4467).x+8} y={latLonToXY(14.6928,-17.4467).y+4}
          fill="#00ff88" fontSize="9" fontFamily="Share Tech Mono">DAKAR</text>
      </svg>
      {/* Tooltip */}
      {tooltip && (
        <div className="map-tip" style={{left:tooltip.x/800*100+"%", top:tooltip.y/400*100+"%"}}>
          IP: {tooltip.ip}<br/>
          {tooltip.city}, {tooltip.country}<br/>
          ISP: {tooltip.isp}<br/>
          Score: {tooltip.score}
        </div>
      )}
    </div>
  );
}

export default function App() {
  const [stats, setStats]         = useState(null);
  const [anomalies, setAnomalies] = useState([]);
  const [flux, setFlux]           = useState([]);
  const [analyse, setAnalyse]     = useState(null);
  const [live, setLive]           = useState([]);
  const [erreur, setErreur]       = useState("");
  const [clock, setClock]         = useState(new Date().toLocaleTimeString());
  const [geo, setGeo]             = useState([]);
  const [form, setForm]           = useState({ proto:6, port_dst:3389, size:1500, ttl:64, freq:200, n_ports:30 });
  const wsRef = useRef(null);

  useEffect(() => {
    fetchAll();
    const iv  = setInterval(fetchAll, 10000);
    const tic = setInterval(() => setClock(new Date().toLocaleTimeString()), 1000);
    wsRef.current = new WebSocket("ws://localhost:8000/ws");
    wsRef.current.onmessage = (e) => {
      try { const r = JSON.parse(e.data); setLive(p => [r,...p].slice(0,30)); } catch {}
    };
    return () => { clearInterval(iv); clearInterval(tic); wsRef.current?.close(); };
  }, []);

  async function fetchAll() {
    try {
      const [s,a,f,g] = await Promise.all([
        axios.get(`${API}/stats`),
        axios.get(`${API}/anomalies`),
        axios.get(`${API}/flux?limit=40`),
        axios.get(`${API}/geo`),
      ]);
      if (s.data && !s.data.error) setStats(s.data);
      setAnomalies(Array.isArray(a.data) ? a.data : []);
      setFlux(Array.isArray(f.data) ? f.data.map((r,i) => ({ i, score: r.suspicion||0, src: r.src })) : []);
      setGeo(Array.isArray(g.data) ? g.data : []);
      setErreur("");
    } catch { setErreur("ERR — API UNREACHABLE"); }
  }

  async function runAnalyse() {
    try { const r = await axios.post(`${API}/analyse`, form); setAnalyse(r.data); }
    catch { setErreur("ERR — ANALYSE FAILED"); }
  }

  return (
    <>
      <style>{css}</style>
      <div className="scanline"/>
      <div className="grid-bg"/>
      <div className="app">

        <div className="header">
          <div>
            <div className="logo-title">🛡 SENSECURE AI</div>
            <div className="logo-sub">▸ THREAT DETECTION PLATFORM · UNCHK SÉNÉGAL</div>
          </div>
          <div style={{textAlign:"right"}}>
            <div className="status-live"><span className="dot"/>SURVEILLANCE ACTIVE</div>
            <div style={{fontFamily:"Share Tech Mono",fontSize:11,color:"#00aa55",marginTop:6}}>
              {new Date().toLocaleDateString()} · {clock}
            </div>
          </div>
        </div>

        {erreur && <div className="error-bar">⚠ {erreur}</div>}

        <div className="stats">
          {[
            { label:"FLUX CAPTURÉS",  value: stats?.total_flux,    cls:"" },
            { label:"IPs UNIQUES",    value: stats?.ips_uniques,   cls:"" },
            { label:"PORTS SCANNÉS",  value: stats?.ports_uniques, cls:"" },
            { label:"ANOMALIES ML",   value: anomalies.length,     cls:"warn" },
            { label:"SCORE MOYEN",    value: stats?.score_moyen,   cls: stats?.score_moyen > 1 ? "danger" : "" },
          ].map((s,i) => (
            <div key={i} className="stat-card">
              <div className="stat-label">{s.label}</div>
              <div className={`stat-value ${s.cls}`}>{s.value ?? "—"}</div>
            </div>
          ))}
        </div>

        {/* Carte mondiale */}
        <div className="full-panel">
          <div className="panel-title">🌍 CARTE DES MENACES — {geo.length} IPs GÉOLOCALISÉES</div>
          <WorldMap geoData={geo}/>
          <div style={{display:"flex",gap:"1rem",marginTop:"8px",flexWrap:"wrap"}}>
            {geo.map((g,i) => (
              <div key={i} style={{fontFamily:"Share Tech Mono",fontSize:11,color:"#00aa55"}}>
                <span style={{color: g.score < -0.65 ? "#ff3344" : "#ffaa00"}}>●</span>
                {" "}{g.ip} · {g.city}, {g.country}
              </div>
            ))}
          </div>
        </div>

        <div className="panels">
          <div className="panel">
            <div className="panel-title">📡 TRAFIC RÉSEAU — SCORES</div>
            {flux.length === 0
              ? <div style={{color:"#00aa55",fontFamily:"Share Tech Mono",fontSize:12}}>NO DATA</div>
              : <ResponsiveContainer width="100%" height={155}>
                  <AreaChart data={flux}>
                    <defs>
                      <linearGradient id="grd" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%"  stopColor="#00ff88" stopOpacity={0.3}/>
                        <stop offset="95%" stopColor="#00ff88" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <XAxis dataKey="i" hide/>
                    <YAxis width={20} tick={{fill:"#00aa55",fontSize:10,fontFamily:"Share Tech Mono"}}/>
                    <Tooltip content={<CustomTooltip/>}/>
                    <Area type="monotone" dataKey="score" stroke="#00ff88" strokeWidth={1.5} fill="url(#grd)" dot={false}/>
                  </AreaChart>
                </ResponsiveContainer>
            }
          </div>

          <div className="panel">
            <div className="panel-title">⚠ ANOMALIES ML — {anomalies.length}</div>
            <div style={{maxHeight:170,overflowY:"auto"}}>
              {anomalies.length === 0
                ? <div style={{color:"#00aa55",fontFamily:"Share Tech Mono",fontSize:12}}>NO ANOMALIES</div>
                : anomalies.slice(0,8).map((a,i) => {
                    const niv = getNiveau(a.score);
                    return (
                      <div key={i} className="alert-row">
                        <span className={`badge ${niv.cls}`}>{niv.label}</span>
                        <span style={{color:"#00ff88",flex:1}}>{a.src}</span>
                        <span style={{color:"#ff3344",fontWeight:700}}>
                          {typeof a.score==="number" ? a.score.toFixed(3) : a.score}
                        </span>
                      </div>
                    );
                  })
              }
            </div>
          </div>
        </div>

        <div className="full-panel">
          <div className="panel-title">🔍 ANALYSE EN TEMPS RÉEL</div>
          <div className="analyse-row">
            {Object.entries(form).map(([k,v]) => (
              <div key={k}>
                <div className="field-label">{k.toUpperCase()}</div>
                <input className="field-input" type="number" value={v}
                  onChange={e => setForm(f => ({...f,[k]:+e.target.value}))}/>
              </div>
            ))}
            <button className="scan-btn" onClick={runAnalyse}>▸ SCAN</button>
          </div>
          {analyse && (
            <div className="result-bar">
              <span className={`badge ${getNiveau(analyse.score).cls}`}>{analyse.niveau}</span>
              <span style={{color:"#00aa55"}}>SCORE ML :</span>
              <span style={{color:analyse.anomalie?"#ff3344":"#00ff88",fontWeight:700}}>{analyse.score}</span>
              <span style={{color:analyse.anomalie?"#ff3344":"#00ff88"}}>
                {analyse.anomalie ? "▸ ANOMALIE DÉTECTÉE" : "▸ TRAFIC NORMAL"}
              </span>
            </div>
          )}
        </div>

        <div className="full-panel">
          <div className="panel-title">💻 FLUX EN DIRECT — WEBSOCKET</div>
          <div className="terminal">
            {live.length === 0
              ? <span className="t-normal">root@sensecure:~$ waiting..._</span>
              : live.map((r,i) => (
                  <div key={i} className={r.suspicion>=3?"t-danger":r.suspicion>=1?"t-warn":"t-normal"}>
                    [{r.ts?.slice(11,19)}] {r.src} → {r.dst} · port={r.port_dst} · score={r.suspicion}
                    {r.suspicion>=3?" ⚠ CRITICAL":r.suspicion>=1?" ! WARNING":""}
                  </div>
                ))
            }
          </div>
        </div>

        <div className="footer">SENSECURE AI v1.0 · UNCHK SÉNÉGAL · CYBERSECURITY INTELLIGENCE PLATFORM</div>
      </div>
    </>
  );
}
