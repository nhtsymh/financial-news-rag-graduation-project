# Graduation Project

## Retrieval-Augmented Generation Question Answering System for Financial News

This repository contains my complete graduation project for building a Retrieval-Augmented Generation (RAG) question answering system for financial news and documents.

The system can process financial news, company announcements, research reports, spreadsheets, and other reference materials. It combines vector retrieval, knowledge graph retrieval, and large language model generation to produce answers with traceable source evidence.

The project includes a Gradio web interface, local offline mode, optional Qdrant and Neo4j integration, Docker deployment files, automated tests, sample data, and technical documentation.

> This project is intended for information retrieval, document analysis, academic demonstration, and research purposes only. It does not constitute financial or investment advice. Always verify the original documents, publication dates, and official announcements before making important decisions.

## Features

- Supports PDF, DOCX, XLSX, CSV, HTML, TXT, and Markdown files.
- Splits documents into configurable overlapping text chunks.
- Provides an offline hash-based embedding model.
- Provides an offline evidence-based extractive answer generator.
- Supports OpenAI-compatible embedding and language model APIs.
- Uses SQLite as the default local vector database.
- Supports Qdrant as an optional vector database.
- Builds a directed financial knowledge graph.
- Uses SQLite as the default local graph database.
- Supports Neo4j as an optional graph database.
- Provides vector retrieval, graph retrieval, and hybrid retrieval.
- Uses Reciprocal Rank Fusion to combine retrieval results.
- Applies lightweight publication-date relevance weighting.
- Returns numbered citations with filenames, page numbers, scores, and excerpts.
- Displays entity relationships using NetworkX and Plotly.
- Provides a Gradio-based interactive web interface.
- Includes sample financial documents and demonstration scripts.
- Includes unit tests and end-to-end tests.
- Includes Docker and Docker Compose deployment configurations.
- Runs without an API key in the default offline mode.

## Application Interface

The Gradio homepage displays the title `毕业项目`, which means “Graduation Project.”

The application contains three main sections:

1. **Intelligent Q&A**

   Users can ask questions about indexed financial documents. The interface supports vector, graph, and hybrid retrieval modes. Answers are accompanied by source citations and entity relationship results.

2. **Document Indexing**

   Users can upload supported files and build the vector index and knowledge graph. The page displays the indexed document list and processing results.

3. **Project Information**

   This section explains the system architecture, available storage backends, offline operation, and usage disclaimer.

The knowledge base status panel displays the number of documents, text chunks, entities, relationships, and the currently selected storage backends.

## System Workflow

The system processes a question through the following stages:

1. A user uploads one or more financial documents.
2. The document parser extracts text and metadata.
3. The extracted text is divided into overlapping chunks.
4. Each chunk is converted into a vector embedding.
5. The chunks and vectors are stored in SQLite or Qdrant.
6. Financial entities and directed relationships are extracted.
7. The entities and relationships are stored in SQLite or Neo4j.
8. The user submits a question.
9. The system performs vector, graph, or hybrid retrieval.
10. Relevant evidence is passed to the offline answer generator or a configured large language model.
11. The application returns an answer, citations, evidence excerpts, and a relationship graph.

## Technology Stack

| Component | Technology |
|---|---|
| Programming language | Python 3.10+ |
| Web interface | Gradio |
| Local vector storage | SQLite |
| External vector database | Qdrant |
| Local graph storage | SQLite |
| External graph database | Neo4j |
| Graph processing | NetworkX |
| Visualization | Plotly |
| PDF processing | pypdf |
| Word processing | python-docx |
| Spreadsheet processing | pandas and openpyxl |
| Local embedding | Hash-based embedding |
| Remote model interface | OpenAI-compatible HTTP API |
| Deployment | Docker and Docker Compose |
| Testing | Python unittest |

## Project Structure

```text
financial_news_rag_project/
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
├── .env.example
├── .gitignore
├── .dockerignore
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
```

## Requirements

The recommended environment is:

- Python 3.10 or Python 3.11
- pip
- Git
- A modern web browser
- Docker Desktop, only when using Docker deployment

The default offline mode does not require Qdrant, Neo4j, an API key, or an external language model.

## Quick Start

### Linux and macOS

Clone the repository:

```bash
git clone https://github.com/nhtsymh/financial-news-rag-graduation-project.git
cd financial-news-rag-graduation-project
```

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the project:

```bash
python -m pip install --upgrade pip
pip install -e .
```

Create the environment configuration:

```bash
cp .env.example .env
```

Load the sample documents:

```bash
python scripts/seed_demo.py
```

Start the application:

```bash
python app.py
```

Open the following address in a browser:

```text
http://127.0.0.1:7860
```

### Windows PowerShell

Clone the repository:

