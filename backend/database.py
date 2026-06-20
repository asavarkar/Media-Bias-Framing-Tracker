from pymongo import MongoClient, ASCENDING
from pymongo.collection import Collection
from datetime import datetime
from backend.config import MONGO_URI, DB_NAME


import certifi
_client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())


def get_client() -> MongoClient:
    global _client
    if _client is None:
        _client = MongoClient(MONGO_URI)
    return _client


def get_db():
    return get_client()[DB_NAME]


def articles() -> Collection:
    return get_db()["articles"]


def clusters() -> Collection:
    return get_db()["clusters"]


def pipeline_runs() -> Collection:
    return get_db()["pipeline_runs"]


def init_indexes():
    articles().create_index([("url", ASCENDING)], unique=True)
    articles().create_index([("cluster_id", ASCENDING)])
    articles().create_index([("fetched_at", ASCENDING)])
    # Drop the old unique index if it exists (created in a previous version),
    # then recreate as non-unique. MongoDB won't let you change a unique index
    # in-place — you must drop and recreate.
    try:
        clusters().drop_index("cluster_id_1")
    except Exception:
        pass  # Index didn't exist — that's fine
    clusters().create_index([("cluster_id", ASCENDING)])


def log_pipeline_run(article_count: int):
    pipeline_runs().insert_one({
        "timestamp": datetime.utcnow(),
        "article_count": article_count,
    })
