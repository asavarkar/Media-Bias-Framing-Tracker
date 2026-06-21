# MediaLens (News Framing Analyzer)

A full-stack NLP application that automatically ingests news articles from 7 major outlets every 4 hours, uses machine learning to cluster articles about the same event, and quantifies how differently each outlet frames that event, highlighting the stories where coverage diverges most sharply across the media landscape.

---

## Architecture

```
NewsAPI + RSS Feeds
        │
        ▼
  ingestion.py          ← Fetches & deduplicates articles into MongoDB
        │
        ▼
  clustering.py         ← Embeds text with all-MiniLM-L6-v2, clusters with K-means
        │
        ▼
  framing.py            ← RoBERTa sentiment scoring + spaCy linguistic features
        │
        ▼
  scoring.py            ← Computes per-cluster divergence score (std dev of outlet sentiments)
        │
        ▼
  FastAPI backend       ← Serves processed data via REST API
        │
        ▼
  React + Chart.js      ← Live dashboard
```

The full pipeline reruns every 4 hours via APScheduler, no manual intervention needed.

---

## Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| Data ingestion | Python + NewsAPI + feedparser | Fetch articles from 7 outlets |
| Embeddings | sentence-transformers (`all-MiniLM-L6-v2`) | Convert text to 384-dim vectors |
| Clustering | scikit-learn K-means | Group articles by event |
| Sentiment | HuggingFace `cardiffnlp/twitter-roberta-base-sentiment-latest` | Per-article sentiment scoring |
| Linguistic features | spaCy + textstat | Hedge ratio, passive voice, readability |
| Database | MongoDB (Atlas or local) | Store articles, clusters, scores |
| Backend API | FastAPI + Uvicorn | Serve data to frontend |
| Scheduler | APScheduler | Run pipeline every 4 hours |
| Frontend | React + Chart.js + Axios | Dashboard UI |

---

## Features

- **Automatic ingestion**: from CNN, BBC News, Fox News, NPR, Politico, The Guardian, and ABC News
- **Semantic clustering**: groups articles about the same event using sentence embeddings, not keyword matching
- **Divergence scoring**: standard deviation of outlet-level mean sentiments per cluster, scaled 0–10
- **Framing features**: hedge ratio, passive voice ratio, Flesch reading ease, average sentence length per article
- **Live dashboard** with four views:
  - Metric cards (articles today, emotional intensity, high-divergence count, topics clustered)
  - Topic bar chart (story clusters sized by coverage volume, colored red if high-divergence)
  - Outlet framing chart (per-outlet sentiment for any selected topic)
  - High-divergence story table (outlet tags, divergence dots, numeric score)
- **ML-derived outlet lean labels**: computed from daily sentiment averages, not hardcoded

---

## Project Structure

```
medialens/
├── backend/
│   ├── main.py          # FastAPI app, all API routes, lifespan startup
│   ├── ingestion.py     # NewsAPI + RSS fetch, merge, MongoDB upsert
│   ├── clustering.py    # Embeddings, K-means clustering, cluster labeling
│   ├── framing.py       # RoBERTa sentiment + spaCy linguistic features
│   ├── scoring.py       # Divergence score computation
│   ├── scheduler.py     # APScheduler setup, pipeline orchestration
│   ├── database.py      # MongoDB connection, collection helpers, indexes
│   └── config.py        # Constants and environment variable loading
├── frontend/
│   ├── src/
│   │   ├── App.jsx               # Root component, page layout
│   │   ├── main.jsx              # React entry point
│   │   ├── api.js                # Axios calls to FastAPI
│   │   ├── index.css             # All styles
│   │   └── components/
│   │       ├── MetricCards.jsx
│   │       ├── TopicBarChart.jsx
│   │       ├── FramingDivergenceChart.jsx
│   │       ├── StoryTable.jsx
│   │       └── OutletSidebar.jsx
│   ├── index.html
│   └── package.json
├── .env.example
├── requirements.txt
└── README.md
```

---

## Setup & Installation

### Prerequisites

- Python 3.10+
- Node.js 18+
- MongoDB (local) or a [MongoDB Atlas](https://www.mongodb.com/atlas) free-tier account
- A free [NewsAPI](https://newsapi.org) key

### 1. Clone the repository

```bash
git clone https://github.com/asavarkar/Media-Bias-Framing-Tracker.git
cd Media-Bias-Framing-Tracker
```

### 2. Python environment

```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### 3. Environment variables

```bash
cp .env.example .env
```

Open `.env` and fill in your values:

```
NEWSAPI_KEY=your_newsapi_key_here
MONGO_URI=mongodb://localhost:27017        # or your Atlas URI
```

### 4. Run the backend

```bash
uvicorn backend.main:app --reload --port 8000
```

On first startup, the server will:
1. Initialize MongoDB indexes
2. Run the full pipeline immediately (fetch → embed → cluster → score)
3. Start the 4-hour scheduler

**Note:** The first pipeline run loads two ML models (sentence-transformer + RoBERTa) and may take 3–8 minutes on CPU. Subsequent runs are faster as models stay loaded in memory.

### 5. Run the frontend

```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:5173`. The dashboard will populate once the first pipeline run completes.

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/summary` | Total articles, avg emotional intensity, high-divergence count, topic count |
| GET | `/api/topics` | All story clusters sorted by article count |
| GET | `/api/framing?topic=Britain` | Per-outlet sentiment for a specific topic (or all topics) |
| GET | `/api/stories?min_divergence=5.0` | High-divergence stories with outlet tags and scores |
| GET | `/api/outlets` | All outlets with article count and ML-derived lean label |
| POST | `/api/pipeline/run` | Manually trigger the full pipeline |
| GET | `/health` | Server health check |

---

## How the Divergence Score Works

For each story cluster:

1. Group all articles by outlet
2. Compute each outlet's mean sentiment score (range: −1.0 to +1.0)
3. Compute the standard deviation across outlet means
4. Scale by 10: `divergence_score = min(std_dev × 10, 10.0)`

**Example:** A cluster where CNN scores −0.6, Fox News scores +0.3, and NPR scores 0.0 has outlet means spread across a range of 0.9 — producing a divergence score of ~5.2. A cluster where all outlets score near −0.2 would score near 0.

Clusters are only scored when covered by 3 or more outlets. Stories scoring ≥ 5.0 are surfaced in the high-divergence table.

---

## Outlets Covered

| Outlet | Source | Status |
|---|---|---|
| CNN | RSS | Active |
| BBC News | RSS | Active |
| Fox News | RSS | Active |
| NPR | RSS | Active |
| Politico | RSS | Active |
| The Guardian | RSS | Active |
| ABC News | RSS | Active |

---

## Deployment (Render.com + MongoDB Atlas Free Tier)

### Backend

1. Push this repo to GitHub
2. Create a [Render](https://render.com) Web Service connected to your repo
3. Set start command: `uvicorn backend.main:app --host 0.0.0.0 --port 8000`
4. Add environment variables in the Render dashboard:
   - `NEWSAPI_KEY`
   - `MONGO_URI` (your Atlas connection string)

### Frontend

1. In `frontend/src/api.js`, the `VITE_API_URL` environment variable controls the backend URL
2. In Render, create a new environment variable: `VITE_API_URL=https://your-backend.onrender.com`
3. Build the frontend: `npm run build`
4. Create a Render Static Site pointed at `frontend/dist`

---

## Built With

Python · FastAPI · MongoDB · HuggingFace Transformers · sentence-transformers · scikit-learn · spaCy · React · Chart.js · Axios · APScheduler
