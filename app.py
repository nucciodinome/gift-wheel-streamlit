import os
import math
import time
import random
import wave
import struct
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np
import streamlit as st
import plotly.express as px


# ----------------------------
# Config base
# ----------------------------
st.set_page_config(
    page_title="Ruota Regali",
    page_icon="🎁",
    layout="wide",
)

ASSETS_DIR = "assets"
SFX_SPIN = os.path.join(ASSETS_DIR, "sfx_spin.wav")
SFX_WIN = os.path.join(ASSETS_DIR, "sfx_win.wav")
SFX_BONUS = os.path.join(ASSETS_DIR, "sfx_bonus.wav")
SFX_MALUS = os.path.join(ASSETS_DIR, "sfx_malus.wav")
SFX_END = os.path.join(ASSETS_DIR, "sfx_end.wav")
BGM_LOOP = os.path.join(ASSETS_DIR, "bgm_loop.wav")


# ----------------------------
# Audio: generatore WAV semplice (originale)
# ----------------------------
def _ensure_assets_dir():
    os.makedirs(ASSETS_DIR, exist_ok=True)


def _write_wav(path: str, samples: np.ndarray, sr: int = 44100):
    samples = np.clip(samples, -1.0, 1.0)
    pcm = (samples * 32767.0).astype(np.int16)

    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(pcm.tobytes())


def _tone(freq: float, dur: float, sr: int = 44100, vol: float = 0.3):
    t = np.linspace(0, dur, int(sr * dur), endpoint=False)
    # leggera armonica per renderlo meno “beep”
    s = np.sin(2 * np.pi * freq * t) + 0.25 * np.sin(2 * np.pi * (2 * freq) * t)
    return vol * s

def _env(samples: np.ndarray, sr: int = 44100, attack=0.01, release=0.08):
    n = len(samples)
    if n == 0:
        return samples

    a = int(sr * attack)
    r = int(sr * release)

    # clamp per evitare a/r > n
    a = max(0, min(a, n))
    r = max(0, min(r, n))

    # se attack + release supera n, ridistribuisci
    if a + r > n:
        # dai priorità a una release minima e riduci l'attack
        r = min(r, n)
        a = max(0, n - r)

    env = np.ones(n, dtype=np.float32)

    if a > 0:
        env[:a] = np.linspace(0.0, 1.0, a, endpoint=True)

    if r > 0:
        env[n - r :] = np.linspace(1.0, 0.0, r, endpoint=True)

    return samples * env


def _chime(path: str, freqs: List[float], dur: float, gap: float = 0.03, sr: int = 44100):
    pieces = []
    for f in freqs:
        s = _tone(f, dur, sr=sr, vol=0.35)
        s = _env(s, sr=sr, attack=0.005, release=0.12)
        pieces.append(s)
        if gap > 0:
            pieces.append(np.zeros(int(sr * gap), dtype=np.float32))
    out = np.concatenate(pieces) if pieces else np.zeros(int(sr * 0.2), dtype=np.float32)
    _write_wav(path, out, sr=sr)


def _noise_burst(path: str, dur: float = 0.35, sr: int = 44100, vol: float = 0.25, lowpass_hz: float = 1200):
    n = int(sr * dur)
    noise = np.random.randn(n).astype(np.float32) * vol

    # low-pass molto semplice (media mobile)
    k = max(3, int(sr / max(lowpass_hz, 100)))
    kernel = np.ones(k, dtype=np.float32) / k
    filtered = np.convolve(noise, kernel, mode="same")
    filtered = _env(filtered, sr=sr, attack=0.005, release=0.12)
    _write_wav(path, filtered, sr=sr)


def _bgm_loop(path: str, sr: int = 44100):
    # loop “festivo” semplice: progressione di accordi (note) in 8 secondi
    # tutto sintetico e originale
    bpm = 110
    beat = 60.0 / bpm
    bar = 4 * beat
    total = 8.0
    t = np.linspace(0, total, int(sr * total), endpoint=False)

    # accordi in Hz (approssimazione): C, Am, F, G
    chords = [
        [261.63, 329.63, 392.00],   # C
        [220.00, 261.63, 329.63],   # Am
        [174.61, 220.00, 261.63],   # F
        [196.00, 246.94, 392.00],   # G (con quinta alta)
    ]

    out = np.zeros_like(t, dtype=np.float32)

    for i, chord in enumerate(chords):
        start = i * bar
        end = min((i + 1) * bar, total)
        idx0 = int(start * sr)
        idx1 = int(end * sr)
        tt = t[idx0:idx1] - start

        s = np.zeros_like(tt, dtype=np.float32)
        for f in chord:
            s += np.sin(2 * np.pi * f * tt) * 0.08
            s += np.sin(2 * np.pi * (f / 2) * tt) * 0.04  # un po’ di “basso”
        s = _env(s, sr=sr, attack=0.02, release=0.2)
        out[idx0:idx1] += s

    # leggero “tick” per dare ritmo
    for b in np.arange(0, total, beat):
        i = int(b * sr)
        j = min(i + int(0.03 * sr), len(out))
        out[i:j] += _env(_noise_click(0.03, sr=sr, vol=0.08), sr=sr, attack=0.001, release=0.02)[: (j - i)]

    out = np.clip(out, -1, 1)
    _write_wav(path, out, sr=sr)


