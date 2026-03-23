"""
Achille — Memory Consolidator
Runs nightly at 3AM. Orchestrates 7 sub-tasks:
1. Deduplicate facts across memory files
2. Archive old journal entries
3. Split large files
4. Update INDEX.md
5. Check for resolved contradictions
6. Detect belief confidence shifts
7. Write consolidation report
"""
import json
import os
import re
import subprocess
import uuid
from datetime import datetime, timedelta
from glob import glob
from pathlib import Path
from zoneinfo import ZoneInfo

from bot.notify import notify_error
from bot.sender import send
from brain.responder import generate_with_model
from config.settings import (
    BELIEF_SHIFT_THRESHOLD,
    BRAIN_REPO_PATH,
    CONSOLIDATION_REPORT_PATH,
    JOURNAL_ARCHIVE_AFTER_DAYS,
    MAX_ASSISTED_PINGS_PER_DAY,
    MODELS,
    SPLIT_THRESHOLD_LINES,
    TIMEZONE,
)
from memory.consolidation_state import add_pending
from memory.reader import list_files, read, read_header
from memory.writer import auto_commit_targeted, write

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

OPUS = MODELS[3]
SONNET = MODELS[2]

MEMORY_DIRS = ["profile", "work", "health", "relations", "open-questions", "projects"]
DEDUP_EXCLUDE = {"profile/beliefs.md", "profile/inherited.md"}


def _count_content_lines(text: str) -> int:
    """Count non-blank lines, excluding YAML frontmatter."""
    body = text
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            body = text[end + 4:]
    return sum(1 for line in body.splitlines() if line.strip())


def _scan_memory_files(dirs: list[str], exclude: set[str] | None = None) -> list[str]:
    """Glob .md files in given brain-repo subdirectories. Returns relative paths."""
    exclude = exclude or set()
    results: list[str] = []
    for d in dirs:
        results.extend(list_files(d))
    return [f for f in results if f not in exclude]


def _read_raw(filepath: str) -> str:
    """Read a brain-repo file INCLUDING frontmatter."""
    full_path = Path(BRAIN_REPO_PATH) / filepath
    if not full_path.exists():
        return ""
    return full_path.read_text(encoding="utf-8")


def _write_preserving_frontmatter(filepath: str, new_body: str, old_raw: str) -> None:
    """Write new body content, keeping original YAML frontmatter if present."""
    frontmatter = ""
    if old_raw.startswith("---"):
        end = old_raw.find("\n---", 3)
        if end != -1:
            frontmatter = old_raw[: end + 4] + "\n\n"
    write(filepath, frontmatter + new_body)


def _parse_json(text: str) -> dict | None:
    """Parse JSON from LLM output, stripping markdown code fences if present."""
    cleaned = text.strip()
    # Strip ```json ... ``` wrapper
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```\w*\n?", "", cleaned)
        cleaned = re.sub(r"\n?```\s*$", "", cleaned)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return None


def _timestamp() -> str:
    """Return current timestamp string for commit messages."""
    return datetime.now(ZoneInfo(TIMEZONE)).strftime("%Y-%m-%d %H:%M")


# ---------------------------------------------------------------------------
# Sub-task 1 — Deduplicate facts
# ---------------------------------------------------------------------------

async def deduplicate_facts(report: dict) -> dict:
    """Scan memory files for semantic duplicates and remove them."""
    files = _scan_memory_files(MEMORY_DIRS, exclude=DEDUP_EXCLUDE)
    files_processed = 0
    duplicates_removed = 0
    details: list[str] = []

    for filepath in files:
        raw = _read_raw(filepath)
        body = read(filepath)  # stripped of frontmatter
        if not body.strip():
            continue

        prompt = (
            "Analyse le fichier Markdown suivant. Identifie les doublons sémantiques "
            "(lignes ou bullet points qui disent la même chose avec des mots différents).\n\n"
            "Retourne UNIQUEMENT un JSON valide :\n"
            '{"has_duplicates": true/false, "cleaned_content": "le contenu sans doublons", '
            '"duplicates_found": ["description courte de chaque doublon supprimé"]}\n\n'
            "Si aucun doublon, retourne has_duplicates: false et cleaned_content identique.\n\n"
            f"Contenu :\n```\n{body}\n```"
        )

        result_text = await generate_with_model(prompt, OPUS)
        parsed = _parse_json(result_text)
        if not parsed:
            details.append(f"{filepath}: LLM output parse error, skipped")
            continue

        files_processed += 1
        if parsed.get("has_duplicates") and parsed.get("cleaned_content"):
            dupes = parsed.get("duplicates_found", [])
            _write_preserving_frontmatter(filepath, parsed["cleaned_content"], raw)
            auto_commit_targeted(
                f"consolidation: dedup {filepath}",
                [filepath],
            )
            duplicates_removed += len(dupes)
            details.append(f"{filepath}: removed {len(dupes)} duplicate(s)")
        else:
            details.append(f"{filepath}: no duplicates")

    return {
        "status": "ok",
        "files_processed": files_processed,
        "duplicates_removed": duplicates_removed,
        "details": details,
    }


