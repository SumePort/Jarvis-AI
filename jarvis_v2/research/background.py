"""Background browser research with evidence, summarization and learning hooks."""
from __future__ import annotations
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor
import threading
import uuid
from jarvis_v2.research.pipeline import ResearchPipeline, ResearchResult
from jarvis_v2.knowledge.learning_store import LearningStore


@dataclass
class BackgroundResearchJob:
    job_id: str
    query: str
    status: str = "queued"
    result: ResearchResult | None = None
    error: str | None = None
    summary: str | None = None
    learned_fingerprint: str | None = None
    events: list[str] = field(default_factory=list)


class BackgroundResearchManager:
    """Run research off the foreground path.

    Research is evidence, not personal memory. If a LearningStore is supplied,
    only the generated synthesis is persisted as learned topic knowledge.
    """

    def __init__(self, pipeline: ResearchPipeline, summarizer=None,
                 learning_store: LearningStore | None = None, max_workers: int = 2):
        self.pipeline = pipeline
        self.summarizer = summarizer
        self.learning_store = learning_store
        self._jobs: dict[str, BackgroundResearchJob] = {}
        self._lock = threading.RLock()
        self._pool = ThreadPoolExecutor(max_workers=max_workers)

    def start(self, query: str, limit: int = 5) -> BackgroundResearchJob:
        job = BackgroundResearchJob("research_" + uuid.uuid4().hex[:16], query)
        with self._lock:
            self._jobs[job.job_id] = job
        self._pool.submit(self._run, job.job_id, query, limit)
        return job

    def _emit(self, job: BackgroundResearchJob, event: str) -> None:
        job.events.append(event)

    def _run(self, job_id: str, query: str, limit: int) -> None:
        with self._lock:
            job = self._jobs[job_id]
            job.status = "running"
            self._emit(job, "started")
        try:
            result = self.pipeline.search(query, limit)
            with self._lock:
                self._emit(self._jobs[job_id], f"sources:{len(result.sources)}")

            summary = self.summarizer(result) if self.summarizer else result.synthesis_context
            learned = None
            if self.learning_store and summary:
                learned = self.learning_store.learn(
                    query, summary, [source.url for source in result.sources]
                )

            with self._lock:
                job = self._jobs[job_id]
                job.result = result
                job.summary = summary
                job.learned_fingerprint = learned.fingerprint if learned else None
                job.status = "completed"
                self._emit(job, "learned" if learned else "completed")
        except Exception as exc:
            with self._lock:
                job = self._jobs[job_id]
                job.error = str(exc)
                job.status = "failed"
                self._emit(job, "failed")

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
