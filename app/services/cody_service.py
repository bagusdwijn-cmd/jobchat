from __future__ import annotations

class CodyStyleService:
    def __init__(self, ai_service, file_service):
        self.ai_service = ai_service
        self.file_service = file_service

    def build_index(self, repo_root):
        files = self.file_service.list_text_files(repo_root)
        index = []
        for f in files[:300]:
            try:
                content = f.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            index.append({"path": str(f.relative_to(repo_root)), "content": content[:6000]})
        return {"files": index}

    def retrieve_context(self, index: dict, question: str, limit: int = 8):
        terms = {t.lower() for t in question.split() if len(t) > 2}
        scored = []
        for item in index.get("files", []):
            text = item["content"].lower()
            score = sum(1 for t in terms if t in text or t in item["path"].lower())
            if score > 0:
                scored.append((score, item))
        scored.sort(key=lambda x: x[0], reverse=True)
        selected = [item for _, item in scored[:limit]] or index.get("files", [])[:limit]
        ctx, used = [], []
        for item in selected:
            used.append(item["path"])
            ctx.append(f"FILE: {item['path']}\n{item['content'][:2500]}")
        return "\n\n".join(ctx), used

    async def answer(self, repo_index: dict, question: str):
        context, used = self.retrieve_context(repo_index, question)
        answer, raw = await self.ai_service.answer_with_repo(question, context)
        return {"question": question, "answer": answer, "used_files": used, "raw_ai": raw}
