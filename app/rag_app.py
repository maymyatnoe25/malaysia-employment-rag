
import html
import re
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

import requests
import streamlit as st

from src.generate import Assistant


# ============================================================
# 1. PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="KerjaRights AI | Employment Law Assistant",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# 2. CONFIGURATION — EASY TO CUSTOMIZE
# ============================================================

APP_NAME = "KerjaRights AI"
APP_SUBTITLE = "MALAYSIAN EMPLOYMENT LAW ASSISTANT"

SOURCE_NAME = "Employment Act 1955 (Act 265)"
SOURCE_DATE = "1 August 2023"
SOURCE_COVERAGE = "Peninsular Malaysia and Labuan"

PRIMARY = "#214D45"
BACKGROUND = "#F7F8F6"
TEXT_COLOR = "#263238"

EXAMPLES = {
    "Paid sick leave": "How many days of paid sick leave do I get?",
    "Maternity leave": "What maternity leave does the Act provide?",
    "Paternity leave": "Can fathers take paid leave when their baby is born?",
    "Resignation notice": "How much notice must I give if I want to resign?",
    "Pregnancy": "Can my employer terminate my employment because I am pregnant?",
    "Working hours": "What does the Act say about working hours?",
    "Overtime": "What does the Act say about overtime pay?",
    "Minimum wage": "What is the minimum monthly wage in Malaysia?",
}


# ============================================================
# 3. CUSTOM CSS
# ============================================================

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Source+Serif+4:wght@400;500;600;700&display=swap');

:root {
    --green: #214D45;
    --green-hover: #173B35;
    --ink: #263238;
    --muted: #68736F;
    --border: #E0E6E2;
    --background: #F7F8F6;
    --cream: #FFF4DB;
}

html, body, [class*="css"], .stApp {
    font-family: 'DM Sans', sans-serif;
    color: var(--ink);
}

.stApp {
    background: var(--background);
}

.block-container {
    max-width: 1120px;
    padding-top: 3rem;
    padding-bottom: 4rem;
}

/* Fix top spacing so the main content is not clipped */
[data-testid="stAppViewBlockContainer"] {
    padding-top: 3rem;
}

h1, h2, h3 {
    color: var(--ink);
}

.brand {
    display: flex;
    align-items: center;
    gap: 13px;
    margin-bottom: 2.5rem;
}

.brand-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 48px;
    height: 48px;
    background: var(--green);
    color: white;
    border-radius: 13px;
    font-size: 25px;
    flex-shrink: 0;
}

.brand-name {
    font-size: 1.15rem;
    font-weight: 700;
    letter-spacing: -0.03em;
    color: var(--green);
}

.brand-subtitle {
    color: var(--muted);
    font-size: 0.68rem;
    font-weight: 600;
    letter-spacing: 0.09em;
    margin-top: 3px;
}

.hero-label {
    color: var(--green);
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-bottom: 0.8rem;
}

.hero-title {
    font-family: 'Source Serif 4', Georgia, serif;
    font-size: clamp(2.2rem, 5vw, 3.5rem);
    font-weight: 600;
    letter-spacing: -0.045em;
    line-height: 1.12;
    margin: 0 0 1rem 0;
}

.hero-description {
    max-width: 720px;
    color: var(--muted);
    font-size: 1.03rem;
    line-height: 1.8;
    margin-bottom: 1.4rem;
}

.source-strip {
    display: flex;
    flex-wrap: wrap;
    gap: 9px;
    margin-bottom: 2rem;
}

.source-chip {
    border: 1px solid var(--border);
    background: white;
    padding: 7px 11px;
    border-radius: 7px;
    font-size: 0.78rem;
    color: #45534E;
}

.section-heading {
    font-family: 'Source Serif 4', Georgia, serif;
    font-size: 1.55rem;
    font-weight: 600;
    letter-spacing: -0.02em;
    margin-bottom: 0.35rem;
}

.section-description {
    color: var(--muted);
    font-size: 0.91rem;
    line-height: 1.65;
    margin-bottom: 1rem;
}

div[data-testid="stTextInput"] input {
    min-height: 3.2rem;
    border: 1px solid #CCD7D1;
    border-radius: 10px;
    background: white;
    font-size: 1rem;
}

div[data-testid="stTextInput"] input:focus {
    border-color: var(--green);
    box-shadow: 0 0 0 2px rgba(33, 77, 69, 0.12);
}

