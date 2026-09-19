import argparse
from collections.abc import Mapping, Sequence
from typing import Any

if __package__ in (None, ""):
    from _bootstrap import configure_console_output, ensure_project_root
else:
    from scripts._bootstrap import configure_console_output, ensure_project_root

ensure_project_root()
configure_console_output()

from backend.main import build_prior_art_engine
from config.settings import settings
from intelligence.patentability.invention_analyzer import InventionAnalyzer
from intelligence.prior_art.providers.mock_provider import MockPriorArtProvider
from intelligence.prior_art.search_engine import PriorArtSearchEngine
from rag.embeddings.embedding_service import BGEEmbeddingService


TEST_INVENTION = {
    "title": "Improved Herbal Wound Healing Formulation",
    "description": (
        "An Ayurvedic herbal formulation containing turmeric, neem and aloe vera "
        "prepared using a modified low-temperature extraction process."
    ),
    "claimed_innovation": "Improved retention of active constituents.",
    "technical_advantage": "Improved stability and compound retention.",
}


def _lines(values: Sequence[Any]) -> str:
    return "\n".join(f"- {value}" for value in values) if values else "NONE"


def format_result(result: Mapping[str, Any]) -> str:
    summary = result.get("search_summary") or {}
    risk = result.get("risk") or {}
    records = result.get("results") or []
    top_lines: list[str] = []
    semantic_lines: list[str] = []
    overlap_lines: list[str] = []
    distinct_lines: list[str] = []
    for record in records[:5]:
        top_lines.append(
            f"#{record.get('rank')} {record.get('publication_number') or 'UNKNOWN'} - "
            f"{record.get('title') or 'Untitled'}"
        )
        similarity = record.get("similarity") or {}
        semantic_lines.append(
            f"#{record.get('rank')}: {similarity.get('overall_similarity', 0)}/100"
        )
        overlap = record.get("feature_overlap") or {}
        matches = overlap.get("matching_features") or []
        overlap_lines.append(f"#{record.get('rank')}: {', '.join(matches) if matches else 'NONE'}")
        if record.get("rank") == 1:
            distinct_lines.extend(overlap.get("apparently_distinct_features") or [])
    provider = summary.get("provider", "NOT CONFIGURED")
    if summary.get("provider_mode") == "mock":
        if "TEST DATA" not in str(provider).upper():
            provider = f"{provider} (TEST DATA / MOCK PROVIDER)"
    return (
        "PRIOR-ART INTELLIGENCE\n\n"
        f"SEARCH PROVIDER\n{provider}\n\n"
        f"SEARCH QUERIES\n{_lines(summary.get('queries_run') or [])}\n\n"
        f"RECORDS FOUND\n{summary.get('records_found', 0)} raw / "
        f"{summary.get('records_analyzed', 0)} analyzed\n\n"
        f"TOP PRIOR ART\n{_lines(top_lines)}\n\n"
        f"SEMANTIC SIMILARITY\n{_lines(semantic_lines)}\n\n"
        f"FEATURE OVERLAP\n{_lines(overlap_lines)}\n\n"
        f"DETECTED PRIOR-ART OVERLAP RISK\n{risk.get('score', 0)}/100 - "
        f"{str(risk.get('level', 'unknown')).replace('_', ' ').upper()}\n\n"
        f"DISTINCT FEATURES\n{_lines(list(dict.fromkeys(distinct_lines)))}\n\n"
        f"LIMITATIONS\n{_lines(result.get('limitations') or [])}"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a Phase-2B prior-art smoke test.")
    parser.add_argument("--provider", choices=("mock", "live"), default="mock")
    parser.add_argument("--limit", type=int, default=10)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    embedder = BGEEmbeddingService(model_name=settings.embedding_model)
    if args.provider == "mock":
        engine = PriorArtSearchEngine(
            MockPriorArtProvider(), embedder, allow_test_provider=True
        )
    else:
        engine = build_prior_art_engine(settings, embedder)
        if engine is None or getattr(engine.provider, "is_test_fixture", False):
            print("Live prior-art provider is not configured.")
            return 0
    invention = InventionAnalyzer().analyze(TEST_INVENTION)
    print(format_result(engine.search(invention, limit=args.limit)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
