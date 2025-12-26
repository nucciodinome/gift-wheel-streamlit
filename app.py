import base64
import json
import os
import random
import time
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple

import numpy as np
import streamlit as st
import streamlit.components.v1 as components


# ----------------------------
# Config
# ----------------------------
st.set_page_config(page_title="Ruota Regali", page_icon="🎁", layout="wide")

ASSETS_DIR = "assets"
DEFAULT_BGM_PATH = os.path.join(ASSETS_DIR, "bgm.mp3")
DEFAULT_SPIN_SFX_PATH = os.path.join(ASSETS_DIR, "spin.mp3")

WHEEL_BULBS = 28  # luci sul bordo
BASE_SPINS = 5    # giri completi prima di fermarsi


# ----------------------------
# Modelli
# ----------------------------
@dataclass(frozen=True)
class SpecialSlot:
    code: str
    label: str
    kind: str  # bonus, malus


SPECIAL_SLOTS = [
    SpecialSlot(code="BONUS_2PICK", label="BONUS: scegli tra 2", kind="bonus"),
    SpecialSlot(code="BONUS_SWAP", label="BONUS: scambio", kind="bonus"),
    SpecialSlot(code="MALUS_WORST2", label="MALUS: peggiore di 2", kind="malus"),
    SpecialSlot(code="MALUS_SKIP", label="MALUS: salta prossimo", kind="malus"),
]


# ----------------------------
# State
# ----------------------------
def init_state():
    if "players" not in st.session_state:
        st.session_state.players = [f"Player {i}" for i in range(1, 11)]
    if "prizes" not in st.session_state:
        st.session_state.prizes = [str(i) for i in range(1, 11)]
    if "assignments" not in st.session_state:
        st.session_state.assignments = {}  # player -> prize
    if "player_idx" not in st.session_state:
        st.session_state.player_idx = 0
    if "burned_prizes" not in st.session_state:
        st.session_state.burned_prizes = set()
    if "burned_specials" not in st.session_state:
        st.session_state.burned_specials = set()
    if "skip_next" not in st.session_state:
        st.session_state.skip_next = set()

    if "pending_effect" not in st.session_state:
        st.session_state.pending_effect = None

    if "music_enabled" not in st.session_state:
        st.session_state.music_enabled = False

    if "bgm_bytes" not in st.session_state:
        st.session_state.bgm_bytes = None
    if "spin_bytes" not in st.session_state:
        st.session_state.spin_bytes = None

    if "wheel_rotation" not in st.session_state:
        st.session_state.wheel_rotation = 0.0  # gradi, cresce

    if "last_audio_event" not in st.session_state:
        st.session_state.last_audio_event = None  # "spin" etc


def reset_game(players: List[str], prizes: List[str]):
    st.session_state.players = players
    st.session_state.prizes = prizes
    st.session_state.assignments = {}
    st.session_state.player_idx = 0
    st.session_state.burned_prizes = set()
    st.session_state.burned_specials = set()
    st.session_state.skip_next = set()
    st.session_state.pending_effect = None
    st.session_state.wheel_rotation = 0.0
    st.session_state.last_audio_event = None


def current_player() -> str:
    return st.session_state.players[st.session_state.player_idx]


def advance_player():
    st.session_state.player_idx = (st.session_state.player_idx + 1) % len(st.session_state.players)


# ----------------------------
# Audio helpers
# ----------------------------
def read_file_bytes(path: str) -> Optional[bytes]:
    if path and os.path.exists(path):
        with open(path, "rb") as f:
            return f.read()
    return None


def bytes_to_data_uri(file_bytes: bytes, mime: str) -> str:
    b64 = base64.b64encode(file_bytes).decode("utf-8")
    return f"data:{mime};base64,{b64}"


# ----------------------------
# Ruota: segmenti e rendering
# ----------------------------
def build_segments() -> List[Dict]:
    # ordine fisso: 10 premi + 4 speciali
    segs = []
    for p in st.session_state.prizes:
        segs.append({"id": f"PRIZE_{p}", "label": p, "kind": "prize"})
    for s in SPECIAL_SLOTS:
        segs.append({"id": s.code, "label": s.label, "kind": s.kind})
    return segs


