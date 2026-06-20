import numpy as np
from backend import database as db
from backend.config import MIN_OUTLETS_FOR_SCORING


def compute_cluster_divergence(articles_in_cluster: list[dict]) -> tuple[float | None, dict]:
    outlet_sentiments: dict[str, list[float]] = {}
    for article in articles_in_cluster:
        source = article.get("source", "unknown")
        score = article.get("sentiment_score")
        if score is None:
            continue
        outlet_sentiments.setdefault(source, []).append(score)

    if len(outlet_sentiments) < MIN_OUTLETS_FOR_SCORING:
        return None, {}

    outlet_means = {
        outlet: float(np.mean(scores))
        for outlet, scores in outlet_sentiments.items()
    }

    std_dev = float(np.std(list(outlet_means.values())))
    divergence_score = round(min(std_dev * 10, 10.0), 2)

    return divergence_score, outlet_means


def run_scoring():
    print("Starting divergence scoring...")
    all_clusters = list(db.clusters().find({}))
    scored = 0

    for cluster in all_clusters:
        cluster_id = cluster["cluster_id"]
        cluster_articles = list(db.articles().find({
            "cluster_id": cluster_id,
            "sentiment_score": {"$ne": None},
        }))

        if not cluster_articles:
            continue

        divergence_score, outlet_means = compute_cluster_divergence(cluster_articles)

        db.clusters().update_one(
            {"cluster_id": cluster_id},
            {"$set": {
                "divergence_score": divergence_score,
                "outlet_scores": outlet_means,
                "article_count": len(cluster_articles),
            }}
        )
        scored += 1

    print(f"Scoring complete: {scored} clusters scored")