# ---------------------------------------------------------------------------
# Sub-task 2 — Archive journals
# ---------------------------------------------------------------------------

async def archive_journals(report: dict) -> dict:
    """Summarize and archive old journal files."""
    tz = ZoneInfo(TIMEZONE)
    now = datetime.now(tz)
    cutoff = now - timedelta(days=JOURNAL_ARCHIVE_AFTER_DAYS)
    today_str = now.strftime("%Y-%m-%d")
    yesterday_str = (now - timedelta(days=1)).strftime("%Y-%m-%d")

    journal_files = list_files("journal")
    # Only direct journal entries (YYYY-MM-DD.md), skip archive/ and subdirs
    pattern = re.compile(r"^journal/(\d{4}-\d{2}-\d{2})\.md$")
    archived = 0
    details: list[str] = []

    for filepath in journal_files:
        m = pattern.match(filepath)
        if not m:
            continue
        date_str = m.group(1)
        # Skip today and yesterday
        if date_str in (today_str, yesterday_str):
            continue
        try:
            file_date = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=tz)
        except ValueError:
            continue
        if file_date >= cutoff:
            continue

        body = read(filepath)
        if not body.strip():
            continue

        # Summarize with Sonnet
        prompt = (
            "Résume ce journal en 2-3 lignes concises (format bullet points). "
            "Garde les faits saillants, supprime les détails.\n\n"
            f"Date : {date_str}\n\n"
            f"Contenu :\n```\n{body}\n```\n\n"
            "Retourne UNIQUEMENT le résumé, pas de JSON."
        )
        summary = await generate_with_model(prompt, SONNET)
        if not summary.strip():
            details.append(f"{filepath}: summarization failed, skipped")
            continue

        # Append to monthly archive
        month_key = date_str[:7]  # YYYY-MM
        archive_path = f"journal/archive/{month_key}.md"
        archive_entry = f"\n## {date_str}\n{summary.strip()}\n"

        # Read existing archive or create header
        archive_raw = _read_raw(archive_path)
        if not archive_raw:
            archive_raw = f"# Archive journal — {month_key}\n"
        write(archive_path, archive_raw + archive_entry)

        # Delete original
        full_original = Path(BRAIN_REPO_PATH) / filepath
        if full_original.exists():
            full_original.unlink()

        auto_commit_targeted(
            f"consolidation: archive {filepath}",
            [filepath, archive_path],
        )
        archived += 1
        details.append(f"{filepath} -> {archive_path}")

    return {
        "status": "ok",
        "journals_archived": archived,
        "details": details,
    }


# ---------------------------------------------------------------------------
# Sub-task 3 — Split large files
# ---------------------------------------------------------------------------