```powershell
git clone https://github.com/nhtsymh/financial-news-rag-graduation-project.git
Set-Location financial-news-rag-graduation-project
```

Create and activate a virtual environment:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install the project:

```powershell
python -m pip install --upgrade pip
pip install -e .
```

Create the environment configuration:

```powershell
Copy-Item .env.example .env
```

Load the sample documents:

```powershell
python scripts\seed_demo.py
```

Start the application:

```powershell
python app.py
```

Open the following address in a browser:

```text
http://127.0.0.1:7860
```

## Basic Usage

1. Start the application.
2. Open `http://127.0.0.1:7860`.
3. Select the **Document Indexing** tab.
4. Upload one or more supported documents.
5. Click the button to build the document index.
6. Wait until the indexing process is complete.
7. Open the **Intelligent Q&A** tab.
8. Select a retrieval mode.
9. Enter a question about the uploaded documents.
10. Review the generated answer, citations, evidence excerpts, and entity relationships.

Two sample documents are included:

```text
data/sample_financial_news.md
data/sample_company_announcement.txt
```

## Offline Mode

Offline mode is enabled by default and requires no external services.

Use the following values in `.env`:

```dotenv
VECTOR_BACKEND=sqlite
GRAPH_BACKEND=sqlite
EMBEDDING_PROVIDER=hash
LLM_PROVIDER=extractive
```

In this mode:

- Vector data is stored locally in SQLite.
- Knowledge graph data is stored locally in SQLite.
- Embeddings are generated using the built-in hash-based embedder.
- Answers are generated by an evidence-based extractive generator.
- Uploaded document content is not sent to an external model service.

Offline mode is suitable for functional testing, classroom demonstration, and graduation project presentations. The built-in hash embedding and extractive answer generator are designed for reliable local operation, but they are not intended to replace production-grade embedding or language models.

## Docker Deployment

To start the application with Qdrant and Neo4j, run:

```bash
docker compose up --build
```

The following services will be available:

| Service | Address |
|---|---|
| Graduation Project application | `http://localhost:7860` |
| Qdrant | `http://localhost:6333` |
| Neo4j Browser | `http://localhost:7474` |
| Neo4j Bolt connection | `bolt://localhost:7687` |

The default Neo4j username is:

```text
neo4j
```

The default development password is defined in `docker-compose.yml`.

Change the default password before deploying the application to a public or production environment.

To stop the services:

```bash
docker compose down
```

To stop the services and remove Docker volumes:

```bash
docker compose down -v
```

Removing volumes permanently deletes the data stored by the Docker services.

## Using Qdrant and Neo4j Locally

Install the optional infrastructure dependencies:

```bash
pip install -e ".[infra]"
```

Configure `.env`:

```dotenv
VECTOR_BACKEND=qdrant
GRAPH_BACKEND=neo4j

QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=
QDRANT_COLLECTION=financial_news_chunks

NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=graduation-project-password
```

Ensure that Qdrant and Neo4j are running before starting the application.

## Connecting an OpenAI-Compatible Language Model

The project supports language model services that expose an OpenAI-compatible API, including Ollama, vLLM, and LocalAI.

Example configuration:

```dotenv
LLM_PROVIDER=openai
LLM_BASE_URL=http://localhost:11434/v1
LLM_API_KEY=ollama
LLM_MODEL=qwen2.5:7b
LLM_TIMEOUT_SECONDS=120
```

The API key value depends on the selected provider. Some local providers accept a placeholder value.

Restart the application after changing `.env`.

## Connecting an OpenAI-Compatible Embedding Model

Example configuration:

```dotenv
EMBEDDING_PROVIDER=openai
EMBEDDING_BASE_URL=http://localhost:11434/v1
EMBEDDING_API_KEY=ollama
EMBEDDING_MODEL=nomic-embed-text
EMBEDDING_DIMENSIONS=768
```

When changing the embedding dimension, use a new Qdrant collection name:

```dotenv
QDRANT_COLLECTION=financial_news_chunks_768
```

A Qdrant collection cannot store vectors with different dimensions in the same collection.

## Retrieval Modes

### Vector Retrieval

Vector retrieval is suitable for:

- Locating specific facts in documents
- Finding semantically related passages
- Retrieving numerical information
- Searching company announcements
- Searching policy and regulatory text

The user question is converted into an embedding and compared with indexed document chunks.

### Graph Retrieval

Graph retrieval is suitable for:

- Company relationships
- Institution relationships
- Policy relationships
- Industry relationships
- Multi-entity questions
- Relationship-chain questions

The system detects entities in the question and searches the directed knowledge graph for related paths.

### Hybrid Retrieval

Hybrid retrieval combines vector and graph results using Reciprocal Rank Fusion.

It is suitable for questions that require both original text evidence and entity relationships.

Hybrid retrieval is the default mode.

## Configuration

