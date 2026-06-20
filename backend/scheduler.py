from apscheduler.schedulers.background import BackgroundScheduler
from backend.config import PIPELINE_INTERVAL_HOURS


def run_pipeline():
    print("=== Running MediaLens pipeline ===")
    try:
        from backend.ingestion import run_ingestion
        from backend.clustering import run_clustering
        from backend.framing import run_framing
        from backend.scoring import run_scoring

        run_ingestion()
        run_clustering()
        run_framing()
        run_scoring()
        print("=== Pipeline complete ===")
    except Exception as e:
        print(f"Pipeline error: {e}")
        raise


def create_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        run_pipeline,
        "interval",
        hours=PIPELINE_INTERVAL_HOURS,
        id="medialens_pipeline",
        replace_existing=True,
    )
    return scheduler
