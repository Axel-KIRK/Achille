import os, sys, subprocess
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

def test_auto_commit_targeted_only_stages_specified_files(tmp_path):
    subprocess.run(["git", "init"], cwd=str(tmp_path), capture_output=True)
    subprocess.run(["git", "config", "user.name", "test"], cwd=str(tmp_path), capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@test"], cwd=str(tmp_path), capture_output=True)
    (tmp_path / "a.md").write_text("initial")
    subprocess.run(["git", "add", "-A"], cwd=str(tmp_path), capture_output=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=str(tmp_path), capture_output=True)
    (tmp_path / "a.md").write_text("modified a")
    (tmp_path / "b.md").write_text("new b")
    from memory.writer import auto_commit_targeted
    result = auto_commit_targeted("test commit", ["a.md"], repo_path=str(tmp_path))
    assert result is True
    status = subprocess.run(["git", "status", "--porcelain"], cwd=str(tmp_path), capture_output=True, text=True)
    assert "b.md" in status.stdout
    assert "a.md" not in status.stdout
