# Ten implementation-specific interview questions

## 1. Why use both an LLM and deterministic Python?

The LLM interprets quotation language into a schema. Python checks rules and arithmetic. `logic.audit_quote` uses Decimal, explicit bases and documented rounding; the model never determines totals or eligibility through free-form reasoning. This separation lets me test the most consequential decisions without calling a model.

## 2. What makes the Q&A real RAG?

`retrieval.chunk_documents` preserves PDF pages, FastEmbed creates local semantic embeddings, and a per-analysis Qdrant index retrieves relevant chunks. The live assistant's search tool supplies those chunks to answer generation. Whole-document prompting happens during extraction, which I do not call RAG. The optional TF-IDF backend is a lexical baseline, not a semantic embedding model.

## 3. How do you know a citation is real?

During extraction I check the cited page exists and supporting text occurs there after whitespace normalization. During Q&A I accept only citation IDs from chunks retrieved in that request, then attach the stored filename/page/passage. These checks prove provenance existence, not full semantic support. A model could still misinterpret a real clause.

## 4. How do you prevent missing shipping from becoming zero?

Each field has a status and nullable value. Only `explicit` fields are usable. `Fact` rejects a missing field containing a value. An explicit zero charge has supporting evidence, while missing shipping blocks a complete total and produces a request for clarification.

## 5. How are tax inclusions and discounts represented?

`Adjustment` accepts exactly one fixed amount or percentage plus an explicit base and an add/included treatment. The audit calculates subtotal, subtracts discount, adds separate shipping/other charges, then applies tax to the stated supported base. Included components are not added again. Ambiguous bases, contradictory inclusions or unsupported tax-inclusive discounts are conservatively unverified.

## 6. How is a recommendation selected?

Each offer receives PASS, FAIL or UNKNOWN for quantity, RAM, storage, warranty, delivery and budget. A verified comparable price is a separate requirement for eligibility. The lowest eligible total wins, with all exact ties returned. Missing facts or unresolved prices that could affect the outcome make the recommendation provisional. There is no arbitrary weighted score.

## 7. Why is what-if analysis reproducible?

It reuses the same validated `Quote` objects and calls `compare` with old and updated requirements. The request schema permits only budget, warranty and delivery changes. There is no LLM call and no repricing. The fixed sample changes from C to B when delivery changes from ten to fourteen days, with Decimal savings of INR 30,000.

## 8. What prevents the assistant from inventing a low price or accessing another session?

The tool accepts a document UUID, not a price, and resolves it from the server-bound analysis. Extra arguments and unknown IDs are rejected. Separate UUID directories and indexes isolate analyses. The assistant has no analysis-switching tool, file-path argument, email capability or purchase action. This isolation is not authentication, so I bind the single-user backend to loopback.

## 9. How did you evaluate the project honestly?

I keep deterministic arithmetic/rule tests, mocked provider-contract tests and live model checks separate. The 26-case synthetic evaluation has 20 development and six held-out cases. It reports denominators for field assertions, expected retrieval passages, citations, answerability and rules. Fixture extraction consistency is not LLM extraction accuracy. Human semantic answer support remains unscored unless explicitly reviewed. I cite the actual validation report rather than inventing accuracy, latency or cost.

## 10. What are its biggest limitations and next experiment?

It supports one English text-based INR laptop offer per PDF, at most three documents. It cannot OCR scans or resolve all complex contractual terms. Top-k retrieval can miss conflicts, and source-matching cannot prove interpretation. I would first gather diverse permissioned quotations with independently labelled fields and clauses, then measure live extraction and answer support on unseen cases before adding complexity.

Practice exercise: trace a single “Vendor B delivery” value from the generated PDF, through Fact evidence and provenance validation, into its FAIL/PASS change and finally the report. Explain each module without reading this guide verbatim.
