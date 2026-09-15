# Financial News Dual-Channel RAG and Knowledge Graph QA System

An evidence-grounded question-answering system for financial news and documents, combining vector retrieval, directed knowledge-graph retrieval, and source-traceable answer generation.

**Undergraduate Thesis Project**<br>
**Developer:** Yibo Feng<br>
**Advisor:** Jinyu Guo<br>
**Original development period:** November 2025 -- June 2026

> **Repository note.** This repository is a cleaned and reproducible open-source edition prepared after the undergraduate thesis defense. The thesis project was developed from November 2025 to June 2026; the public repository was organized and released afterward in September 2026. Its GitHub commit history therefore records the post-defense open-source preparation and maintenance process, rather than the full original development timeline. Private documents, deployment-specific data, and credentials are not included; the repository instead provides synthetic sample documents and an offline-capable implementation that can be reproduced without an API key.

The public edition focuses on the portable dual-channel retrieval and evidence-tracing pipeline implemented in this repository. All technical claims in this README refer only to the code currently provided here.

---

## Overview

Financial documents often contain two complementary forms of information:

- **Textual evidence**, such as policy statements, company announcements, numerical disclosures, and explanatory passages.
- **Relational evidence**, such as company--institution, policy--industry, and event--entity relationships.

A vector-only system may retrieve relevant passages while overlooking explicit entity relationships. A graph-only system may recover relationships but lose the surrounding source context. This project therefore uses two retrieval channels and fuses their ranked results before answer generation:

1. **Vector retrieval** locates relevant document chunks.
2. **Knowledge-graph retrieval** expands entities and directed relationships.
3. **Reciprocal Rank Fusion (RRF)** combines both ranked evidence lists.
4. **Answer generation** produces an answer grounded in numbered source evidence.
5. **Provenance and visualization** expose filenames, page numbers, excerpts, scores, and the retrieved relationship graph.

The system supports a fully local demonstration path as well as optional Qdrant, Neo4j, and OpenAI-compatible model services.

---

## Core Capabilities

- Parses PDF, DOCX, XLSX, CSV, HTML, TXT, and Markdown documents.
- Preserves source filenames, document identifiers, and PDF page numbers.
- Splits documents into configurable overlapping chunks.
- Supports local deterministic hash embeddings for offline demonstration.
- Supports OpenAI-compatible embedding endpoints for semantic retrieval.
- Uses SQLite as the default local vector store.
- Supports Qdrant as an optional external vector database.
- Extracts financial entities and directed relationships with a transparent rule-based pipeline.
- Uses SQLite as the default local graph store.
- Supports Neo4j as an optional external graph database.
- Provides vector, graph, and hybrid retrieval modes.
- Combines vector and graph rankings with weighted Reciprocal Rank Fusion.
- Applies lightweight publication-date relevance weighting.
- Generates evidence-grounded answers through either a local extractive generator or an OpenAI-compatible language-model endpoint.
- Returns numbered citations with titles, filenames, page numbers, scores, and evidence excerpts.
- Visualizes retrieved entity relationships with NetworkX and Plotly.
- Provides a Gradio interface for document indexing, question answering, provenance inspection, and graph exploration.
- Includes synthetic sample documents, automated tests, a smoke benchmark, technical documentation, and Docker deployment files.

---

## Public Release Scope

The default configuration is intentionally self-contained:

| Component | Default offline implementation | Optional implementation |
| --- | --- | --- |
| Vector storage | SQLite | Qdrant |
| Graph storage | SQLite | Neo4j |
| Embeddings | Deterministic hash-based embedder | OpenAI-compatible embedding endpoint |
| Answer generation | Evidence-based extractive generator | OpenAI-compatible language-model endpoint |
| Entity extraction | Transparent rule-based financial entity extractor | Replaceable through the same indexing interface |
| Interface | Local Gradio application | Containerized Gradio application |

The offline components are provided for reproducibility, testing, and demonstration. The hash-based embedder, rule-based entity extractor, and extractive answer generator are not presented as substitutes for production-grade trained models.

---

## System Architecture

~~~text
Financial documents
        |
        v
Document parsing and metadata extraction
        |
        v
Overlapping text chunking
        |
        +-----------------------------+
        |                             |
        v                             v
Embedding generation          Financial entity and
        |                      relationship extraction
        v                             |
SQLite / Qdrant                       v
vector storage                SQLite / Neo4j graph storage
        |                             |
        v                             v
