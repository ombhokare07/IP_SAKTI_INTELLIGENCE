from datetime import datetime, timezone

from intelligence.regulations.regulation_engine import RegulationEngine
from intelligence.regulations.version_tracker import VersionTracker
from intelligence.traditional_knowledge.tk_engine import TraditionalKnowledgeEngine
from rag.citations.citation_generator import build_citations
from services.database_service import DatabaseService
from services.report_service import ReportService


def test_tk_without_search_is_not_reported_as_zero_matches():
    result = TraditionalKnowledgeEngine().assess({"description": "turmeric wound use"})

    assert result["search_performed"] is False
    assert result["matches_evaluated"] is False
    assert result["matches"] is None
    assert result["match_count"] is None
    assert result["risk"]["level"] == "insufficient_evidence"
    assert result["clearance_status"] == "not_assessed"
    assert result["clearance_summary"] == "TK clearance: Not assessed"
    assert result["risk"]["conclusion"] == "Cannot be determined — authorized TK search not performed."


def test_unauthorized_real_tk_provider_is_not_called():
    class UnauthorizedProvider:
        mode = "local"
        authorized = False

        def search(self, _query):
            raise AssertionError("An unauthorized TK source must not be searched.")

    result = TraditionalKnowledgeEngine(UnauthorizedProvider()).assess({"description": "neem use"})

    assert result["status"] == "tk_search_not_authorized"
    assert result["search_performed"] is False
    assert result["matches"] is None


def test_unconfigured_regulation_source_uses_missing_evidence_wording(tmp_path):
    engine = RegulationEngine(VersionTracker(DatabaseService(tmp_path / "runtime.sqlite3")))
    result = engine.compare({"jurisdictions": ["IN"], "product_category": "herbal_product"})

    joined = " ".join(result["limitations"])
    assert "No configured regulatory evidence source was available" in joined
    assert "No requirement was found in this corpus" not in joined


def test_report_separates_task_and_source_mode_and_keeps_snapshot(tmp_path):
    assessment = {"status": "grounded", "mode": "local", "citations": [{"id": "source-1"}], "limitations": ["Original limitation."]}
    report = ReportService(DatabaseService(tmp_path / "runtime.sqlite3")).create("Saved answer", "ask", assessment)

    assert report["task"] == "Ask IP-SAKTI"
    assert report["source_mode"] == "grounded"
    assert report["assessment"] == assessment
    created = datetime.fromisoformat(report["created_at"])
    assert created.tzinfo is not None
    assert created.utcoffset() == timezone.utc.utcoffset(created)


def test_public_citations_do_not_disclose_absolute_local_paths():
    citation = build_citations([{
        "chunk_id": "chunk-1",
        "source": r"D:\\private\\authority.pdf",
        "path": r"D:\\private\\authority.pdf",
        "page": 1,
        "text": "Evidence text.",
    }])[0]

    assert citation["source"] == "authority.pdf"
    assert "path" not in citation
    assert "D:\\" not in str(citation)
