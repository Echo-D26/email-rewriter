import streamlit as st
from core import (
    TONES, CHIPS, rewrite_email, refine_email, analyze_email, diff_html,
)

st.set_page_config(page_title="Email Rewriter", page_icon="✉️", layout="wide")

# ---------- Styling ----------
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Newsreader:opsz,wght@6..72,500;6..72,700&display=swap');
.hero h1 {font-family:'Newsreader',Georgia,serif; font-size:2.6rem; margin:0; letter-spacing:-0.01em;}
.hero p {opacity:.7; margin:.2rem 0 1.2rem 0;}
.diffbox {border:1px solid rgba(128,128,128,.3); border-radius:10px; padding:1rem 1.1rem; line-height:1.75; min-height:160px;}
.diffhead {font-size:.85rem; opacity:.65; margin-bottom:.4rem;}
.del {background:rgba(239,68,68,.25); text-decoration:line-through; border-radius:3px; padding:0 2px;}
.ins {background:rgba(34,197,94,.28); border-radius:3px; padding:0 2px;}
.meter {margin-bottom:1.1rem;}
.mhead {display:flex; justify-content:space-between; font-size:.95rem; margin-bottom:.35rem;}
.track {position:relative; height:12px; border-radius:6px; background:rgba(128,128,128,.22);}
.fill {height:100%; border-radius:6px; background:linear-gradient(90deg,#14b8a6,#6366f1); transition:width .6s;}
.orig {position:absolute; top:-4px; width:4px; height:20px; border-radius:2px; background:rgba(128,128,128,.9);}
.mends {display:flex; justify-content:space-between; font-size:.75rem; opacity:.6; margin-top:.25rem;}
.flag {border-left:4px solid #f59e0b; background:rgba(245,158,11,.12); padding:.6rem .9rem; border-radius:6px; margin-bottom:.5rem;}
.flag.hard {border-left-color:#ef4444; background:rgba(239,68,68,.12);}
.ok {border-left:4px solid #22c55e; background:rgba(34,197,94,.12); padding:.6rem .9rem; border-radius:6px;}
</style>
<div class="hero"><h1>Email Rewriter</h1>
<p>Rewrite it, see exactly what changed, and check it before you send.</p></div>
""",
    unsafe_allow_html=True,
)

SAMPLE = "hey can u send me the report asap. i need it for [Client Name] and its late already"

METERS = [
    ("formality", "Formality", "Casual", "Formal"),
    ("warmth", "Warmth", "Reserved", "Warm"),
    ("directness", "Directness", "Indirect", "Direct"),
]

FLAG_TITLES = {
    "blunt": "May sound blunt",
    "buried_ask": "Main ask is buried",
    "vague_ask": "Ask is vague",
    "placeholder": "Placeholder left in",
    "info": "Note",
}


def meter_html(label, low, high, before, after):
    change = after - before
    arrow = "▲" if change > 0 else "▼" if change < 0 else "•"
    return (
        f'<div class="meter"><div class="mhead"><b>{label}</b>'
        f"<span>{before} → {after} {arrow} {abs(change)}</span></div>"
        f'<div class="track"><div class="fill" style="width:{after}%"></div>'
        f'<div class="orig" style="left:{before}%"></div></div>'
        f'<div class="mends"><span>{low}</span><span>{high}</span></div></div>'
    )


def load_sample():
    st.session_state.email_input = SAMPLE


# ---------- Session state ----------
if "versions" not in st.session_state:
    st.session_state.versions = []  # each item: {"text": ..., "analysis": ...}
    st.session_state.original = ""

# ---------- Input ----------
left, right = st.columns([3, 1])
with left:
    email = st.text_area("Your email", key="email_input", height=170,
                         placeholder="Paste your rough email here...")
with right:
    tone = st.pills("Tone", TONES, default="professional") or "professional"
    st.button("Try a sample", on_click=load_sample, use_container_width=True)
    generate = st.button("✨ Rewrite", type="primary", use_container_width=True)

if generate:
    if not email.strip():
        st.warning("Paste an email first.")
    else:
        try:
            with st.spinner("Rewriting..."):
                text = rewrite_email(email, tone)
            with st.spinner("Checking tone and pitfalls..."):
                analysis = analyze_email(email, text)
            st.session_state.original = email
            st.session_state.versions = [{"text": text, "analysis": analysis}]
            st.toast("Done!", icon="✅")
        except Exception as e:
            st.error(f"Something went wrong: {e}")

# ---------- Result ----------
versions = st.session_state.versions
if versions:
    current = versions[-1]
    original = st.session_state.original

    st.markdown("### Result")
    st.code(current["text"], language=None)  # the box has a built-in copy button

    # One-click chips
    st.caption("Quick edits")
    chip_cols = st.columns(len(CHIPS) + 1)
    clicked = None
    for col, (label, instruction) in zip(chip_cols, CHIPS.items()):
        if col.button(label, key=label, use_container_width=True):
            clicked = instruction
    if len(versions) > 1 and chip_cols[-1].button(" Undo", use_container_width=True):
        versions.pop()
        st.rerun()

    if clicked:
        try:
            with st.spinner("Applying edit..."):
                new_text = refine_email(current["text"], clicked)
                new_analysis = analyze_email(original, new_text)
            versions.append({"text": new_text, "analysis": new_analysis})
            st.rerun()
        except Exception as e:
            st.error(f"Could not apply that edit: {e}")

    pitfalls = current["analysis"]["pitfalls"]
    tab_diff, tab_tone, tab_check = st.tabs(
        [" What changed", " Tone meter", f" Before you send ({len(pitfalls)})"]
    )

    with tab_diff:
        old_html, new_html = diff_html(original, current["text"])
        c1, c2 = st.columns(2)
        c1.markdown(f'<div class="diffhead">Original · removed words in red</div>'
                    f'<div class="diffbox">{old_html}</div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="diffhead">Rewritten · new words in green</div>'
                    f'<div class="diffbox">{new_html}</div>', unsafe_allow_html=True)

    with tab_tone:
        scores = current["analysis"]["scores"]
        st.caption("Grey marker = your original. Bar = the rewritten version.")
        cols = st.columns(3)
        for col, (key, label, low, high) in zip(cols, METERS):
            col.markdown(
                meter_html(label, low, high, scores["original"][key], scores["rewritten"][key]),
                unsafe_allow_html=True,
            )

    with tab_check:
        if not pitfalls:
            st.markdown('<div class="ok"> No problems found. This looks ready to send.</div>',
                        unsafe_allow_html=True)
        for p in pitfalls:
            kind = p.get("type", "info")
            hard = "hard" if kind == "placeholder" else ""
            st.markdown(
                f'<div class="flag {hard}"><b>{FLAG_TITLES.get(kind, "Note")}</b><br>'
                f'{p.get("message", "")}</div>',
                unsafe_allow_html=True,
            )