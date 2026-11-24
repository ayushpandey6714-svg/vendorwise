# Validation actually performed

**Completed local live workflow (24 November 2026):** The user successfully extracted all three synthetic quotations in live mode in analysis `88791277-b63b-4be0-8250-b15e0e9d6210`. A separate verification reused those saved live extractions, rebuilt the local TF-IDF index and confirmed Vendor C at 10 days, Vendor B at 14 days with INR 30,000 savings, and the report attachment endpoint. A new live OpenRouter Q&A request answered that Vendor B covers battery manufacturing defects for 12 months; its validated citation points to page 2 and directly supports that answer. The answer and source were manually reviewed. See `evaluation/results/live-final-checks.json` and `live-sample-report.md`. This verifies the sample workflow, not general accuracy on arbitrary customer PDFs. Docker/WSL are absent locally. The added `.github/workflows/docker-check.yml` builds the actual Linux image and exercises its public fixture workflow when run on GitHub; **that remote job has not yet run**, and no public URL has been deployed.

**First live OpenRouter check (24 November 2026):** The locally supplied key authenticated successfully. Two `openrouter/free` runs returned invalid extraction fields. A specific free NVIDIA model returned an unsupported-document decision for a supported sample. With `baidu/ernie-5.5-flash-preview:free`, `vendor_a.pdf` passed structured and provenance validation, but `vendor_b.pdf` hit HTTP 429 from the provider. The full three-vendor comparison, live cited Q&A and what-if flow therefore **did not pass**. Requests stopped after the rate limit; no paid model was used. See `evaluation/results/openrouter-live.json` and the captured history (partial history only). The extraction prompt now explicitly states adjustment and Fact invariants, and schema-validation failures receive at most one fresh extraction attempt before failing. A regression suite including bounded repair passed **64 tests in 11.19 seconds**; type checking passed. This is partial live integration evidence, not an extraction-accuracy score. Docker remains unavailable and public deployment is not verified.

**OpenRouter follow-up (24 November 2026):** The expanded suite passed **62 tests in 16.12 seconds**, and type checking passed. New mocked contracts verify provider key/endpoint isolation, structured extraction, bounded comparison tool calls, required routing parameters and failures for authentication, quota and provider unavailability. See `evaluation/results/pytest-openrouter.xml`. No actual OpenRouter request has been made; a locally configured key and live validation remain required. Docker build and public deployment remain unverified.

**Gemini follow-up (23 November 2026):** Google Chat Completions support was added alongside OpenAI Responses. The expanded suite passed **57 tests in 12.43 seconds**, and type checking passed. The 11 new tests cover provider configuration/isolation and mocked HTTP contracts for structured extraction, bounded tool execution, thought-signature preservation, invented citations, forbidden tools, excess calls, quota exhaustion, invalid JSON, empty responses and refusals. See `evaluation/results/pytest-gemini.xml`. A running FastAPI + Streamlit agent-API check verified the missing-Gemini-key guidance with no application warnings or tracebacks; see `evaluation/results/gemini-ui-smoke.json`. Test processes were stopped afterward. **No live Gemini requests were made:** credentials, account quota, model acceptance of this extraction schema, and real extraction/answer quality remain unverified. Public Docker mode remains sample-only fixture mode.

**Deployment-preparation follow-up:** Docker/Compose/Render files and a restricted public sample-demo mode were subsequently added. The expanded suite passed **46 tests**, including public-demo UI and backend checks; type checking and YAML parsing passed. See `evaluation/results/pytest-deployment.xml`. Docker CLI was unavailable, so no Linux image build or cloud deployment is claimed. The original 40-test baseline and synthetic evaluation results below remain historical results, not a rerun of live model quality.

Date: **23 November 2026**. Environment: **Windows, Python 3.14.7**. Exact package versions and corpus hashes are in `evaluation/results/environment.json`; the complete environment is pinned in `requirements-lock.txt`.

## Automated checks

| Check | Observed result |
|---|---|
| `python -m pytest -q --junitxml=evaluation/results/pytest.xml` | **40 passed in 5.07 seconds** on the final full run |
| `ty check streamlit_app.py vendorwise evaluation scripts --output-format concise` | **All checks passed** |
| `python -m pip check` | **No broken requirements found** |
| Python compilation | Passed for backend, frontend, scripts and tests |
| `python -m scripts.smoke_ui` | Passed using a real localhost FastAPI process and headless Streamlit AppTest |
| Running Streamlit agent API | Passed creation/extraction, comparison, delivery what-if and cited Q&A over localhost HTTP |
| Synthetic PDFs | Nine two-page PDFs generated; both layouts and all 18 pages rendered and visually inspected |
| Generator reproducibility | Regenerating all nine PDFs produced byte-identical SHA256 hashes |

