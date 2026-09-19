# Agent Design

The agent layer is a bounded request orchestrator, not an autonomous legal agent. It cannot obtain credentials, browse arbitrary sources, submit filings, change external systems, or turn missing evidence into a conclusion.

## Routing

`agents.intent_classifier.IntentClassifier` gives an explicit UI intent priority. Otherwise it applies auditable keyword rules, removes overlapping patent/prior-art and regulation/international matches, and selects at most four intents. Report creation and translation are never inferred when doing so could cause an unexpected operation; callers select them explicitly.

Supported routes are `ask`, `patent`, `ayush`, `international`, `prior_art`, `traditional_knowledge`, `compliance`, `regulation`, `translation`, and `report`.

## Task agents

| Agent | Responsibility |
| --- | --- |
| RAG/ask | Use the configured source-grounded RAG pipeline. |
| Patent | Coordinate patentability screening and prior-art limits. |
| AYUSH | Analyze AYUSH/TK-oriented product context without claiming clearance. |
| Prior art | Invoke only the configured provider and preserve its provenance/mode. |
| Traditional knowledge | Run extraction, similarity, and evidence-grounded risk scoring. |
| International regulation | Compare the selected supported jurisdictions. |
| Regulation | Retrieve regulatory requirements and change intelligence. |
| Compliance | Detect requirements/missing fields and calculate screening coverage. |
| Translation | Use dictionary/gateway translation while preserving evidence tokens. |
| Report | Save a screening snapshot and render JSON, Markdown, or HTML. |

## Safety agents

After task agents finish, three deterministic gates always run:

1. The citation agent accepts only citations tied to returned evidence and records rejected references.
2. The evidence agent evaluates traceability, evidence mode, coverage, and screening sufficiency.
3. The contradiction agent identifies conflicting evidence and forces a review status with zero trust.

If screening evidence is insufficient, the orchestrator replaces any definitive synthesis with the no-evidence response. Mock evidence is retained only to demonstrate workflow and receives zero real-world trust. Each response includes the safety limitations and the scoring disclaimer.

## Multilingual handling

Input language is detected or accepted as a caller hint. Terminology is normalized before routing. Translation to English can be used for analysis, and the answer can be translated back, but the original text and translation metadata remain in the trace. URLs, numeric locators, and citation tokens are protected during gateway translation.

## Failure behavior

An individual agent failure becomes `agent_failed`; mixed requests can return `partial`. Provider exception bodies, model output errors, and credentials are not exposed. A failure never becomes evidence of novelty, TK clearance, or legal compliance.
