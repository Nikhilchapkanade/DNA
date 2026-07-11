# Lead Researcher: Nikhil Chapkanade | PRN: 20230802111
# Bio-DNA OS External Services Integration

from __future__ import annotations

from contextlib import asynccontextmanager
import httpx

from app.core.config import get_settings
from app.services.brightdata_mcp_client import BrightDataMCPClient


class ExternalContextService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.brightdata = BrightDataMCPClient()

    async def tavily_lookup(self, query: str) -> list[dict]:
        # Local offline mode fallback
        if not self.settings.tavily_api_key:
            return [
                {
                    "title": "Local Bioinformatics Context Lookup",
                    "url": "http://localhost",
                    "content": "No Tavily API key provided. Running pipeline diagnostic offline under Bio-DNA OS.",
                }
            ]

        url = "https://api.tavily.com/search"
        payload = {
            "api_key": self.settings.tavily_api_key,
            "query": query,
            "search_depth": "advanced",
            "max_results": 5,
            "include_raw_content": False,
        }
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
        return data.get("results", [])

    async def brightdata_validate(self, dataset: str) -> dict:
        query = (
            f"Find recent incident patterns and best practices for structural bioinformatics pipeline errors involving biological asset {dataset}. "
            "Return concise validation checks."
        )
        return await self.brightdata.discover(query)
