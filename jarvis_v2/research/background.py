"""Background browser research and evidence-learning orchestration."""
from __future__ import annotations
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, Future
import threading
from jarvis_v2.research.pipeline import ResearchPipeline, ResearchResult


@dataclass
class BackgroundResearchJob:
    job_id: str
    query: str
    status: str = "queued"
    result: ResearchResult | None = None
    error: str | None = None
    summary: str | None = None


class BackgroundResearchManager:
    """Run research without blocking the foreground assistant.

    The provider owns browser/search access. Results are retained as evidence;
    they are not silently promoted to permanent personal memory.
    """

    def __init__(self, pipeline: ResearchPipeline, summarizer=None, max_workers: int = 2):
        self.pipeline = pipeline
        self.summarizer = summarizer
        self._jobs: dict[str, BackgroundResearchJob] = {}
        self._lock = threading.RLock()
        self._pool = ThreadPoolExecutor(max_workers=max_workers)

    def start(self, query: str, limit: int = 5) -> BackgroundResearchJob:
        import uuid
        job = BackgroundResearchJob("research_" + uuid.uuid4().hex[:16], query)
        with self._lock:
            self._jobs[job.job_id] = job
        self._pool.submit(self._run, job.job_id, query, limit)
        return job

    def _run(self, job_id: str, query: str, limit: int) -> None:
        with self._lock:
            self._jobs[job_id].status = "running"
        try:
            result = self.pipeline.search(query, limit)
            summary = self.summarizer(result) if self.summarizer else None
            with self._lock:
                job = self._jobs[job_id]
                job.result, job.summary, job.status = result, summary, "completed"
        except Exception as exc:
            with self._lock:
                self._jobs[job_id].error, self._jobs[job_id].status = str(exc), "failed"

    def get(self, job_id: str) -> BackgroundResearchJob | None:
        with self._lock:
            return self._jobs.get(job_id)

    def wait(self, job_id: str, timeout: float | None = None) -> BackgroundResearchJob:
        import time
        started = time.time()
        while True:
            job = self.get(job_id)
            if job is None:
                raise KeyError(job_id)
            if job.status in {"completed", "failed"}:
                return job
            if timeout is not None and time.time() - started >= timeout:
                return job
            time.sleep(0.05)

    def close(self) -> None:
        self._pool.shutdown(wait=False, cancel_futures=True)