div[data-testid="stButton"] > button,
div[data-testid="stFormSubmitButton"] > button {
    border-radius: 9px;
    min-height: 2.7rem;
    font-weight: 600;
    transition: all 0.15s ease;
}

div[data-testid="stFormSubmitButton"] > button {
    background: var(--green);
    color: white;
    border: 1px solid var(--green);
}

div[data-testid="stFormSubmitButton"] > button:hover {
    background: var(--green-hover);
    border-color: var(--green-hover);
    color: white;
}

div[data-testid="stButton"] > button {
    background: white;
    border: 1px solid var(--border);
    color: var(--ink);
}

div[data-testid="stButton"] > button:hover {
    border-color: var(--green);
    color: var(--green);
}

div[data-testid="stExpander"] {
    background: white;
    border: 1px solid var(--border);
    border-radius: 10px;
    overflow: hidden;
}

.result-card {
    background: white;
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.4rem;
    margin-top: 1rem;
}

.result-eyebrow {
    color: var(--green);
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-bottom: 0.5rem;
}

.result-title {
    font-family: 'Source Serif 4', Georgia, serif;
    font-size: 1.45rem;
    font-weight: 600;
    margin-bottom: 0.5rem;
}

.section-number {
    display: inline-block;
    color: var(--green);
    background: #EAF1ED;
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 1rem;
    font-weight: 700;
    margin-bottom: 0.9rem;
}

.legal-text {
    font-family: 'Source Serif 4', Georgia, serif;
    color: #303A36;
    font-size: 1.02rem;
    line-height: 1.85;
    overflow-wrap: anywhere;
}

.legal-text p {
    margin: 0 0 0.9rem 0;
}

.ai-card {
    background: var(--cream);
    border: 1px solid #F0DFB8;
    border-left: 4px solid #A87924;
    border-radius: 10px;
    padding: 1.25rem 1.4rem;
    margin-top: 1.2rem;
    overflow-wrap: anywhere;
}

.ai-heading {
    color: #79551C;
    font-size: 0.92rem;
    font-weight: 700;
    margin-bottom: 0.65rem;
}

.ai-text {
    color: #303A36;
    font-size: 0.98rem;
    line-height: 1.8;
    white-space: pre-wrap;
}

.quote-box {
    border-left: 3px solid #C9B783;
    padding-left: 1rem;
    margin-top: 1rem;
    color: #4D554F;
    font-family: 'Source Serif 4', Georgia, serif;
    line-height: 1.75;
}

.info-note {
    background: #EEF3F0;
    border: 1px solid #D8E5DD;
    border-radius: 9px;
    padding: 1rem 1.1rem;
    line-height: 1.7;
    margin-top: 1rem;
}

.warning-note {
    background: #FFF4DB;
    border: 1px solid #F0DFB8;
    border-radius: 9px;
    padding: 1rem 1.1rem;
    line-height: 1.7;
    margin-top: 1rem;
}

.disclaimer {
    border-top: 1px solid var(--border);
    margin-top: 3rem;
    padding-top: 1.2rem;
    color: var(--muted);
    font-size: 0.82rem;
    line-height: 1.8;
}

div[data-testid="stMetric"] {
    background: white;
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1rem;
}

div[data-testid="stMetricLabel"] {
    font-size: 0.82rem;
}

div[data-testid="stMetricValue"] {
    color: var(--green);
}

[data-testid="stSidebar"] {
    background: #F0F3F0;
}

.sidebar-heading {
    color: var(--green);
    font-weight: 700;
    font-size: 0.88rem;
    margin-top: 1rem;
    margin-bottom: 0.4rem;
}

