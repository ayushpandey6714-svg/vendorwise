"""Presentation only. Every extraction, comparison and answer comes from FastAPI."""
import os
from pathlib import Path

import httpx
import streamlit as st
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env", override=False)
BASE = os.getenv("VENDORWISE_API_URL", "http://127.0.0.1:8000").rstrip("/")
st.set_page_config(page_title="VendorWise", page_icon=":material/fact_check:", layout="wide")
for key, default in {"analysis_id": None, "quotes": [], "comparison": None,
                     "what_if": None, "answers": [], "report": None}.items():
    st.session_state.setdefault(key, default)


def api(method, path, **kwargs):
    try:
        response = httpx.request(method, BASE + path, timeout=600, **kwargs)
        if response.is_error:
            try:
                detail = response.json().get("detail", response.text)
            except ValueError:
                detail = response.text
            st.error(f"Backend returned {response.status_code}: {detail}")
            return None
        return response.text if "text/markdown" in response.headers.get("content-type", "") else response.json()
    except httpx.RequestError:
        st.error("Cannot reach the backend. Start FastAPI on 127.0.0.1:8000 and retry.")
        return None


def display_comparison(result):
    st.info(result["explanation"])
    rows = []
    for offer in result["offers"]:
        audit = offer["audit"]
        rows.append({"Vendor": offer["vendor"],
                     **{c["requirement"].title(): c["status"] for c in offer["checks"]},
                     "Stated INR": audit["stated_total"], "Calculated INR": audit["calculated_total"],
                     "Verified comparable": audit["comparable"], "Eligible": offer["eligible"]})
    st.dataframe(rows, hide_index=True, alt="Vendor requirement results and stated versus calculated costs")
    for offer in result["offers"]:
        with st.expander(f"{offer['vendor']} — reasons and pricing audit"):
            for check in offer["checks"]:
                st.write(f"**{check['requirement'].title()} · {check['status']}** — {check['reason']}")
                for e in check["evidence"]:
                    st.caption(f"{e['filename']} · PDF page {e['page']}")
                    st.text(e["text"])
            audit = offer["audit"]
            if not audit["complete"]:
                st.warning("Cannot independently verify the total.")
            for issue in audit["issues"]:
                st.warning(issue)
            for step in audit["steps"]:
                st.text(step)
            st.caption("Calculated results use the extracted source inputs. Tolerance: INR 0.01. Interpretations still require review.")
            with st.expander("Calculation source inputs"):
                for e in audit["source_inputs"]:
                    st.caption(f"{e['filename']} · PDF page {e['page']}")
                    st.text(e["text"])


st.title("VendorWise")
st.caption("AI quotation auditor and comparison assistant · Laptops · INR · Up to 3 PDFs")
health = api("GET", "/health")
public_demo = bool(health and health.get("public_demo"))
if health:
    with st.sidebar:
        st.subheader("Runtime")
        st.write(f"Mode: **{health['mode']}**")
        st.write(f"Local embeddings: **{health['embedding_backend']}**")
        st.caption("Public sample demo. Analyses are temporary; no personal documents." if public_demo else
                   "Single-user local app. Session IDs are not authentication.")
        if st.session_state.analysis_id:
            st.code(st.session_state.analysis_id, language=None)
        if st.button("New analysis", key="reset"):
            for key in ("analysis_id", "quotes", "comparison", "what_if", "answers", "report"):
                del st.session_state[key]
            st.rerun()
    if health["mode"] == "fixture":
        st.warning("SYNTHETIC FIXTURE MODE — exact sample data and a deterministic demo assistant. No LLM is called.")
    elif not health["provider_configured"]:
        st.warning("Live mode needs the selected provider's API key in the backend's .env file: OPENROUTER_API_KEY, GEMINI_API_KEY or OPENAI_API_KEY. Never paste keys into this UI.")

