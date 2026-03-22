"""
Achille — Memory Reader
Lit les fichiers Markdown depuis le repo brain.
"""
import os
from pathlib import Path
from config.settings import BRAIN_REPO_PATH


def read(filepath: str, summary: bool = False) -> str:
    """Lit un fichier MD depuis le brain repo."""
    full_path = Path(BRAIN_REPO_PATH) / filepath
    if not full_path.exists():
        return f"[fichier introuvable: {filepath}]"
    
    content = full_path.read_text(encoding="utf-8")
    
    if summary and len(content) > 2000:
        # Garder les 50 premières lignes comme résumé
        lines = content.split("\n")
        content = "\n".join(lines[:50]) + "\n\n[... tronqué pour le contexte]"
    
    return content


def list_files(directory: str = "") -> list[str]:
    """Liste les fichiers MD dans un dossier du brain repo."""
    dir_path = Path(BRAIN_REPO_PATH) / directory
    if not dir_path.exists():
        return []
    
    files = []
    for f in dir_path.rglob("*.md"):
        relative = f.relative_to(BRAIN_REPO_PATH)
        files.append(str(relative))
    return sorted(files)


def read_index() -> str:
    """Lit INDEX.md — toujours chargé."""
    return read("INDEX.md")


def read_system_prompt() -> str:
    """Lit SYSTEM_PROMPT.md — toujours chargé."""
    return read("SYSTEM_PROMPT.md")


def read_sycophancy_protocol() -> str:
    """Lit SYCOPHANCY.md en résumé — toujours chargé."""
    return read("SYCOPHANCY.md", summary=True)


def read_contradictions() -> str:
    """Lit contradictions.md — toujours chargé."""
    return read("open-questions/contradictions.md")


def read_facts() -> str:
    """Lit profile/facts.md — toujours chargé."""
    return read("profile/facts.md")


def estimate_tokens(text: str) -> int:
    """Estimation grossière : ~4 chars par token en français."""
    return len(text) // 4
