# Summarizer v2

Transcript summarization and routing via LangGraph. Classifies calls (AE/Sales, CSM, Internal, SDR) and runs expert summarization with optional Voss and methodology (e.g. MEDDPICC) analysis.

## Stategraph

The pipeline is implemented as a LangGraph state graph: transcript and metadata are classified (Level 1 → call type), then routed by confidence and length. High-confidence transcripts go to type-specific expert nodes; low confidence or short transcripts use the fallback node for a neutral summary. For **AE/Sales** calls, a Level 2 classifier detects the AE stage (discovery, demo, proposal, negotiation), then parallel LLM calls produce summarization, Voss framework, and methodology (e.g. MEDDPICC) output, combined into enriched sales intelligence. Other types produce technical (Internal), health (CSM), or pitch (SDR) summaries.

![Summarizer stategraph](docs/stategraph.png)

## Project structure

```
summarizer-v2/
├── app/
│   ├── api/
│   │   ├── main.py          # FastAPI app entry, router mount
│   │   ├── routes.py        # POST /summarize, GET /health, GET /health/ready
│   │   └── schemas.py       # SummarizeRequest, SummarizeResponse (Pydantic)
│   ├── config.py            # Loads config.yaml, builds LLM (Groq)
│   ├── graph/
│   │   ├── state.py         # CallState TypedDict (transcript, call_type, summaries, etc.)
│   │   ├── workflow.py      # LangGraph workflow definition
│   │   └── nodes/
│   │       ├── classifiers.py   # Level-1/2 call-type classification
│   │       ├── sales_expert.py  # AE/Sales expert (stages: discovery, demo, proposal, negotiation)
│   │       ├── csm_expert.py    # CSM/Post-Sale expert (QBR vs general)
│   │       ├── internal_expert.py
│   │       ├── sdr.py
│   │       └── fallback.py      # Unclassified fallback summarization
│   ├── prompts/
│   │   ├── loader.py        # Jinja2 prompt loader
│   │   ├── classifiers/     # level_1.md, level_2.md
│   │   ├── summarization/   # ae/, csm/, internal.md, sdr.md
│   │   ├── fallback/        # fallback_template.md
│   │   ├── methodologies/   # meddpicc.md
│   │   └── voss_framework/  # demo, discovery, negotiation, proposal
│   ├── transcript_parser/
│   │   ├── models.py        # Transcript/turn models
│   │   └── parser.py        # Parse transcript JSON → turns/text
│   ├── utils/
│   │   ├── json_to_html.py
│   │   ├── llm_response.py  # clean_json_response
│   │   ├── logger/          # Logging setup (configure_logging)
│   │   └── scoring/         # meddpicc.py
│   └── tools/
│       ├── render_json.py   # CLI: python -m app.tools.render_json <input.json> [output.html]
│       └── json_viewer.html # Static HTML viewer
├── config.yaml              # LLM, routing, csm, methodology, fallback, meddpicc
├── server.py                # Uvicorn entrypoint (python server.py)
├── setup.sh                 # venv + pip install
├── requirements.txt
├── data/                    # Sample data (transcript.txt, meddpicc*.json)
├── transcripts/             # Transcript folders (JSON, label-map, domains, etc.)
└── notebooks/                # graph_test.ipynb, meddpicc_test.ipynb
```

Run from the project root so imports like `app.graph.workflow` and `app.transcript_parser.parser` resolve.

---

## Setup

1. Create and activate a virtual environment (Python 3.11 recommended):

   ```bash
   ./setup.sh
   ```

   Or manually:

   ```bash
   uv venv --python 3.11
   source .venv/bin/activate   # or .venv\Scripts\activate on Windows
   uv pip install -r requirements.txt
   ```

2. Set your Groq API key (e.g. in a `.env` file at the project root):

   ```
   GROQ_API_KEY=your_key_here
   ```

   The app loads `.env` via `python-dotenv` when building the LLM.

## Configuration

Runtime configuration is in `config.yaml` at the project root. Override the path with the `APP_CONFIG` environment variable. Keys include:

- `llm`: model name and temperature
- `routing`: confidence threshold, min word count, call type to path mapping
- `csm`, `methodology`, `fallback`, `meddpicc`: expert-specific settings

---

## API documentation

Base URL (local): `http://localhost:8000` (or as configured when running the server).

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Liveness check; returns `{"status": "ok"}`. |
| `GET` | `/health/ready` | Readiness check; returns 503 if `GROQ_API_KEY` is not set. |
| `POST` | `/summarize` | Run the summarizer graph on the given transcript. |

Interactive OpenAPI docs: **`GET /docs`** (Swagger UI).

### POST /summarize

**Request body** (`application/json`):

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `transcript` | string | Yes | Plain text transcript to summarize. |
| `metadata` | object | No | Optional metadata (e.g. `meeting_title`, `participant_domains`, `internal_domains`). Default: `{}`. |
| `org_config` | object | No | Optional org config (e.g. `sales_methodology`). Default: `{}`. |

**Response** (200): JSON object. Only non-`null` fields are present. Possible keys:

