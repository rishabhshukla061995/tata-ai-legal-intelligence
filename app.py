import start_backend  # noqa: F401 — boots FastAPI in background thread
from datetime import date, timedelta

import httpx
import pandas as pd
import streamlit as st

from config import BACKEND_URL, HISTORY_TURNS
from utils.highlight import highlight_html

ALL_DOCS = "All Documents"

# ─────────────────────────────────────────────────────────────
# Page config & global CSS
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Tata Legal AI — Document Intelligence",
    layout="wide",
    page_icon="⚖️",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
/* ── Google Font ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Playfair+Display:wght@700&display=swap');

/* ── Root variables ── */
:root {
    --navy:    #0F1B35;
    --teal:    #0D6E6E;
    --teal-lt: #E6F4F4;
    --gold:    #C9933A;
    --gold-lt: #FBF4E8;
    --slate:   #4A5568;
    --muted:   #718096;
    --bg:      #F7F8FA;
    --white:   #FFFFFF;
    --border:  #E2E8F0;
    --danger:  #C53030;
    --warn:    #D97706;
    --ok:      #276749;
}

/* ── App shell ── */
.stApp { background: var(--bg); font-family: 'Inter', sans-serif; }

/* ── Hide default Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }

/* ── Custom header banner ── */
.hero-banner {
    background: linear-gradient(135deg, var(--navy) 0%, #1a2f5e 60%, #0D3B5E 100%);
    border-radius: 12px;
    padding: 28px 36px 22px;
    margin-bottom: 24px;
    display: flex;
    align-items: center;
    gap: 20px;
    box-shadow: 0 4px 24px rgba(15,27,53,.18);
}
.hero-title {
    font-family: 'Playfair Display', serif;
    font-size: 2rem;
    font-weight: 700;
    color: #FFFFFF;
    margin: 0 0 4px;
    letter-spacing: -.01em;
}
.hero-sub {
    font-size: 0.9rem;
    color: rgba(255,255,255,.65);
    margin: 0;
    font-weight: 400;
}
.hero-badge {
    background: rgba(201,147,58,.2);
    border: 1px solid rgba(201,147,58,.5);
    color: var(--gold);
    font-size: 0.72rem;
    font-weight: 600;
    padding: 2px 10px;
    border-radius: 20px;
    display: inline-block;
    margin-top: 6px;
    letter-spacing: .05em;
    text-transform: uppercase;
}

/* ── Stat cards ── */
.stat-row { display: flex; gap: 14px; margin-bottom: 20px; flex-wrap: wrap; }
.stat-card {
    flex: 1; min-width: 130px;
    background: var(--white);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 14px 18px;
    box-shadow: 0 1px 4px rgba(0,0,0,.05);
}
.stat-card .label { font-size: 0.75rem; color: var(--muted); font-weight: 500; text-transform: uppercase; letter-spacing: .06em; }
.stat-card .value { font-size: 1.75rem; font-weight: 700; color: var(--navy); line-height: 1.1; margin-top: 2px; }
.stat-card .detail { font-size: 0.78rem; color: var(--slate); margin-top: 2px; }
.stat-card.teal  { border-left: 3px solid var(--teal); }
.stat-card.gold  { border-left: 3px solid var(--gold); }
.stat-card.red   { border-left: 3px solid var(--danger); }
.stat-card.green { border-left: 3px solid var(--ok); }

/* ── Action button cluster ── */
.action-row { display: flex; gap: 10px; margin-bottom: 16px; flex-wrap: wrap; }

/* ── Streamlit button overrides ── */
.stButton > button {
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    padding: 8px 18px !important;
    border: 1.5px solid var(--border) !important;
    background: var(--white) !important;
    color: var(--navy) !important;
    transition: all .15s ease !important;
}
.stButton > button:hover {
    border-color: var(--teal) !important;
    color: var(--teal) !important;
    box-shadow: 0 2px 8px rgba(13,110,110,.12) !important;
}
.stButton > button[kind="primary"], .primary-btn > button {
    background: var(--teal) !important;
    color: white !important;
    border-color: var(--teal) !important;
}
.stButton > button[kind="primary"]:hover { background: #0a5858 !important; }

/* ── Chat bubbles ── */
.chat-user {
    background: var(--navy);
    color: #fff;
    border-radius: 16px 16px 4px 16px;
    padding: 12px 18px;
    margin: 8px 0 8px auto;
    max-width: 72%;
    font-size: 0.9rem;
    line-height: 1.55;
}
.chat-ai {
    background: var(--white);
    border: 1px solid var(--border);
    border-radius: 16px 16px 16px 4px;
    padding: 12px 18px;
    margin: 8px auto 8px 0;
    max-width: 88%;
    font-size: 0.9rem;
    line-height: 1.6;
    box-shadow: 0 1px 4px rgba(0,0,0,.06);
}
.chat-timestamp { font-size: 0.7rem; color: var(--muted); margin-top: 2px; }

/* ── Source expander ── */
.src-chunk {
    background: var(--teal-lt);
    border-left: 3px solid var(--teal);
    border-radius: 0 6px 6px 0;
    padding: 10px 14px;
    margin: 8px 0;
    font-size: 0.84rem;
    line-height: 1.6;
    color: var(--slate);
}
mark { background: #FDE68A; color: #111; padding: 0 2px; border-radius: 2px; }

/* ── Risk badge ── */
.risk-badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: .04em;
}
.risk-high   { background: #FEE2E2; color: #C53030; }
.risk-medium { background: #FEF3C7; color: #D97706; }
.risk-low    { background: #DCFCE7; color: #276749; }

/* ── Progress bar override ── */
.stProgress > div > div > div { background: var(--teal) !important; border-radius: 8px; }

/* ── Tab styling ── */
.stTabs [role="tab"] {
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    color: var(--slate) !important;
    padding: 8px 20px !important;
}
.stTabs [aria-selected="true"] {
    color: var(--teal) !important;
    border-bottom: 3px solid var(--teal) !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: var(--white) !important;
    border-right: 1px solid var(--border) !important;
}
.sidebar-logo {
    background: var(--navy);
    color: white;
    border-radius: 10px;
    padding: 12px 14px;
    margin-bottom: 16px;
    font-weight: 700;
    font-size: 0.95rem;
    letter-spacing: -.01em;
}

/* ── Info/warning callouts ── */
.callout {
    border-radius: 8px;
    padding: 12px 16px;
    font-size: 0.85rem;
    margin: 10px 0;
    display: flex;
    gap: 10px;
    align-items: flex-start;
}
.callout.info  { background: var(--teal-lt); border-left: 3px solid var(--teal); color: var(--slate); }
.callout.warn  { background: var(--gold-lt); border-left: 3px solid var(--gold); color: var(--slate); }
.callout.error { background: #FEF2F2;         border-left: 3px solid var(--danger); color: #7F1D1D; }

/* ── Deadline row colors ── */
.dl-overdue { color: var(--danger); font-weight: 600; }
.dl-soon    { color: var(--warn);   font-weight: 600; }
.dl-ok      { color: var(--ok); }

/* ── Metric override ── */
[data-testid="stMetricValue"] { font-size: 1.8rem !important; color: var(--navy) !important; }
[data-testid="stMetricLabel"] { font-size: 0.78rem !important; color: var(--muted) !important; }

/* ── Dataframe ── */
[data-testid="stDataFrame"] { border-radius: 10px; overflow: hidden; }

/* ── Upload area ── */
[data-testid="stFileUploader"] {
    border: 2px dashed var(--border) !important;
    border-radius: 10px !important;
    background: var(--white) !important;
}

/* ── Divider ── */
hr { border-color: var(--border) !important; margin: 20px 0 !important; }

/* ── Spinner ── */
.stSpinner { color: var(--teal) !important; }

/* ── Selectbox ── */
[data-baseweb="select"] > div { border-radius: 8px !important; border-color: var(--border) !important; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# Backend helpers
# ─────────────────────────────────────────────────────────────
def api(method: str, path: str, raw: bool = False, **kwargs):
    try:
        r = httpx.request(method, f"{BACKEND_URL}{path}", timeout=300, **kwargs)
    except httpx.HTTPError:
        return None, f"Backend not reachable at {BACKEND_URL}. Start with: uvicorn backend.main:app --reload"
    if r.status_code >= 400:
        try:
            return None, r.json().get("detail", r.text)
        except ValueError:
            return None, r.text
    return (r.content if raw else r.json()), None


def callout(icon: str, message: str, kind: str = "info"):
    st.markdown(f'<div class="callout {kind}"><span>{icon}</span><span>{message}</span></div>',
                unsafe_allow_html=True)


def show_sources(sources, answer: str = ""):
    if not sources:
        return
    with st.expander(f"📚 {len(sources)} source chunk{'s' if len(sources) != 1 else ''} retrieved"):
        for s in sources:
            score_str = f" · relevance {s['score']:.0%}" if s.get("score") is not None else ""
            st.markdown(f"**📄 {s['source']}**{score_str}")
            st.markdown(
                f"<div class='src-chunk'>{highlight_html(s['text'], answer)}</div>",
                unsafe_allow_html=True,
            )


def risk_badge(level: str) -> str:
    cls = {"High": "risk-high", "Medium": "risk-medium", "Low": "risk-low"}.get(level, "")
    return f'<span class="risk-badge {cls}">{level}</span>'


def stat_card(label: str, value, detail: str = "", color: str = "teal") -> str:
    return (f'<div class="stat-card {color}">'
            f'<div class="label">{label}</div>'
            f'<div class="value">{value}</div>'
            f'<div class="detail">{detail}</div>'
            f'</div>')


# ─────────────────────────────────────────────────────────────
# Session state defaults
# ─────────────────────────────────────────────────────────────
for key, default in {
    "messages": [], "uploaded": set(), "risk": None, "schedule": None,
    "eval": None, "panel": None, "report": None,
}.items():
    st.session_state.setdefault(key, default)


# ─────────────────────────────────────────────────────────────
# Health check (do this once; stop early if backend is down)
# ─────────────────────────────────────────────────────────────
import time as _time
for _attempt in range(15):
    health, err = api("GET", "/health")
    if not err:
        break
    _time.sleep(1)
if err:
    st.markdown("""
    <div class="hero-banner">
        <div>
            <div class="hero-title">⚖️ Tata Legal AI</div>
            <div class="hero-sub">Document Intelligence System</div>
        </div>
    </div>""", unsafe_allow_html=True)
    st.markdown(f'<div class="callout error">🔌 <strong>Backend offline.</strong> {err}</div>',
                unsafe_allow_html=True)
    st.stop()

llm = health["llm"]
docs, _ = api("GET", "/documents")
docs = docs or []
uploads = [d["name"] for d in docs if d["type"] == "upload"]
kb_docs = [d["name"] for d in docs if d["type"] == "knowledge_base"]


# ─────────────────────────────────────────────────────────────
# Hero banner
# ─────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="hero-banner">
<div style="font-size:2.8rem; line-height:1;">⚖️</div>
<div style="flex:1">
<div class="hero-title">Tata Group Legal AI Intelligence</div>
<div class="hero-sub">Multi-document RAG · Automated audit · Risk scoring · Deadline tracking</div>
<span class="hero-badge">🤖 {llm['provider'].upper()} · {llm['model']}</span>
{"" if health['llm_configured'] else '<span class="hero-badge" style="border-color:rgba(201,58,58,.5);background:rgba(201,58,58,.15);color:#f87171;margin-left:8px;">⚠️ API key missing</span>'}
</div>
<div style="text-align:right;color:rgba(255,255,255,.5);font-size:0.78rem;">
{len(uploads)} uploaded<br>
{len(kb_docs)} policy files<br>
{len(uploads)+len(kb_docs)} total docs
</div>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="sidebar-logo">⚖️ Tata Legal AI</div>', unsafe_allow_html=True)

    language = st.selectbox("🌐 Answer language", health.get("languages", ["English"]))

    st.markdown("**📂 Upload a contract**")
    uploaded_file = st.file_uploader(
        "Drop PDF, DOCX, TXT, MD or CSV",
        type=["txt", "md", "pdf", "docx", "csv"],
        label_visibility="collapsed",
    )
    if uploaded_file is not None:
        key = (uploaded_file.name, uploaded_file.size)
        if key not in st.session_state.uploaded:
            with st.spinner(f"Indexing {uploaded_file.name}…"):
                data, err = api("POST", "/upload", files={"file": (uploaded_file.name, uploaded_file.getvalue())})
            if err:
                callout("❌", err, "error")
            else:
                st.session_state.uploaded.add(key)
                st.success(f"✅ {data['name']} · {data['chunks']} chunks indexed")
                st.rerun()

    st.divider()

    # Document list
    st.markdown("**📄 Indexed documents**")
    if uploads:
        st.markdown("*Uploaded contracts*")
        for name in uploads:
            col1, col2 = st.columns([4, 1])
            col1.markdown(f"📎 {name}", help=name)
            if col2.button("🗑", key=f"del_{name}", help=f"Remove {name}"):
                api("DELETE", f"/documents/{name}")
                st.rerun()
    if kb_docs:
        st.caption(f"🏛️ Tata policy KB · {len(kb_docs)} files")

    st.divider()

    if st.button("🗑️ Clear conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    if st.button("🔄 Re-index knowledge base", use_container_width=True):
        with st.spinner("Re-indexing…"):
            api("POST", "/reindex")
        st.success("Knowledge base re-indexed")

    # Recent history
    history_data, _ = api("GET", "/history")
    if history_data:
        st.divider()
        with st.expander(f"🕓 Recent queries ({len(history_data)})"):
            for item in history_data[:6]:
                st.markdown(f"**{item['task'].title()}** · `{item.get('source') or 'All'}`")
                st.caption(item["question"][:80] + ("…" if len(item["question"]) > 80 else ""))


all_names = uploads + kb_docs
options = [ALL_DOCS] + all_names


def pick(label: str, key: str, opts=None):
    choice = st.selectbox(label, opts or options, key=key)
    return None if choice == ALL_DOCS else choice


# ─────────────────────────────────────────────────────────────
# Tabs
# ─────────────────────────────────────────────────────────────
tab_chat, tab_policy, tab_risk, tab_dates, tab_eval = st.tabs([
    "💬 Chat & Audits",
    "🛡️ Policy Check & Compare",
    "📊 Risk Dashboard",
    "🗓️ Deadline Tracker",
    "🧪 Accuracy Test",
])


# ═══════════════════════════════════════════════════════════════
# TAB 1 — Chat & Audits
# ═══════════════════════════════════════════════════════════════
with tab_chat:
    col_top, col_doc = st.columns([3, 2])
    with col_top:
        st.markdown("#### 💬 Chat with your legal documents")
        st.caption("Ask questions, run audits, download reports. The AI cites its sources.")
    with col_doc:
        source = pick("Scope to document:", "chat_doc")

    # One-click audit buttons
    st.markdown("**Quick audits**")
    b1, b2, b3 = st.columns(3)
    audit_summarize = b1.button("🔍 Summarize", use_container_width=True, help="Executive summary of the agreement")
    audit_risks     = b2.button("⚠️ Detect Risks", use_container_width=True, help="Hidden and legal risk clauses")
    audit_deadlines = b3.button("🗓️ Key Dates", use_container_width=True, help="Extract all deadlines and notice periods")

    actions = {"summarize": audit_summarize, "risks": audit_risks, "deadlines": audit_deadlines}
    labels  = {"summarize": "Summary", "risks": "Risk report", "deadlines": "Deadlines & terms"}

    for task, clicked in actions.items():
        if clicked:
            with st.spinner(f"Running {labels[task].lower()}…"):
                data, err = api("POST", "/ask", json={"task": task, "source": source, "language": language})
            if err:
                st.session_state.messages.append({"role": "assistant", "content": f"❌ {err}", "sources": [], "error": True})
            else:
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"**{labels[task]}: {source or ALL_DOCS}**\n\n{data['answer']}",
                    "sources": data["sources"],
                })

    # Report download
    with st.expander("📥 Generate full Word report"):
        st.caption("Runs all analyses (summary, risks, deadlines, risk score) and produces a .docx — takes ~60s.")
        if st.button("⚙️ Build report", key="gen_report"):
            with st.spinner("Generating report — this takes about a minute…"):
                content, err = api("POST", "/report", raw=True, json={"source": source, "language": language})
            if err:
                callout("❌", err, "error")
            else:
                st.session_state.report = (content, source or ALL_DOCS)
        if st.session_state.report:
            content, name = st.session_state.report
            st.download_button(
                f"⬇️ Download: {name}.docx", content,
                file_name="contract_report.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True,
            )

    st.divider()

    # Chat conversation
    if not st.session_state.messages:
        st.markdown("""
        <div class="callout info">
            💡 <strong>Try asking:</strong>
            "What are the payment terms?" · "Summarize the liability clauses" · "When does the contract expire?"
        </div>""", unsafe_allow_html=True)
    else:
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                st.markdown(f'<div class="chat-user">🧑 {msg["content"]}</div>', unsafe_allow_html=True)
            else:
                is_error = msg.get("error", False)
                bg = "#FEF2F2" if is_error else ""
                st.markdown(
                    f'<div class="chat-ai" style="{"background:"+bg if bg else ""}">'
                    f'⚖️ {msg["content"]}</div>',
                    unsafe_allow_html=True,
                )
                show_sources(msg.get("sources", []), msg["content"])


# chat_input must stay outside tabs (Streamlit constraint)
if query := st.chat_input("Ask a question about the selected document…"):
    history = [
        {"role": m["role"], "content": m["content"]}
        for m in st.session_state.messages if not m.get("error")
    ][-HISTORY_TURNS:]
    st.session_state.messages.append({"role": "user", "content": query})
    with st.spinner("Thinking…"):
        chat_source = st.session_state.get("chat_doc")
        data, err = api("POST", "/ask", json={
            "task": "chat",
            "source": chat_source if chat_source != ALL_DOCS else None,
            "question": query,
            "history": history,
            "language": language,
        })
    if err:
        st.session_state.messages.append({"role": "assistant", "content": f"❌ {err}", "sources": [], "error": True})
    else:
        st.session_state.messages.append({"role": "assistant", "content": data["answer"], "sources": data["sources"]})
    st.rerun()


# ═══════════════════════════════════════════════════════════════
# TAB 2 — Policy Check & Compare
# ═══════════════════════════════════════════════════════════════
with tab_policy:
    col_p1, col_p2 = st.columns(2, gap="large")

    with col_p1:
        st.markdown("#### 🛡️ Policy compliance check")
        st.caption("Checks every clause of an uploaded contract against Tata's internal policy knowledge base.")
        if not uploads:
            callout("📂", "Upload a contract in the sidebar first.", "warn")
        else:
            contract = st.selectbox("Contract to check", uploads, key="policy_doc")
            if st.button("▶ Run policy check", use_container_width=True):
                with st.spinner("Comparing clauses with Tata policy…"):
                    data, err = api("POST", "/ask", json={"task": "compliance", "source": contract, "language": language})
                st.session_state.panel = ("Policy check", contract, data, err)

    with col_p2:
        st.markdown("#### ⚖️ Compare two documents")
        st.caption("Side-by-side clause-by-clause comparison — highlights which is more favourable.")
        if len(all_names) < 2:
            callout("📄", "You need at least two documents indexed to compare.", "info")
        else:
            a_col, b_col = st.columns(2)
            doc_a = a_col.selectbox("Document A", all_names, key="cmp_a")
            doc_b = b_col.selectbox("Document B", all_names, index=min(1, len(all_names)-1), key="cmp_b")
            if st.button("▶ Compare documents", use_container_width=True):
                with st.spinner("Comparing clause by clause…"):
                    data, err = api("POST", "/ask", json={
                        "task": "compare", "source": doc_a, "source_b": doc_b, "language": language,
                    })
                st.session_state.panel = ("Comparison", f"{doc_a}  vs  {doc_b}", data, err)

    # Results panel
    if st.session_state.panel:
        title, name, data, err = st.session_state.panel
        st.divider()
        st.markdown(f"#### {title}: `{name}`")
        if err:
            callout("❌", err, "error")
        else:
            st.markdown(data["answer"])
            show_sources(data["sources"], data["answer"])


# ═══════════════════════════════════════════════════════════════
# TAB 3 — Risk Dashboard
# ═══════════════════════════════════════════════════════════════
with tab_risk:
    st.markdown("#### 📊 Contract risk dashboard")
    r_col1, r_col2 = st.columns([3, 1])
    with r_col1:
        risk_doc = pick("Document to score:", "risk_doc")
    with r_col2:
        st.markdown("<br>", unsafe_allow_html=True)
        run_risk = st.button("▶ Calculate risk score", use_container_width=True)

    if run_risk:
        with st.spinner("Scoring contract risks…"):
            data, err = api("POST", "/risk-score", json={"source": risk_doc, "language": language})
        st.session_state.risk = (risk_doc or ALL_DOCS, data, err)

    if st.session_state.risk:
        name, data, err = st.session_state.risk
        if err:
            callout("❌", err, "error")
        else:
            score = data["overall_score"]
            level = data["level"]
            icon  = {"High": "🔴", "Medium": "🟠", "Low": "🟢"}.get(level, "⚪")
            cnt   = data["counts"]

            # Stat cards
            st.markdown(
                '<div class="stat-row">'
                + stat_card("Overall score", f"{score}/100", level, "red" if level == "High" else "gold" if level == "Medium" else "green")
                + stat_card("Risk level", f"{icon} {level}", f"out of {len(data['risks'])} risks", "teal")
                + stat_card("High severity", cnt["High"], "clauses to fix urgently", "red")
                + stat_card("Medium severity", cnt["Medium"], "clauses to review", "gold")
                + stat_card("Low / clear", cnt["Low"], "compliant clauses", "green")
                + '</div>',
                unsafe_allow_html=True,
            )

            # Progress bar
            bar_col, label_col = st.columns([6, 1])
            bar_col.progress(score / 100)
            label_col.markdown(f"<div style='font-size:1.4rem;font-weight:700;color:var(--navy);text-align:right'>{score}%</div>", unsafe_allow_html=True)

            st.caption(f"**{name}:** {data['summary']}")

            # Chart
            chart_df = pd.DataFrame(
                {"Count": [cnt[k] for k in ["High", "Medium", "Low"]]},
                index=["High risk", "Medium risk", "Low risk"],
            )
            st.bar_chart(chart_df, color="#0D6E6E")

            # Risk table with badges
            if data["risks"]:
                st.markdown("**Identified risks**")
                rows = []
                for r in data["risks"]:
                    rows.append({
                        "Severity": r.get("severity", ""),
                        "Clause": r.get("clause", ""),
                        "Issue": r.get("issue", ""),
                        "Recommended fix": r.get("fix", r.get("recommendation", "")),
                    })
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════════════
# TAB 4 — Deadline Tracker
# ═══════════════════════════════════════════════════════════════
with tab_dates:
    st.markdown("#### 🗓️ Deadline tracker")
    st.caption("Enter the contract period — the AI extracts every notice period and turns it into a real calendar date.")

    d1, d2, d3, d4 = st.columns([2, 1, 1, 1])
    dl_doc = d1.selectbox("Document", options, key="dl_doc")
    start  = d2.date_input("Start date",  date.today())
    end    = d3.date_input("End date",    date.today() + timedelta(days=365))
    d4.markdown("<br>", unsafe_allow_html=True)
    run_dl = d4.button("▶ Build schedule", use_container_width=True)

    if run_dl:
        with st.spinner("Extracting deadlines…"):
            data, err = api("POST", "/deadlines/schedule", json={
                "source": None if dl_doc == ALL_DOCS else dl_doc,
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
            })
        st.session_state.schedule = (dl_doc, data, err)

    if st.session_state.schedule:
        name, data, err = st.session_state.schedule
        if err:
            callout("❌", err, "error")
        else:
            rows = data.get("deadlines", [])
            if not rows:
                callout("✅", "No deadlines found in this document.", "info")
            else:
                # Summary counts
                today_str = date.today().isoformat()
                overdue = sum(1 for r in rows if (r.get("due_date") or "") and (r.get("due_date") or "") < today_str)
                upcoming = sum(1 for r in rows if today_str <= (r.get("due_date") or "") <= (date.today() + timedelta(days=30)).isoformat())

                st.markdown(
                    '<div class="stat-row">'
                    + stat_card("Total deadlines", len(rows), "extracted from document", "teal")
                    + stat_card("Overdue", overdue, "past today", "red")
                    + stat_card("Due within 30d", upcoming, "coming soon", "gold")
                    + '</div>',
                    unsafe_allow_html=True,
                )

                table = pd.DataFrame(rows).reindex(
                    columns=["due_date", "status", "term", "description", "event", "source"])
                table.columns = ["Due date", "Status", "Term", "Description", "Starts from", "Source"]
                st.dataframe(table.fillna(""), use_container_width=True, hide_index=True)

                # Calendar + email
                dl_col1, dl_col2 = st.columns(2)
                with dl_col1:
                    ics, _ = api("POST", "/deadlines/ics", raw=True, json={"contract": name, "deadlines": rows})
                    if ics:
                        st.download_button(
                            "📅 Add to calendar (.ics)", ics,
                            file_name="contract_deadlines.ics", mime="text/calendar",
                            use_container_width=True,
                        )
                with dl_col2:
                    with st.form("remind_form"):
                        email = st.text_input("📧 Email reminders to:", placeholder="you@example.com")
                        if st.form_submit_button("Send", use_container_width=True):
                            if not health.get("email_configured"):
                                callout("⚠️", "Email not configured. Add SMTP settings to .env — use the .ics file instead.", "warn")
                            elif not email:
                                callout("⚠️", "Enter an email address.", "warn")
                            else:
                                res, err = api("POST", "/deadlines/remind",
                                               json={"email": email, "contract": name, "deadlines": rows})
                                if err:
                                    callout("❌", err, "error")
                                else:
                                    st.success(f"✅ Sent to {res['sent_to']}")


# ═══════════════════════════════════════════════════════════════
# TAB 5 — Accuracy Test
# ═══════════════════════════════════════════════════════════════
with tab_eval:
    st.markdown("#### 🧪 Accuracy test")
    st.caption(
        "Asks 13 benchmark questions (including one the documents can't answer) "
        "and grades retrieval, answer quality, and citation accuracy."
    )

    ev1, ev2 = st.columns([3, 1])
    with ev2:
        st.markdown("<br>", unsafe_allow_html=True)
        run_eval = st.button("▶ Run test (~60s)", use_container_width=True)

    if run_eval:
        progress_bar = st.progress(0, text="Starting evaluation…")
        with st.spinner("Running 13 benchmark questions…"):
            data, err = api("POST", "/evaluate")
        progress_bar.progress(100, text="Done!")
        st.session_state.eval = (data, err)

    if st.session_state.eval:
        data, err = st.session_state.eval
        if err:
            callout("❌", err, "error")
        else:
            # Metric cards
            ret   = data["retrieval_hit_rate"]
            ans   = data["answer_accuracy"]
            cite  = data["citation_accuracy"]

            st.markdown(
                '<div class="stat-row">'
                + stat_card("Retrieval hit rate",  f"{ret}%",  "correct chunks found", "teal" if ret >= 70 else "gold")
                + stat_card("Answer accuracy",     f"{ans}%",  "correct answers",      "teal" if ans >= 70 else "gold")
                + stat_card("Citation accuracy",   f"{cite}%", "correct source cited", "teal" if cite >= 70 else "gold")
                + '</div>',
                unsafe_allow_html=True,
            )

            # Combined score
            avg = round((ret + ans + cite) / 3)
            st.progress(avg / 100)
            st.caption(f"Combined average: **{avg}%**")

            # Results table
            st.markdown("**Question-level breakdown**")
            table = pd.DataFrame(data["results"])
            for col in ["retrieval_hit", "answer_correct", "citation_ok"]:
                if col in table.columns:
                    table[col] = table[col].map({True: "✅", False: "❌"})
            st.dataframe(table, use_container_width=True, hide_index=True)

