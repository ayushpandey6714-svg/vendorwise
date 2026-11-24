# Evaluation protocol

`dev.json` contains 20 development cases. `heldout.json` contains six separate cases reserved for final evaluation after the code and development checks stabilize. They are synthetic variants, not an independent real-world benchmark. Fixture labels are intentionally supplied facts, so fixture field consistency cannot establish generalization or LLM extraction accuracy.

Do not tune against the held-out file. If a held-out failure leads to a code/prompt change, document that it is now a regression set and create a new unseen subset for a future generalization claim. In this delivery the held-out run is performed after the development checks. Consult the validation report for what actually ran.

## Commands

From the project root:

```powershell
.\.venv\Scripts\python -m evaluation.run --split dev --mode fixture --embeddings tfidf
.\.venv\Scripts\python -m evaluation.run --split heldout --mode fixture --embeddings tfidf
.\.venv\Scripts\python -m evaluation.run --split dev --mode fixture --embeddings fastembed
# Explicit external API calls; may incur charges:
.\.venv\Scripts\python -m evaluation.run --split dev --mode live --embeddings fastembed
```

Each run writes a JSON result with individual checks, failures, mode, backend and latency. Any failed case exits nonzero. Errors are retained as failed cases; do not omit them from the case denominator. Assertion-level denominators describe checks reached, so read them alongside the all-case pass count when a setup/provider error occurred.

## Scoring and denominators

| Metric | Numerator / denominator |
|---|---|
| Case pass rate | Cases where all scored checks pass and no exception occurs / every case in the selected split |
| Extraction fields | Exact normalized values matching reference / explicitly enumerated field expectations; numerical strings compare as Decimal. Only live mode uses this label. |
| Fixture field consistency | Same matching test for manifest fixtures; a plumbing/regression check, not extraction quality |
| Calculation assertions | Matching total, completeness, comparability or discrepancy / listed expected calculation properties |
| Requirement offer status | Correct aggregate PASS/FAIL/UNKNOWN / expected offer statuses; unit tests additionally check individual criteria |
| Recommendation cases | Exact expected winner names / comparison cases |
| Retrieval expected passages | Expected filename + actual page + whitespace-normalized target text retrieved / listed expected passages; a multi-vendor case contributes one per expected vendor |
| Citation validity | Returned citations pointing to exact text in the stated source page and filename / returned citations. Empty citation lists contribute no denominator. |
| Answerability | Expected evidence-absent flag / answer cases, including unanswerable questions |
| Support passage proxy | Expected supporting text present in a returned citation / cases with a support-text expectation. **Not semantic entailment accuracy.** |
| What-if assertions | Correct winners and savings / explicitly enumerated expectations |
| Case latency | Wall-clock milliseconds from analysis creation through the case assertion, including extraction/index creation. Median across every attempted case. Cold downloads can dominate; this is not pure Q&A latency. |

The API also returns measured ask-request latency. Costs are not measured. Semantic answer support is **not automatically scored**: the runner stores `human_answer_support: null` for manual review. For a live review, mark each substantive claim supported/unsupported against its cited passages; score supported claims / all reviewed substantive claims, record reviewer and rubric, and include answerability errors. Review conflicting and absent-evidence answers explicitly.

## Three kinds of evidence

1. Pure pytest tests check deterministic rules and validation.
2. Fixture API/UI tests exercise real parsing/indexing/HTTP and known demo facts. Mocked provider tests exercise SDK serialization/structured parsing or bounded-loop contracts. Neither proves live-model quality.
3. Explicit live evaluation calls the actual configured provider, records its outputs and errors, and must be reported separately. No live run is claimed without credentials and recorded results.
