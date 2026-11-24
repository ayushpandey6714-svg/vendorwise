"""Readable Markdown report with deterministic results and inspectable source inputs."""
from .logic import compare


def escape(text):
    return str(text).replace("<", "&lt;").replace(">", "&gt;").replace("|", "\\|").replace("\n", " ")


def markdown_report(a):
    result = compare(a.quotes, a.requirements)
    lines = ["# VendorWise quotation audit", "", f"Analysis: {a.analysis_id}",
             f"Mode: **{a.mode}** | Local embeddings: **{a.embedding_backend}**", "",
             "SYNTHETIC FIXTURE DEMO - not real customer data." if a.mode == "fixture" else
             "Model-extracted evidence requires human review; this is a local portfolio tool.", "",
             "## Buyer requirements", ""]
    lines += [f"- {k}: {v}" for k, v in a.requirements.model_dump().items()]
    lines += ["", "## Recommendation", "", result.explanation, "",
              "Rule: lowest verified comparable total among offers passing every mandatory requirement.",
              "Rounding: INR 0.01, ROUND_HALF_UP per monetary line; discrepancy tolerance INR 0.01."]
    for offer in result.offers:
        q = next(q for q in a.quotes if q.document_id == offer.document_id)
        lines += ["", f"## {escape(offer.vendor)}", "", f"Requirements: {offer.requirements_status}; eligible: {offer.eligible}",
                  f"Vendor-stated total: {offer.audit.stated_total}",
                  f"Calculated total: {offer.audit.calculated_total}; comparable: {offer.audit.comparable}", ""]
        lines += [f"- **{c.requirement}: {c.status}** - {escape(c.reason)}" for c in offer.checks]
        lines += ["", "### Pricing audit", ""] + [f"- {s}" for s in offer.audit.steps]
        if not offer.audit.complete:
            lines.append("Cannot independently verify the total.")
        lines += [f"- {issue}" for issue in offer.audit.issues]
        lines += ["", "### Extracted facts and source evidence", ""]
        for name in type(q).model_fields:
            fact = getattr(q, name)
            if not hasattr(fact, "status"):
                continue
            lines.append(f"- **{name}** ({fact.status}): {escape(fact.value)}")
            for evidence in fact.evidence:
                lines.append(f"  - {escape(evidence.filename)}, PDF page {evidence.page}: {escape(evidence.text)}")
    lines += ["", "Mechanical evidence validation checks page/text existence, not correctness of every interpretation.",
              "Session isolation is not authentication. Review supplier terms before any purchasing decision."]
    return "\n".join(lines) + "\n"
