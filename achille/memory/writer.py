"""
Achille — Memory Writer
Écrit et met à jour les fichiers MD dans le brain repo.
"""
import os
import subprocess
from datetime import datetime
from pathlib import Path
from config.settings import BRAIN_REPO_PATH


def write(filepath: str, content: str) -> None:
    """Écrit (écrase) un fichier MD."""
    full_path = Path(BRAIN_REPO_PATH) / filepath
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content, encoding="utf-8")


def append(filepath: str, content: str) -> None:
    """Ajoute du contenu à la fin d'un fichier MD."""
    full_path = Path(BRAIN_REPO_PATH) / filepath
    full_path.parent.mkdir(parents=True, exist_ok=True)
    
    existing = ""
    if full_path.exists():
        existing = full_path.read_text(encoding="utf-8")
    
    full_path.write_text(existing + "\n" + content, encoding="utf-8")


def append_journal_entry(text: str) -> None:
    """Ajoute une entrée au journal du jour."""
    today = datetime.now().strftime("%Y-%m-%d")
    filepath = f"journal/{today}.md"
    full_path = Path(BRAIN_REPO_PATH) / filepath
    
    if not full_path.exists():
        header = f"# Journal — {today}\n\n"
        write(filepath, header)
    
    timestamp = datetime.now().strftime("%H:%M")
    append(filepath, f"\n### {timestamp}\n{text}\n")


def auto_commit(message: str = "auto: conversation update") -> bool:
    """Git add + commit + push."""
    try:
        cwd = BRAIN_REPO_PATH
        
        # Add all changes
        subprocess.run(
            ["git", "add", "-A"],
            cwd=cwd, check=True, capture_output=True
        )
        
        # Check if there are changes to commit
        result = subprocess.run(
            ["git", "diff", "--cached", "--quiet"],
            cwd=cwd, capture_output=True
        )
        
        if result.returncode == 0:
            # Nothing to commit
            return False
        
        # Commit
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        subprocess.run(
            ["git", "commit", "-m", f"{message} ({timestamp})"],
            cwd=cwd, check=True, capture_output=True
        )
        
        # Push (non-blocking, fire and forget)
        subprocess.Popen(
            ["git", "push", "origin", "main"],
            cwd=cwd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"[git error] {e}")
        return False