with st.container(border=True):
    st.subheader("1. Buyer requirements and quotations")
    st.caption("Delivery is measured in calendar days from the vendor's stated starting event. Quantities must match exactly.")
    with st.form("requirements"):
        col1, col2, col3 = st.columns(3)
        quantity = col1.number_input("Laptop quantity", min_value=1, max_value=10000, value=20)
        budget = col1.number_input("Total budget (INR)", min_value=0, max_value=1000000000, value=1200000, step=10000)
        ram = col2.number_input("Minimum RAM (GB)", min_value=1, max_value=1024, value=16)
        storage = col2.number_input("Minimum storage (GB)", min_value=1, max_value=100000, value=512)
        warranty = col3.number_input("Minimum warranty (months)", min_value=0, max_value=120, value=36)
        delivery = col3.number_input("Maximum delivery (calendar days)", min_value=1, max_value=730, value=10)
        if public_demo:
            uploads = []
            use_samples = True
            st.info("This public demo uses the three synthetic quotations from Vendors A, B and C. Personal uploads are disabled. Change the requirements to try different outcomes.")
        else:
            uploads = st.file_uploader("Text-based quotation PDFs", type=["pdf"], accept_multiple_files=True,
                                       help="Up to three files, 10 MiB and 20 pages each. Scans and multiple offers per PDF are unsupported.")
            use_samples = st.checkbox("Use the three synthetic demo PDFs (A, B and C)", value=False, key="use_samples")
        submitted = st.form_submit_button("Create analysis and extract", type="primary", disabled=not health, key="create_analysis")
    if submitted:
        if not use_samples and not 1 <= len(uploads) <= 3:
            st.error("Choose one to three PDFs, or select the synthetic demo.")
        else:
            req = {"quantity": quantity, "budget": str(budget), "min_ram_gb": ram,
                   "min_storage_gb": storage, "min_warranty_months": warranty,
                   "max_delivery_days": delivery}
            with st.spinner("Creating analysis, extracting evidence and indexing page passages…"):
                created = api("POST", "/analyses", json=req)
                if created:
                    st.session_state.analysis_id = created["analysis_id"]
                    st.session_state.quotes, st.session_state.answers = [], []
                    st.session_state.comparison = st.session_state.what_if = st.session_state.report = None
                    files = ([(f"vendor_{v}.pdf", (ROOT / "samples" / f"vendor_{v}.pdf").read_bytes()) for v in "abc"]
                             if use_samples else [(f.name, f.getvalue()) for f in uploads])
                    prefix = f"/analyses/{created['analysis_id']}"
                    uploaded = api("POST", prefix + "/documents", files=[("files", (name, data, "application/pdf")) for name, data in files])
                    if uploaded:
                        result = api("POST", prefix + "/extract")
                        if result:
                            st.session_state.quotes = result
                            st.session_state.comparison = api("POST", prefix + "/compare")

if st.session_state.analysis_id and not st.session_state.quotes:
    if st.button("Retry extraction for current analysis"):
        with st.spinner("Extracting current uploaded PDFs…"):
            prefix = f"/analyses/{st.session_state.analysis_id}"
            result = api("POST", prefix + "/extract")
            if result:
                st.session_state.quotes = result
                st.session_state.comparison = api("POST", prefix + "/compare")
                st.rerun()

