import base64
import os
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Ruota Regali", page_icon="🎁", layout="wide")

ASSETS = "assets"

FILES = {
    "bgm": os.path.join(ASSETS, "bgm.mp3"),
    "spin": os.path.join(ASSETS, "spin.mp3"),
    "gift": os.path.join(ASSETS, "gift.mp3"),
    "malus": os.path.join(ASSETS, "malus.mp3"),
    "gift_box": os.path.join(ASSETS, "gift_box.png"),
    "malus1": os.path.join(ASSETS, "malus1.png"),
    "malus2": os.path.join(ASSETS, "malus2.png"),
    "malus3": os.path.join(ASSETS, "malus3.png"),
    "malus4": os.path.join(ASSETS, "malus4.png"),
}

def b64(path: str) -> str:
    if not os.path.exists(path):
        st.error(f"File mancante: {path}")
        st.stop()
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

b64s = {k: b64(v) for k, v in FILES.items()}

st.markdown(
    """
    <style>
      .block-container { padding-top: 1.1rem; padding-bottom: 1.2rem; }
      header, footer { visibility: hidden; height: 0; }
    </style>
    """,
    unsafe_allow_html=True,
)

html = f"""
<div id="app">
  <div class="topbar">
    <div class="title">🎁 Ruota Regali</div>
    <div class="turn" id="turnLabel">Turno: Player 1</div>
  </div>

  <div class="stage">
    <div class="wheel-wrap">
      <div class="pointer" title="pointer"></div>

      <div class="rim" id="rim"></div>

      <div class="wheel" id="wheel">
        <div class="face" id="face"></div>
        <div class="labels" id="labels"></div>
        <div class="hub"></div>
      </div>
    </div>

    <div class="controls">
      <button id="spinBtn" class="spin">SPIN</button>

      <div class="meta">
        <div class="pill">Premi rimasti: <span id="remaining">10</span></div>
        <div class="pill">Imprevisti bruciati: <span id="burnedMalus">0</span></div>
      </div>

      <div class="assignments" id="assignments"></div>
    </div>
  </div>

  <!-- Overlay premio -->
  <div class="overlay" id="overlayGift" aria-hidden="true">
    <div class="card big" id="giftCard">
      <div class="imgwrap">
        <img class="img" id="giftImg" src="data:image/png;base64,{b64s["gift_box"]}" alt="gift"/>
        <div class="num" id="giftNum">1</div>
      </div>
      <div class="row-actions">
        <button class="ok" id="giftOk" disabled>OK</button>
        <div class="hint" id="giftHint">OK disponibile tra <span id="giftCountdown">12</span>s</div>
      </div>
    </div>
  </div>

  <!-- Overlay malus -->
  <div class="overlay" id="overlayMalus" aria-hidden="true">
    <div class="card" id="malusCard">
      <div class="imgwrap">
        <img class="img" id="malusImg" src="data:image/png;base64,{b64s["malus1"]}" alt="malus"/>
      </div>

      <div class="row-actions">
        <div class="left-pack" id="packPickWrap" style="display:none;">
          <div class="packLabel">Numero pacco scelto</div>
          <input id="packPick" class="packInput" inputmode="numeric" placeholder="1-10" />
        </div>

        <button class="ok" id="malusOk" disabled>OK</button>
        <div class="hint" id="malusHint">OK disponibile tra <span id="malusCountdown">12</span>s</div>
      </div>
    </div>
  </div>

  <!-- Audio -->
  <audio id="bgm" autoplay loop preload="auto" playsinline>
    <source src="data:audio/mpeg;base64,{b64s["bgm"]}" type="audio/mpeg" />
  </audio>
  <audio id="spinSfx" preload="auto" playsinline>
    <source src="data:audio/mpeg;base64,{b64s["spin"]}" type="audio/mpeg" />
  </audio>
  <audio id="giftSfx" preload="auto" playsinline>
    <source src="data:audio/mpeg;base64,{b64s["gift"]}" type="audio/mpeg" />
  </audio>
  <audio id="malusSfx" preload="auto" playsinline>
    <source src="data:audio/mpeg;base64,{b64s["malus"]}" type="audio/mpeg" />
  </audio>
</div>

<style>
  :root {{
    --bg: #0B1220;
    --panel: rgba(17, 26, 46, 0.78);
    --gold: #E2B24A;
    --deep-red: #7C1430;
    --cream: #F4E2C6;
    --red: #B51E1E;
    --gray: #7A7A7A;
    --text: #E5E7EB;
  }}

  body {{ background: var(--bg); }}
  #app {{ color: var(--text); font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial; }}

  .topbar {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin: 0 0 14px 0;
    padding: 10px 14px;
    background: var(--panel);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 16px;
    backdrop-filter: blur(6px);
  }}
  .title {{ font-weight: 950; letter-spacing: 0.02em; font-size: 18px; }}
  .turn {{ font-weight: 900; opacity: 0.95; }}

  .stage {{
    display: grid;
    grid-template-columns: 1.25fr 0.75fr;
    gap: 18px;
    align-items: start;
  }}

  .wheel-wrap {{
    position: relative;
    width: min(820px, 94vw);
    aspect-ratio: 1/1;
    margin: 0 auto;
  }}

  /* Pointer più bello, punta verso il basso */
  .pointer {{
    position: absolute;
    top: -0.5%;
    left: 50%;
    transform: translateX(-50%);
    width: 72px;
    height: 72px;
    z-index: 60;
    filter: drop-shadow(0 10px 10px rgba(0,0,0,0.35));
  }}
  .pointer::before {{
    content: "";
    position: absolute;
    inset: 0;
    border-radius: 999px;
    background: radial-gradient(circle at 30% 30%, #FFE9A6 0%, #E2B24A 35%, #A47A1F 70%, #5A3A08 100%);
    box-shadow: inset 0 0 0 6px rgba(255,255,255,0.12);
  }}
  .pointer::after {{
    content: "";
    position: absolute;
    left: 50%;
    bottom: -22px;
    transform: translateX(-50%);
    width: 0; height: 0;
    border-left: 18px solid transparent;
    border-right: 18px solid transparent;
    border-top: 30px solid var(--gold);
  }}

  .rim {{
    position: absolute;
    inset: 0;
    border-radius: 50%;
    z-index: 8;
    pointer-events: none;
  }}

  /* Lampadine vere: messe sopra la rim, visibili */
  .bulb {{
    position: absolute;
    top: 50%;
    left: 50%;
    width: 13px;
    height: 13px;
    margin-left: -6.5px;
    margin-top: -6.5px;
    border-radius: 999px;
    transform-origin: 0 0;
    animation: blink 1.05s infinite;
  }}
  .bulb.a {{
    background: #FFD36B;
    box-shadow: 0 0 12px rgba(255, 210, 110, 0.98);
  }}
  .bulb.b {{
    background: #FF6B6B;
    box-shadow: 0 0 12px rgba(255, 105, 105, 0.92);
    animation-delay: 0.22s;
  }}
  @keyframes blink {{
    0% {{ opacity: 0.35; filter: saturate(0.9); }}
    50% {{ opacity: 1; filter: saturate(1.25); }}
    100% {{ opacity: 0.35; filter: saturate(0.9); }}
  }}

  .wheel {{
    position: absolute;
    inset: 6%;
    border-radius: 50%;
    transform: rotate(0deg);
    z-index: 10;
  }}

  .face {{
    position: absolute;
    inset: 0;
    border-radius: 50%;
    box-shadow:
      inset 0 0 0 10px rgba(226, 178, 74, 0.92),
      inset 0 0 0 16px rgba(124, 20, 48, 0.92),
      0 24px 44px rgba(0,0,0,0.48);
  }}

  .labels {{
    position: absolute;
    inset: 0;
    border-radius: 50%;
    pointer-events: none;
  }}

  /* Label posizionati correttamente: niente accatastamento */
  .seg-label {{
    position: absolute;
    top: 50%;
    left: 50%;
    transform-origin: 0 0;
    width: 44%;
    text-align: right;
    padding-right: 10%;
    font-weight: 1000;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    color: rgba(255,255,255,0.92);
    text-shadow: 0 3px 4px rgba(0,0,0,0.35);
    user-select: none;
    font-size: clamp(14px, 2.0vw, 28px);
  }}
  .seg-label.active {{
    filter: drop-shadow(0 0 10px rgba(255, 240, 170, 0.92));
  }}
  .seg-label.burned {{
    color: rgba(255,255,255,0.55);
    text-shadow: none;
  }}

  .hub {{
    position: absolute;
    inset: 40%;
    border-radius: 50%;
    background: radial-gradient(circle at 30% 30%, #FFE9A6 0%, #D8A83A 35%, #A47A1F 70%, #5A3A08 100%);
    box-shadow: inset 0 0 0 8px rgba(255,255,255,0.12), 0 10px 22px rgba(0,0,0,0.35);
  }}

  .controls {{
    background: var(--panel);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 16px;
    padding: 14px;
  }}

  .spin {{
    width: 100%;
    font-size: 22px;
    font-weight: 1000;
    padding: 14px 16px;
    border-radius: 16px;
    border: 0;
    cursor: pointer;
    background: linear-gradient(180deg, #F3C35A 0%, #C58B19 100%);
    color: #23180A;
    box-shadow: 0 14px 26px rgba(0,0,0,0.35);
  }}
  .spin:disabled {{ opacity: 0.55; cursor: not-allowed; }}

  .meta {{
    display: flex;
    gap: 10px;
    margin-top: 12px;
    flex-wrap: wrap;
  }}
  .pill {{
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.08);
    padding: 10px 12px;
    border-radius: 14px;
    font-weight: 900;
  }}

  .assignments {{
    margin-top: 12px;
    font-size: 14px;
    line-height: 1.35;
    opacity: 0.95;
  }}
  .assignments .row {{
    display: flex;
    justify-content: space-between;
    padding: 7px 0;
    border-bottom: 1px solid rgba(255,255,255,0.06);
  }}
  .assignments .row:last-child {{ border-bottom: 0; }}
  .assignments .p {{ font-weight: 900; }}
  .assignments .v {{ opacity: 0.9; }}

  /* Overlay */
  .overlay {{
    position: fixed;
    inset: 0;
    display: grid;
    place-items: center;
    background: rgba(0,0,0,0.50);
    opacity: 0;
    pointer-events: none;
    transition: opacity 220ms ease;
    z-index: 9999;
  }}
  .overlay.show {{
    opacity: 1;
    pointer-events: auto;
  }}

  .card {{
    background: rgba(17, 26, 46, 0.92);
    border: 1px solid rgba(255,255,255,0.10);
    border-radius: 18px;
    padding: 14px;
    width: min(720px, 90vw);
    box-shadow: 0 34px 90px rgba(0,0,0,0.60);
    transform: scale(0.85);
    opacity: 0;
  }}
  .card.big {{
    width: min(760px, 92vw);
  }}
  .card.pop {{
    animation: popIn 520ms cubic-bezier(0.16, 0.85, 0.18, 1) forwards;
  }}
  @keyframes popIn {{
    0% {{ transform: scale(0.70); opacity: 0; }}
    70% {{ transform: scale(1.03); opacity: 1; }}
    100% {{ transform: scale(1.00); opacity: 1; }}
  }}

  .imgwrap {{
    position: relative;
    display: grid;
    place-items: center;
    padding: 10px;
  }}
  .img {{
    width: 100%;
    max-height: 66vh;
    object-fit: contain;
    border-radius: 12px;
    background: rgba(255,255,255,0.02);
  }}

  /* Numero sul pacco, leggibile e "in stile" */
  .num {{
    position: absolute;
    inset: 0;
    display: grid;
    place-items: center;
    font-weight: 1000;
    font-size: clamp(64px, 9vw, 132px);
    color: #FFE9A6;
    text-shadow: 0 10px 22px rgba(0,0,0,0.55);
    letter-spacing: 0.03em;
    -webkit-text-stroke: 3px rgba(0,0,0,0.25);
    pointer-events: none;
  }}

  .row-actions {{
    display: flex;
    align-items: end;
    justify-content: space-between;
    gap: 12px;
    padding: 10px 8px 4px 8px;
    flex-wrap: wrap;
  }}

  .ok {{
    background: linear-gradient(180deg, #F3C35A 0%, #C58B19 100%);
    color: #23180A;
    border: 0;
    border-radius: 14px;
    padding: 12px 20px;
    font-weight: 1000;
    font-size: 16px;
    cursor: pointer;
    min-width: 130px;
  }}
  .ok:disabled {{
    opacity: 0.55;
    cursor: not-allowed;
  }}

  .hint {{
    opacity: 0.9;
    font-weight: 800;
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.08);
    padding: 10px 12px;
    border-radius: 14px;
    flex: 1;
    min-width: 220px;
  }}

  .left-pack {{
    display: grid;
    gap: 6px;
    min-width: 240px;
  }}
  .packLabel {{
    font-weight: 900;
    opacity: 0.95;
  }}
  .packInput {{
    border-radius: 12px;
    border: 1px solid rgba(255,255,255,0.16);
    background: rgba(0,0,0,0.22);
    color: var(--text);
    padding: 12px 12px;
    font-size: 16px;
    font-weight: 900;
    outline: none;
  }}

  @media (max-width: 980px) {{
    .stage {{ grid-template-columns: 1fr; }}
  }}
</style>

<script>
(() => {{
  // -----------------------------
  // Config gioco
  // -----------------------------
  const players = Array.from({{length: 10}}, (_, i) => `Player ${{i+1}}`);

  // 10 premi + 4 imprevisti equidistanti
  // Ordine spicchi: distribuiamo 4 malus a 90°
  // Con 14 spicchi: posizioni malus 0, 3, 7, 10 (circa equidistanti)
  const prizes = Array.from({{length: 10}}, (_, i) => String(i+1));

  const malusDefs = [
    {{ id: "MALUS_1", label: "IMPREVISTO", kind: "malus", img: "malus1" }},
    {{ id: "MALUS_2", label: "IMPREVISTO", kind: "malus", img: "malus2" }},
    {{ id: "MALUS_3", label: "IMPREVISTO", kind: "malus", img: "malus3" }},
    {{ id: "MALUS_4", label: "IMPREVISTO", kind: "malus", img: "malus4" }},
  ];

  // Costruiamo segs con 14 spicchi e 4 malus equidistanti.
  // Inseriamo premi negli slot restanti in ordine.
  const malusPositions = new Set([0, 3, 7, 10]);
  const segs = [];
  let prizeIdx = 0;
  let malusIdx = 0;
  for (let i = 0; i < 14; i++) {{
    if (malusPositions.has(i)) {{
      segs.push(malusDefs[malusIdx++]);
    }} else {{
      const p = prizes[prizeIdx++];
      segs.push({{ id: `PRIZE_${{p}}`, label: p, kind: "prize" }});
    }}
  }}

  const bulbsCount = 32;
  const spinSeconds = 10;

  // -----------------------------
  // DOM
  // -----------------------------
  const wheel = document.getElementById("wheel");
  const face = document.getElementById("face");
  const labels = document.getElementById("labels");
  const rim = document.getElementById("rim");
  const spinBtn = document.getElementById("spinBtn");
  const turnLabel = document.getElementById("turnLabel");
  const remainingEl = document.getElementById("remaining");
  const burnedMalusEl = document.getElementById("burnedMalus");
  const assignmentsEl = document.getElementById("assignments");

  const overlayGift = document.getElementById("overlayGift");
  const giftCard = document.getElementById("giftCard");
  const giftNum = document.getElementById("giftNum");
  const giftOk = document.getElementById("giftOk");
  const giftCountdown = document.getElementById("giftCountdown");

  const overlayMalus = document.getElementById("overlayMalus");
  const malusCard = document.getElementById("malusCard");
  const malusImg = document.getElementById("malusImg");
  const malusOk = document.getElementById("malusOk");
  const malusCountdown = document.getElementById("malusCountdown");
  const packPickWrap = document.getElementById("packPickWrap");
  const packPick = document.getElementById("packPick");

  const bgm = document.getElementById("bgm");
  const spinSfx = document.getElementById("spinSfx");
  const giftSfx = document.getElementById("giftSfx");
  const malusSfx = document.getElementById("malusSfx");

  // immagini malus (base64 injected via python)
  const malusImgMap = {{
    "malus1": "data:image/png;base64,{b64s["malus1"]}",
    "malus2": "data:image/png;base64,{b64s["malus2"]}",
    "malus3": "data:image/png;base64,{b64s["malus3"]}",
    "malus4": "data:image/png;base64,{b64s["malus4"]}",
  }};

  // -----------------------------
  // Stato gioco
  // -----------------------------
  let rotation = 0;
  let playerIdxTurn = 0;

  const burnedPrizes = new Set();
  const burnedMalus = new Set();
  const assignments = {{}};

  // malus 1: applicare reorder dopo il successivo turno
  // memorizziamo "pendingReorderAfterNextFor": nome player
  let pendingReorderAfterNextFor = null;

  // per evitare input durante overlay
  let overlayLock = false;

  const sliceDeg = 360 / segs.length;

  function isBurned(id) {{
    if (id.startsWith("PRIZE_")) return burnedPrizes.has(id.split("_")[1]);
    return burnedMalus.has(id);
  }}

  function segColor(i, seg) {{
    if (isBurned(seg.id)) return "#7A7A7A";
    if (seg.kind === "prize") return (i % 2 === 0) ? "#B51E1E" : "#F4E2C6";
    // malus oro
    return "#D8A83A";
  }}

  function buildGradient() {{
    const stops = segs.map((seg, i) => {{
      const c = segColor(i, seg);
      const a0 = i * sliceDeg;
      const a1 = (i + 1) * sliceDeg;
      return `${{c}} ${{a0}}deg ${{a1}}deg`;
    }});
    return `conic-gradient(from -90deg, ${{stops.join(", ")}})`;
  }}

  function renderLabels(activeIndex = null) {{
    labels.innerHTML = "";
    segs.forEach((seg, i) => {{
      const angle = (i + 0.5) * sliceDeg;

      const div = document.createElement("div");
      div.className = "seg-label";
      if (isBurned(seg.id)) div.classList.add("burned");
      if (activeIndex !== null && i === activeIndex) div.classList.add("active");

      div.textContent = (seg.kind === "malus") ? "IMPREVISTO" : seg.label;

      // posizionamento corretto:
      // 1) sposta l'origine al centro (translate(-50%,-50%))
      // 2) ruota di angle
      // 3) trasla lungo raggio (in px) verso l'esterno
      // 4) contro-ruota per tenere testo dritto
      const r = 250; // raggio label, calibrato per wheel grande
      div.style.transform =
        `translate(-50%, -50%) rotate(${{angle}}deg) translate(${{r}}px, 0px) rotate(${{-angle}}deg)`;

      labels.appendChild(div);
    }});
  }}

  function renderBulbs() {{
    rim.innerHTML = "";
    for (let i = 0; i < bulbsCount; i++) {{
      const b = document.createElement("div");
      b.className = "bulb " + (i % 2 === 0 ? "a" : "b");
      const ang = 360 * i / bulbsCount;
      b.style.transform = `rotate(${{ang}}deg) translateY(-49%)`;
      rim.appendChild(b);
    }}
  }}

  function currentPlayer() {{
    return players[playerIdxTurn];
  }}

  function remainingPrizes() {{
    return prizes.filter(x => !burnedPrizes.has(x)).length;
  }}

  function updateUI() {{
    turnLabel.textContent = `Turno: ${{currentPlayer()}}`;
    remainingEl.textContent = String(remainingPrizes());
    burnedMalusEl.textContent = String(burnedMalus.size);

    const rows = players.map(pl => {{
      const val = assignments[pl] ? assignments[pl] : "";
      const state = assignments[pl] ? "✅" : "⏳";
      return `<div class="row"><div class="p">${{pl}}</div><div class="v">${{state}} ${{val}}</div></div>`;
    }});
    assignmentsEl.innerHTML = rows.join("");

    spinBtn.disabled = overlayLock || (remainingPrizes() === 0);
  }}

  function burnSegment(seg) {{
    if (seg.kind === "prize") burnedPrizes.add(seg.label);
    else burnedMalus.add(seg.id);
  }}

  function fadeAudioTo(audio, target, ms) {{
    try {{
      const start = audio.volume;
      const delta = target - start;
      const steps = Math.max(1, Math.floor(ms / 16));
      let i = 0;
      const timer = setInterval(() => {{
        i++;
        audio.volume = Math.max(0, Math.min(1, start + delta * (i / steps)));
        if (i >= steps) clearInterval(timer);
      }}, 16);
    }} catch (e) {{}}
  }}

  function computeRotationForIndex(index, extraSpins) {{
    const center = (index + 0.5) * sliceDeg;
    const base = (360 - center) % 360;
    return extraSpins * 360 + base;
  }}

  function pickStartIndex() {{
    return Math.floor(Math.random() * segs.length);
  }}

  async function playSpinAudio() {{
    try {{
      spinSfx.currentTime = 0;
      await spinSfx.play();
      setTimeout(() => {{
        try {{
          spinSfx.pause();
          spinSfx.currentTime = 0;
        }} catch (e) {{}}
      }}, spinSeconds * 1000);
    }} catch (e) {{}}
  }}

  async function playGiftAudio() {{
    try {{
      giftSfx.currentTime = 0;
      await giftSfx.play();
    }} catch (e) {{}}
  }}

  async function playMalusAudio() {{
    try {{
      malusSfx.currentTime = 0;
      await malusSfx.play();
    }} catch (e) {{}}
  }}

  function showGiftOverlay(prizeLabel) {{
    overlayLock = true;
    spinBtn.disabled = true;

    giftNum.textContent = prizeLabel;

    overlayGift.classList.add("show");
    giftCard.classList.remove("pop");
    void giftCard.offsetWidth;
    giftCard.classList.add("pop");

    giftOk.disabled = true;
    let t = 12;
    giftCountdown.textContent = String(t);

    const timer = setInterval(() => {{
      t -= 1;
      giftCountdown.textContent = String(Math.max(0, t));
      if (t <= 0) {{
        clearInterval(timer);
        giftOk.disabled = false;
      }}
    }}, 1000);
  }}

  function hideGiftOverlay() {{
    overlayGift.classList.remove("show");
    giftCard.classList.remove("pop");
    overlayLock = false;
    updateUI();
  }}

  function showMalusOverlay(malusSeg) {{
    overlayLock = true;
    spinBtn.disabled = true;

    malusImg.src = malusImgMap[malusSeg.img];

    overlayMalus.classList.add("show");
    malusCard.classList.remove("pop");
    void malusCard.offsetWidth;
    malusCard.classList.add("pop");

    // malus2: input visibile solo quando compare OK
    packPickWrap.style.display = "none";
    packPick.value = "";

    malusOk.disabled = true;
    let t = 12;
    malusCountdown.textContent = String(t);

    const timer = setInterval(() => {{
      t -= 1;
      malusCountdown.textContent = String(Math.max(0, t));
      if (t <= 0) {{
        clearInterval(timer);
        malusOk.disabled = false;
        if (malusSeg.id === "MALUS_2") {{
          packPickWrap.style.display = "grid";
          packPick.focus();
        }}
      }}
    }}, 1000);
  }}

  function hideMalusOverlay() {{
    overlayMalus.classList.remove("show");
    malusCard.classList.remove("pop");
    packPickWrap.style.display = "none";
    overlayLock = false;
    updateUI();
  }}

  function advanceTurn() {{
    playerIdxTurn = (playerIdxTurn + 1) % players.length;
  }}

  // Reorder players in-place helpers
  function movePlayerToEnd(playerName) {{
    const i = players.indexOf(playerName);
    if (i < 0) return;
    const p = players.splice(i, 1)[0];
    players.push(p);
  }}

  // Malus 1: riposiziona dopo il successivo turno.
  // Implementazione: memorizza il player; quando termina il prossimo turno (dopo che si assegna un premio o si chiude un overlay),
  // sposta quel player a immediatamente dopo il player che ha appena giocato.
  function applyPendingReorderAfterNext(lastPlayedPlayer) {{
    if (!pendingReorderAfterNextFor) return;

    const target = pendingReorderAfterNextFor;
    pendingReorderAfterNextFor = null;

    // posizione: dopo lastPlayedPlayer
    const idxLast = players.indexOf(lastPlayedPlayer);
    const idxTarget = players.indexOf(target);
    if (idxLast < 0 || idxTarget < 0) return;
    if (idxTarget === idxLast + 1) return; // già dopo

    const p = players.splice(idxTarget, 1)[0];
    const insertAt = Math.min(players.length, idxLast + 1);
    players.splice(insertAt, 0, p);
  }}

  async function resolveBurnedByNudging(startIdx) {{
    let idx = startIdx;
    let safety = 0;

    while (isBurned(segs[idx].id)) {{
      renderLabels(idx);

      idx = (idx + 1) % segs.length;

      const nudge = computeRotationForIndex(idx, 0);
      rotation = (Math.floor(rotation / 360) * 360) + nudge;

      wheel.style.transition = "transform 280ms ease";
      wheel.style.transform = `rotate(${{rotation}}deg)`;

      await new Promise(r => setTimeout(r, 300));

      safety++;
      if (safety > segs.length + 2) break;
    }}

    return idx;
  }}

  async function spin() {{
    if (overlayLock) return;

    const player = currentPlayer();

    // se ha già premio: salta
    if (assignments[player]) {{
      advanceTurn();
      updateUI();
      return;
    }}

    spinBtn.disabled = true;

    // fade out bgm
    try {{
      bgm.volume = (typeof bgm.volume === "number") ? bgm.volume : 0.7;
      fadeAudioTo(bgm, 0.0, 350);
    }} catch (e) {{}}

    // audio spin 10s
    playSpinAudio();

    // costruisci wheel
    face.style.background = buildGradient();
    renderLabels(null);

    const startIdx = pickStartIndex();
    const targetRot = computeRotationForIndex(startIdx, 8);
    rotation = rotation + targetRot;

    wheel.style.transition = `transform ${{spinSeconds}}s cubic-bezier(0.10, 0.75, 0.10, 1)`;
    wheel.style.transform = `rotate(${{rotation}}deg)`;

    await new Promise(r => setTimeout(r, spinSeconds * 1000));

    // se capita su bruciato, micro-scatto avanti finché trova valido
    const finalIdx = await resolveBurnedByNudging(startIdx);

    renderLabels(finalIdx);

    const seg = segs[finalIdx];
    if (isBurned(seg.id)) {{
      // tutto bruciato, non dovrebbe accadere
      spinBtn.disabled = false;
      fadeAudioTo(bgm, 0.7, 450);
      updateUI();
      return;
    }}

    // brucia subito seg
    burnSegment(seg);

    // aggiorna ruota (grigi)
    face.style.background = buildGradient();
    renderLabels(finalIdx);

    // premio o malus
    if (seg.kind === "prize") {{
      assignments[player] = seg.label;

      await playGiftAudio();
      showGiftOverlay(seg.label);

      // l'avanzamento turno avviene quando si preme OK (dopo 12s)
      return;
    }}

    // malus
    await playMalusAudio();
    showMalusOverlay(seg);

    // effetti malus (alcuni immediati, altri alla conferma OK)
    if (seg.id === "MALUS_1") {{
      // riposiziona dopo il successivo turno
      pendingReorderAfterNextFor = player;
    }}

    if (seg.id === "MALUS_3") {{
      // per ultimo subito
      movePlayerToEnd(player);
    }}

    if (seg.id === "MALUS_4") {{
      // altro tentativo: non avanzare turno alla chiusura, resta sullo stesso player
      // lo gestiamo nel click OK (non chiamando advanceTurn)
    }}

    // malus2: assegnazione pacco gestita al click OK con input
  }}

  // -----------------------------
  // OK handlers
  // -----------------------------
  giftOk.addEventListener("click", () => {{
    const lastPlayed = currentPlayer();

    hideGiftOverlay();

    // dopo chiusura premio: applica reorder pendente (malus1) riferito al turno successivo
    applyPendingReorderAfterNext(lastPlayed);

    // avanza turno
    advanceTurn();

    // fade in bgm
    try {{
      fadeAudioTo(bgm, 0.7, 450);
      bgm.play().catch(() => {{}});
    }} catch (e) {{}}

    updateUI();
  }});

  malusOk.addEventListener("click", () => {{
    const lastPlayed = currentPlayer();

    // recupera quale malus era mostrato guardando src dell'immagine
    // (si può anche tenere stato, qui usiamo un piccolo stato dedicato)
  }});

  let activeMalusId = null;

  function setActiveMalusIdFromImg() {{
    const src = malusImg.getAttribute("src") || "";
    if (src.includes("{b64s["malus1"]}".slice(0, 20))) activeMalusId = "MALUS_1";
    else if (src.includes("{b64s["malus2"]}".slice(0, 20))) activeMalusId = "MALUS_2";
    else if (src.includes("{b64s["malus3"]}".slice(0, 20))) activeMalusId = "MALUS_3";
    else if (src.includes("{b64s["malus4"]}".slice(0, 20))) activeMalusId = "MALUS_4";
  }}

  // aggancia ogni volta che si cambia immagine
  const origShowMalus = showMalusOverlay;
  showMalusOverlay = function(malusSeg) {{
    activeMalusId = malusSeg.id;
    return origShowMalus(malusSeg);
  }}

  malusOk.addEventListener("click", () => {{
    const player = currentPlayer();

    // malus2: assegna pacco scelto e brucia
    if (activeMalusId === "MALUS_2") {{
      const raw = (packPick.value || "").trim();
      const n = parseInt(raw, 10);

      if (!Number.isFinite(n) || n < 1 || n > 10) {{
        alert("Inserisci un numero pacco valido (1-10).");
        return;
      }}
      const pack = String(n);
      if (burnedPrizes.has(pack)) {{
        alert("Quel pacco è già bruciato. Scegline un altro.");
        return;
      }}

      assignments[player] = pack;
      burnedPrizes.add(pack);

      // aggiorna wheel: quel premio diventa grigio
      face.style.background = buildGradient();
      renderLabels(null);
    }}

    hideMalusOverlay();

    // malus4: altro tentativo, non avanza turno
    if (activeMalusId === "MALUS_4") {{
      // fade in bgm e resta sullo stesso player
      try {{
        fadeAudioTo(bgm, 0.7, 450);
        bgm.play().catch(() => {{}});
      }} catch (e) {{}}
      updateUI();
      return;
    }}

    // dopo chiusura malus: applica reorder pendente se il turno appena concluso è "quello successivo"
    applyPendingReorderAfterNext(player);

    // avanza turno normalmente
    advanceTurn();

    // fade in bgm
    try {{
      fadeAudioTo(bgm, 0.7, 450);
      bgm.play().catch(() => {{}});
    }} catch (e) {{}}

    updateUI();
  }});

  // -----------------------------
  // Init
  // -----------------------------
  function init() {{
    renderBulbs();
    face.style.background = buildGradient();
    renderLabels(null);
    updateUI();

    // tenta autoplay bgm (browser può bloccare finché non c'è click)
    try {{
      bgm.volume = 0.7;
      bgm.play().catch(() => {{}});
    }} catch (e) {{}}

    spinBtn.addEventListener("click", () => {{
      // spesso questo click sblocca audio
      try {{ bgm.play().catch(() => {{}}); }} catch (e) {{}}
      spin();
    }});
  }}

  init();
}})();
</script>
"""

components.html(html, height=980, scrolling=False)


