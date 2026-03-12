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

- `strategic_llm`, `technical_llm`: model name, temperature, reasoning settings, token limits
- `routing`: fallback confidence levels, min word count, call type to path mapping
- `call_types`: allowed call types for classification
- `csm`, `methodology`, `fallback`, `meddpicc`: expert-specific settings

---

## API documentation

Base URL (local): `http://localhost:8000` (or as configured when running the server).

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Liveness check; returns `{"status": "ok"}`. |
| `GET` | `/health/ready` | Readiness check; returns 503 if `GROQ_API_KEY` is not set. |
| `POST` | `/summarize` | Run the summarizer graph on the given transcript turns. |
| `POST` | `/recompute` | Re-run the summarizer graph with user-provided classification overrides. |

Interactive OpenAPI docs: **`GET /docs`** (Swagger UI).

### POST /summarize

**Request body** (`application/json`):

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `transcript` | array of objects | Yes | Transcript turns with speaker/timestamp info, as produced by your upstream system. |
| `metadata` | object | Yes | Call metadata. Must include at least `user_map` (participant email → display name) and `topic` (meeting title). May include `internal_domains` to distinguish internal participants. |
| `org_config` | object | No | Optional org config (e.g. `sales_methodology`). Default: `{}`. |

**Response** (200): JSON object. Only non-`null` fields are present. Possible keys:

| Field | Type | Description |
|-------|------|-------------|
| `call_type` | string | One of: `AE/Sales`, `CSM/Post-Sale`, `Internal`, `SDR/Outbound`, `Unclassified`. |
| `ae_stage` | string | For AE/Sales: e.g. `discovery`, `demo`, `proposal`, `negotiation`. |
| `confidence_score` | number | Overall classification confidence (0–1). |
| `confidence_level` | string | Discrete confidence band used for routing, one of: `LOW`, `MEDIUM`, `HIGH`, `VERY HIGH`. |
| `final_summary` | object | Expert-generated summary (shape depends on call type and templates). |
| `voss_analysis` | object | Voss framework analysis (when applicable for AE/Sales). |
| `methodology_analysis` | object | Methodology (e.g. MEDDPICC) analysis (when applicable for AE/Sales). |
| `participant_roles` | array of objects | Inferred participant roles, e.g. `[{ "name": "...", "role": "vendor_ae" }, ...]`. |
| `expert_insights` | object | Additional expert insights (call-type specific). |
| `call_type_reasoning` | string | Free-text explanation of the Level 1 classification. |
| `ae_stage_reasoning` | string | Free-text explanation of the AE stage classification (AE/Sales only). |

The response model is configured with `extra = "allow"`, so additional non-null fields may be present over time. Treat unknown fields as non-breaking extensions.

Errors: `503` with a JSON `detail` message if summarization fails or dependencies (e.g. Groq) are unavailable.

---

### POST /recompute

Re-runs the summarizer graph for a call while allowing you to override the Level 1 and Level 2 classifications. This is useful when a human has corrected the call type or AE stage and you want to regenerate summaries with the updated labels.

**Request body** (`application/json`):

Same shape as `POST /summarize`, plus:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `call_type` | string | No | User-corrected L1 classification. Must be one of: `AE/Sales`, `CSM/Post-Sale`, `Internal/Implementation`, `SDR/Outbound`, `Unclassified`. |
| `ae_stage` | string | No | User-corrected L2 AE stage (e.g. `Discovery`, `Demo`, `Proposal`, `Negotiation`). Only relevant when `call_type = "AE/Sales"`. |

If `call_type` and/or `ae_stage` are provided, the corresponding classifier nodes are bypassed and the supplied values flow directly through the graph.

**Response** (200): Same structure as `POST /summarize`.

---

## Sample payload

### Request (POST /summarize)

```json
{
  "transcript": [
    {
      "start_time": "00:00:29",
      "end_time": "00:00:35",
      "speaker": "Anika Ahlstrom",
      "text": "Recording in progress."
    },
    {
      "start_time": "00:02:43",
      "end_time": "00:02:47",
      "speaker": "Gopinath Perkinian",
      "text": "Hi, team."
    },
    {
      "start_time": "00:02:44",
      "end_time": "00:05:48",
      "speaker": "Brian Dracup",
      "text": "Hello, everyone. Good morning. We're excited to walk through the sales engagement workflow today and show you how SDRs manage tasks, sequences, and outreach."
    }
  ],
  "metadata": {
    "topic": "Alteryx SE RFP - 2nd Demo",
    "user_map": {
      "anika@alteryx.com": "Anika Ahlstrom",
      "gopinath@aviso.com": "Gopinath Perkinian",
      "brian@aviso.com": "Brian Dracup"
    },
    "internal_domains": ["aviso.com"],
    "participant_domains": ["alteryx.com", "aviso.com"]
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
  "confidence_level": "HIGH",
  "final_summary": {
    "overview": "Second demo for Alteryx focused on sales engagement: day-in-the-life of an SDR, task management, and sequences.",
    "key_topics": ["Sales engagement workflow", "SDR task and sequence management", "Aviso vs Outreach/SalesLoft/Gainsight"],
    "next_steps": ["Internal alignment on timeline (February)", "Follow-up from prospect"]
  },
  "participant_roles": [
    { "name": "Brian Dracup", "role": "vendor_ae" },
    { "name": "Austin Brown", "role": "prospect" },
    { "name": "Gopinath Perkinian", "role": "vendor_pm" }
  ],
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

## Running

- **API:** Start the server as above; use `POST /summarize` with a JSON body, `GET /health` for liveness, `GET /health/ready` for readiness, and `GET /docs` for interactive API docs.
- **Notebooks:** Run `notebooks/graph_test.ipynb` or `notebooks/meddpicc_test.ipynb` from the project root.
