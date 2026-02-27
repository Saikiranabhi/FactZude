# FactZude — AI Fact Checker

> An AI-powered fact-checking web app that verifies any claim in real-time by searching the web, analysing evidence with a large language model, and returning a clear verdict with a confidence score and sources.

---

## Features

- **Real-time web search** via Tavily API to gather up-to-date evidence
- **AI-powered reasoning** using LLaMA 3.3 70B (via Groq) to analyse evidence
- **Structured verdicts** — True, False, or Uncertain with a 0–100% confidence score
- **Source links** — every result includes clickable references from the web
- **Split-panel UI** — clean input on the left, live result on the right
- **Fast async backend** — non-blocking LLM and search calls via FastAPI
- **Docker + Nginx ready** — production-deployable out of the box
- **AWS ECS CI/CD** — GitHub Actions workflow for automated deployment

---

## Tech Stack

| Layer       | Technology                          |
|-------------|-------------------------------------|
| Frontend    | HTML, CSS, Vanilla JS               |
| Backend     | FastAPI, Python 3.11                |
| LLM         | LLaMA 3.3 70B via Groq API          |
| Web Search  | Tavily Search API (LangChain)       |
| AI Framework| LangChain, LangChain-Groq           |
| Server      | Uvicorn (ASGI)                      |
| Proxy       | Nginx                               |
| Container   | Docker, Docker Compose              |
| CI/CD       | GitHub Actions → AWS ECS            |

---

## Folder Structure

```
ai_fact_checker/
│
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI app entry point, CORS, router
│   ├── routes.py        # API endpoint definitions
│   ├── workflow.py      # Core fact-check logic (search + LLM)
│   ├── prompts.py       # LLM prompt template
│   ├── models.py        # Pydantic request/response models
│   ├── utils.py         # PDF text extraction utility
│   └── sse.py           # Server-Sent Events helper
│
├── frontend/
│   ├── index.html       # Split-panel UI
│   ├── style.css        # All styles and responsive layout
│   └── app.js           # Fetch logic, state management, rendering
│
├── infra/
│   ├── docker-compose.yml   # App + Nginx services
│   └── nginx.conf           # Reverse proxy config
│
├── .github/
│   └── workflows/
│       └── deploy.yml   # AWS ECS deployment pipeline
│
├── Dockerfile
├── requirements.txt
├── .env                 # (not committed) API keys
├── .gitignore
├── .dockerignore
└── README.md
```

---

## Environment Variables

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
```

| Variable         | Description                              | Get it from                          |
|------------------|------------------------------------------|--------------------------------------|
| `GROQ_API_KEY`   | API key for Groq LLM inference           | https://console.groq.com             |
| `TAVILY_API_KEY` | API key for Tavily real-time web search  | https://app.tavily.com               |

---

## Installation

### Prerequisites
- Python 3.10+
- pip
- (Optional) Docker + Docker Compose

### 1. Clone the repository

```bash
git clone https://github.com/Saikiranabhi/factzude.git
cd factzude/ai_fact_checker
```

### 2. Create a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
uv pip install -r requirements.txt
```

### 4. Create your `.env` file

```bash
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

Then open `.env` and fill in your API keys.

---

## How to Run

### Local Development (two terminals)

**Terminal 1 — Start the backend:**

```bash
cd ai_fact_checker
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS/Linux

uvicorn app.main:app --reload
```

Backend runs at: `http://127.0.0.1:8000`

**Terminal 2 — Serve the frontend:**

```bash
cd ai_fact_checker/frontend
python -m http.server 5500
```

Live Demo of website: 

> https://factzude-2.onrender.com/

---

### Docker (Production)

**Build and run with Docker Compose:**

```bash
cd ai_fact_checker/infra
docker-compose up --build
```

This starts:
- `ai_fact_checker` — FastAPI app on internal port 8000
- `ai_fact_checker_nginx` — Nginx reverse proxy on port 80

App is available at: `http://localhost`

**Run backend only with Docker:**

```bash
docker build -t ai-fact-checker .
docker run -p 8000:8000 --env-file .env ai-fact-checker
```

---

## API Endpoints

### `GET /`
Health check.

**Response:**
```json
{ "status": "running" }
```

---

### `POST /fact-check`
Verify a claim using AI and web search.

**Request body:**
```json
{
  "claim": "The Great Wall of China is visible from space."
}
```

**Response:**
```json
{
  "claim": "The Great Wall of China is visible from space.",
  "verdict": "False",
  "confidence": 0.92,
  "explanation": "Multiple authoritative sources including NASA confirm the Great Wall is too narrow to be seen from space with the naked eye.",
  "sources": [
    {
      "title": "NASA - Visibility of the Great Wall from Space",
      "url": "https://www.nasa.gov/..."
    }
  ]
}
```

**Verdict values:** `True` | `False` | `Uncertain`  
**Confidence:** Float between `0.0` and `1.0`

---

## Example Usage

**Via browser:** Open `http://localhost:5500`, type a claim, click **Verify**.

**Via Python:**
```python
import requests

res = requests.post("http://127.0.0.1:8000/fact-check", json={
    "claim": "Humans only use 10% of their brain."
})
print(res.json())
```

---

## CI/CD — AWS ECS Deployment

The GitHub Actions workflow (`.github/workflows/deploy.yml`) automatically deploys on every push to `main`.

**Required GitHub Secrets:**

| Secret               | Description                        |
|----------------------|------------------------------------|
| `AWS_ACCESS_KEY_ID`  | AWS IAM access key                 |
| `ECR_REPO`           | Full ECR image URI                 |
| `ECS_CLUSTER_NAME`   | Name of your ECS cluster           |
| `ECS_SERVICE_NAME`   | Name of your ECS service           |

Set these in: **GitHub repo → Settings → Secrets and variables → Actions**

---

## Interactive API Docs

FastAPI auto-generates interactive docs while the server is running:
