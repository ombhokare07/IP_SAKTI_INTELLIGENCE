"""Deterministic synthetic prior-art records for explicit tests and demos only."""

from intelligence.prior_art.providers.base import PriorArtRecord


MOCK_PROVIDER_NAME = "TEST DATA / MOCK PROVIDER"


class MockPriorArtProvider:
    name = MOCK_PROVIDER_NAME
    is_test_fixture = True

    def __init__(self, records: list[PriorArtRecord] | None = None) -> None:
        self.records = list(records) if records is not None else self._fixtures()
        self.calls: list[tuple[str, int]] = []

    @staticmethod
    def _fixtures() -> list[PriorArtRecord]:
        return [
            PriorArtRecord(
                publication_number="TEST-FIXTURE-0001",
                title="Synthetic herbal wound-healing composition",
                abstract=(
                    "TEST FIXTURE: a herbal wound-healing formulation containing "
                    "turmeric, neem, and aloe vera extracts."
                ),
                applicants=["Synthetic Applicant A"],
                inventors=["Fixture Inventor One"],
                publication_date="2020-01-15",
                filing_date="2019-03-20",
                priority_date="2018-03-21",
                jurisdiction="TEST",
                classification_codes=["TEST-A61K"],
                claims=[
                    "TEST FIXTURE CLAIM: a wound-healing composition comprising turmeric and neem.",
                ],
                source_url="mock://prior-art/TEST-FIXTURE-0001",
                provider=MOCK_PROVIDER_NAME,
            ),
            PriorArtRecord(
                publication_number="TEST-FIXTURE-0002",
                title="Synthetic low-temperature botanical extraction process",
                abstract=(
                    "TEST FIXTURE: botanical material is extracted at low temperature "
                    "to reduce degradation of heat-sensitive active compounds."
                ),
                applicants=["Synthetic Applicant B"],
                inventors=["Fixture Inventor Two"],
                publication_date="2021-06-10",
                filing_date="2020-04-02",
                priority_date="2020-04-02",
                jurisdiction="TEST",
                classification_codes=["TEST-C11B"],
                claims=[
                    "TEST FIXTURE CLAIM: maintaining extraction temperature below a selected threshold.",
                ],
                source_url="mock://prior-art/TEST-FIXTURE-0002",
                provider=MOCK_PROVIDER_NAME,
            ),
            PriorArtRecord(
                publication_number="TEST-FIXTURE-0003",
                title="Synthetic mechanical irrigation controller",
                abstract="TEST FIXTURE: a controller regulates water delivery using soil sensors.",
                applicants=[],
                inventors=[],
                publication_date=None,
                filing_date=None,
                priority_date=None,
                jurisdiction="TEST",
                classification_codes=[],
                claims=[],
                source_url="mock://prior-art/TEST-FIXTURE-0003",
                provider=MOCK_PROVIDER_NAME,
            ),
        ]

    def search(self, query: str, limit: int = 10) -> list[PriorArtRecord]:
        if not query.strip():
            raise ValueError("query cannot be blank")
        if limit <= 0:
            raise ValueError("limit must be greater than zero")
        self.calls.append((query.strip(), limit))
        terms = {term.casefold() for term in query.split() if len(term) > 2}
        ranked = sorted(
            self.records,
            key=lambda record: len(
                terms
                & set(
                    f"{record.title or ''} {record.abstract or ''}".casefold().replace("-", " ").split()
                )
            ),
            reverse=True,
        )
        return ranked[:limit]
