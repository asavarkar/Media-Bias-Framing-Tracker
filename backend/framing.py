import spacy
import textstat
from transformers import pipeline as hf_pipeline
from backend import database as db

_sentiment_pipe = None
_nlp = None

HEDGE_WORDS = {
    "may", "might", "could", "possibly", "allegedly", "reportedly",
    "appears", "seems", "suggests", "claims", "according", "purportedly",
    "supposedly", "ostensibly", "perhaps", "maybe",
}


def get_sentiment_pipe():
    global _sentiment_pipe
    if _sentiment_pipe is None:
        _sentiment_pipe = hf_pipeline(
            "sentiment-analysis",
            model="cardiffnlp/twitter-roberta-base-sentiment-latest",
            truncation=True,
            max_length=512,
        )
    return _sentiment_pipe


def get_nlp():
    global _nlp
    if _nlp is None:
        _nlp = spacy.load("en_core_web_sm")
    return _nlp


def get_sentiment(text: str) -> float:
    text = text.strip()
    if not text:
        return 0.0
    try:
        result = get_sentiment_pipe()(text[:512])[0]
        label = result["label"].lower()
        score = result["score"]
        if "negative" in label:
            return -score
        elif "positive" in label:
            return score
        return 0.0
    except Exception as e:
        print(f"Sentiment error: {e}")
        return 0.0


def extract_framing_features(text: str) -> dict:
    if not text:
        return {
            "hedge_ratio": 0.0,
            "passive_ratio": 0.0,
            "reading_ease": 0.0,
            "avg_sentence_length": 0.0,
        }
    nlp = get_nlp()
    doc = nlp(text[:2000])
    tokens = [t for t in doc if not t.is_punct and not t.is_space]

    hedge_count = sum(1 for t in tokens if t.lemma_.lower() in HEDGE_WORDS)
    hedge_ratio = hedge_count / max(len(tokens), 1)

    passive_count = sum(
        1 for token in doc
        if token.dep_ in ("nsubjpass", "auxpass")
    )
    sents = list(doc.sents)
    passive_ratio = passive_count / max(len(sents), 1)

    try:
        reading_ease = textstat.flesch_reading_ease(text)
    except Exception:
        reading_ease = 0.0

    avg_sent_len = sum(len(list(s)) for s in sents) / max(len(sents), 1)

    return {
        "hedge_ratio": round(hedge_ratio, 4),
        "passive_ratio": round(passive_ratio, 4),
        "reading_ease": round(reading_ease, 2),
        "avg_sentence_length": round(avg_sent_len, 2),
    }


def run_framing():
    print("Starting framing analysis...")
    unanalyzed = list(db.articles().find({
        "sentiment_score": None,
        "title": {"$exists": True, "$ne": ""},
    }))

    count = 0
    for article in unanalyzed:
        text = " ".join(filter(None, [
            article.get("title", ""),
            article.get("description", ""),
            article.get("content", ""),
        ]))

        sentiment = get_sentiment(text[:512])
        features = extract_framing_features(text)

        db.articles().update_one(
            {"_id": article["_id"]},
            {"$set": {
                "sentiment_score": sentiment,
                "framing_features": features,
            }}
        )
        count += 1

    print(f"Framing complete: {count} articles analyzed")
