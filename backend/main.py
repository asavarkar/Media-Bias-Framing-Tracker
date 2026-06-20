from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from backend import database as db
from backend.scheduler import create_scheduler, run_pipeline
from backend.config import HIGH_DIVERGENCE_THRESHOLD

scheduler = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global scheduler
    db.init_indexes()
    # Run pipeline once on startup
    try:
        run_pipeline()
    except Exception as e:
        print(f"Initial pipeline run failed: {e}")
    scheduler = create_scheduler()
    scheduler.start()
    yield
    if scheduler:
        scheduler.shutdown()


app = FastAPI(title="MediaLens API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/summary")
def get_summary():
    since = datetime.utcnow() - timedelta(hours=28)
    total_articles = db.articles().count_documents({"fetched_at": {"$gte": since}})

    # Average emotional intensity: map sentiment -1..1 to 0..10
    pipeline = [
        {"$match": {"fetched_at": {"$gte": since}, "sentiment_score": {"$ne": None}}},
        {"$group": {"_id": None, "avg_sentiment": {"$avg": {"$abs": "$sentiment_score"}}}},
    ]
    result = list(db.articles().aggregate(pipeline))
    avg_intensity = round((result[0]["avg_sentiment"] * 10) if result else 0.0, 1)

    high_div = db.clusters().count_documents({
        "divergence_score": {"$gte": HIGH_DIVERGENCE_THRESHOLD}
    })
    topic_count = db.clusters().count_documents({})

    return {
        "total_articles": total_articles,
        "avg_emotional_intensity": avg_intensity,
        "high_divergence_count": high_div,
        "topic_count": topic_count,
    }


@app.get("/api/topics")
def get_topics():
    # Deduplicate by label — multiple pipeline runs create multiple clusters
    # with the same label. Group by label, keep the one with the most articles.
    pipeline = [
        {"$match": {"label": {"$exists": True, "$ne": ""}}},
        {"$sort": {"article_count": -1}},
        {"$group": {
            "_id": "$label",
            "cluster_id": {"$first": "$cluster_id"},
            "label":        {"$first": "$label"},
            "article_count":  {"$first": "$article_count"},
            "divergence_score": {"$first": "$divergence_score"},
        }},
        {"$sort": {"article_count": -1}},
        {"$limit": 20},
    ]
    clusters = list(db.clusters().aggregate(pipeline))
    return [
        {
            "cluster_id": c["cluster_id"],
            "label": c.get("label", "Unknown"),
            "article_count": c.get("article_count") or 0,
            "divergence_score": c.get("divergence_score"),
        }
        for c in clusters
    ]


@app.get("/api/framing")
def get_framing(topic: str = Query(default=None)):
    query = {}
    if topic:
        # Find all clusters matching the topic label
        matching = list(db.clusters().find(
            {"label": {"$regex": topic, "$options": "i"}},
            {"cluster_id": 1}
        ))
        if matching:
            ids = [c["cluster_id"] for c in matching]
            query["cluster_id"] = {"$in": ids}

    articles = list(db.articles().find(
        {**query, "sentiment_score": {"$ne": None}, "source": {"$exists": True}},
        {"source": 1, "sentiment_score": 1, "framing_features": 1, "title": 1}
    ).limit(200))

    # Aggregate by outlet
    outlet_data: dict[str, dict] = {}
    for a in articles:
        source = a["source"]
        if source not in outlet_data:
            outlet_data[source] = {"sentiments": [], "hedge_ratios": [], "reading_ease": []}
        outlet_data[source]["sentiments"].append(a.get("sentiment_score", 0))
        ff = a.get("framing_features") or {}
        outlet_data[source]["hedge_ratios"].append(ff.get("hedge_ratio", 0))
        outlet_data[source]["reading_ease"].append(ff.get("reading_ease", 0))

    result = []
    for outlet, data in outlet_data.items():
        import numpy as np
        result.append({
            "outlet": outlet,
            "avg_sentiment": round(float(np.mean(data["sentiments"])), 3),
            "avg_hedge_ratio": round(float(np.mean(data["hedge_ratios"])), 4),
            "avg_reading_ease": round(float(np.mean(data["reading_ease"])), 2),
            "article_count": len(data["sentiments"]),
        })

    return sorted(result, key=lambda x: x["avg_sentiment"])


