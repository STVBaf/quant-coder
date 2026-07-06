"""Bridge the research loop to the DB in a background thread.

No Celery/broker: research is long (minutes) but low-volume, so we run each task
in a daemon thread and persist progress as `ResearchIteration` rows. The frontend
polls the task's status + iterations. Django's DB connection is per-thread, so we
close it at the end to avoid leaking connections.
"""
import threading
from concurrent.futures import ThreadPoolExecutor

from django.db import close_old_connections

from .loop import run_research


def _make_event_sink(task_id: int, executor: ThreadPoolExecutor):
    """Return an on_event(kind, payload) that appends ordered iteration rows.

    The loop calls this from inside an asyncio event loop, where Django forbids
    synchronous ORM. We offload each write to a single-worker executor thread
    (no running event loop there) and block until it finishes, which both
    satisfies Django's async-safety check and preserves iteration order.
    """
    from ..models import ResearchIteration

    counter = {"n": 0}

    def _write(seq: int, kind: str, payload: dict):
        ResearchIteration.objects.create(
            task_id=task_id, seq=seq, kind=kind, payload=payload
        )

    def on_event(kind: str, payload: dict):
        counter["n"] += 1
        executor.submit(_write, counter["n"], kind, payload).result()

    return on_event


def _worker(task_id: int):
    from ..models import ResearchTask

    close_old_connections()
    task = ResearchTask.objects.get(id=task_id)
    task.status = "running"
    task.save(update_fields=["status", "updated_at"])

    # Single-thread executor: ORM writes run here, off the event loop thread.
    executor = ThreadPoolExecutor(max_workers=1)
    on_event = _make_event_sink(task_id, executor)
    try:
        report = run_research(task.prompt, task.codes, on_event)
        task.report = report or ""
        task.status = "done"
    except Exception as e:  # surface failure to the UI, don't crash the thread
        task.error = f"{type(e).__name__}: {e}"
        task.status = "failed"
        on_event("status", {"stage": "failed", "error": task.error})
    finally:
        task.save()
        executor.shutdown(wait=True)
        close_old_connections()


def start_task(task_id: int):
    """Kick off the research loop in a daemon thread and return immediately."""
    t = threading.Thread(target=_worker, args=(task_id,), daemon=True)
    t.start()
