import html
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

import requests
import streamlit as st

from src.generate import Assistant

st.set_page_config(page_title="Ask the Employment Act", layout="centered")

EXAMPLES = {
    "Sick leave": "How many days of paid sick leave do I get?",
    "Paternity leave": "Can fathers take paid leave when their baby is born?",
    "Resigning": "How much notice must I give if I resign after three years?",
    "Pregnancy": "Can my employer fire me because I am pregnant?",
    "Minimum wage": "What is the minimum monthly wage in Malaysia?",
}

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Public+Sans:wght@400;500;600&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&display=swap');
:root { --ink:#1D2430; --muted:#5B6573; --green:#0F4C45; --wash:#F3F5F4;
        --rule:#D5DBD8; --amber:#8A5A00; --amberbg:#FFF6E5; }
html, body, [class*="css"], .stApp { font-family:'Public Sans', system-ui, sans-serif; color:var(--ink); }
#MainMenu, footer, header[data-testid="stHeader"] { visibility:hidden; height:0; }
.block-container { max-width:820px; padding-top:2.6rem; padding-bottom:4rem; }

h1.title { font-family:'Source Serif 4', Georgia, serif; font-weight:600; font-size:2.35rem;
           line-height:1.15; margin:0 0 .5rem 0; letter-spacing:-0.01em; }
p.lead { color:var(--muted); font-size:1.02rem; line-height:1.55; margin:0 0 1.6rem 0; max-width:60ch; }

[data-testid="stTextInput"] input { font-size:1.12rem; padding:.85rem 1rem; border:1.5px solid var(--rule);
           border-radius:8px; background:#fff; }
[data-testid="stTextInput"] input:focus { border-color:var(--green); box-shadow:0 0 0 3px rgba(15,76,69,.15); }
[data-testid="stTextInput"] label { display:none; }

.stButton > button { border:1px solid var(--rule); background:#fff; color:var(--ink); border-radius:999px;
           font-size:.88rem; padding:.25rem .9rem; font-weight:500; white-space:nowrap; }
.stButton > button:hover { border-color:var(--green); color:var(--green); }

.statute { display:grid; grid-template-columns:92px 1fr; gap:1.4rem; border-top:3px solid var(--green);
           padding-top:1.1rem; margin-top:1.8rem; }
.margin { font-family:'Source Serif 4', Georgia, serif; color:var(--green); font-size:2rem;
          font-weight:600; line-height:1; }
.margin small { display:block; font-family:'Public Sans', sans-serif; font-size:.78rem; color:var(--muted);
          font-weight:400; margin-bottom:.35rem; }
.statute h2 { font-family:'Source Serif 4', Georgia, serif; font-size:1.35rem; font-weight:600;
          margin:0 0 .7rem 0; line-height:1.3; }
.statute p { font-family:'Source Serif 4', Georgia, serif; font-size:1.06rem; line-height:1.72;
          margin:0 0 .75rem 0; max-width:68ch; }
.src-note { color:var(--muted); font-size:.82rem; margin-top:.4rem; }

.sumblock { background:var(--amberbg); border-left:4px solid var(--amber); padding:1rem 1.2rem;
            border-radius:4px; margin-top:2rem; }
.sumblock .tag { font-weight:600; color:var(--amber); font-size:.92rem; margin-bottom:.5rem; }
.sumblock p { margin:.2rem 0 .6rem 0; line-height:1.6; }
.sumblock blockquote { margin:.4rem 0 0 0; padding-left:.9rem; border-left:2px solid var(--rule);
            font-family:'Source Serif 4', Georgia, serif; font-size:.98rem; color:#3a4350; }
.plain { background:var(--wash); border-radius:6px; padding:.9rem 1.1rem; margin-top:2rem; color:var(--ink); }
.small { color:var(--muted); font-size:.84rem; line-height:1.55; margin-top:2.4rem; max-width:70ch; }

@media (max-width:640px) {
  .statute { grid-template-columns:1fr; gap:.6rem; }
  h1.title { font-size:1.8rem; }
}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


@st.cache_resource(show_spinner="Loading the Act and the search model...")
def load_assistant():
    a = Assistant()
    meta = {}
    for u in a.retriever.units:
        meta.setdefault(u["section_id"], u)
    return a, meta


def ollama_up():
    try:
        requests.get("http://localhost:11434/api/tags", timeout=2)
        return True
    except Exception:
        return False


def paragraphs(text):
    return "".join(f"<p>{html.escape(p.strip())}</p>"
                   for p in text.split("\n") if p.strip())


def set_question(q):
    st.session_state["q"] = q


def statute_panel(u, body, truncated):
    heading = html.escape(u["heading"]) if u["heading"] else "Text of the section"
    note = ('<div class="src-note">Long section: showing the first 4,000 characters.</div>'
            if truncated else "")
    st.markdown(
        f'<div class="statute"><div class="margin"><small>Section</small>{html.escape(u["section"])}</div>'
        f'<div><h2>{heading}</h2>{paragraphs(body)}{note}</div></div>',
        unsafe_allow_html=True)


assistant, meta = load_assistant()

st.markdown('<h1 class="title">Ask the Employment Act</h1>'
            '<p class="lead">Type a question about your rights at work and see the section of the '
            'Employment Act 1955 that is closest to it. Covers Peninsular Malaysia and Labuan, text '
            'as at 1 August 2023. General information, not legal advice.</p>',
            unsafe_allow_html=True)

st.text_input("Your question", key="q", placeholder="For example: how much notice do I give if I resign?")
cols = st.columns(len(EXAMPLES))
for col, (label, q) in zip(cols, EXAMPLES.items()):
    col.button(label, on_click=set_question, args=(q,), key=f"ex_{label}")

up = ollama_up()
use_ai = st.toggle("Also show a summary written by a language model", value=False, disabled=not up)
if not up:
    st.caption("Summaries need Ollama running on this computer, so this switch is off.")

question = st.session_state.get("q", "")
if question:
    result = None
    if use_ai:
        with st.spinner("Reading the sections..."):
            result = assistant.answer(question)
        ids = result["retrieved"]
    else:
        ids = [u["section_id"] for u, _ in assistant.retriever.search(question, "hybrid", k=3)]

    first = ids[0]
    full = assistant.full[first]
    statute_panel(meta[first], full.split("\n", 1)[-1], len(full) >= 4000)

    others = ids[1:]
    if others:
        st.markdown('<div style="height:1.2rem"></div>', unsafe_allow_html=True)
        for sid in others:
            u = meta[sid]
            label = f"Also close: Section {u['section']}" + (f", {u['heading']}" if u["heading"] else "")
            with st.expander(label):
                st.write(assistant.full[sid].split("\n", 1)[-1])

    if result is not None:
        if result["unsupported"]:
            st.markdown('<div class="plain">The language model wrote an answer that could not be '
                        'matched to the Act, so it is hidden. Please read the sections above.</div>',
                        unsafe_allow_html=True)
        elif result["abstained"]:
            st.markdown('<div class="plain">The language model did not find a direct answer. '
                        'The closest sections are above, and the answer may still be in them.</div>',
                        unsafe_allow_html=True)
        else:
            cited = ", ".join(f"Section {c[1:]}" for c in result["cited"])
            st.markdown(
                '<div class="sumblock"><div class="tag">Summary by a language model. It can be wrong, '
                'so check it against the text above.</div>'
                f'<p>{html.escape(result["answer"])}</p>'
                f'<blockquote>{html.escape(result["quote"])}</blockquote>'
                f'<div class="src-note">The quote was found in: {html.escape(cited)}</div></div>',
                unsafe_allow_html=True)

st.markdown('<div class="small">How reliable is this? On 19 questions I held back for testing, the '
            'right section was among the top three results for 14. A language model summary was '
            'fully correct for 4, partly correct for 2, wrong for 3, and declined for 10 (graded '
            'by me). It declined all 3 questions that the Act does not cover. A summary can quote a '
            'real sentence and still give the wrong answer, so read the section. The sample is small, '
            'so treat these numbers as a guide.</div>', unsafe_allow_html=True)