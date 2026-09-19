# Knowledge Graph Status

The supplied project contains a knowledge-graph scaffold under `knowledge_graph/` and repository/client placeholders under `database/graph/`. It models concepts such as products, ingredients, patents, regulations, authorities, and jurisdictions.

The finalized runtime does **not** require Neo4j and does not treat a generated graph as authoritative evidence. No populated knowledge graph or live graph database is bundled. Current API conclusions are based on the explicitly returned RAG, provider, local-corpus, or fixture evidence described in each response.

## Intended future boundary

If the scaffold is connected later, a graph node or relationship should always retain:

- source evidence identifier and mode;
- source URL or local locator and page where applicable;
- exact supporting excerpt;
- jurisdiction and authority;
- effective/version and retrieval timestamps;
- extraction method and review status.

Graph traversal must not promote an extracted relationship into a legal fact. Unsupported edges should be excluded from citations and scoring. Synthetic nodes must remain marked mock through every downstream query and report.

Because graph population and a reviewed extraction workflow are outside the finalized feature path, `database/graph`, `knowledge_graph`, and `scripts/build_knowledge_graph.py` should be regarded as preserved extension points, not a configured production capability.