async def split_large_files(report: dict) -> dict:
    """Split memory files exceeding SPLIT_THRESHOLD_LINES into thematic sub-files."""
    files = _scan_memory_files(MEMORY_DIRS)
    splits_done = 0
    details: list[str] = []

    for filepath in files:
        raw = _read_raw(filepath)
        content_lines = _count_content_lines(raw)
        if content_lines <= SPLIT_THRESHOLD_LINES:
            continue

        body = read(filepath)  # stripped
        prompt = (
            f"Ce fichier fait {content_lines} lignes de contenu. "
            "Découpe-le en 2 à 5 sous-fichiers thématiques.\n\n"
            "Retourne UNIQUEMENT un JSON valide :\n"
            '{"splits": [{"filename": "nom-du-fichier.md", '
            '"title": "Titre pour le header", '
            '"content": "contenu markdown du sous-fichier"}]}\n\n'
            "Règles :\n"
            "- Chaque filename doit être un slug (minuscules, tirets)\n"
            "- Le contenu doit être complet — aucune ligne ne doit être perdue\n"
            "- Ne pas inclure de frontmatter YAML, je l'ajouterai\n\n"
            f"Fichier source : {filepath}\n\n"
            f"Contenu :\n```\n{body}\n```"
        )

        result_text = await generate_with_model(prompt, OPUS)
        parsed = _parse_json(result_text)
        if not parsed or "splits" not in parsed:
            details.append(f"{filepath}: LLM output parse error, skipped")
            continue

        splits = parsed["splits"]
        if not splits or len(splits) < 2:
            details.append(f"{filepath}: LLM returned <2 splits, skipped")
            continue

        # Validate completeness: count non-blank lines
        original_lines = _count_content_lines(raw)
        split_lines = sum(
            _count_content_lines(s.get("content", "")) for s in splits
        )
        if original_lines > 0:
            ratio = abs(split_lines - original_lines) / original_lines
            if ratio > 0.05:
                details.append(
                    f"{filepath}: line count mismatch ({original_lines} vs {split_lines}), "
                    f"ratio={ratio:.1%}, ABORTED"
                )
                continue

        # Write split files
        parent_dir = str(Path(filepath).parent)
        now_iso = datetime.now(ZoneInfo(TIMEZONE)).strftime("%Y-%m-%d")
        committed_files: list[str] = []

        for s in splits:
            fname = s.get("filename", "")
            if not fname.endswith(".md"):
                fname += ".md"
            new_path = f"{parent_dir}/{fname}"
            title = s.get("title", fname.replace(".md", "").replace("-", " ").title())
            frontmatter = (
                f"---\ntitle: {title}\n"
                f"source: split from {filepath}\n"
                f"date: {now_iso}\n---\n\n"
            )
            write(new_path, frontmatter + s["content"])
            committed_files.append(new_path)

        # Delete original
        full_original = Path(BRAIN_REPO_PATH) / filepath
        if full_original.exists():
            full_original.unlink()
        committed_files.append(filepath)

        # Update INDEX.md — will be fully rebuilt in update_index, but
        # we note the change for the atomic commit
        auto_commit_targeted(
            f"consolidation: split {filepath} into {len(splits)} files",
            committed_files,
        )
        splits_done += 1
        details.append(f"{filepath} -> {len(splits)} sub-files")

    return {
        "status": "ok",
        "splits": splits_done,
        "details": details,
    }


# ---------------------------------------------------------------------------
# Sub-task 4 — Update INDEX.md
# ---------------------------------------------------------------------------

async def update_index(report: dict) -> dict:
    """Regenerate INDEX.md to reflect current file tree."""
    all_files = _scan_memory_files(MEMORY_DIRS + ["journal"])
    current_index = _read_raw("INDEX.md")

    file_list = "\n".join(f"- {f}" for f in sorted(all_files))

    prompt = (
        "Voici la liste actuelle de tous les fichiers mémoire :\n\n"
        f"{file_list}\n\n"
        "Et voici l'INDEX.md actuel :\n```\n{index}\n```\n\n"
        "Mets à jour l'INDEX.md :\n"
        "- Ajoute les fichiers nouveaux avec une description d'une ligne\n"
        "- Supprime les fichiers qui n'existent plus\n"
        "- Garde la structure existante (sections, titres)\n"
        "- Conserve les descriptions existantes pour les fichiers inchangés\n\n"
        "Retourne UNIQUEMENT le contenu complet du nouveau INDEX.md (pas de JSON, pas de code fences)."
    ).format(index=current_index)

    new_index = await generate_with_model(prompt, SONNET)
    if not new_index.strip():
        return {"status": "error", "error": "LLM returned empty INDEX.md"}

    # Sanity check: must contain an existing section header
    if "## Profil" not in new_index and "## Profile" not in new_index:
        return {
            "status": "error",
            "error": "INDEX.md sanity check failed: missing '## Profil' section",
        }

    # Count added/removed by comparing file mentions
    old_files = set(re.findall(r"`([^`]+\.md)`", current_index))
    new_files_mentioned = set(re.findall(r"`([^`]+\.md)`", new_index))
    added = len(new_files_mentioned - old_files)
    removed = len(old_files - new_files_mentioned)

    write("INDEX.md", new_index)
    auto_commit_targeted("consolidation: update INDEX.md", ["INDEX.md"])

    return {
        "status": "ok",
        "added": added,
        "removed": removed,
        "updated": len(new_files_mentioned & old_files),
    }