def _noise_click(dur: float, sr: int = 44100, vol: float = 0.1):
    n = int(sr * dur)
    x = (np.random.randn(n).astype(np.float32) * vol)
    return x


def ensure_audio_assets():
    _ensure_assets_dir()
    if not os.path.exists(SFX_SPIN):
        _noise_burst(SFX_SPIN, dur=0.35, lowpass_hz=2200)
    if not os.path.exists(SFX_WIN):
        _chime(SFX_WIN, [523.25, 659.25, 783.99, 1046.5], dur=0.12)
    if not os.path.exists(SFX_BONUS):
        _chime(SFX_BONUS, [659.25, 783.99, 987.77], dur=0.12)
    if not os.path.exists(SFX_MALUS):
        _chime(SFX_MALUS, [392.00, 311.13, 246.94], dur=0.12)
    if not os.path.exists(SFX_END):
        _chime(SFX_END, [523.25, 659.25, 783.99, 1046.5, 1318.5], dur=0.12)
    if not os.path.exists(BGM_LOOP):
        _bgm_loop(BGM_LOOP)


# ----------------------------
# Logica gioco
# ----------------------------
@dataclass
class SpecialSlot:
    code: str
    label: str
    kind: str  # "bonus" or "malus"


SPECIAL_SLOTS = [
    SpecialSlot(code="BONUS_2SPIN_PICK", label="BONUS: 2 giri e scegli", kind="bonus"),
    SpecialSlot(code="BONUS_STEAL", label="BONUS: scambia con qualcuno", kind="bonus"),
    SpecialSlot(code="MALUS_2SPIN_WORST", label="MALUS: 2 giri e prendi il peggiore", kind="malus"),
    SpecialSlot(code="MALUS_SKIP_TURN", label="MALUS: perdi il turno dopo", kind="malus"),
]


def init_state():
    if "players" not in st.session_state:
        st.session_state.players = [f"Player {i}" for i in range(1, 11)]
    if "remaining_prizes" not in st.session_state:
        st.session_state.remaining_prizes = [str(i) for i in range(1, 11)]
    if "assignments" not in st.session_state:
        st.session_state.assignments = {}  # player -> prize string
    if "player_idx" not in st.session_state:
        st.session_state.player_idx = 0
    if "pending_effect" not in st.session_state:
        st.session_state.pending_effect = None  # dict with effect info
    if "skip_next" not in st.session_state:
        st.session_state.skip_next = set()  # players who must skip next turn
    if "last_sfx" not in st.session_state:
        st.session_state.last_sfx = None
    if "music_on" not in st.session_state:
        st.session_state.music_on = False


def reset_game(players: List[str], prizes: List[str]):
    st.session_state.players = players
    st.session_state.remaining_prizes = prizes
    st.session_state.assignments = {}
    st.session_state.player_idx = 0
    st.session_state.pending_effect = None
    st.session_state.skip_next = set()
    st.session_state.last_sfx = None


def current_player() -> str:
    return st.session_state.players[st.session_state.player_idx]


def advance_player():
    st.session_state.player_idx = (st.session_state.player_idx + 1) % len(st.session_state.players)


def spin_segment() -> Tuple[str, str]:
    """
    Returns (type, value)
    type in {"prize", "special"}
    """
    segments = []
    for p in st.session_state.remaining_prizes:
        segments.append(("prize", p))
    for s in SPECIAL_SLOTS:
        segments.append(("special", s.code))

    if not segments:
        return ("special", "END")

    return random.choice(segments)


def prize_order_key(p: str) -> int:
    try:
        return int(p)
    except Exception:
        return 10**9