def is_burned(seg_id: str) -> bool:
    if seg_id.startswith("PRIZE_"):
        prize = seg_id.split("_", 1)[1]
        return prize in st.session_state.burned_prizes
    return seg_id in st.session_state.burned_specials


def seg_color(i: int, seg: Dict) -> str:
    # palette stile “casino”: rosso e crema, bonus oro, malus bordeaux
    if is_burned(seg["id"]):
        return "#7A7A7A"
    if seg["kind"] == "prize":
        return "#B51E1E" if (i % 2 == 0) else "#F4E2C6"
    if seg["kind"] == "bonus":
        return "#D8A83A"
    return "#7C1430"


def build_conic_gradient(segs: List[Dict]) -> str:
    n = len(segs)
    slice_deg = 360.0 / n
    stops = []
    for i, seg in enumerate(segs):
        c = seg_color(i, seg)
        a0 = i * slice_deg
        a1 = (i + 1) * slice_deg
        stops.append(f"{c} {a0:.4f}deg {a1:.4f}deg")
    # from -90deg così il primo spicchio inizia in alto
    return "conic-gradient(from -90deg, " + ", ".join(stops) + ")"


def compute_target_rotation_for_index(index: int, n: int, extra_spins: int = BASE_SPINS) -> float:
    slice_deg = 360.0 / n
    center_deg = (index + 0.5) * slice_deg
    # vogliamo portare il centro in alto (0deg “top” dopo from -90deg), quindi ruotiamo di (360 - center)
    base = (360.0 - center_deg) % 360.0
    return extra_spins * 360.0 + base


def render_wheel_html(
    segs: List[Dict],
    rotation_deg: float,
    highlight_index: Optional[int],
    big: bool = True,
) -> str:
    n = len(segs)
    gradient = build_conic_gradient(segs)
    size_px = 680 if big else 520

    # etichette: posizionate con trasformazioni
    slice_deg = 360.0 / n
    label_divs = []
    for i, seg in enumerate(segs):
        angle = (i + 0.5) * slice_deg
        # testo corto per premi, testo più piccolo per speciali
        label = seg["label"]
        short = label if seg["kind"] == "prize" else ("BONUS" if seg["kind"] == "bonus" else "MALUS")
        burned_cls = "burned" if is_burned(seg["id"]) else ""
        active_cls = "active" if (highlight_index is not None and i == highlight_index) else ""
        label_divs.append(
            f"""
            <div class="seg-label {burned_cls} {active_cls}"
                 style="transform: rotate({angle:.4f}deg) translateY(-39%) rotate({-angle:.4f}deg);">
              {short}
            </div>
            """
        )

    bulbs = "\n".join([f'<div class="bulb b{i}"></div>' for i in range(WHEEL_BULBS)])

    # luci: posizionate su circonferenza
    bulb_css = []
    for i in range(WHEEL_BULBS):
        ang = (360.0 * i) / WHEEL_BULBS
        bulb_css.append(
            f"""
            .b{i} {{
              transform: rotate({ang:.4f}deg) translateY(-49%);
            }}
            """
        )

    html = f"""
    <div class="wheel-wrap">
      <div class="pointer"></div>

      <div class="rim">
        {bulbs}
      </div>

      <div class="wheel" style="--rot: {rotation_deg:.4f}deg;">
        <div class="face"></div>
        {''.join(label_divs)}
        <div class="hub"></div>
      </div>
    </div>

    <style>
      .wheel-wrap {{
        position: relative;
        width: min({size_px}px, 92vw);
        aspect-ratio: 1 / 1;
        margin: 0 auto;
      }}

      .pointer {{
        position: absolute;
        top: 0.8%;
        left: 50%;
        transform: translateX(-50%);
        width: 0;
        height: 0;
        border-left: 22px solid transparent;
        border-right: 22px solid transparent;
        border-bottom: 42px solid #E2B24A;
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
        background: #FFD36B;
        box-shadow: 0 0 10px rgba(255, 210, 110, 0.95);
        transform-origin: 0 0;
        animation: blink 1.1s infinite;
      }}

      /* alterna fase di blink */
      .bulb:nth-child(2n) {{
        animation-delay: 0.22s;
        background: #FF6B6B;
        box-shadow: 0 0 10px rgba(255, 105, 105, 0.9);
      }}

      @keyframes blink {{
        0% {{ opacity: 0.35; filter: saturate(0.9); }}
        50% {{ opacity: 1; filter: saturate(1.2); }}
        100% {{ opacity: 0.35; filter: saturate(0.9); }}
      }}

      {''.join(bulb_css)}

      .wheel {{
        position: absolute;
        inset: 6%;
        border-radius: 50%;
        transform: rotate(var(--rot));
        transition: transform 2.6s cubic-bezier(0.12, 0.62, 0.10, 1);
        z-index: 10;
      }}

      .face {{
        position: absolute;
        inset: 0;
        border-radius: 50%;
        background: {gradient};
        box-shadow:
          inset 0 0 0 10px rgba(226, 178, 74, 0.9),
          inset 0 0 0 16px rgba(120, 20, 48, 0.9),
          0 22px 40px rgba(0,0,0,0.45);
      }}

      .seg-label {{
        position: absolute;
        top: 50%;
        left: 50%;
        transform-origin: center center;
        width: 46%;
        text-align: right;
        padding-right: 8%;
        font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial;
        font-weight: 900;
        letter-spacing: 0.02em;
        color: rgba(255,255,255,0.92);
        text-shadow: 0 3px 4px rgba(0,0,0,0.35);
        user-select: none;
        font-size: clamp(14px, 2.2vw, 28px);
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
    </style>
    """
    return html


