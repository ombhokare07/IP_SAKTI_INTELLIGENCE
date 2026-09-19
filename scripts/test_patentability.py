import argparse
from collections.abc import Mapping, Sequence
from typing import Any

import httpx

if __package__ in (None, ""):
    from _bootstrap import configure_console_output, ensure_project_root
else:
    from scripts._bootstrap import configure_console_output, ensure_project_root

ensure_project_root()
configure_console_output()


TEST_INVENTION = {
    "title": "Improved Herbal Wound Healing Formulation",
    "description": (
        "An Ayurvedic herbal formulation containing turmeric, neem and aloe vera "
        "prepared using a modified low-temperature extraction process intended to "
        "preserve heat-sensitive compounds."
    ),
    "claimed_innovation": (
        "The low-temperature extraction process is claimed to improve retention of "
        "active constituents compared with conventional preparation."
    ),
    "technical_advantage": "Improved stability and active-compound retention.",
}


def _lines(values: Sequence[Any]) -> str:
    return "\n".join(f"- {value}" for value in values) if values else "NONE"


def format_result(result: Mapping[str, Any]) -> str:
    invention = result.get("invention") or {}
    assessment = result.get("assessment") or {}
    novelty = assessment.get("novelty") or {}
    inventive = assessment.get("inventive_step") or {}
    trust = result.get("trust") or {}
    sources = [
        f"[{item.get('citation_id', '?')}] {item.get('source', 'UNKNOWN')}"
        + (f", page {item['page']}" if item.get("page") else "")
        for item in result.get("citations") or []
    ]
    risk_lines = [
        f"{risk.get('severity', 'unknown').upper()}: {risk.get('type')} - {risk.get('reason')}"
        for risk in result.get("risks") or []
    ]
    return (
        "PATENTABILITY PRE-SCREEN\n\n"
        f"INVENTION\n{invention.get('title', '')}\n"
        f"Type: {invention.get('invention_type', 'unknown')}\n\n"
        f"READINESS SCORE\n{assessment.get('readiness_score', 0)}/100 - "
        f"{str(assessment.get('readiness_level', 'unknown')).replace('_', ' ').upper()}\n\n"
        f"NOVELTY PRE-SCREEN\n{novelty.get('score', 0)}/100 - "
        f"{str(novelty.get('status', 'unknown')).replace('_', ' ').upper()}\n\n"
        f"INVENTIVE STEP PRE-SCREEN\n{inventive.get('score', 0)}/100 - "
        f"{str(inventive.get('status', 'unknown')).replace('_', ' ').upper()}\n\n"
        f"POTENTIAL RISKS\n{_lines(risk_lines)}\n\n"
        f"EVIDENCE GAPS\n{_lines(result.get('evidence_gaps') or [])}\n\n"
        f"SOURCES\n{_lines(sources)}\n\n"
        f"TRUST SCORE\n{trust.get('trust_score', 0)}/100 - "
        f"{str(trust.get('level', 'unknown')).replace('_', ' ').upper()}\n\n"
        f"LIMITATIONS\n{_lines(result.get('limitations') or [])}"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the Phase-2A manual pre-screen.")
    parser.add_argument(
        "--api-url",
        default="http://127.0.0.1:8000/api/patentability/check",
        help="Local patentability endpoint",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        response = httpx.post(args.api_url, json=TEST_INVENTION, timeout=120)
    except httpx.RequestError:
        print("Patentability API request failed. Check that the API is running.")
        return 1
    if response.is_error:
        try:
            detail = response.json().get("detail", "Request failed")
        except ValueError:
            detail = "Request failed"
        print(f"Patentability API error ({response.status_code}): {detail}")
        return 1
    print(format_result(response.json()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
