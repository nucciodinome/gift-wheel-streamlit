import base64
import os
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Ruota Regali", page_icon="🎁", layout="wide")

ASSETS_DIR = "assets"
BGM_PATH = os.path.join(ASSETS_DIR, "bgm.mp3")
SPIN_PATH = os.path.join(ASSETS_DIR, "spin.mp3")
GIFT_PATH = os.path.join(ASSETS_DIR, "gift.mp3")

def b64_file(path: str) -> str:
    if not os.path.exists(path):
        st.error(f"File mancante: {path}")
        st.stop()
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

bgm_b64 = b64_file(BGM_PATH)
spin_b64 = b64_file(SPIN_PATH)
gift_b64 = b64_file(GIFT_PATH)

# UI minimale, niente menu setup
st.markdown(
    """
    <style>
      .block-container { padding-top: 1.2rem; padding-bottom: 1.2rem; }
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
      <div class="pointer"></div>

      <div class="rim" id="rim">
        <!-- bulbs injected by JS -->
      </div>

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
        <div class="pill">Bonus/Malus bruciati: <span id="burnedSpecials">0</span></div>
      </div>
      <div class="assignments" id="assignments"></div>
    </div>
  </div>

  <div class="overlay" id="overlay" aria-hidden="true">
    <div class="gift-card" id="giftCard">
      <div class="stars">
        <span>✨</span><span>✨</span><span>✨</span><span>✨</span><span>✨</span>
      </div>
      <div class="gift-box">
        <div class="gift-num" id="giftNum">1</div>
      </div>
      <div class="stars">
        <span>✨</span><span>✨</span><span>✨</span><span>✨</span><span>✨</span>
      </div>
    </div>
  </div>

  <!-- Audio -->
  <audio id="bgm" autoplay loop preload="auto" playsinline>
    <source src="data:audio/mpeg;base64,{bgm_b64}" type="audio/mpeg" />
  </audio>

  <audio id="spinSfx" preload="auto" playsinline>
    <source src="data:audio/mpeg;base64,{spin_b64}" type="audio/mpeg" />
  </audio>

  <audio id="giftSfx" preload="auto" playsinline>
    <source src="data:audio/mpeg;base64,{gift_b64}" type="audio/mpeg" />
  </audio>
</div>

<style>
  :root {{
    --bg: #0B1220;
    --panel: #111A2E;
    --gold: #E2B24A;
    --deep-red: #7C1430;
    --cream: #F4E2C6;
    --red: #B51E1E;
    --gray: #707070;
    --text: #E5E7EB;
  }}

  body {{ background: var(--bg); }}
  #app {{
    color: var(--text);
    font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial;
  }}

  .topbar {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin: 0 0 14px 0;
    padding: 10px 14px;
    background: rgba(17, 26, 46, 0.75);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 16px;
    backdrop-filter: blur(6px);
  }}
  .title {{
    font-weight: 900;
    letter-spacing: 0.02em;
    font-size: 18px;
  }}
  .turn {{
    font-weight: 800;
    opacity: 0.95;
  }}

  .stage {{
    display: grid;
    grid-template-columns: 1.2fr 0.8fr;
    gap: 18px;
    align-items: start;
  }}

  .wheel-wrap {{
    position: relative;
    width: min(760px, 92vw);
    aspect-ratio: 1 / 1;
    margin: 0 auto;
  }}

  .pointer {{
    position: absolute;
    top: 0.6%;
    left: 50%;
    transform: translateX(-50%);
    width: 0; height: 0;
    border-left: 24px solid transparent;
    border-right: 24px solid transparent;
    border-bottom: 46px solid var(--gold);
    filter: drop-shadow(0 6px 6px rgba(0,0,0,0.35));
    z-index: 50;
  }}

  .rim {{
    position: absolute;
    inset: 0;
    border-radius: 50%;
    background: radial-gradient(circle at 50% 50%, rgba(0,0,0,0) 62%, rgba(0,0,0,0.45) 86%, rgba(0,0,0,0.85) 100%);
    z-index: 5;
  }}

  .bulb {{
    position: absolute;
    top: 50%;
    left: 50%;
    width: 12px;
    height: 12px;
    margin-left: -6px;
    margin-top: -6px;
    border-radius: 50%;
    transform-origin: 0 0;
    animation: blink 1.1s infinite;
  }}
  .bulb.a {{
    background: #FFD36B;
    box-shadow: 0 0 10px rgba(255, 210, 110, 0.95);
  }}
  .bulb.b {{
    background: #FF6B6B;
    box-shadow: 0 0 10px rgba(255, 105, 105, 0.9);
    animation-delay: 0.22s;
  }}

  @keyframes blink {{
    0% {{ opacity: 0.35; filter: saturate(0.9); }}
    50% {{ opacity: 1; filter: saturate(1.2); }}
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
      inset 0 0 0 10px rgba(226, 178, 74, 0.9),
      inset 0 0 0 16px rgba(124, 20, 48, 0.9),
      0 22px 40px rgba(0,0,0,0.45);
  }}

  .labels {{
    position: absolute;
    inset: 0;
    border-radius: 50%;
    pointer-events: none;
  }}

  .seg-label {{
    position: absolute;
    top: 50%;
    left: 50%;
    width: 46%;
    text-align: right;
    padding-right: 8%;
    font-weight: 900;
    letter-spacing: 0.02em;
    color: rgba(255,255,255,0.92);
    text-shadow: 0 3px 4px rgba(0,0,0,0.35);
    user-select: none;
    font-size: clamp(14px, 2.2vw, 30px);
  }}
  .seg-label.burned {{
    color: rgba(255,255,255,0.55);
    text-shadow: none;
  }}
  .seg-label.active {{
    filter: drop-shadow(0 0 10px rgba(255, 240, 170, 0.85));
  }}

  .hub {{
    position: absolute;
    inset: 40%;
    border-radius: 50%;
    background: radial-gradient(circle at 30% 30%, #FFE9A6 0%, #D8A83A 35%, #A47A1F 70%, #5A3A08 100%);
    box-shadow: inset 0 0 0 8px rgba(255,255,255,0.12), 0 10px 22px rgba(0,0,0,0.35);
  }}

  .controls {{
    background: rgba(17, 26, 46, 0.75);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 16px;
    padding: 14px;
  }}

  .spin {{
    width: 100%;
    font-size: 22px;
    font-weight: 900;
    padding: 14px 16px;
    border-radius: 16px;
    border: 0;
    cursor: pointer;
    background: linear-gradient(180deg, #F3C35A 0%, #C58B19 100%);
    color: #23180A;
    box-shadow: 0 14px 26px rgba(0,0,0,0.35);
  }}
  .spin:disabled {{
    opacity: 0.55;
    cursor: not-allowed;
  }}

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
    font-weight: 800;
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
  .assignments .p {{ font-weight: 800; }}
  .assignments .v {{ opacity: 0.9; }}

  .overlay {{
    position: fixed;
    inset: 0;
    display: grid;
    place-items: center;
    background: rgba(0,0,0,0.45);
    opacity: 0;
    pointer-events: none;
    transition: opacity 200ms ease;
    z-index: 9999;
  }}
  .overlay.show {{
    opacity: 1;
    pointer-events: auto;
  }}

  .gift-card {{
    display: grid;
    gap: 14px;
    place-items: center;
    transform: scale(0.7);
    opacity: 0;
  }}
  .gift-card.go {{
    animation: giftPop 2s ease forwards;
  }}
  @keyframes giftPop {{
    0% {{ transform: scale(0.55); opacity: 0; }}
    15% {{ transform: scale(1.02); opacity: 1; }}
    35% {{ transform: scale(0.96); }}
    55% {{ transform: scale(1.03); }}
    75% {{ transform: scale(0.98); }}
    100% {{ transform: scale(1.25); opacity: 0; }}
  }}

  .gift-box {{
    width: min(420px, 72vw);
    aspect-ratio: 1 / 1;
    border-radius: 28px;
    background: linear-gradient(180deg, #E03B3B 0%, #8F1414 100%);
    box-shadow: 0 24px 60px rgba(0,0,0,0.55), inset 0 0 0 10px rgba(255,255,255,0.12);
    display: grid;
    place-items: center;
    position: relative;
  }}
  .gift-box::before {{
    content: "";
    position: absolute;
    inset: 0;
    border-radius: 28px;
    background: linear-gradient(90deg, rgba(226,178,74,0.0) 0%, rgba(226,178,74,0.9) 48%, rgba(226,178,74,0.0) 100%);
    mix-blend-mode: overlay;
    opacity: 0.75;
  }}
  .gift-num {{
    font-size: clamp(56px, 7vw, 110px);
    font-weight: 1000;
    color: #FFE9A6;
    text-shadow: 0 8px 18px rgba(0,0,0,0.45);
    position: relative;
    z-index: 1;
  }}
  .stars {{
    font-size: 28px;
    opacity: 0.95;
    filter: drop-shadow(0 6px 10px rgba(0,0,0,0.35));
  }}

  @media (max-width: 980px) {{
    .stage {{
      grid-template-columns: 1fr;
    }}
  }}
</style>

<script>
(() => {{
  const players = Array.from({{length: 10}}, (_, i) => `Player ${{i+1}}`);
  const specials = [
    {{ id: "BONUS_2PICK", label: "BONUS: scegli tra 2", kind: "bonus" }},
    {{ id: "BONUS_SWAP", label: "BONUS: scambio", kind: "bonus" }},
    {{ id: "MALUS_WORST2", label: "MALUS: peggiore di 2", kind: "malus" }},
    {{ id: "MALUS_SKIP", label: "MALUS: salta prossimo", kind: "malus" }},
  ];
  const prizes = Array.from({{length: 10}}, (_, i) => String(i+1));
  const segs = [
    ...prizes.map(p => ({{ id: `PRIZE_${{p}}`, label: p, kind: "prize" }})),
    ...specials
  ];

  const wheel = document.getElementById("wheel");
  const face = document.getElementById("face");
  const labels = document.getElementById("labels");
  const rim = document.getElementById("rim");
  const spinBtn = document.getElementById("spinBtn");
  const turnLabel = document.getElementById("turnLabel");
  const remainingEl = document.getElementById("remaining");
  const burnedSpecialsEl = document.getElementById("burnedSpecials");
  const assignmentsEl = document.getElementById("assignments");

  const overlay = document.getElementById("overlay");
  const giftCard = document.getElementById("giftCard");
  const giftNum = document.getElementById("giftNum");

  const bgm = document.getElementById("bgm");
  const spinSfx = document.getElementById("spinSfx");
  const giftSfx = document.getElementById("giftSfx");

  const bulbsCount = 28;
  const sliceDeg = 360 / segs.length;

  let rotation = 0;
  let playerIdx = 0;

  const burnedPrizes = new Set();
  const burnedSpecials = new Set();
  const assignments = {{}};
  const skipNext = new Set();

  function isBurned(id) {{
    if (id.startsWith("PRIZE_")) return burnedPrizes.has(id.split("_")[1]);
    return burnedSpecials.has(id);
  }}

  function segColor(i, seg) {{
    if (isBurned(seg.id)) return "#707070";
    if (seg.kind === "prize") return (i % 2 === 0) ? "#B51E1E" : "#F4E2C6";
    if (seg.kind === "bonus") return "#D8A83A";
    return "#7C1430";
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

      const short = (seg.kind === "prize") ? seg.label : (seg.kind === "bonus" ? "BONUS" : "MALUS");
      div.textContent = short;

      div.style.transform = `rotate(${{angle}}deg) translateY(-39%) rotate(${{-angle}}deg)`;
      labels.appendChild(div);
    }});
  }}

  function renderRimBulbs() {{
    rim.innerHTML = "";
    for (let i = 0; i < bulbsCount; i++) {{
      const b = document.createElement("div");
      b.className = "bulb " + (i % 2 === 0 ? "a" : "b");
      const ang = 360 * i / bulbsCount;
      b.style.transform = `rotate(${{ang}}deg) translateY(-49%)`;
      rim.appendChild(b);
    }}
  }}

  function updateUI() {{
    const p = players[playerIdx];
    turnLabel.textContent = `Turno: ${{p}}`;

    const remaining = prizes.filter(x => !burnedPrizes.has(x)).length;
    remainingEl.textContent = String(remaining);
    burnedSpecialsEl.textContent = String(burnedSpecials.size);

    const rows = players.map(pl => {{
      const val = assignments[pl] ? assignments[pl] : "";
      const state = assignments[pl] ? "✅" : "⏳";
      return `<div class="row"><div class="p">${{pl}}</div><div class="v">${{state}} ${{val}}</div></div>`;
    }});
    assignmentsEl.innerHTML = rows.join("");
    spinBtn.disabled = remaining === 0;
  }}

  function burnSegment(seg) {{
    if (seg.kind === "prize") burnedPrizes.add(seg.label);
    else burnedSpecials.add(seg.id);
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

  function nextUnburnedIndex(startIdx) {{
    let idx = startIdx;
    const path = [];
    let safety = 0;
    while (isBurned(segs[idx].id)) {{
      path.push(idx);
      idx = (idx + 1) % segs.length;
      safety++;
      if (safety > segs.length + 2) break;
    }}
    return {{ finalIdx: idx, skippedPath: path }};
  }}

  async function playSpinAudio10s() {{
    if (!spinSfx) return;
    try {{
      spinSfx.currentTime = 0;
      await spinSfx.play();
      setTimeout(() => {{
        try {{
          spinSfx.pause();
          spinSfx.currentTime = 0;
        }} catch (e) {{}}
      }}, 10000);
    }} catch (e) {{}}
  }}

  async function playGiftAudio() {{
    if (!giftSfx) return;
    try {{
      giftSfx.currentTime = 0;
      await giftSfx.play();
    }} catch (e) {{}}
  }}

  function showGiftAnimation(numberStr) {{
    giftNum.textContent = numberStr;
    overlay.classList.add("show");
    giftCard.classList.remove("go");
    void giftCard.offsetWidth;
    giftCard.classList.add("go");

    setTimeout(() => {{
      overlay.classList.remove("show");
      giftCard.classList.remove("go");
    }}, 2000);
  }}

  function advancePlayer() {{
    playerIdx = (playerIdx + 1) % players.length;
  }}

  function applySpecial(seg, player) {{
    const avail = prizes.filter(x => !burnedPrizes.has(x));
    if (avail.length === 0) return;

    if (seg.id === "MALUS_SKIP") {{
      skipNext.add(player);
      return;
    }}

    if (seg.id === "BONUS_2PICK") {{
      const a = avail[Math.floor(Math.random() * avail.length)];
      const bPool = avail.filter(x => x !== a);
      const b = bPool.length ? bPool[Math.floor(Math.random() * bPool.length)] : a;
      const chosen = window.confirm(`BONUS: scegli tra ${{a}} e ${{b}}. OK=${{a}}, Annulla=${{b}}`) ? a : b;
      burnedPrizes.add(chosen);
      assignments[player] = chosen;
      return;
    }}

    if (seg.id === "MALUS_WORST2") {{
      const a = avail[Math.floor(Math.random() * avail.length)];
      const bPool = avail.filter(x => x !== a);
      const b = bPool.length ? bPool[Math.floor(Math.random() * bPool.length)] : a;
      const ai = parseInt(a, 10);
      const bi = parseInt(b, 10);
      const worst = (Number.isFinite(ai) && Number.isFinite(bi)) ? (ai > bi ? a : b) : b;
      burnedPrizes.add(worst);
      assignments[player] = worst;
      return;
    }}

    if (seg.id === "BONUS_SWAP") {{
      const targets = players.filter(pl => pl !== player && assignments[pl]);
      if (!targets.length) {{
        const x = avail[Math.floor(Math.random() * avail.length)];
        burnedPrizes.add(x);
        assignments[player] = x;
        return;
      }}
      const t = targets[Math.floor(Math.random() * targets.length)];
      const tmp = assignments[t];
      assignments[t] = assignments[player] ? assignments[player] : "";
      assignments[player] = tmp;
      return;
    }}
  }}

  async function spin() {{
    const player = players[playerIdx];

    if (assignments[player]) {{
      advancePlayer();
      updateUI();
      return;
    }}

    if (skipNext.has(player)) {{
      skipNext.delete(player);
      advancePlayer();
      updateUI();
      return;
    }}

    spinBtn.disabled = true;

    try {{
      bgm.volume = bgm.volume || 0.7;
      fadeAudioTo(bgm, 0.0, 350);
    }} catch (e) {{}}

    playSpinAudio10s();

    const startIdx = pickStartIndex();
    const {{ finalIdx, skippedPath }} = nextUnburnedIndex(startIdx);

    renderLabels(null);
    face.style.background = buildGradient();

    const targetRot = computeRotationForIndex(startIdx, 7);
    rotation = rotation + targetRot;

    wheel.style.transition = "transform 10s cubic-bezier(0.10, 0.75, 0.10, 1)";
    wheel.style.transform = `rotate(${{rotation}}deg)`;

    await new Promise(resolve => setTimeout(resolve, 10000));

    // “passa allo spicchio successivo” se bruciato, con piccoli scatti
    let idx = startIdx;
    let safety = 0;
    while (isBurned(segs[idx].id)) {{
      renderLabels(idx);
      idx = (idx + 1) % segs.length;

      const nudge = computeRotationForIndex(idx, 0);
      rotation = (Math.floor(rotation / 360) * 360) + nudge;

      wheel.style.transition = "transform 280ms ease";
      wheel.style.transform = `rotate(${{rotation}}deg)`;

      await new Promise(resolve => setTimeout(resolve, 300));
      safety++;
      if (safety > segs.length + 2) break;
    }}

    // idx è il primo non bruciato
    renderLabels(idx);

    const seg = segs[idx];
    burnSegment(seg);

    // aggiorna grafica wheel: grigio su bruciati
    face.style.background = buildGradient();
    renderLabels(idx);

    if (seg.kind === "prize") {{
      assignments[player] = seg.label;
      await playGiftAudio();
      showGiftAnimation(seg.label);
      await new Promise(resolve => setTimeout(resolve, 2000));
      advancePlayer();
    }} else {{
      // special: bruciato ma niente pacco premio
      applySpecial(seg, player);
      advancePlayer();
    }}

    // fade in bgm
    try {{
      fadeAudioTo(bgm, 0.7, 450);
      bgm.play().catch(() => {{}});
    }} catch (e) {{}}

    updateUI();
    spinBtn.disabled = prizes.filter(x => !burnedPrizes.has(x)).length === 0 ? true : false;
  }}

  function init() {{
    renderRimBulbs();
    face.style.background = buildGradient();
    renderLabels(null);
    updateUI();

    // prova autoplay bgm
    try {{
      bgm.volume = 0.7;
      bgm.play().catch(() => {{}});
    }} catch (e) {{}}

    spinBtn.addEventListener("click", () => {{
      // spesso questo click sblocca audio autoplay
      try {{ bgm.play().catch(() => {{}}); }} catch (e) {{}}
      spin();
    }});
  }}

  init();
}})();
</script>
"""

components.html(html, height=980, scrolling=False)

