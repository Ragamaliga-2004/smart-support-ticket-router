# Smart Support Ticket Router

A small full-stack demo that classifies a customer-support complaint with the **OpenAI Decisions API** (`gpt-6-luna`) and shows a clear three-stage routing flow.

> **Demo only** — no real ticket is created or assigned. This is not a production support platform. Classification accuracy has not been established against labelled test data. API access and billing/credits may be required.

---

## What visitors will see

Three stages on one screen:

| Stage | Name | Purpose |
| --- | --- | --- |
| 1 | **User Input** | Enter or pick a complaint, then click Analyze |
| 2 | **Decision Engine** | Live call to OpenAI Decisions API (`choice` question) |
| 3 | **Final Decision** | Model category + application routing recommendation |

The UI clearly separates:

- **Model classification** — what the API returned  
- **Application recommendation** — what this demo recommends (route vs manual review)

```
┌──────────────┐     ┌──────────────────┐     ┌─────────────────┐
│ 1. User Input│ ──► │ 2. Decision Engine│ ──► │ 3. Final Decision│
│  complaint   │     │  gpt-6-luna      │     │  route / review  │
└──────────────┘     └──────────────────┘     └─────────────────┘
```

---

## Architecture

```
Browser (React + Vite :5173)
        │  POST /api/classify  { "complaint": "..." }
        ▼
Backend (FastAPI :8000)
        │  POST https://api.openai.com/v1/decisions
        │  model: gpt-6-luna  ·  question type: choice
        ▼
OpenAI Decisions API
        │  answers[] → category, optional confidence / probabilities
        ▼
Backend JSON  →  UI stages 2 & 3
```

**Security:** `OPENAI_API_KEY` lives only on the server. The browser never calls OpenAI directly.

---

## Project structure

```
DecisionApi/
├── backend/                 # FastAPI API
│   ├── app/
│   │   ├── main.py          # POST /api/classify, GET /api/health
│   │   ├── decisions_client.py  # Decisions API call + parsing
│   │   ├── schemas.py       # Request/response models
│   │   └── config.py        # Thresholds, categories, env loading
│   ├── tests/               # Mocked unit tests (no paid API calls)
│   └── requirements.txt
├── frontend/                # React + TypeScript + Vite UI
│   ├── src/
│   │   ├── App.tsx
│   │   ├── api.ts
│   │   ├── types.ts
│   │   └── components/      # UserInput, DecisionEngine, FinalDecision
│   └── package.json
├── .env.example             # Placeholder only — copy to .env
├── .gitignore
└── README.md
```

---

## Categories

| Value | Meaning |
| --- | --- |
| `billing` | Payments, duplicate charges, invoices, refunds |
| `technical` | Login problems, software errors, product malfunctions |
| `shipping` | Delivery delays, tracking, missing packages |
| `other` | Anything else → usually manual review |

**Application policy (not the API itself):** recommend manual review when category is `other`, confidence is missing, or confidence is below `0.70`.

---

## Quick start

### Prerequisites

- Python **3.11+**
- Node.js **20+** and npm
- OpenAI API key with access to **Decisions API** and model **`gpt-6-luna`**

### 1. Clone and configure secrets

```bash
git clone https://github.com/Ragamaliga-2004/smart-support-ticket-router.git
cd smart-support-ticket-router

cp .env.example .env
```

Edit `.env`:

```env
OPENAI_API_KEY=sk-your-key-here
```

**Never commit `.env`.** Never put the key in frontend code.

### 2. Start the backend

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Health check: http://localhost:8000/api/health

### 3. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173**  
Vite proxies `/api` → `http://localhost:8000`.

---

## Demo script (5 minutes)

1. Open the app — confirm all three stages are visible.
2. Click a sample complaint, then **Analyze complaint**.
3. Watch Stage 2 move: Ready → Processing → Completed (or Error).
4. In Stage 3, point out:
   - Model classification (API answer)
   - Application recommendation (demo policy)
   - Note that **no external ticket was created**

### Sample complaints

| Complaint | Typical category |
| --- | --- |
| I was charged twice for my order. | `billing` |
| I cannot log into my account. | `technical` |
| My package has not arrived and tracking has not updated. | `shipping` |
| I would like to suggest a new product feature. | `other` |

Outputs can vary — the model classifies by meaning, not only keywords.

---

## API contract

### `POST /api/classify`

**Request**

```json
{ "complaint": "I was charged twice for my order." }
```

**Success `200`**

```json
{
  "success": true,
  "category": "billing",
  "confidence": 0.93,
  "probabilities": [
    { "value": "billing", "probability": 0.95 },
    { "value": "technical", "probability": 0.02 },
    { "value": "shipping", "probability": 0.01 },
    { "value": "other", "probability": 0.02 }
  ],
  "model": "gpt-6-luna"
}
```

`confidence` and `probabilities` may be `null` if omitted by the API. Example values above are **illustrative only**.

**Error `422` / `500` / `502` / `504`**

```json
{
  "success": false,
  "error": "Human-readable message",
  "category": null,
  "confidence": null,
  "probabilities": null,
  "model": null
}
```

The app does **not** invent a successful result when the API fails.

---

## Tests

All automated tests **mock** OpenAI. No paid API key required.

```bash
# Backend
cd backend
pytest

# Frontend
cd frontend
npm test
```

### Manual live-API checklist

1. Valid key → each sample complaint returns a category.
2. Stage 2 shows model `gpt-6-luna` and question type `choice`.
3. Stage 3 separates model classification vs application recommendation.
4. Bad key → clear error, not a fake success.
5. Empty / overlong input → validation errors.

---

## Troubleshooting

| Symptom | What to check |
| --- | --- |
| Auth failed / 401 | Invalid key, or restart backend after editing `.env` |
| Access denied / 403 | Project permissions; Decisions API + `gpt-6-luna` access |
| Rate limit / 429 | Quota, billing, or rate limits |
| Timeout / network | Connectivity / firewall |
| Model unavailable | Confirm `POST /v1/decisions` and `gpt-6-luna` — this app does not swap models |
| CORS errors | Use `http://localhost:5173` or set `CORS_ORIGIN` |

---

## Tech stack

| Layer | Choice |
| --- | --- |
| Frontend | React, TypeScript, Vite |
| Backend | Python, FastAPI, httpx |
| AI | OpenAI Decisions API (`gpt-6-luna`) |
| Tests | pytest, Vitest + Testing Library |

---

## Scope (intentionally small)

- No auth, database, queues, Docker, or ticket-system integrations
- Complaints are not stored
- Confidence values are API-reported estimates, not guarantees
- Manual-review threshold `0.70` is application policy — not statistically validated

---

## License

MIT — feel free to use this as a learning / demo project.
