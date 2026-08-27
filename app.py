import warnings
warnings.filterwarnings("ignore")

import json, sqlite3
import yaml
import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(page_title="AEO Citation Tracker", layout="wide")

cfg = yaml.safe_load(open("config.yaml"))
con = sqlite3.connect("data/tracker.db", check_same_thread=False)

BRANDS = [(b["key"], b["label"]) for b in cfg["brands"]]
QUERIES = {q["id"]: q["text"] for q in cfg["queries"]}
US = "simplismart"

st.title("AEO Citation Tracker")
st.caption("Are we cited by AI answer engines for the queries our buyers ask?")

providers = [p[0] for p in con.execute(
    "SELECT DISTINCT provider FROM responses ORDER BY provider").fetchall()]
prov = st.radio("Engine", providers, horizontal=True)

runs = [r[0] for r in con.execute(
    "SELECT DISTINCT run_id FROM responses WHERE provider=? ORDER BY run_id DESC",
    (prov,)).fetchall()]
run = st.selectbox("Run", runs)

ok = [r[0] for r in con.execute(
    "SELECT query_id FROM responses WHERE run_id=? AND provider=? AND error IS NULL",
    (run, prov)).fetchall()]

if not ok:
    st.error(f"No queries succeeded in this run — every call to {prov} failed. "
             "Nothing below is meaningful. Pick another run.")
    st.stop()

if len(ok) < len(QUERIES):
    st.warning(f"{len(ok)} of {len(QUERIES)} queries succeeded. "
               "Failed queries show as unknown, not as absent.")

# ---------- headline ----------
st.subheader("Share of voice")
cols = st.columns(len(BRANDS))
counts = {}
for i, (bkey, label) in enumerate(BRANDS):
    n = con.execute(
        "SELECT COUNT(*) FROM mentions WHERE run_id=? AND provider=? AND brand=? "
        "AND mentioned=1 AND query_id IN (%s)" % ",".join("?" * len(ok)),
        (run, prov, bkey, *ok)).fetchone()[0]
    counts[label] = n
    cols[i].metric(label, f"{n}/{len(ok)}",
                   delta="us" if bkey == US else None,
                   delta_color="off")

# ---------- matrix ----------
st.subheader("Which queries mention whom")
rows = []
for qid, qtext in QUERIES.items():
    row = {"Query": f"{qid}  {qtext[:52]}"}
    for bkey, label in BRANDS:
        if qid not in ok:
            row[label] = "?"
            continue
        hit = con.execute(
            "SELECT mentioned FROM mentions WHERE run_id=? AND query_id=? "
            "AND provider=? AND brand=?", (run, qid, prov, bkey)).fetchone()
        row[label] = "YES" if hit and hit[0] else "—"
    rows.append(row)

def paint(v):
    if v == "YES":
        return "background-color:#1b5e20;color:white;font-weight:600"
    if v == "?":
        return "background-color:#5d4037;color:#ffcc80"
    return "color:#666"

st.dataframe(
    pd.DataFrame(rows).style.map(paint, subset=[l for _, l in BRANDS]),
    width='stretch', hide_index=True,
)
st.caption("YES = mentioned · — = not mentioned · ? = query failed, unknown")

# ---------- trend ----------
st.subheader("Change over time")
trend = []
for r in runs:
    rok = [x[0] for x in con.execute(
        "SELECT query_id FROM responses WHERE run_id=? AND provider=? AND error IS NULL",
        (r, prov)).fetchall()]
    if not rok:
        continue
    for bkey, label in BRANDS:
        n = con.execute(
            "SELECT COUNT(*) FROM mentions WHERE run_id=? AND provider=? AND brand=? "
            "AND mentioned=1 AND query_id IN (%s)" % ",".join("?" * len(rok)),
            (r, prov, bkey, *rok)).fetchone()[0]
        trend.append({"Run": r, "Brand": label,
                      "Share %": round(100 * n / len(rok))})

if trend:
    df = pd.DataFrame(trend).sort_values("Run")
    fig = px.line(df, x="Run", y="Share %", color="Brand", markers=True)
    fig.update_layout(height=380, yaxis_range=[-5, 105])
    st.plotly_chart(fig, width='stretch')
    st.caption("Runs where every query failed are omitted rather than plotted as zero.")

# ---------- raw ----------
st.subheader("Raw responses")
for qid, qtext in QUERIES.items():
    r = con.execute(
        "SELECT response_text, citations, error, latency_ms FROM responses "
        "WHERE run_id=? AND query_id=? AND provider=?", (run, qid, prov)).fetchone()
    if not r:
        continue
    text, cites, err, ms = r
    label = f"{qid} — {qtext}"
    with st.expander(f"{'FAILED  ' if err else ''}{label}"):
        if err:
            st.error(err)
        else:
            st.caption(f"{ms} ms")
            st.markdown(text)
            urls = json.loads(cites or "[]")
            if urls:
                st.caption(f"{len(urls)} sources")
                for u in urls:
                    st.write(f"- {u}")
