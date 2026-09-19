# Design Contributions

The project combines several screening workflows around one evidence contract. Its value lies in traceable integration and failure semantics rather than a claim of automated legal judgment.

- **Evidence-first outcomes:** missing or weak evidence is a first-class result. Definitive language is suppressed instead of inferred from a score.
- **Provider honesty:** `live`, `local`, `mock`, and `unconfigured` modes flow through evidence, trust, UI, reports, and status APIs. Configuration is separated from verified success.
- **Patent/TK/regulation cross-screening:** invention features, ingredients, therapeutic uses, and processes can be examined across prior-art and traditional-knowledge workflows without conflating their legal standards.
- **Deterministic orchestration:** explicit or inspectable keyword routing makes agent selection reproducible; post-routing citation, evidence, and contradiction agents enforce common safety rules.
- **Version-aware compliance:** jurisdiction requirements, version snapshots, diffs, impact analysis, missing-field detection, and journeys share the same evidence limitations.
- **Citation-safe multilingual design:** language detection and AYUSH normalization work offline, while translation masks URLs, numbers, and citation tokens before calling a gateway.
- **Graceful optional integrations:** Gemini, EPO OPS, TK/regulation gateways, translation, and voice services can all be absent without preventing the local API from starting.
- **Immutable reporting snapshots:** reports can be created from stored assessment results so later provider changes do not silently rewrite the original screening basis.

These mechanisms improve auditability and workflow safety. They do not validate a patent claim, confer freedom to operate, establish TK clearance, or certify regulatory compliance.