if st.session_state.quotes:
    prefix = f"/analyses/{st.session_state.analysis_id}"
    compare_tab, evidence_tab, whatif_tab, qa_tab = st.tabs(["Comparison", "Extracted data & evidence", "What if?", "Document Q&A"])
    with compare_tab:
        st.subheader("2. Vendor comparison")
        if st.session_state.comparison:
            display_comparison(st.session_state.comparison)
        if st.button("Prepare Markdown report"):
            st.session_state.report = api("GET", prefix + "/report")
        if st.session_state.report:
            st.download_button("Download audit report", st.session_state.report, "vendorwise-report.md", mime="text/markdown")
    with evidence_tab:
        st.subheader("Inspect every extracted field")
        st.caption("A matching source passage confirms provenance, not that every interpretation is correct. Missing is not zero.")
        for quote in st.session_state.quotes:
            with st.expander(quote["filename"], expanded=True):
                rows = [{"Field": name, "Value": str(fact["value"]), "Status": fact["status"], "Note": fact["note"]}
                        for name, fact in quote.items() if isinstance(fact, dict) and "status" in fact]
                st.dataframe(rows, hide_index=True, alt="Extracted quotation facts, explicit or missing status, and notes")
                fields = [name for name, fact in quote.items() if isinstance(fact, dict) and "status" in fact]
                selected = st.selectbox("Source field", fields, key=f"source_{quote['document_id']}")
                for e in quote[selected]["evidence"]:
                    st.caption(f"{e['filename']} · PDF page {e['page']} · document {e['document_id']}")
                    st.text(e["text"])
                if not quote[selected]["evidence"]:
                    st.info("No supporting source text is available for this field.")
    with whatif_tab:
        st.subheader("Change requirements, reuse the same quotations")
        st.caption("No PDF re-extraction or LLM calls. Offered quantities and prices remain fixed. Applying changes updates the current analysis.")
        current = st.session_state.comparison["requirements"]
        with st.form("whatif"):
            new_budget = st.number_input("Updated budget (INR)", min_value=0, max_value=1000000000,
                                         value=int(float(current["budget"])), step=10000, key="wi_budget")
            new_warranty = st.slider("Updated minimum warranty (months)", 0, 120, current["min_warranty_months"], key="wi_warranty")
            new_delivery = st.slider("Updated maximum delivery (calendar days)", 1, 730, current["max_delivery_days"], key="wi_delivery")
            changed = st.form_submit_button("Apply what-if requirements", key="apply_whatif")
        if changed:
            result = api("POST", prefix + "/what-if", json={"budget": str(new_budget),
                         "min_warranty_months": new_warranty, "max_delivery_days": new_delivery})
            if result:
                st.session_state.what_if = result
                st.session_state.comparison = result["updated"]
                st.session_state.report = None
                st.rerun()
        if st.session_state.what_if:
            result = st.session_state.what_if
            before, after = result["previous"], result["updated"]
            st.dataframe([{"Requirement": key, "Previous": str(val), "Updated": str(after["requirements"][key])}
                          for key, val in before["requirements"].items()], hide_index=True, alt="Previous and updated buyer requirements")
            def names(c, field):
                return ", ".join(o["vendor"] for o in c["offers"] if o["document_id"] in c[field]) or "None"
            st.write(f"Eligible vendors: **{names(before, 'eligible_document_ids')} → {names(after, 'eligible_document_ids')}**")
            st.write(f"Recommendation: **{names(before, 'recommendation_ids')} → {names(after, 'recommendation_ids')}**")
            if result["savings"] is not None:
                st.metric("Previous recommended total minus updated total (INR)", f"{float(result['savings']):,.2f}")
            for change in result["changes"]:
                st.write(change)
    with qa_tab:
        st.subheader("Ask the current analysis")
        st.caption("Try: Does Vendor B include battery replacement? · Which vendor qualifies? · Audit Vendor C's total.")
        with st.form("question"):
            question = st.text_input("Question", max_chars=2000, key="qa_question")
            ids = {q["document_id"]: q["filename"] for q in st.session_state.quotes}
            filters = st.multiselect("Optional document filter", list(ids), format_func=lambda x: ids[x])
            ask_clicked = st.form_submit_button("Ask documents", key="ask_documents")
        if ask_clicked and question.strip():
            with st.spinner("Retrieving evidence and running the assistant…"):
                answer = api("POST", prefix + "/ask", json={"question": question, "document_ids": filters or None})
                if answer:
                    st.session_state.answers.append((question, answer))
        for question, answer in reversed(st.session_state.answers):
            with st.container(border=True):
                st.write(f"**{question}**")
                st.text(answer["answer"])
                if answer["conflict"]:
                    st.warning("Conflicting source evidence: review all cited terms.")
                for citation in answer["citations"]:
                    st.caption(f"{citation['filename']} · PDF page {citation['page']} · {citation['citation_id']}")
                    st.text(citation["text"])
                for calculation in answer["calculations"]:
                    st.json(calculation, expanded=False)
                if answer["comparison"]:
                    display_comparison(answer["comparison"])
                with st.expander("Actual tool activity"):
                    for event in answer["activity"]:
                        st.write(f"**{event['tool']}** — {event['outcome']}")
                    st.caption(f"Backend latency: {answer['latency_ms']} ms · Mode: {answer['mode']}")