Vector retrieval              Multi-hop graph retrieval
        |                             |
        +-------------+---------------+
                      |
                      v
            Reciprocal Rank Fusion
                      |
                      v
       Extractive or model-based generation
                      |
                      v
 Answer + numbered citations + evidence + graph
~~~

The project separates parsing, chunking, embeddings, storage, retrieval, generation, and presentation behind small modules so that individual components can be replaced without rewriting the complete pipeline.

---

## Retrieval Pipeline

### Vector Retrieval

The question is embedded using the configured embedding provider and compared with indexed document chunks. Results can be restricted to selected documents, and a small bounded recency bonus is applied when a valid publication date is available.

Vector retrieval is useful for:

- locating specific facts and numerical disclosures;
- finding semantically related passages;
- searching company announcements and research reports;
- retrieving policy and regulatory text.

### Knowledge-Graph Retrieval

During indexing, the system detects financial entities such as companies, institutions, industries, policies, and events. Directed relationships retain the identifiers of the supporting document and text chunk.

At query time, recognized entities are used as graph seeds. The system expands related entities and relationships for the configured number of hops and maps the resulting graph evidence back to its source chunks.

Graph retrieval is useful for:

- company and institution relationships;
- policy and industry relationships;
- event--entity connections;
- questions involving multiple related entities;
- relationship-chain exploration.

### Hybrid Retrieval

Vector similarity scores and graph confidence scores are not directly comparable. Hybrid mode therefore combines their ranking positions using weighted Reciprocal Rank Fusion:

~~~text
RRF(d) = sum of weight(channel) / (60 + rank(channel, d))
~~~

The current implementation assigns a weight of 1.0 to the vector channel and 0.9 to the graph channel. Hybrid retrieval is the default mode.

### Evidence-Grounded Answering

Retrieved chunks are passed to either:

- the built-in extractive generator, which creates a local evidence-only response; or
- a configured OpenAI-compatible language-model service.

The final interface exposes the answer together with numbered citations, source metadata, evidence excerpts, and retrieved relationships so that users can inspect the original basis of each response.

---

## Supported Document Types

| Format | Extension | Notes |
| --- | --- | --- |
| PDF | .pdf | Text extraction with page-number preservation; OCR is not included |
| Word | .docx | Paragraph and table extraction |
| Excel | .xlsx | Multi-sheet extraction through pandas and openpyxl |
| CSV | .csv | UTF-8/UTF-8-SIG tabular extraction |
| HTML | .html, .htm | Text extraction from local HTML files |
| Plain text | .txt | UTF-8 text |
| Markdown | .md | UTF-8 text |

---

## Technology Stack

| Area | Technology |
| --- | --- |
| Language | Python 3.10+ |
| User interface | Gradio |
| Local vector storage | SQLite |
| External vector database | Qdrant |
| Local graph storage | SQLite |
| External graph database | Neo4j |
| Graph processing | NetworkX |
| Visualization | Plotly |
| Document processing | pypdf, python-docx, pandas, openpyxl |
| Remote model integration | OpenAI-compatible HTTP APIs |
| Deployment | Docker and Docker Compose |
| Testing | Python unittest |

---

## Quick Start

The default offline mode requires no API key, external model, Qdrant instance, or Neo4j instance.

### Linux and macOS

~~~bash
git clone https://github.com/nhtsymh/financial-news-rag-graduation-project.git
cd financial-news-rag-graduation-project

python3 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
pip install -e .

python scripts/seed_demo.py
python app.py
~~~

### Windows PowerShell

~~~powershell
git clone https://github.com/nhtsymh/financial-news-rag-graduation-project.git
Set-Location financial-news-rag-graduation-project

py -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
pip install -e .

python scripts\seed_demo.py
python app.py
~~~

Open the application at:

~~~text
http://127.0.0.1:7860
~~~

The bundled demonstration uses synthetic financial documents and local SQLite storage.

---

## Basic Usage

1. Start the application.
2. Open the **Document Indexing** tab.
3. Upload one or more supported documents.
4. Build the document index.
5. Open the **Intelligent Q&A** tab.
6. Select vector, graph, or hybrid retrieval.
7. Optionally restrict retrieval to selected documents.
8. Enter a question about the indexed material.
9. Inspect the answer, numbered citations, evidence excerpts, and entity graph.

Two synthetic demonstration documents are included:

~~~text
data/sample_financial_news.md
data/sample_company_announcement.txt
~~~

The company and events in the sample data are fictional and are included only to demonstrate the indexing and retrieval workflow.

---

## Configuration