def apply_special_effect(effect_code: str, player: str):
    remaining = st.session_state.remaining_prizes

    # Se non ci sono più premi, fine
    if not remaining:
        return

    if effect_code == "BONUS_2SPIN_PICK":
        a = random.choice(remaining)
        b = random.choice([x for x in remaining if x != a] or [a])
        st.session_state.pending_effect = {"type": "pick_best_of_two", "player": player, "options": sorted([a, b], key=prize_order_key)}
        st.session_state.last_sfx = SFX_BONUS
        return

    if effect_code == "MALUS_2SPIN_WORST":
        a = random.choice(remaining)
        b = random.choice([x for x in remaining if x != a] or [a])
        st.session_state.pending_effect = {"type": "pick_worst_of_two", "player": player, "options": sorted([a, b], key=prize_order_key)}
        st.session_state.last_sfx = SFX_MALUS
        return

    if effect_code == "MALUS_SKIP_TURN":
        st.session_state.skip_next.add(player)
        st.session_state.pending_effect = {"type": "info", "player": player, "message": "Hai preso un malus: al tuo prossimo giro salti il turno."}
        st.session_state.last_sfx = SFX_MALUS
        return

    if effect_code == "BONUS_STEAL":
        # Se non esistono assegnazioni, diventa bonus “extra scelta” (scegli tra 2)
        assigned_players = [pl for pl in st.session_state.assignments.keys() if pl != player]
        if not assigned_players:
            a = random.choice(remaining)
            b = random.choice([x for x in remaining if x != a] or [a])
            st.session_state.pending_effect = {"type": "pick_best_of_two", "player": player, "options": sorted([a, b], key=prize_order_key)}
            st.session_state.last_sfx = SFX_BONUS
            return

        st.session_state.pending_effect = {"type": "steal", "player": player, "targets": assigned_players}
        st.session_state.last_sfx = SFX_BONUS
        return

    st.session_state.pending_effect = {"type": "info", "player": player, "message": "Slot speciale non riconosciuto, nessun effetto applicato."}


def assign_prize(player: str, prize: str):
    st.session_state.assignments[player] = prize
    if prize in st.session_state.remaining_prizes:
        st.session_state.remaining_prizes.remove(prize)
    st.session_state.last_sfx = SFX_WIN


def game_finished() -> bool:
    return len(st.session_state.remaining_prizes) == 0


# ----------------------------
# UI
# ----------------------------
ensure_audio_assets()
init_state()

st.title("🎁 Ruota Regali")
st.caption("Premi bruciabili, 4 slot bonus/malus, audio incluso. Pronta per Streamlit Community Cloud.")

with st.sidebar:
    st.header("Impostazioni")
    names_txt = st.text_area(
        "Nomi partecipanti (uno per riga)",
        value="\n".join(st.session_state.players),
        height=220,
    )
    prizes_txt = st.text_area(
        "Premi disponibili (uno per riga, default 1-10)",
        value="\n".join([str(i) for i in range(1, 11)]),
        height=220,
    )

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("Nuova partita", use_container_width=True):
            players = [x.strip() for x in names_txt.splitlines() if x.strip()]
            prizes = [x.strip() for x in prizes_txt.splitlines() if x.strip()]
            if not players:
                players = [f"Player {i}" for i in range(1, 11)]
            if not prizes:
                prizes = [str(i) for i in range(1, 11)]
            reset_game(players, prizes)
            st.rerun()

    with col_b:
        if st.button("Reset audio", use_container_width=True):
            st.session_state.last_sfx = None
            st.session_state.music_on = False
            st.rerun()

    st.divider()
    st.subheader("Audio")
    st.write("Se il browser blocca l’autoplay, clicca prima un bottone nella pagina.")
    if st.button("Attiva musica", use_container_width=True):
        st.session_state.music_on = True

    st.caption("La musica è un loop WAV sintetico incluso nel repo (originale).")


# Musica di sottofondo
if st.session_state.music_on:
    st.audio(BGM_LOOP, loop=True)

# Effetto sonoro “one-shot” dopo azioni
if st.session_state.last_sfx:
    st.audio(st.session_state.last_sfx)
    # evita che resti riprodotto a ogni rerun
    st.session_state.last_sfx = None


left, right = st.columns([1.2, 1])

