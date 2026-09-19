# RAG and Evidence Design

The Phase-1 RAG implementation is preserved as the grounding foundation for IP-SAKTI.

## Ingestion

`scripts/ingest_documents.py` discovers PDFs, extracts page-aware text, cleans it, produces deterministic overlapping chunks, embeds them with the configured BGE model, and upserts them into the configured Chroma collection. Metadata preserves source filename, resolved local path, one-based page, and deterministic chunk identity.

Document upload and RAG ingestion are separate operations. Uploading preserves the source file and its hash; indexing a stored PDF is explicit. If embedding/indexing fails, the document remains stored and no successful indexing claim is made.

## Retrieval and generation

The runtime uses:

1. `ChromaRetriever` to retrieve the configured top-k chunks;
2. relevance and sufficiency thresholds to determine whether the evidence can support generation;
3. `GroundedAnswerGenerator` and `GeminiLLMService` only when `GEMINI_API_KEY` is configured;
4. citation generation/validation and the trust engine to expose source traceability.

An empty or unavailable collection, insufficient relevance, missing Gemini configuration, invalid citations, or a provider error yields an unavailable/insufficient-evidence outcome rather than a definitive response.

## Trust semantics

Trust and evidence scores summarize retrieval relevance, claim support, citation integrity, contradiction signals, hallucination risk, and traceability within the evidence available to the current request. They do not represent legal correctness, probability of patent grant, freedom to operate, regulatory approval, or TK clearance.

Mock evidence always receives zero real-world trust. Contradictory evidence forces review and suppresses a synthesized conclusion. Source snippets and page locators remain visible so a user can inspect the basis of the screening.

## Provider independence

RAG requires Gemini for generation, but the FastAPI application does not. Missing credentials leave `/api/chat` safely unavailable while health, status, local documents/reports, deterministic orchestration, and configured independent providers can still operate. Prior-art search is built independently so EPO OPS does not depend on a Gemini key.

## Evaluation

The automated suite uses injected retrievers, LLM clients, and HTTP transports. It checks evidence refusal, citations, ingestion/retrieval behavior, mock separation, provider failures, and the original Phase-1/2A/2B regression suite without requiring network access.