@media (max-width: 640px) {
    .block-container {
        padding-top: 1.2rem;
    }

    .brand {
        margin-bottom: 1.7rem;
    }

    .hero-title {
        font-size: 2.2rem;
    }

    .result-card {
        padding: 1rem;
    }

    .legal-text {
        font-size: 0.98rem;
    }
}
</style>
"""

st.markdown(CSS, unsafe_allow_html=True)


# ============================================================
# 4. LOAD EXISTING RAG ASSISTANT
# ============================================================

@st.cache_resource(show_spinner="Loading the Act and search models...")
def load_assistant():
    assistant = Assistant()
    metadata = {}

    for unit in assistant.retriever.units:
        metadata.setdefault(unit["section_id"], unit)

    return assistant, metadata


def ollama_up():
    try:
        response = requests.get(
            "http://localhost:11434/api/tags",
            timeout=2,
        )
        return response.ok
    except requests.RequestException:
        return False


assistant, metadata = load_assistant()


# ============================================================
# 5. SESSION STATE AND HELPERS
# ============================================================

if "question_input" not in st.session_state:
    st.session_state["question_input"] = ""

if "active_question" not in st.session_state:
    st.session_state["active_question"] = ""

if "result_cache" not in st.session_state:
    st.session_state["result_cache"] = {}


def choose_question(question):
    """Populate the question box and submit the selected example."""
    st.session_state["question_input"] = question
    st.session_state["active_question"] = question


def clean_answer(answer):
    """Remove a trailing bracketed citation such as [s60F]."""
    return re.sub(r"\s*\[[^\]]*\]\s*$", "", answer).strip()


def safe_paragraphs(text):
    """Escape source text before inserting it into HTML."""
    return "".join(
        f"<p>{html.escape(paragraph.strip())}</p>"
        for paragraph in text.splitlines()
        if paragraph.strip()
    )


def section_body(section_id):
    """Return the body using the same parsing convention as the old app."""
    full_text = assistant.full[section_id]
    return full_text.split("\n", 1)[-1]


def section_heading(unit):
    heading = unit.get("heading", "")
    if heading:
        return f"Section {unit['section']}: {heading}"
    return f"Section {unit['section']}"


def get_results(question, use_ai):
    """
    Cache results for the same question and mode during this session.
    The underlying retrieval and generation implementations are unchanged.
    """
    cache_key = (question.strip(), use_ai)

    if cache_key in st.session_state["result_cache"]:
        return st.session_state["result_cache"][cache_key]


    if use_ai:
        with st.spinner("Searching the Act and preparing the explanation..."):
            result = assistant.answer(question)

        ids = result["retrieved"]
    else:
        with st.spinner("Searching the Employment Act..."):
            ids = [
                unit["section_id"]
                for unit, _score in assistant.retriever.search(
                    question, "hybrid", k=3
                )
            ]
        result = None

    data = (ids, result)
    st.session_state["result_cache"][cache_key] = data

    # Keep the cache bounded during longer sessions.
    if len(st.session_state["result_cache"]) > 20:
        oldest_key = next(iter(st.session_state["result_cache"]))
        del st.session_state["result_cache"][oldest_key]

    return data


# ============================================================
# 6. SIDEBAR
# ============================================================

with st.sidebar:
    st.markdown(
        f"""
        <div class="brand" style="margin-bottom:1.3rem">
            <div class="brand-icon">⚖</div>
            <div>
                <div class="brand-name">{html.escape(APP_NAME)}</div>
                <div class="brand-subtitle">EMPLOYMENT LAW AI</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### About this assistant")
    st.write(
        "Ask questions about employment rights and explore relevant "
        "provisions retrieved from the indexed legislation."
    )

    st.markdown('<div class="sidebar-heading">LEGAL SOURCE</div>',
                unsafe_allow_html=True)
    st.write(SOURCE_NAME)
    st.caption(f"Indexed text date: {SOURCE_DATE}")
    st.caption(f"Stated coverage: {SOURCE_COVERAGE}")

    st.divider()

    st.markdown("### Answer mode")
    ollama_available = ollama_up()

    mode_options = ["Legal sources only"]
    if ollama_available:
        mode_options.append("Sources + AI explanation")

    selected_mode = st.radio(
        "Choose how results are displayed",
        mode_options,
        index=0,
        help="AI explanations require the local Ollama service.",
    )

    use_ai = selected_mode == "Sources + AI explanation"

    if not ollama_available:
        st.info(
            "AI explanations are unavailable because Ollama could not "
            "be reached at localhost:11434. Source retrieval remains available."
        )

    st.divider()

    with st.expander("How does it work?"):
        st.markdown(
            """
            1. **Ask:** Enter a question about employment rights.
            2. **Retrieve:** The system searches the indexed Act for relevant sections.
            3. **Verify:** Read the original legal text.
            4. **Explain:** Optionally request an AI-generated explanation.
            """
        )

    with st.expander("Important limitations"):
        st.write(
            "The indexed text is dated 1 August 2023. This interface does "
            "not independently verify whether the text reflects subsequent "
            "legal amendments. Retrieval can miss relevant provisions, and "
            "AI-generated explanations can be incorrect."
        )

    st.caption("For general information and educational purposes only.")


# ============================================================
# 7. MAIN HEADER
# ============================================================