with left:
    st.subheader("Ruota")
    remaining = st.session_state.remaining_prizes
    segments_labels = [f"🎁 {p}" for p in remaining] + [s.label for s in SPECIAL_SLOTS]

    if segments_labels:
        fig = px.pie(
            names=segments_labels,
            values=[1] * len(segments_labels),
            hole=0.25,
        )
        fig.update_traces(textposition="inside", textinfo="label")
        fig.update_layout(
            showlegend=False,
            margin=dict(l=10, r=10, t=10, b=10),
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.success("Nessun segmento: la partita è finita!")

    st.divider()
    st.subheader("Turno")

    pl = current_player()
    already = pl in st.session_state.assignments

    # Gestione skip turno
    if pl in st.session_state.skip_next:
        st.warning(f"{pl} deve saltare questo turno (malus).")
        if st.button("Conferma salto turno", use_container_width=True):
            st.session_state.skip_next.remove(pl)
            advance_player()
            st.session_state.last_sfx = SFX_MALUS
            st.rerun()

    elif already:
        st.info(f"{pl} ha già un premio: {st.session_state.assignments[pl]}")
        if st.button("Vai al prossimo", use_container_width=True):
            advance_player()
            st.rerun()

    else:
        st.write(f"Gioca: **{pl}**")

        if st.session_state.pending_effect is None:
            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                if st.button("🎡 SPIN", use_container_width=True, type="primary", disabled=game_finished()):
                    st.session_state.last_sfx = SFX_SPIN
                    typ, val = spin_segment()

                    if typ == "prize":
                        assign_prize(pl, val)
                        advance_player()
                    else:
                        apply_special_effect(val, pl)

                    # Se finiti i premi dopo assegnazione
                    if game_finished():
                        st.session_state.last_sfx = SFX_END

                    st.rerun()

            with col2:
                st.metric("Premi rimasti", len(remaining))
            with col3:
                st.metric("Assegnati", len(st.session_state.assignments))

        else:
            pe = st.session_state.pending_effect
            st.info("Esito speciale!")

            if pe["type"] == "pick_best_of_two":
                opts = pe["options"]
                st.write(f"BONUS per **{pe['player']}**: scegli tra **{opts[0]}** e **{opts[1]}**")
                chosen = st.radio("Scegli il premio", opts, horizontal=True)
                if st.button("Conferma scelta", use_container_width=True, type="primary"):
                    assign_prize(pe["player"], chosen)
                    st.session_state.pending_effect = None
                    advance_player()
                    if game_finished():
                        st.session_state.last_sfx = SFX_END
                    st.rerun()

            elif pe["type"] == "pick_worst_of_two":
                opts = pe["options"]
                worst = opts[-1]  # “peggiore” = numero più alto (personalizzabile)
                st.write(f"MALUS per **{pe['player']}**: tra **{opts[0]}** e **{opts[1]}** ti tocca **{worst}**")
                if st.button("Accetta il malus", use_container_width=True, type="primary"):
                    assign_prize(pe["player"], worst)
                    st.session_state.pending_effect = None
                    advance_player()
                    if game_finished():
                        st.session_state.last_sfx = SFX_END
                    st.rerun()

            elif pe["type"] == "steal":
                st.write(f"BONUS per **{pe['player']}**: puoi scambiare il tuo premio con qualcuno (quando lo avrai).")
                st.write("Meccanica: scegli un giocatore già assegnato, gli rubi il premio e lui torna in pool con un nuovo spin subito.")
                target = st.selectbox("Scegli chi colpire", pe["targets"])
                if st.button("Esegui scambio", use_container_width=True, type="primary"):
                    stolen_prize = st.session_state.assignments[target]
                    # target perde il premio, torna non assegnato, e il premio rubato va al player corrente
                    del st.session_state.assignments[target]
                    assign_prize(pe["player"], stolen_prize)

                    st.session_state.pending_effect = {"type": "info", "player": target, "message": f"{target} ha perso il premio e dovrà rigirare al suo prossimo turno."}
                    advance_player()
                    if game_finished():
                        st.session_state.last_sfx = SFX_END
                    st.rerun()

            else:
                st.write(pe.get("message", ""))
                if st.button("Continua", use_container_width=True):
                    st.session_state.pending_effect = None
                    advance_player()
                    st.rerun()


with right:
    st.subheader("Tabellone")

    # Stato premi
    st.write("**Premi rimanenti:**")
    if st.session_state.remaining_prizes:
        st.code(", ".join(st.session_state.remaining_prizes))
    else:
        st.success("Tutti i premi sono stati assegnati!")

    st.divider()

    # Tabella assegnazioni
    st.write("**Assegnazioni:**")
    rows = []
    for p in st.session_state.players:
        rows.append(
            {
                "Giocatore": p,
                "Premio": st.session_state.assignments.get(p, ""),
                "Stato": "✅" if p in st.session_state.assignments else "⏳",
            }
        )
    st.dataframe(rows, use_container_width=True, hide_index=True)

    st.divider()

    if game_finished():
        st.balloons()
        st.success("Partita finita! Buone feste 🎄🎁")
        if st.button("Ricomincia con stessi nomi", use_container_width=True):
            reset_game(st.session_state.players, [str(i) for i in range(1, 11)])
            st.rerun()