The application reads optional settings from a local <code>.env</code> file in the project root. No configuration file is required for the default offline mode.

### Default Offline Mode

If no <code>.env</code> file is present, the application uses:

~~~dotenv
VECTOR_BACKEND=sqlite
GRAPH_BACKEND=sqlite
EMBEDDING_PROVIDER=hash
LLM_PROVIDER=extractive
~~~

In this mode:

- vector and graph records remain in local SQLite databases;
- no document content is sent to an external model service;
- embeddings are produced by the deterministic local hash embedder;
- answers are assembled only from retrieved evidence.

### Optional Environment Variables

| Variable | Default | Description |
| --- | --- | --- |
| FNRAG_DATA_DIR | ./runtime_data | Runtime data directory |
| VECTOR_BACKEND | sqlite | sqlite or qdrant |
| GRAPH_BACKEND | sqlite | sqlite or neo4j |
| CHUNK_SIZE | 1024 | Approximate maximum chunk size |
| CHUNK_OVERLAP | 256 | Overlap between adjacent chunks |
| TOP_K | 5 | Default number of returned evidence chunks |
| GRAPH_HOPS | 2 | Maximum graph traversal depth |
| EMBEDDING_PROVIDER | hash | hash or openai |
| EMBEDDING_DIMENSIONS | 384 | Embedding dimensions |
| EMBEDDING_BASE_URL | empty | OpenAI-compatible embedding endpoint |
| EMBEDDING_API_KEY | empty | Embedding-service API key |
| EMBEDDING_MODEL | nomic-embed-text | Embedding model name |
| LLM_PROVIDER | extractive | extractive or openai |
| LLM_BASE_URL | empty | OpenAI-compatible chat-completions endpoint |
| LLM_API_KEY | empty | Language-model API key |
| LLM_MODEL | qwen2.5:7b | Language model name |
| LLM_TIMEOUT_SECONDS | 120 | Remote request timeout |
| QDRANT_URL | http://localhost:6333 | Qdrant address |
| QDRANT_API_KEY | empty | Optional Qdrant API key |
| QDRANT_COLLECTION | financial_news_chunks | Qdrant collection |
| NEO4J_URI | bolt://localhost:7687 | Neo4j Bolt address |
| NEO4J_USER | neo4j | Neo4j username |
| NEO4J_PASSWORD | password | Neo4j password |
| GRADIO_SERVER_NAME | 127.0.0.1 | Gradio bind address |
| GRADIO_SERVER_PORT | 7860 | Gradio port |
| GRADIO_SHARE | false | Whether to create a Gradio share link |

### OpenAI-Compatible Models

To use an OpenAI-compatible language model, create a local <code>.env</code> file containing values such as:

~~~dotenv
LLM_PROVIDER=openai
LLM_BASE_URL=http://localhost:11434/v1
LLM_API_KEY=ollama
LLM_MODEL=qwen2.5:7b
LLM_TIMEOUT_SECONDS=120
~~~

The same interface can be used with Ollama, vLLM, LocalAI, or another service exposing an OpenAI-compatible chat-completions endpoint.

To use an OpenAI-compatible embedding service:

~~~dotenv
EMBEDDING_PROVIDER=openai
EMBEDDING_BASE_URL=http://localhost:11434/v1
EMBEDDING_API_KEY=ollama
EMBEDDING_MODEL=nomic-embed-text
EMBEDDING_DIMENSIONS=768
~~~

When the embedding dimensions change, use a new Qdrant collection name.

---

## Qdrant and Neo4j

### Docker Compose

The repository includes a Docker Compose configuration for running the application with Qdrant and Neo4j:

~~~bash
docker compose up --build
~~~

| Service | Address |
| --- | --- |
| Gradio application | http://localhost:7860 |
| Qdrant | http://localhost:6333 |
| Neo4j Browser | http://localhost:7474 |
| Neo4j Bolt | bolt://localhost:7687 |

The password included in <code>docker-compose.yml</code> is intended only for local demonstration. Change it before exposing any service beyond a trusted local environment.

Stop the services with:

~~~bash
docker compose down
~~~

To stop the services and permanently delete their Docker volumes:

~~~bash
docker compose down -v
~~~

### Local Application with External Backends

Install the optional infrastructure dependencies:

~~~bash
pip install -e ".[infra]"
~~~

Create a local <code>.env</code> file:

~~~dotenv
VECTOR_BACKEND=qdrant
GRAPH_BACKEND=neo4j

QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=
QDRANT_COLLECTION=financial_news_chunks

NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=replace-with-a-local-password
~~~

