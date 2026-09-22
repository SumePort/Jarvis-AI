from jarvis_v2.research.background import BackgroundResearchManager
from jarvis_v2.research.pipeline import ResearchPipeline, ResearchSource
from jarvis_v2.knowledge.learning_store import LearningStore

class Provider:
    def search(self, query, limit=5):
        return [ResearchSource("Source", "https://example.com", "evidence")]

def test_background_research_learns(tmp_path):
    store = LearningStore(tmp_path / "learned.jsonl")
    manager = BackgroundResearchManager(
        ResearchPipeline(Provider()),
        summarizer=lambda result: "validated synthesis",
        learning_store=store,
    )
    job = manager.start("new ai technology")
    done = manager.wait(job.job_id, 2)
    assert done.status == "completed"
    assert done.summary == "validated synthesis"
    assert done.learned_fingerprint
    assert store.latest("new ai technology").summary == "validated synthesis"
    manager.close()