# ----------------------------
# Logica spin con "salto" su bruciati
# ----------------------------
def pick_start_index(n: int) -> int:
    return random.randrange(n)


def next_unburned_index(segs: List[Dict], start_idx: int) -> Tuple[int, List[int]]:
    """
    Restituisce (idx_finale, lista_idx_passati_incluso_start_se_bruciato).
    Se lo start è bruciato, viene aggiunto ai passaggi e si va avanti fino a trovare valido.
    """
    n = len(segs)
    path = []
    idx = start_idx
    safety = 0
    while is_burned(segs[idx]["id"]):
        path.append(idx)
        idx = (idx + 1) % n
        safety += 1
        if safety > n + 2:
            break
    return idx, path


def burn_segment(seg: Dict):
    if seg["kind"] == "prize":
        st.session_state.burned_prizes.add(seg["label"])
    else:
        st.session_state.burned_specials.add(seg["id"])


def assign_prize(player: str, prize_label: str):
    st.session_state.assignments[player] = prize_label
    st.session_state.burned_prizes.add(prize_label)


def remaining_prizes_count() -> int:
    return len([p for p in st.session_state.prizes if p not in st.session_state.burned_prizes])


def game_finished() -> bool:
    return remaining_prizes_count() == 0


# ----------------------------
# Special effects
# ----------------------------
def apply_special(seg: Dict, player: str):
    code = seg["id"]
    prizes_avail = [p for p in st.session_state.prizes if p not in st.session_state.burned_prizes]
    if not prizes_avail:
        return

    if code == "BONUS_2PICK":
        a = random.choice(prizes_avail)
        b_pool = [x for x in prizes_avail if x != a]
        b = random.choice(b_pool) if b_pool else a
        st.session_state.pending_effect = {"type": "pick_one", "player": player, "options": [a, b], "title": "BONUS: scegli tra due"}
        return

    if code == "MALUS_WORST2":
        a = random.choice(prizes_avail)
        b_pool = [x for x in prizes_avail if x != a]
        b = random.choice(b_pool) if b_pool else a
        # “peggiore” = numero più alto se sono numeri, altrimenti seconda opzione
        def key(x):
            try:
                return int(x)
            except Exception:
                return 10**9
        worst = max([a, b], key=key)
        st.session_state.pending_effect = {"type": "forced", "player": player, "prize": worst, "title": "MALUS: prendi il peggiore di due"}
        return

    if code == "MALUS_SKIP":
        st.session_state.skip_next.add(player)
        st.session_state.pending_effect = {"type": "info", "title": "MALUS", "message": "Al tuo prossimo giro salti il turno."}
        return

    if code == "BONUS_SWAP":
        targets = [pl for pl in st.session_state.assignments.keys() if pl != player]
        if not targets:
            # fallback: come bonus 2pick
            a = random.choice(prizes_avail)
            b_pool = [x for x in prizes_avail if x != a]
            b = random.choice(b_pool) if b_pool else a
            st.session_state.pending_effect = {"type": "pick_one", "player": player, "options": [a, b], "title": "BONUS: scegli tra due"}
            return
        st.session_state.pending_effect = {"type": "swap", "player": player, "targets": targets, "title": "BONUS: scambio"}
        return

    st.session_state.pending_effect = {"type": "info", "title": "Slot speciale", "message": "Nessun effetto configurato."}


