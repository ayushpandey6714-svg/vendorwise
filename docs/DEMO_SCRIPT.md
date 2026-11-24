# VendorWise: 90-second demo

Before starting: run the backend/frontend, choose the synthetic A/B/C demo, and complete extraction. For a repeatable no-credential demonstration use fixture mode and say so. Keep the evidence tab ready. Do not describe fixture output as a live LLM result.

**0–15 seconds — problem and scope**

“VendorWise helps a buyer compare laptop quotations using requirements, price arithmetic and source evidence. This demonstration uses clearly labelled synthetic PDFs. I am running fixture mode, which exercises the backend and retrieval without calling an LLM. The project also contains an OpenAI integration.”

**15–35 seconds — compliance versus cost**

“For 20 laptops, our budget is 12 lakh, warranty must be three years and delivery must be within ten calendar days. Vendor C qualifies. A is cheaper but fails warranty. B fails delivery. An offer is eligible only when all requirements pass and its independently calculated total matches the stated total.”

Point at C's pricing steps and open its warranty evidence: filename and actual PDF page 2.

**35–55 seconds — distinctive what-if**

Change delivery to 14 days and click Apply.

“B now qualifies and is 30,000 rupees cheaper than C. This update uses the same validated facts and pure Python rules. It does not re-extract PDFs, call the LLM or assume a different order quantity gets the same price.”

**55–75 seconds — retrieval and uncertainty**

Ask “Does Vendor B include battery replacement?” Show the retrieved page 2 passage and actual tool activity.

“The search embeds the question, retrieves passages from the current analysis, and attaches validated citations. Fixture mode displays these passages. Live mode generates a concise answer from them. If battery coverage is missing, the system says the documents do not establish it; missing is not an exclusion.”

**75–90 seconds — correctness and honest limits**

“Money calculations use Decimal, not LLM arithmetic. Tests cover incomplete charges, discrepancies, session isolation and citation validation. I keep deterministic tests, fixture evaluations and live-model checks separate. This version supports small text-based INR laptop PDFs; scans and public multi-user deployment are outside scope.”

Optional follow-up: start a separate analysis with `incorrect_total.pdf` and open the INR 500 discrepancy requiring clarification. Download the Markdown evidence report.
