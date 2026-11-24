"""Run via python -m evaluation.run --split dev --mode fixture --embeddings tfidf."""
import argparse
import json
import statistics
import tempfile
import time
from collections import defaultdict
from dataclasses import replace
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from vendorwise.config import ROOT, Settings
from vendorwise.logic import audit_quote
from vendorwise.pdf import normalized
from vendorwise.retrieval import VectorIndex
from vendorwise.schemas import AskRequest, Requirements, WhatIfRequest
from vendorwise.service import Service

DEFAULT = dict(quantity=20, budget="1200000", min_ram_gb=16, min_storage_gb=512,
               min_warranty_months=36, max_delivery_days=10)


def equal(actual, expected):
    if actual is None or expected is None:
        return actual is expected
    if isinstance(actual, bool) or isinstance(expected, bool):
        return actual == expected
    try:
        return Decimal(str(actual)) == Decimal(str(expected))
    except (InvalidOperation, ValueError):
        return actual == expected


def run(split, mode, embeddings, output):
    cases = json.loads((ROOT / "evaluation" / f"{split}.json").read_text(encoding="utf-8"))
    metrics = defaultdict(lambda: {"passed": 0, "total": 0})
    records: list[dict[str, Any]] = []
    work = ROOT / "work"
    work.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="evaluation-", dir=work) as temp:
        settings = replace(Settings.from_env(), data_dir=Path(temp), mode=mode, embedding_backend=embeddings)
        if mode == "live" and (not settings.api_key or settings.api_key.startswith("your-")):
            raise SystemExit("Live evaluation requires OPENAI_API_KEY in the local environment/.env; no fallback.")
        service = Service(settings)
        # Share only the local model cache; document indexes remain isolated.
        cache = ROOT / "data" / "model_cache"
        service.index = lambda a: VectorIndex(
            service.repo.folder(a.analysis_id) / "index", embeddings, settings.embedding_model, cache)
        for case in cases:
            start = time.perf_counter()
            record: dict[str, Any] = {"id":case["id"], "kind":case["kind"], "checks":[], "error":None}
            def score(metric, passed):
                metrics[metric]["total"] += 1
                metrics[metric]["passed"] += int(bool(passed))
                record["checks"].append({"metric":metric, "passed":bool(passed)})
            try:
                req = Requirements(**{**DEFAULT, **case.get("requirements", {})})
                a = service.repo.create(req, mode, embeddings)
                service.upload(a.analysis_id, [(f"{name}.pdf", (ROOT / "samples" / f"{name}.pdf").read_bytes()) for name in case["samples"]])
                quotes = service.extract(a.analysis_id)
                a = service.ready(a.analysis_id)
                expected = case["expected"]
                if case["kind"] == "extraction":
                    for name, target in expected.items():
                        field, *nested = name.split(".")
                        actual = getattr(quotes[0], field).value
                        if nested and actual is not None:
                            actual = getattr(actual, nested[0])
                        score("extraction_fields" if mode == "live" else "fixture_field_consistency", equal(actual, target))
                elif case["kind"] == "calculation":
                    audit = audit_quote(quotes[0])
                    for name, target in expected.items():
                        score("calculation_assertions", equal(getattr(audit, name), target))
                elif case["kind"] == "comparison":
                    comparison = service.compare(a.analysis_id)
                    winners = [o.vendor for o in comparison.offers if o.document_id in comparison.recommendation_ids]
                    score("recommendation_cases", winners == expected["winners"])
                    for offer, status in zip(comparison.offers, expected["statuses"]):
                        score("requirement_offer_status", offer.requirements_status == status)
                elif case["kind"] == "retrieval":
                    chunks = service.index(a).search(a, case["question"])
                    filenames = expected.get("all_filenames", [expected.get("filename")])
                    for filename in filenames:
                        score("retrieval_expected_passages", any(c.filename == filename and c.page == expected["page"] and normalized(expected["contains"]).lower() in normalized(c.text).lower() for c in chunks))
                    record["retrieved_ids"] = [c.citation_id for c in chunks]
                elif case["kind"] == "answer":
                    answer = service.ask(a.analysis_id, AskRequest(question=case["question"]))
                    score("answerability_cases", answer.evidence_absent == expected["evidence_absent"])
                    # Mechanical citation validity is scored per returned citation, not per answer.
                    for c in answer.citations:
                        doc = next(d for d in a.documents if d.document_id == c.document_id)
                        score("citation_validity", c.text in doc.pages[c.page - 1] and c.filename == doc.filename)
                    if "support_contains" in expected:
                        score("support_passage_proxy", any(normalized(expected["support_contains"]) in normalized(c.text) for c in answer.citations))
                    record["answer"] = answer.model_dump(mode="json")
                    record["human_answer_support"] = None
                elif case["kind"] == "whatif":
                    result = service.what_if(a.analysis_id, WhatIfRequest(**case["change"]))
                    winners = [o.vendor for o in result.updated.offers if o.document_id in result.updated.recommendation_ids]
                    score("whatif_assertions", winners == expected["winners"])
                    score("whatif_assertions", equal(result.savings, expected["savings"]))
            except Exception as exc:
                record["error"] = f"{type(exc).__name__}: {exc}"
            record["latency_ms"] = round((time.perf_counter() - start) * 1000, 2)
            record["passed"] = record["error"] is None and bool(record["checks"]) and all(c["passed"] for c in record["checks"])
            records.append(record)
            print(f"{case['id']} {case['kind']}: {'PASS' if record['passed'] else 'FAIL'} ({record['latency_ms']} ms)", flush=True)
    latency = [r["latency_ms"] for r in records]
    result = {"timestamp_utc": datetime.now(timezone.utc).isoformat(), "split":split, "mode":mode,
              "embeddings":embeddings, "cases_passed":sum(r["passed"] for r in records), "cases_total":len(cases),
              "metrics":dict(metrics), "median_case_latency_ms":statistics.median(latency),
              "human_answer_support":"Not scored; review answers against cited passages manually.",
              "live_model_quality":"Not measured" if mode == "fixture" else "See actual case results; synthetic corpus only.",
              "records":records}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k != "records"}, indent=2))
    return 0 if result["cases_passed"] == len(cases) else 1


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--split", choices=["dev","heldout"], default="dev")
    p.add_argument("--mode", choices=["fixture","live"], default="fixture")
    p.add_argument("--embeddings", choices=["tfidf","fastembed"], default="tfidf")
    p.add_argument("--output", type=Path)
    args = p.parse_args()
    raise SystemExit(run(args.split, args.mode, args.embeddings,
        args.output or ROOT / "evaluation" / "results" / f"{args.split}-{args.mode}-{args.embeddings}.json"))