The main environment variables are listed below.

| Variable | Default value | Description |
|---|---|---|
| `FNRAG_DATA_DIR` | `./runtime_data` | Local runtime data directory |
| `VECTOR_BACKEND` | `sqlite` | Vector backend: `sqlite` or `qdrant` |
| `GRAPH_BACKEND` | `sqlite` | Graph backend: `sqlite` or `neo4j` |
| `CHUNK_SIZE` | `1024` | Approximate maximum chunk size |
| `CHUNK_OVERLAP` | `256` | Overlap between adjacent chunks |
| `TOP_K` | `5` | Default number of retrieval results |
| `GRAPH_HOPS` | `2` | Maximum graph retrieval depth |
| `EMBEDDING_PROVIDER` | `hash` | Embedding provider: `hash` or `openai` |
| `EMBEDDING_DIMENSIONS` | `384` | Embedding vector dimensions |
| `EMBEDDING_BASE_URL` | `http://localhost:11434/v1` | Embedding API base URL |
| `EMBEDDING_MODEL` | `nomic-embed-text` | Embedding model name |
| `LLM_PROVIDER` | `extractive` | Answer provider: `extractive` or `openai` |
| `LLM_BASE_URL` | `http://localhost:11434/v1` | Language model API base URL |
| `LLM_MODEL` | `qwen2.5:7b` | Language model name |
| `LLM_TIMEOUT_SECONDS` | `120` | Language model request timeout |
| `QDRANT_URL` | `http://localhost:6333` | Qdrant server address |
| `QDRANT_COLLECTION` | `financial_news_chunks` | Qdrant collection name |
| `NEO4J_URI` | `bolt://localhost:7687` | Neo4j connection address |
| `NEO4J_USER` | `neo4j` | Neo4j username |
| `GRADIO_SERVER_NAME` | `127.0.0.1` | Gradio server bind address |
| `GRADIO_SERVER_PORT` | `7860` | Gradio server port |
| `GRADIO_SHARE` | `false` | Whether to create a Gradio share link |

## Testing

Run all unit and end-to-end tests:

```bash
python -m unittest discover -s tests -v
```

Run the syntax compilation check:

```bash
python -m compileall -q app.py src tests scripts
```

Run the retrieval benchmark:

```bash
python scripts/benchmark.py
```

The core automated tests do not require Gradio, Qdrant, Neo4j, or an external language model.

## Data Storage

By default, runtime data is stored in:

```text
runtime_data/
```

This directory is excluded from Git through `.gitignore`.

The directory may contain:

- Parsed document metadata
- Text chunks
- Vector records
- Knowledge graph entities
- Knowledge graph relationships
- Local SQLite database files

Delete the directory only when you intentionally want to reset the local knowledge base.

## Security and Privacy

- Never commit a real `.env` file.
- Never commit API keys, passwords, tokens, or private credentials.
- Only `.env.example` should be stored in the repository.
- Review documents before uploading them to external model services.
- SQLite offline mode keeps document processing local.
- Remote embedding or language model providers may receive document excerpts.
- Change the default Neo4j password before public deployment.
- Do not expose Qdrant or Neo4j directly to the public internet without authentication.
- Review generated answers against their cited source documents.
- Knowledge graph relationships may contain extraction errors.

## Limitations

- The built-in PDF parser does not perform OCR on scanned image-only PDF files.
- The offline hash embedding model provides lower semantic quality than a production embedding model.
- The extractive answer generator cannot provide the same reasoning quality as a large language model.
- Rule-based entity and relationship extraction may produce missing or incorrect relationships.
- Publication-date weighting is lightweight and does not replace time-aware financial analysis.
- Generated answers depend on the quality and completeness of the uploaded documents.
- This system must not be used as an automated financial trading or investment decision system.

## Extending the Project

The project is designed with replaceable components.

### Custom Entity Extractor

Implement an extractor compatible with:

```python
FinancialEntityExtractor.extract()
```

### Custom Embedding Model

Implement an embedder compatible with:

```python
Embedder.embed()
```

### Custom Language Model

Implement a language model compatible with:

```python
LanguageModel.generate()
```

### Custom Vector Store

Implement the vector store interface used by the indexing and retrieval services.

### Custom Graph Store

Implement the graph store interface used by the indexing and graph retrieval services.

## Documentation

Additional documentation is available in:

```text
docs/architecture.md
docs/defense-guide.md
```

`architecture.md` explains the internal system design.

`defense-guide.md` provides a suggested graduation project demonstration and presentation process.

## License

This project is released under the MIT License.

See the `LICENSE` file for details.

## Disclaimer

This software is an academic graduation project.

It is provided without any guarantee of accuracy, completeness, availability, or fitness for a particular purpose. Financial information generated or retrieved by the system should always be verified against original and official sources.
