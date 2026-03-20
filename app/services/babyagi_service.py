from __future__ import annotations
from app.services.search_service import duckduckgo_search

class BabyAGIService:
    def __init__(self, ai_service):
        self.ai_service = ai_service

    async def run(self, goal: str):
        tool_context = "Tools tersedia: SEARCH_WEB (DuckDuckGo HTML), ANALYZE, DRAFT, REPORT. Tidak login ke situs atau kirim email tanpa review."
        plan, raw = await self.ai_service.plan_tasks(goal, tool_context)
        executions = []
        for step in plan.get("steps", [])[:5]:
            action = (step.get("action") or "").upper()
            if action == "SEARCH_WEB":
                query = step.get("details") or goal
                try:
                    hits = duckduckgo_search(query, max_results=5)
                    executions.append({"step": step.get("title", ""), "action": action, "output": hits})
                except Exception as e:
                    executions.append({"step": step.get("title", ""), "action": action, "output": f"search_failed: {e}"})
            else:
                executions.append({"step": step.get("title", ""), "action": action, "output": step.get("details", "")})
        return {"goal": plan.get("goal", goal), "summary": plan.get("summary", ""), "steps": plan.get("steps", []), "executions": executions, "result": plan.get("result", ""), "raw_ai": raw}