@app.get("/api/stories")
def get_stories(
    min_divergence: float = Query(default=5.0),
    topic: str = Query(default="all"),
):
    query: dict = {"divergence_score": {"$gte": min_divergence}}
    if topic != "all":
        query["label"] = {"$regex": topic, "$options": "i"}

    # Fetch all matching clusters then deduplicate by label in Python,
    # keeping the highest-scoring cluster per label.
    raw_clusters = list(db.clusters().find(query).sort("divergence_score", -1).limit(200))
    seen_labels: set = set()
    deduped = []
    for c in raw_clusters:
        label = c.get("label", "Unknown")
        if label not in seen_labels:
            seen_labels.add(label)
            deduped.append(c)
        if len(deduped) == 50:
            break

    stories = []
    for c in deduped:
        cluster_id = c["cluster_id"]
        sample_articles = list(db.articles().find(
            {"cluster_id": cluster_id},
            {"source": 1, "title": 1, "url": 1}
        ).limit(8))

        outlet_tags = list({a["source"] for a in sample_articles})
        headline = sample_articles[0]["title"] if sample_articles else c.get("label", "")

        stories.append({
            "cluster_id": cluster_id,
            "label": c.get("label", "Unknown"),
            "headline": headline,
            "divergence_score": c.get("divergence_score"),
            "outlet_scores": c.get("outlet_scores", {}),
            "outlet_tags": outlet_tags,
            "article_count": c.get("article_count", len(sample_articles)),
        })

    return stories


@app.get("/api/outlets")
def get_outlets():
    since = datetime.utcnow() - timedelta(hours=28)
    pipeline = [
        {"$match": {"fetched_at": {"$gte": since}, "sentiment_score": {"$ne": None}}},
        {"$group": {
            "_id": "$source",
            "article_count": {"$sum": 1},
            "avg_sentiment": {"$avg": "$sentiment_score"},
        }},
        {"$sort": {"article_count": -1}},
    ]
    results = list(db.articles().aggregate(pipeline))

    outlets = []
    for r in results:
        avg = r.get("avg_sentiment", 0) or 0
        if avg > 0.15:
            lean = "positive"
        elif avg < -0.15:
            lean = "negative"
        else:
            lean = "neutral"

        outlets.append({
            "outlet": r["_id"],
            "article_count": r["article_count"],
            "avg_sentiment": round(avg, 3),
            "lean_label": lean,
        })

    return outlets


@app.get("/api/outlets/{outlet_name}/articles")
def get_outlet_articles(outlet_name: str):
    """Return all articles from a specific outlet, for the sidebar link panel."""
    since = datetime.utcnow() - timedelta(hours=28)
    results = list(db.articles().find(
        {
            "source": outlet_name,
            "fetched_at": {"$gte": since},
            "url": {"$exists": True, "$ne": ""},
            "title": {"$exists": True, "$ne": ""},
        },
        {"title": 1, "url": 1, "published_at": 1, "sentiment_score": 1}
    ).sort("published_at", -1).limit(30))

    return [
        {
            "title": a.get("title", ""),
            "url": a.get("url", ""),
            "published_at": a.get("published_at", ""),
            "sentiment_score": a.get("sentiment_score"),
        }
        for a in results
    ]


@app.post("/api/pipeline/run")
def trigger_pipeline():
    """Manually trigger the full pipeline (for testing)."""
    try:
        run_pipeline()
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}


@app.get("/health")
def health():
    return {"status": "ok", "time": datetime.utcnow().isoformat()}
