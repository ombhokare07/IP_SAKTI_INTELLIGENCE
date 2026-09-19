# Offline Demonstration Flow

This flow exercises the interface without claiming live patent, traditional-knowledge, or regulatory access.

## Start an explicit synthetic demo

From the project root:

```powershell
python scripts/setup.py --mode offline --demo
.\.venv\Scripts\Activate.ps1
python -m uvicorn backend.main:app --reload
```

In a second terminal:

```powershell
cd frontend
npm run dev
```

The `--demo` option enables labelled fixtures only in a non-production environment. Never use demo configuration to make a substantive legal decision.

## Suggested walkthrough

1. Open **Settings** and show that prior-art/TK/regulation providers are marked mock while Gemini, translation, STT, and TTS remain unconfigured unless separately supplied.
2. Open **Dashboard** to review provider health, evidence terminology, and recent local artifacts.
3. Submit **Prior-Art Intelligence** input and inspect the visible `TEST DATA`/mock labels, source cards, zero real-world trust, and novelty limitation.
4. Submit **Traditional Knowledge Risk** input and confirm the extracted ingredients, uses, processes, similarity evidence, risk meter, and explicit absence of TK clearance.
5. Use **Global Regulation Compare**, **Document Compliance**, **Regulation Changes**, and **Compliance Journey** to exercise the illustrative regulation fixture. Point out that it is not official/current law.
6. Use **Ask IP-SAKTI** for deterministic orchestration. With Gemini unconfigured, RAG-specific chat remains unavailable or evidence-insufficient; it does not fabricate an answer.
7. Upload a small PDF/TXT/MD document in **Knowledge Library**. PDF vector ingestion additionally requires the full embedding/vector dependencies.
8. Create and export a report. The report preserves mode, citations, trust/evidence metadata, and limitations.
9. Show **Regulatory Alerts** and **Reports**, then return to **Settings** to explain live credential requirements.

## Expected safety observations

- Mock/synthetic data is visually and structurally labelled.
- No mock prior-art result yields a final novelty claim.
- No mock or unauthorized TK result yields TK clearance.
- No illustrative regulation fixture yields a definitive legal-compliance conclusion.
- Scores describe workflow/evidence quality, not legal correctness or patent-grant probability.

Remove or replace the local `.env` before configuring a real deployment. Never copy provider credentials into screenshots, reports, frontend settings, or demo recordings.
