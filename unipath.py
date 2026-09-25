import os
import sys
from pathlib import Path

def resolve_workspace_context() -> dict:
    """Discovers project root from any subfolder depth and loads active context."""
    current = Path.cwd().resolve()
    
    # Traverse upward to find anchor file
    project_root = None
    for parent in [current] + list(current.parents):
        if (parent / "Cargo.toml").exists() or (parent / ".cargo-doctor").exists():
            project_root = parent
            break

    if not project_root:
        project_root = current

    doctor_dir = project_root / ".cargo-doctor"
    
    return {
        "cwd": current,
        "project_root": project_root,
        "is_subfolder": current != project_root,
        "doctor_dir": doctor_dir,
        "blueprints": doctor_dir / "blueprints",
        "aliases": doctor_dir / "aliases",
        "tmp_sandbox": doctor_dir / "tmp"
    }