| Field | Type | Description |
|-------|------|-------------|
| `call_type` | string | One of: `AE/Sales`, `CSM/Post-Sale`, `Internal`, `SDR/Outbound`, `Unclassified`. |
| `ae_stage` | string | For AE/Sales: e.g. `discovery`, `demo`, `proposal`, `negotiation`. |
| `confidence_score` | number | Classification confidence (0–1). |
| `final_summary` | object | Expert-generated summary. |
| `voss_analysis` | object | Voss framework analysis (when applicable). |
| `methodology_analysis` | object | Methodology (e.g. MEDDPICC) analysis (when applicable). |
| `participant_roles` | object | Inferred participant roles. |
| `expert_insights` | object | Additional expert insights. |

Errors: `503` with a JSON `detail` message if summarization fails or dependencies (e.g. Groq) are unavailable.

---

## Sample payload

### Request (POST /summarize)

```json
{
  "transcript": "[00:00:29] Anika Ahlstrom: Recording in progress.\n[00:02:43] Gopinath Perkinian: Hi, team.\n[00:02:44] Brian Dracup: Hello, everyone. Good morning. We're excited to walk through the sales engagement workflow today and show you how SDRs manage tasks, sequences, and outreach.\n[00:05:48] Austin Brown: I wasn't on the last demo but watched the recording. Did you come to market as a forecast tool, competing with Clari?\n[00:06:04] Brian Dracup: Our roots were in forecasting about ten years ago. We've since evolved into an end-to-end platform—forecasting, conversation intelligence, sales engagement, and customer success—so you can replace point solutions like Outreach, SalesLoft, and Gainsight.",
  "metadata": {
    "meeting_title": "Alteryx SE RFP - 2nd Demo",
    "participant_domains": ["alteryx.com", "aviso.com"],
    "internal_domains": ["aviso.com"]
  },
  "org_config": {
    "sales_methodology": "MEDDPICC"
  }
}
```

### Example response (200)

```json
{
  "call_type": "AE/Sales",
  "ae_stage": "demo",
  "confidence_score": 0.89,
  "final_summary": {
    "overview": "Second demo for Alteryx focused on sales engagement: day-in-the-life of an SDR, task management, and sequences.",
    "key_topics": ["Sales engagement workflow", "SDR task and sequence management", "Aviso vs Outreach/SalesLoft/Gainsight"],
    "next_steps": ["Internal alignment on timeline (February)", "Follow-up from prospect"]
  },
  "participant_roles": {
    "Brian Dracup": "Vendor / AE",
    "Austin Brown": "Prospect",
    "Gopinath Perkinian": "Vendor / PM"
  },
  "methodology_analysis": {
    "framework": "MEDDPICC",
    "dimensions": [
      { "dimension": "metrics", "score": 0, "status": "Missing/Identified" },
      { "dimension": "economic_buyer", "score": 0, "status": "Missing" },
      { "dimension": "decision_criteria", "score": 4, "status": "aligned" }
    ]
  }
}
```

*(Actual response fields and structure depend on call type, stage, and config; only non-null values are returned.)*

---

## Usage examples

### Running the API

From the project root:

```bash
python server.py
```

Or with uvicorn:

```bash
uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000
```

### cURL — health and summarize

```bash
# Liveness
curl -s http://localhost:8000/health

# Readiness (requires GROQ_API_KEY)
curl -s http://localhost:8000/health/ready

# Summarize (minimal body)
curl -s -X POST http://localhost:8000/summarize \
  -H "Content-Type: application/json" \
  -d '{"transcript": "Your full transcript text here."}'

# Summarize with metadata and org_config
curl -s -X POST http://localhost:8000/summarize \
  -H "Content-Type: application/json" \
  -d '{
    "transcript": "Speaker A: We need to align on the timeline. Speaker B: February works.",
    "metadata": {"meeting_title": "Q4 Planning"},
    "org_config": {"sales_methodology": "MEDDPICC"}
  }'
```

### Python (requests)

```python
import requests

url = "http://localhost:8000/summarize"
payload = {
    "transcript": open("data/transcript.txt").read(),
    "metadata": {"meeting_title": "Demo Call"},
    "org_config": {},
}
resp = requests.post(url, json=payload)
resp.raise_for_status()
print(resp.json())
```

### Notebooks

Open `notebooks/graph_test.ipynb` or `notebooks/meddpicc_test.ipynb` and run the cells with the project root as the working directory so paths and imports resolve. The notebooks use the compiled graph and sample transcripts.

### JSON viewer (CLI)

To render a JSON file (e.g. summarizer output) as HTML:

```bash
python -m app.tools.render_json data/meddpicc9.json output.html
```

Then open `output.html` in a browser.

---

## Running

- **API:** Start the server as above; use `POST /summarize` with a JSON body, `GET /health` for liveness, `GET /health/ready` for readiness, and `GET /docs` for interactive API docs.
- **Notebooks:** Run `notebooks/graph_test.ipynb` or `notebooks/meddpicc_test.ipynb` from the project root.