The test suite includes **two explicitly marked mocked-provider tests**: OpenAI SDK structured-output serialization/parsing over a mocked HTTP transport, and bounded assistant-loop/tool execution. The other 38 tests cover deterministic rules, validation and local fixture integrations. None of these is a live LLM quality measurement.

The UI checks verified: upload three samples → extract/index → recommend C → change delivery to 14 days → recommend B and show INR 30,000 savings → retrieve Vendor B battery terms from actual PDF page 2 → generate a Markdown report. `ui-smoke.json` records the AppTest run; `running-ui-smoke.json` records the running-server check. Neither is a visual browser test.

## Synthetic evaluation results

Both embedding backends used real local Qdrant indexes. FastEmbed downloaded and executed **BAAI/bge-small-en-v1.5** locally. Extraction and answer generation were explicitly in **fixture mode**.

| Run | Cases passed | Median complete-case latency |
|---|---:|---:|
| Development, TF-IDF | 20 / 20 | 158.755 ms |
| Held-out, TF-IDF | 6 / 6 | 183.405 ms |
| Development, local BGE | 20 / 20 | 399.375 ms |
| Held-out, local BGE | 6 / 6 | 659.135 ms |

These latencies include analysis creation, PDF processing, fixture extraction, index construction and the case operation. They exclude first-run model download in the final recorded runs. They are small-corpus measurements on this machine, not a service-level guarantee or a pure Q&A benchmark.

The development split passed 24/24 fixture field assertions, 15/15 calculation assertions, 4/4 recommendation cases, 6/6 aggregate offer-status checks, 7/7 expected retrieval passages, 2/2 answerability checks, 1/1 returned citation checks, 1/1 supporting-passage proxy and 2/2 what-if assertions for each embedding backend.

The held-out split passed 3/3 fixture field assertions, 3/3 calculation assertions, 2/2 recommendation cases, 5/5 aggregate offer-status checks, 1/1 expected retrieval passages and 1/1 unanswerable-question check for each backend. No answer citations were returned in its unanswerable case, so held-out citation validity has no denominator; it is not claimed as 100%.

The six held-out cases were first run after the development checks passed. No business-rule, retrieval or prompt changes were made in response to their results. They are synthetic variants and a modest regression check, not evidence of real-world generalization. Raw per-case results and denominators are in the four JSON files in `evaluation/results/`.

## Failures found and corrected during development

- A fixture question router initially matched “battery” inside a synthetic sample reference identifier. Word-boundary matching corrected this false evidence-presence result.
- The development scorer initially treated PDF line wrapping as a missing expected passage. Expected-text checks now normalize whitespace; exact citation-text/source validation remains unchanged.
- The first model download attempted an auxiliary Hugging Face cache outside the workspace. Auxiliary caches were redirected into project storage; the subsequent model download and semantic runs succeeded.
- The sandbox's redirected temporary directory rejected an atomic file replacement in the evaluation runner. Evaluation/smoke scratch directories now reside under the project's ignored `work/` folder. Atomic application-state replacement was preserved.
- Type checking identified nullable/un-narrowed values; explicit narrowing and JSON annotations resolved them.

The final running Streamlit server emitted no application warnings or tracebacks during the checked interactions. AppTest emitted its standard bare-mode `missing ScriptRunContext` warning. Hugging Face reported that Windows symlinks were unavailable and that downloads were unauthenticated; the model still downloaded and ran successfully. No administrator mode or external credentials were needed for embeddings.

## Live integrations and unmeasured quality

- **Exercised:** real local PDF parsing, FastEmbed/ONNX semantic inference, local Qdrant storage/retrieval, FastAPI HTTP, Streamlit runtime, fixture tool execution and OpenAI SDK contract parsing with a mocked HTTP response.
- **Not exercised:** live OpenAI extraction, live model-selected tool calls and live generated answers. `OPENAI_API_KEY` was not configured. No fallback model responses were substituted in live mode.
- **Not measured:** live extraction accuracy, human-reviewed semantic answer support, API cost, real-customer outcomes, adversarial prompt-injection robustness and public multi-user behavior.

See `evaluation/README.md` for the scoring rubric and opt-in live evaluation command. This report deliberately does not convert fixture correctness into an LLM accuracy claim.
