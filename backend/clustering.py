import uuid
from datetime import datetime, timedelta
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import normalize
from sentence_transformers import SentenceTransformer
import spacy
from backend import database as db

_embed_model = None
_nlp = None


def get_embed_model():
    global _embed_model
    if _embed_model is None:
        _embed_model = SentenceTransformer("all-MiniLM-L6-v2")
    return _embed_model


def get_nlp():
    global _nlp
    if _nlp is None:
        _nlp = spacy.load("en_core_web_sm")
    return _nlp


def embed_articles(articles: list[dict]) -> np.ndarray:
    model = get_embed_model()
    texts = [f"{a['title']}. {a.get('description') or ''}" for a in articles]
    return model.encode(texts, batch_size=32, show_progress_bar=False)


def cluster_embeddings(embeddings: np.ndarray, n_clusters: int) -> list[int]:
    normed = normalize(embeddings)
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    return kmeans.fit_predict(normed).tolist()


def generate_cluster_label(articles: list[dict]) -> str:
    """Extract the most common named entity or noun phrase from titles."""
    nlp = get_nlp()
    entity_counts: dict[str, int] = {}
    for a in articles:
        doc = nlp(a.get("title", "")[:200])
        for ent in doc.ents:
            if ent.label_ in ("PERSON", "ORG", "GPE", "EVENT", "NORP", "LOC"):
                entity_counts[ent.text] = entity_counts.get(ent.text, 0) + 1
    if entity_counts:
        return max(entity_counts, key=entity_counts.get)
    # Fallback: most common noun chunk
    noun_counts: dict[str, int] = {}
    for a in articles:
        doc = nlp(a.get("title", "")[:200])
        for chunk in doc.noun_chunks:
            text = chunk.text.strip()
            if len(text) > 3:
                noun_counts[text] = noun_counts.get(text, 0) + 1
    if noun_counts:
        return max(noun_counts, key=noun_counts.get)
    return "Miscellaneous"


def run_clustering():
    print("Starting clustering...")
    since = datetime.utcnow() - timedelta(hours=28)
    articles = list(db.articles().find({
        "fetched_at": {"$gte": since},
        "title": {"$exists": True, "$ne": ""},
    }))

    if len(articles) < 5:
        print(f"Not enough articles to cluster: {len(articles)}")
        return

    embeddings = embed_articles(articles)

    # Save embeddings back to articles
    for article, emb in zip(articles, embeddings):
        db.articles().update_one(
            {"_id": article["_id"]},
            {"$set": {"embedding": emb.tolist()}}
        )

    n_clusters = max(5, len(articles) // 15)
    labels = cluster_embeddings(embeddings, n_clusters)

    # Group by cluster label
    cluster_groups: dict[int, list] = {}
    for article, label in zip(articles, labels):
        cluster_groups.setdefault(label, []).append(article)

    # Write cluster docs and update articles
    for label_idx, group in cluster_groups.items():
        cluster_id = str(uuid.uuid4())
        cluster_label = generate_cluster_label(group)
        article_ids = [str(a["_id"]) for a in group]

        db.clusters().update_one(
            {"cluster_id": cluster_id},
            {"$set": {
                "cluster_id": cluster_id,
                "label": cluster_label,
                "article_ids": article_ids,
                "divergence_score": None,
                "outlet_scores": {},
                "created_at": datetime.utcnow(),
            }},
            upsert=True,
        )

        for article in group:
            db.articles().update_one(
                {"_id": article["_id"]},
                {"$set": {"cluster_id": cluster_id}}
            )

    print(f"Clustering complete: {n_clusters} clusters from {len(articles)} articles")