# ---------------------------------------------------------------------------
# Sub-task 5 — Check contradictions
# ---------------------------------------------------------------------------

async def check_contradictions(report: dict) -> dict:
    """Check if any recorded contradictions have been resolved."""
    contradictions_content = read("open-questions/contradictions.md")
    if not contradictions_content.strip():
        return {"status": "ok", "resolved_candidates": 0, "pings_sent": 0}

    # Gather all fact/belief files for context
    fact_files = _scan_memory_files(["profile", "work", "health", "relations"])
    context_parts: list[str] = []
    for fp in fact_files:
        body = read(fp)
        if body.strip():
            context_parts.append(f"### {fp}\n{body}")
    context = "\n\n".join(context_parts)

    prompt = (
        "Voici les contradictions enregistrées :\n\n"
        f"{contradictions_content}\n\n"
        "Et voici le contexte actuel (faits, croyances, profil) :\n\n"
        f"{context}\n\n"
        "Y a-t-il des contradictions qui semblent maintenant résolues "
        "(les faits récents montrent clairement une direction) ?\n\n"
        "Retourne UNIQUEMENT un JSON valide :\n"
        '{"resolved": [{"contradiction": "résumé court", '
        '"resolution": "comment elle est résolue", '
        '"question_for_axel": "question courte pour confirmer"}]}\n\n'
        "Si aucune contradiction résolue, retourne {\"resolved\": []}."
    )

    result_text = await generate_with_model(prompt, OPUS)
    parsed = _parse_json(result_text)
    if not parsed:
        return {"status": "error", "error": "LLM output parse error"}

    resolved = parsed.get("resolved", [])
    pings_remaining = report.get("_pings_remaining", MAX_ASSISTED_PINGS_PER_DAY)
    pings_sent = 0

    for item in resolved:
        if pings_remaining <= 0:
            break
        question = item.get("question_for_axel", "")
        contradiction = item.get("contradiction", "")
        if not question:
            continue

        msg = (
            f"🔄 **Contradiction peut-être résolue**\n\n"
            f"_{contradiction}_\n\n"
            f"{question}\n\n"
            f"Réponds oui/non."
        )
        sent = await send(msg)
        if sent:
            pending_id = str(uuid.uuid4())[:8]
            add_pending(
                id=pending_id,
                type="contradiction_resolved",
                data=item,
                message_text=question,
            )
            pings_sent += 1
            pings_remaining -= 1

    # Store remaining budget for beliefs step
    report["_pings_remaining"] = pings_remaining

    return {
        "status": "ok",
        "resolved_candidates": len(resolved),
        "pings_sent": pings_sent,
    }


# ---------------------------------------------------------------------------
# Sub-task 6 — Check beliefs
# ---------------------------------------------------------------------------

