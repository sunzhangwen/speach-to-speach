from __future__ import annotations

from pathlib import Path
from typing import Any


def install_local_silero_patch(repo_dir: Path, hub: Any = None) -> None:
    """Redirect the pipeline's Silero Torch Hub request to its project cache."""
    if hub is None:
        import torch

        hub = torch.hub

    if hasattr(hub, "_project_original_load"):
        return

    local_repo = repo_dir.resolve()
    if not local_repo.is_dir():
        raise FileNotFoundError(f"Local Silero repository not found: {local_repo}")

    original_load = hub.load
    hub._project_original_load = original_load

    def load(repo_or_dir: str, model: str, *args: Any, **kwargs: Any) -> Any:
        if repo_or_dir == "snakers4/silero-vad":
            return original_load(str(local_repo), model, source="local")
        return original_load(repo_or_dir, model, *args, **kwargs)

    hub.load = load