Start Qdrant and Neo4j before launching the local application.

---

## Data and Privacy

By default, runtime files are stored under:

~~~text
runtime_data/
~~~

This directory may contain:

- copied upload files;
- parsed-document metadata;
- text chunks and embeddings;
- graph entities and relationships;
- local SQLite databases.

Before committing changes from a local clone, make sure that <code>.env</code>, <code>runtime_data/</code>, private documents, database files, credentials, and service tokens remain untracked.

When remote embedding or language-model services are enabled, document excerpts may be sent to the configured service. Review the data policy of that service before uploading private or confidential material.

The public repository contains only synthetic demonstration documents. It does not include private thesis data, personal financial data, or production credentials.

---

## Testing and Validation

Run the unit and end-to-end tests:

~~~bash
python -m unittest discover -s tests -v
~~~

Run a syntax compilation check:

~~~bash
python -m compileall -q app.py src tests scripts
~~~

Run the bundled smoke benchmark:

~~~bash
python scripts/benchmark.py
~~~

The current benchmark reports query latency and returned citation counts for three demonstration questions over the two bundled synthetic documents. It is intended as a functional smoke benchmark, not as a retrieval-quality benchmark or evidence of production performance.

The automated test suite covers:

- overlapping chunk construction and stable identifiers;
- invalid chunk-configuration handling;
- document-scoped vector retrieval;
- end-to-end hybrid indexing and question answering;
- directed relationship extraction and graph search;
- malformed Unicode-surrogate sanitization.

The core tests use the default local components and do not require Gradio, Qdrant, Neo4j, Docker, or an external model service.

---

## Project Structure

~~~text
financial-news-rag-graduation-project/
├── app.py
├── pyproject.toml
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── Makefile
├── LICENSE
├── SECURITY.md
├── CHANGELOG.md
├── README.md
├── data/
│   ├── sample_financial_news.md
│   └── sample_company_announcement.txt
├── docs/
│   ├── architecture.md
│   └── defense-guide.md
├── scripts/
│   ├── benchmark.py
│   ├── run.sh
│   └── seed_demo.py
├── src/
│   └── financial_news_rag/
│       ├── __init__.py
│       ├── catalog.py
│       ├── chunking.py
│       ├── config.py
│       ├── embeddings.py
│       ├── graph_store.py
│       ├── indexing.py
│       ├── llm.py
│       ├── models.py
│       ├── parsers.py
│       ├── qa.py
│       ├── retrieval.py
│       ├── service.py
│       ├── ui.py
│       ├── vector_store.py
│       └── visualization.py
└── tests/
    ├── test_chunking.py
    ├── test_end_to_end.py
    ├── test_graph.py
    └── test_parsers.py
~~~

---

## Additional Documentation

- [Architecture](docs/architecture.md) explains the indexing, retrieval, storage, and evidence-tracing design.
- [Defense Guide](docs/defense-guide.md) records the suggested undergraduate thesis demonstration flow and common technical questions.
- [Security Policy](SECURITY.md) summarizes credential, data, and deployment precautions.
- [Changelog](CHANGELOG.md) records changes made for the public release.

---

## Limitations

- Scanned image-only PDFs require OCR before indexing.
- The offline hash embedder is designed for deterministic demonstration and has lower semantic quality than a trained embedding model.
- The built-in extractive generator cannot match the reasoning or language quality of a capable language model.
- The default entity and relationship extractor is rule-based and may miss entities or generate incorrect relationships.
- Graph traversal retrieves relationship paths but does not by itself guarantee correct multi-step reasoning.
- Publication-date weighting is lightweight and should not be interpreted as financial time-series modeling.
- Retrieval quality depends on document coverage, parsing quality, chunk settings, and the configured embedding model.
- The included smoke benchmark does not measure Recall@K, ranking quality, factual accuracy, or real-world financial performance.
- Optional Qdrant, Neo4j, and remote-model deployments require additional service configuration and security hardening.

---

## Responsible Use

This project is intended for information retrieval, document analysis, academic demonstration, and research. It does not provide financial or investment advice and must not be used as an automated trading or investment-decision system.

Always verify generated answers against the cited source documents, publication dates, and official announcements before making important decisions.

---

## License

This project is released under the [MIT License](LICENSE).

---

## Academic Context

This system was developed by **Yibo Feng** as an undergraduate thesis project under the supervision of **Jinyu Guo**. The public repository was prepared after the thesis defense to provide a cleaned, privacy-conscious, and reproducible implementation for academic review and further development.
