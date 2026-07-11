# Lead Researcher: Nikhil Chapkanade | PRN: 20230802111
# Bio-DNA OS Analyst Agent

from __future__ import annotations

import json
from contextlib import asynccontextmanager

from app.services.external_apis import ExternalContextService
from app.services.llm_gateway import LLMGateway
from app.services.prompts import ROOT_CAUSE_PROMPT


class AnalystAgent:
    def __init__(self) -> None:
        self.llm = LLMGateway()
        self.external_context = ExternalContextService()

    async def analyze_issue(self, issue: dict, lineage_context: list[dict], schema_context: dict) -> dict:
        tavily_context = await self.external_context.tavily_lookup(
            f"structural bioinformatics pipeline root cause for {issue['issue_type']} in biological asset {issue.get('dataset', '')}"
        )
        
        # Calculate dynamic candidate invalidation rate based on mutation count
        latest_len = len(schema_context.get("latest", []))
        prev_len = len(schema_context.get("previous", []))
        mutations_count = abs(latest_len - prev_len)
        if mutations_count == 0:
            mutations_count = 1  # baseline
        invalidated_scale = mutations_count * 250
        
        payload = {
            "issue": issue,
            "lineage_context": lineage_context,
            "schema_context": schema_context,
            "tavily_context": tavily_context,
            "computed_invalidation_scale": invalidated_scale,
            "methodology": "Downstream Target Invalidation Scale = Mutations Count * 250 compound candidates"
        }
        
        result = await self.llm.complete(ROOT_CAUSE_PROMPT, payload)
        try:
            parsed = json.loads(result)
            parsed["issue_type"] = issue["issue_type"]
            parsed["invalidated_candidates"] = invalidated_scale
            return parsed
        except json.JSONDecodeError:
            return {
                "issue_type": issue["issue_type"],
                "root_cause": result,
                "impact": f"Downstream target invalidation of approximately {invalidated_scale} candidates detected.",
                "confidence": 0.5,
                "invalidated_candidates": invalidated_scale
            }
