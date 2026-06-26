from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path


class RepoManager:
    def __init__(self, repo_url: str, base_commit: str, work_dir: str | None = None) -> None:
        self._repo_url = repo_url
        self._base_commit = base_commit
        self._owned_tmpdir: str | None = None
        if work_dir is None:
            self._owned_tmpdir = tempfile.mkdtemp(prefix="auto_debugger_")
            self._work_dir = Path(self._owned_tmpdir)
        else:
            self._work_dir = Path(work_dir)
            self._work_dir.mkdir(parents=True, exist_ok=True)
        self._repo_path: Path | None = None

    def clone_and_checkout(self) -> Path:
        if self._repo_path is not None:
            return self._repo_path

        repo_name = self._repo_url.rstrip("/").split("/")[-1]
        if repo_name.endswith(".git"):
            repo_name = repo_name[:-4]
        dest = self._work_dir / repo_name

        if not dest.exists():
            subprocess.run(
                ["git", "clone", self._repo_url, str(dest)],
                check=True,
                capture_output=True,
            )

        subprocess.run(
            ["git", "checkout", self._base_commit],
            cwd=dest,
            check=True,
            capture_output=True,
        )

        self._repo_path = dest
        return dest

    def get_repo_path(self) -> Path:
        return self.clone_and_checkout()

    def read_file(self, file_path: str) -> str:
        repo = self.clone_and_checkout()
        return (repo / file_path).read_text(encoding="utf-8")

    def write_file(self, file_path: str, content: str) -> None:
        repo = self.clone_and_checkout()
        target = repo / file_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

    def list_files(self, pattern: str = "**/*.py") -> list[str]:
        repo = self.clone_and_checkout()
        return [str(p.relative_to(repo)) for p in repo.glob(pattern) if p.is_file()]

    def run_tests(self, test_names: tuple[str, ...]) -> tuple[bool, str]:
        repo = self.clone_and_checkout()
        result = subprocess.run(
            ["python", "-m", "pytest", *test_names, "-x", "--tb=short", "-q"],
            cwd=repo,
            capture_output=True,
            text=True,
            timeout=300,
        )
        output = result.stdout + result.stderr
        return result.returncode == 0, output

    def apply_patch(self, patch: str) -> tuple[bool, str]:
        repo = self.clone_and_checkout()
        result = subprocess.run(
            ["git", "apply", "--check"],
            cwd=repo,
            input=patch,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            return False, result.stderr

        subprocess.run(
            ["git", "apply"],
            cwd=repo,
            input=patch,
            capture_output=True,
            text=True,
            check=True,
        )
        return True, ""

    def cleanup(self) -> None:
        if self._owned_tmpdir and Path(self._owned_tmpdir).exists():
            shutil.rmtree(self._owned_tmpdir, ignore_errors=True)
            self._owned_tmpdir = None
        self._repo_path = None

    def __enter__(self) -> "RepoManager":
        return self

    def __exit__(self, *_: object) -> None:
        self.cleanup()

