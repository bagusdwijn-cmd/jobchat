from __future__ import annotations
from pathlib import Path
import zipfile, shutil

TEXT_EXTENSIONS = {".py",".js",".ts",".tsx",".jsx",".json",".md",".txt",".yaml",".yml",".html",".css",".sql",".java",".go",".rs",".php",".rb",".c",".cpp",".h",".cs",".sh"}

class FileService:
    def __init__(self, base_path: str | Path):
        self.base_path = Path(base_path)

    def user_dir(self, chat_id: int) -> Path:
        p = self.base_path / f"user_{chat_id}"
        p.mkdir(parents=True, exist_ok=True)
        return p

    def cv_dir(self, chat_id: int) -> Path:
        p = self.user_dir(chat_id) / "cv"
        p.mkdir(parents=True, exist_ok=True)
        return p

    def attachment_dir(self, chat_id: int) -> Path:
        p = self.user_dir(chat_id) / "attachments"
        p.mkdir(parents=True, exist_ok=True)
        return p

    def jobs_dir(self, chat_id: int) -> Path:
        p = self.user_dir(chat_id) / "jobs"
        p.mkdir(parents=True, exist_ok=True)
        return p

    def repo_dir(self, chat_id: int) -> Path:
        p = self.user_dir(chat_id) / "repos"
        p.mkdir(parents=True, exist_ok=True)
        return p

    def extract_repo_zip(self, chat_id: int, repo_name: str, zip_path: Path) -> Path:
        target = self.repo_dir(chat_id) / repo_name
        if target.exists():
            shutil.rmtree(target)
        target.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(target)
        return target

    def list_text_files(self, root: Path):
        items = []
        for p in root.rglob("*"):
            if p.is_file() and p.suffix.lower() in TEXT_EXTENSIONS:
                items.append(p)
        return items