# ----------------------------
# UI
# ----------------------------
init_state()

st.title("🎁 Ruota Regali")
st.caption("Stile casino, luci lampeggianti, audio da file, premi e bonus/malus bruciabili con salto automatico sugli spicchi bruciati.")

with st.sidebar:
    st.header("Setup")

    names_txt = st.text_area("Partecipanti (uno per riga)", value="\n".join(st.session_state.players), height=200)
    prizes_txt = st.text_area("Premi (uno per riga)", value="\n".join(st.session_state.prizes), height=200)

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Nuova partita", use_container_width=True):
            players = [x.strip() for x in names_txt.splitlines() if x.strip()]
            prizes = [x.strip() for x in prizes_txt.splitlines() if x.strip()]
            if not players:
                players = [f"Player {i}" for i in range(1, 11)]
            if not prizes:
                prizes = [str(i) for i in range(1, 11)]
            reset_game(players, prizes)
            st.rerun()

    with c2:
        if st.button("Spegni musica", use_container_width=True):
            st.session_state.music_enabled = False
            st.rerun()

    st.divider()
    st.subheader("Audio (file)")

    bgm_up = st.file_uploader("Musica di sottofondo (mp3)", type=["mp3", "wav", "ogg"])
    spin_up = st.file_uploader("Suono spin (mp3)", type=["mp3", "wav", "ogg"])

    if bgm_up is not None:
        st.session_state.bgm_bytes = bgm_up.read()
    if spin_up is not None:
        st.session_state.spin_bytes = spin_up.read()

    if st.button("Attiva musica", use_container_width=True):
        st.session_state.music_enabled = True

    st.caption("Se non carichi file qui, la app prova a usare assets/bgm.mp3 e assets/spin.mp3 nel repo.")


# Audio playback
bgm_bytes = st.session_state.bgm_bytes or read_file_bytes(DEFAULT_BGM_PATH)
spin_bytes = st.session_state.spin_bytes or read_file_bytes(DEFAULT_SPIN_SFX_PATH)

if st.session_state.music_enabled and bgm_bytes:
    st.audio(bgm_bytes, loop=True)

if st.session_state.last_audio_event == "spin" and spin_bytes:
    st.audio(spin_bytes)
    st.session_state.last_audio_event = None


# Layout principale
left, right = st.columns([1.35, 1])

segs = build_segments()
n = len(segs)