st.markdown(
    f"""
    <div class="brand">
        <div class="brand-icon">⚖</div>
        <div>
            <div class="brand-name">{html.escape(APP_NAME)}</div>
            <div class="brand-subtitle">{html.escape(APP_SUBTITLE)}</div>
        </div>
    </div>

    <div class="hero-label">Employment rights, made easier to understand</div>
    <h1 class="hero-title">Understand your rights at work.</h1>
    <div class="hero-description">
        Ask questions about Malaysian employment law, find relevant
        provisions of the Employment Act 1955, and explore the original
        legal text with optional AI-assisted explanations.
    </div>

    <div class="source-strip">
        <span class="source-chip">📘 {html.escape(SOURCE_NAME)}</span>
        <span class="source-chip">Text dated {html.escape(SOURCE_DATE)}</span>
        <span class="source-chip">{html.escape(SOURCE_COVERAGE)}</span>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# 8. QUESTION FORM
# ============================================================

st.markdown(
    '<div class="section-heading">What would you like to know?</div>'
    '<div class="section-description">'
    'Ask in everyday language. The assistant will search the indexed '
    'legislation for relevant provisions.'
    '</div>',
    unsafe_allow_html=True,
)

with st.form("question_form", clear_on_submit=False):
    st.text_input(
        "Your question",
        key="question_input",
        placeholder="e.g. How many days of paid sick leave am I entitled to?",
        label_visibility="collapsed",
    )

    submitted = st.form_submit_button(
        "Find relevant sections",
        type="primary",
        use_container_width=True,
    )

    if submitted:
        st.session_state["active_question"] = (
            st.session_state["question_input"].strip()
        )


st.markdown(
    '<div style="font-size:.84rem;font-weight:600;margin:1.2rem 0 .7rem 0">'
    'Explore a topic</div>',
    unsafe_allow_html=True,
)

example_items = list(EXAMPLES.items())

for start in range(0, len(example_items), 4):
    row = st.columns(4)
    for column, (label, question) in zip(row, example_items[start:start + 4]):
        column.button(
            label,
            key=f"example_{label}",
            use_container_width=True,
            on_click=choose_question,
            args=(question,),
        )


# ============================================================
# 9. RETRIEVAL RESULTS
# ============================================================

question = st.session_state.get("active_question", "").strip()

if question:
    st.divider()

    st.markdown(
        '<div class="section-heading">Your search results</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="section-description">Question: '
        f'{html.escape(question)}</div>',
        unsafe_allow_html=True,
    )

    try:
        ids, result = get_results(question, use_ai)

        # Remove duplicate section IDs without changing their order.
        ids = list(dict.fromkeys(ids))

        if not ids:
            st.warning(
                "No relevant sections were retrieved. Try rephrasing "
                "your question or using a more specific employment-law topic."
            )
        else:
            first_id = ids[0]

            if first_id not in metadata or first_id not in assistant.full:
                st.error(
                    "The retrieved section could not be matched to its "
                    "source text. Please check the retrieval metadata."
                )
            else:
                first_unit = metadata[first_id]
                first_body = section_body(first_id)

                st.markdown(
                    f"""
                    <div class="result-card">
                        <div class="result-eyebrow">
                            Most relevant retrieved provision
                        </div>
                        <div class="section-number">
                            Section {html.escape(str(first_unit['section']))}
                        </div>
                        <div class="result-title">
                            {html.escape(first_unit.get('heading') or 'Legal provision')}
                        </div>
                        <div class="legal-text">
                            {safe_paragraphs(first_body)}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                if len(assistant.full[first_id]) >= 4000:
                    st.caption(
                        "This section is long. Check the indexed source "
                        "for the complete provision."
                    )

                other_ids = [
                    sid for sid in ids[1:]
                    if sid in metadata and sid in assistant.full
                ]

                if other_ids:
                    st.markdown("#### Other relevant sections")

                    for sid in other_ids:
                        unit = metadata[sid]
                        with st.expander(section_heading(unit)):
                            st.markdown(
                                f'<div class="legal-text">'
                                f'{safe_paragraphs(section_body(sid))}'
                                f'</div>',
                                unsafe_allow_html=True,
                            )

            # ------------------------------------------------
            # 10. OPTIONAL AI EXPLANATION
            # ------------------------------------------------

            if result is not None:
                st.markdown("### AI-assisted explanation")

                if result.get("unsupported", False):
                    st.markdown(
                        """
                        <div class="warning-note">
                            <strong>Explanation not displayed</strong><br>
                            The generated answer could not be matched to
                            the indexed Act. Please inspect the retrieved
                            legal provisions above.
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                elif result.get("abstained", False):
                    st.markdown(
                        """
                        <div class="info-note">
                            <strong>No direct answer was generated.</strong><br>
                            The closest retrieved sections are shown above,
                            but they may not directly answer your question.
                            Try rephrasing your question if appropriate.
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                else:
                    answer = clean_answer(result.get("answer", ""))
                    quote = result.get("quote", "")
                    cited_sections = result.get("cited", [])

                    if isinstance(cited_sections, (list, tuple)):
                        cited = ", ".join(
                            f"Section {str(section).lstrip('sS')}"
                            for section in cited_sections
                        )
                    else:
                        cited = str(cited_sections)

                    st.markdown(
                        f"""
                        <div class="ai-card">
                            <div class="ai-heading">
                                ✦ AI-generated explanation
                            </div>
                            <div class="ai-text">
                                {html.escape(answer)}
                            </div>
                            <div class="quote-box">
                                <strong>Quoted legal text</strong><br><br>
                                {html.escape(quote)}
                            </div>
                            <div style="font-size:.8rem;color:#6A604A;margin-top:1rem">
                                Citation reported by the assistant:
                                {html.escape(cited or 'No citation supplied')}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    st.caption(
                        "The quoted text is checked by the existing "
                        "assistant logic, but that does not prove that "
                        "the explanation is correct or complete. Compare "
                        "it with the retrieved legal provision."
                    )

    except Exception:
        st.error(
            "Something went wrong while retrieving or displaying the "
            "results. Please check the application logs and confirm that "
            "the search models and required services are available."
        )
        st.exception(sys.exc_info()[1])


# ============================================================
# 11. EVALUATION DASHBOARD
# ============================================================

st.divider()

st.markdown(
    '<div class="section-heading">How reliable is the assistant?</div>'
    '<div class="section-description">'
    'Initial manually assessed evaluation on 19 held-out questions. '
    'These results are preliminary, not a guarantee of future performance.'
    '</div>',
    unsafe_allow_html=True,
)

metric_cols = st.columns(2)

with metric_cols[0]:
    st.metric(
        "Top-3 retrieval success",
        "14 / 19",
        help="The correct section appeared among the top three results.",
    )

with metric_cols[1]:
    st.metric(
        "Top-3 retrieval rate",
        "73.7%",
        help="14 divided by 19 held-out questions.",
    )

st.markdown("#### AI summary assessment")

summary_cols = st.columns(4)

summary_metrics = [
    ("Fully correct", "4", "21.1% of all test questions"),
    ("Partly correct", "2", "10.5% of all test questions"),
    ("Incorrect", "3", "15.8% of all test questions"),
    ("Declined", "10", "52.6% of all test questions"),
]

for col, (label, value, help_text) in zip(summary_cols, summary_metrics):
    with col:
        st.metric(label, value, help=help_text)

st.markdown(
    """
    <div class="warning-note">
        <strong>Important evaluation limitation</strong><br>
        In the reported test, the assistant declined all 3 questions
        judged to be outside the Act's coverage. The test set is small
        and was graded manually by the author. A real quotation from
        legislation does not guarantee a correct explanation.
        The indexed text is dated 1 August 2023.
    </div>
    """,
    unsafe_allow_html=True,
)

with st.expander("Evaluation methodology and known limitations"):
    st.markdown(
        """
        - **Retrieval:** the correct section appeared among the top three
          retrieved results for 14 of 19 held-out questions.
        - **Summary assessment:** 4 fully correct, 2 partly correct,
          3 incorrect, and 10 declined, based on the author's manual grading.
        - **Out-of-scope questions:** 3 of 3 were declined in the reported test.
        - **Known failure:** an explanation may quote a real sentence but
          still give the wrong answer, such as an incorrect notice period
          for a particular length of service.
        - **Limitations:** the sample is small and does not establish
          performance across all employment-law questions.
        """
    )


# ============================================================
# 12. FOOTER
# ============================================================

st.markdown(
    f"""
    <div class="disclaimer">
        <strong>{html.escape(APP_NAME)}</strong><br>
        Source: {html.escape(SOURCE_NAME)}. Indexed text dated
        {html.escape(SOURCE_DATE)}. Stated coverage:
        {html.escape(SOURCE_COVERAGE)}.<br><br>
        This tool provides general information for educational purposes
        and is not legal advice. The displayed source date does not
        establish that the legislation is current. Verify relevant
        provisions against applicable official sources and amendments.
    </div>
    """,
    unsafe_allow_html=True,
)