async def check_beliefs(report: dict) -> dict:
    """Detect belief confidence shifts based on recent journal evidence."""
    # Find belief files (handle splits like beliefs-1.md, beliefs-work.md)
    all_profile = list_files("profile")
    belief_files = [f for f in all_profile if "beliefs" in Path(f).stem]
    if not belief_files:
        return {"status": "ok", "shifts_detected": 0, "pings_sent": 0, "details": []}

    beliefs_content = ""
    for bf in belief_files:
        body = read(bf)
        if body.strip():
            beliefs_content += f"\n### {bf}\n{body}\n"

    # Gather recent journal content (archive + today)
    journal_files = list_files("journal")
    journal_content = ""
    for jf in journal_files:
        body = read(jf)
        if body.strip():
            journal_content += f"\n### {jf}\n{body}\n"

    if not journal_content.strip():
        return {"status": "ok", "shifts_detected": 0, "pings_sent": 0, "details": []}

    prompt = (
        "Voici les croyances d'Axel avec leur niveau de confiance (1-5) :\n\n"
        f"{beliefs_content}\n\n"
        "Et voici les entrées récentes du journal :\n\n"
        f"{journal_content}\n\n"
        f"Y a-t-il des croyances dont la confiance devrait changer d'au moins "
        f"{BELIEF_SHIFT_THRESHOLD} points (basé sur les preuves du journal) ?\n\n"
        "Retourne UNIQUEMENT un JSON valide :\n"
        '{"shifts": [{"belief": "la croyance", "current_confidence": N, '
        '"proposed_confidence": M, "evidence": "résumé des preuves", '
        '"question_for_axel": "question courte pour confirmer"}]}\n\n'
        'Si aucun changement significatif, retourne {"shifts": []}.'
    )

    result_text = await generate_with_model(prompt, OPUS)
    parsed = _parse_json(result_text)
    if not parsed:
        return {"status": "error", "error": "LLM output parse error"}

    shifts = parsed.get("shifts", [])
    pings_remaining = report.get("_pings_remaining", MAX_ASSISTED_PINGS_PER_DAY)
    pings_sent = 0
    details: list[str] = []

    for item in shifts:
        belief = item.get("belief", "")
        current = item.get("current_confidence", "?")
        proposed = item.get("proposed_confidence", "?")
        evidence = item.get("evidence", "")
        question = item.get("question_for_axel", "")

        details.append(f"{belief}: {current} -> {proposed} ({evidence})")

        if not question or pings_remaining <= 0:
            continue

        msg = (
            f"💡 **Évolution de croyance détectée**\n\n"
            f"_{belief}_\n"
            f"Confiance : {current} → {proposed}\n\n"
            f"Preuve : {evidence}\n\n"
            f"{question}\n\n"
            f"Réponds oui/non."
        )
        sent = await send(msg)
        if sent:
            pending_id = str(uuid.uuid4())[:8]
            add_pending(
                id=pending_id,
                type="belief_shift",
                data=item,
                message_text=question,
            )
            pings_sent += 1
            pings_remaining -= 1

    report["_pings_remaining"] = pings_remaining

    return {
        "status": "ok",
        "shifts_detected": len(shifts),
        "pings_sent": pings_sent,
        "details": details,
    }


# ---------------------------------------------------------------------------
# Sub-task 7 — Write report (sync, no LLM)
# ---------------------------------------------------------------------------

def write_report(report: dict) -> None:
    """Write consolidation report as JSON."""
    path = Path(CONSOLIDATION_REPORT_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2, default=str)


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

SUB_TASKS = [
    ("dedup", deduplicate_facts),
    ("archive_journals", archive_journals),
    ("split_large_files", split_large_files),
    ("update_index", update_index),
    ("check_contradictions", check_contradictions),
    ("check_beliefs", check_beliefs),
]


async def run_daily_consolidation() -> dict:
    """Main entry point — runs all consolidation sub-tasks sequentially."""
    tz = ZoneInfo(TIMEZONE)
    report = {
        "started_at": datetime.now(tz).isoformat(),
        "finished_at": None,
        "steps": {},
        "errors": [],
        "_pings_remaining": MAX_ASSISTED_PINGS_PER_DAY,
    }

    for name, func in SUB_TASKS:
        try:
            result = await func(report)
            report["steps"][name] = result
        except Exception as e:
            report["steps"][name] = {"status": "error", "error": str(e)}
            report["errors"].append(f"{name}: {e}")
            print(f"[consolidator] {name} failed: {e}")
            await notify_error(f"consolidation.{name}", e)

    report["finished_at"] = datetime.now(tz).isoformat()

    # Write report (sync)
    write_report(report)

    # Single git push at the end (fire and forget)
    try:
        subprocess.Popen(
            ["git", "push", "origin", "main"],
            cwd=BRAIN_REPO_PATH,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception as e:
        print(f"[consolidator] git push failed: {e}")

    # Clean internal key from report before returning
    report.pop("_pings_remaining", None)
    return report