with left:
    st.subheader("Ruota")

    wheel_placeholder = st.empty()

    # Rendering iniziale
    wheel_html = render_wheel_html(segs, st.session_state.wheel_rotation, highlight_index=None, big=True)
    wheel_placeholder.markdown("", unsafe_allow_html=True)
    components.html(wheel_html, height=760, scrolling=False)

    st.divider()
    st.subheader("Turno")

    pl = current_player()

    if pl in st.session_state.assignments:
        st.info(f"{pl} ha già preso: {st.session_state.assignments[pl]}")
        if st.button("Vai al prossimo", use_container_width=True):
            advance_player()
            st.rerun()

    elif pl in st.session_state.skip_next:
        st.warning(f"{pl} deve saltare questo turno.")
        if st.button("Conferma salto turno", use_container_width=True):
            st.session_state.skip_next.remove(pl)
            advance_player()
            st.rerun()

    else:
        st.write(f"Tocca a: **{pl}**")
        st.caption("Se esce uno spicchio bruciato, la ruota scorre allo spicchio successivo finché trova uno valido.")

        # Gestione effetti pendenti
        pe = st.session_state.pending_effect
        if pe is not None:
            st.success(pe.get("title", "Evento"))

            if pe["type"] == "pick_one":
                opts = pe["options"]
                choice = st.radio("Scegli", opts, horizontal=True)
                if st.button("Conferma", type="primary", use_container_width=True):
                    assign_prize(pe["player"], choice)
                    st.session_state.pending_effect = None
                    advance_player()
                    st.rerun()

            elif pe["type"] == "forced":
                prize = pe["prize"]
                st.write(f"Ti tocca: **{prize}**")
                if st.button("Accetta", type="primary", use_container_width=True):
                    assign_prize(pe["player"], prize)
                    st.session_state.pending_effect = None
                    advance_player()
                    st.rerun()

            elif pe["type"] == "swap":
                target = st.selectbox("Con chi vuoi scambiare", pe["targets"])
                if st.button("Esegui scambio", type="primary", use_container_width=True):
                    stolen = st.session_state.assignments[target]
                    del st.session_state.assignments[target]
                    assign_prize(pe["player"], stolen)
                    st.session_state.pending_effect = {"type": "info", "title": "Scambio effettuato", "message": f"{target} torna senza premio e rigira al suo turno."}
                    advance_player()
                    st.rerun()

            else:
                st.write(pe.get("message", ""))
                if st.button("Continua", use_container_width=True):
                    st.session_state.pending_effect = None
                    advance_player()
                    st.rerun()

        else:
            disabled = game_finished()
            if st.button("🎡 SPIN", type="primary", use_container_width=True, disabled=disabled):
                st.session_state.last_audio_event = "spin"

                # 1) scegli index casuale, anche se bruciato
                start_idx = pick_start_index(n)
                final_idx, skipped = next_unburned_index(segs, start_idx)

                # 2) animazione: prima fermata sullo start, poi “passi” sugli altri se bruciati
                path = [start_idx] + [(x + 1) % n for x in skipped]  # include scorrimenti
                # dedup consecutivo
                compact = []
                for x in path:
                    if not compact or compact[-1] != x:
                        compact.append(x)

                # animazione in step
                for step_i, idx in enumerate(compact):
                    target_rot = compute_target_rotation_for_index(idx, n, extra_spins=BASE_SPINS if step_i == 0 else 0)
                    st.session_state.wheel_rotation += target_rot

                    wheel_html_step = render_wheel_html(segs, st.session_state.wheel_rotation, highlight_index=idx, big=True)
                    components.html(wheel_html_step, height=760, scrolling=False)

                    # pausa per rendere visibile il “salto”
                    time.sleep(0.55 if step_i == 0 else 0.28)

                # 3) applica esito sul final_idx
                seg = segs[final_idx]
                if is_burned(seg["id"]):
                    # fallback di sicurezza
                    st.warning("Tutti gli spicchi sembrano bruciati.")
                else:
                    # brucia subito bonus/malus quando usati
                    burn_segment(seg)

                    if seg["kind"] == "prize":
                        assign_prize(pl, seg["label"])
                        advance_player()
                    else:
                        apply_special(seg, pl)

                st.rerun()


with right:
    st.subheader("Stato")

    st.metric("Premi rimasti", remaining_prizes_count())
    st.metric("Premi assegnati", len(st.session_state.assignments))
    st.divider()

    st.write("**Premi assegnati**")
    rows = []
    for p in st.session_state.players:
        rows.append({"Giocatore": p, "Premio": st.session_state.assignments.get(p, ""), "Stato": "✅" if p in st.session_state.assignments else "⏳"})
    st.dataframe(rows, use_container_width=True, hide_index=True)

    st.divider()
    st.write("**Bruciati**")
    st.write("Premi:", ", ".join(sorted(list(st.session_state.burned_prizes), key=lambda x: int(x) if str(x).isdigit() else 9999)) or "nessuno")
    st.write("Bonus/Malus:", ", ".join(sorted(list(st.session_state.burned_specials))) or "nessuno")

    if game_finished():
        st.success("Partita finita!")

