"""Environment-backed Jarvis settings."""
from __future__ import annotations
import os
from dataclasses import dataclass

@dataclass(frozen=True)
class Settings:
    local_llm_url: str = os.getenv("LOCAL_LLM_URL", "http://127.0.0.1:8080/v1")
    local_llm_model: str = os.getenv("LOCAL_LLM_MODEL", "local-model")
    project_memory_dir: str = os.getenv("JARVIS_PROJECT_MEMORY_DIR", "data/project_memory")
    require_authentication: bool = os.getenv("JARVIS_REQUIRE_AUTH", "true").lower() == "true"

settings = Settings()
