# Lead Researcher: Nikhil Chapkanade | PRN: 20230802111
# Bio-DNA OS Local LLM Gateway with Offline Mock Fallback

from __future__ import annotations

import json
from contextlib import asynccontextmanager
import httpx

from app.core.config import get_settings


class LLMGateway:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def complete(self, prompt: str, payload: dict) -> str:
        # Check if local model URL is active
        is_local = "localhost" in self.settings.llm_base_url or "127.0.0.1" in self.settings.llm_base_url
        
        # If API key is missing and we aren't targeting a local server, trigger the offline mock fallback
        if not self.settings.llm_api_key and not is_local:
            return self._mock_response(prompt, payload)

        body = {
            "model": self.settings.llm_model,
            "messages": [
                {"role": "system", "content": prompt},
                {"role": "user", "content": json.dumps(payload)},
            ],
            "temperature": 0.2,
        }
        
        headers = {
            "Content-Type": "application/json",
        }
        if self.settings.llm_api_key:
            headers["Authorization"] = f"Bearer {self.settings.llm_api_key}"

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(f"{self.settings.llm_base_url.rstrip('/')}/chat/completions", headers=headers, json=body)
                resp.raise_for_status()
                data = resp.json()
            return data["choices"][0]["message"]["content"]
        except Exception:
            # If the remote or local LLM server fails (e.g. Ollama offline), fallback to the mock data
            return self._mock_response(prompt, payload)

    def _mock_response(self, prompt: str, payload: dict) -> str:
        # Determine prompt type
        if "AnalystAgent" in prompt:
            res = {
                "root_cause": "Format drift: upstream sequence format column renamed to conformation_format, creating a contract drift.",
                "impact": f"Downstream target invalidation of approximately {payload.get('computed_invalidation_scale', 750)} candidates detected.",
                "confidence": 0.95
            }
            return json.dumps(res)
            
        elif "ExplainerAgent" in prompt:
            res = {
                "executive_summary": f"A sequence database formatting revision in {payload.get('dataset', 'peptide_fasta_sequences')} broke the downstream AlphaFold prediction pipeline.",
                "root_cause": "Upstream sequence format column was renamed to conformation_format, creating a contract drift.",
                "business_impact": "Downstream Target Invalidation Scale is 750 virtual drug screening candidates (critical). virtual screening docking matrices targeting COX-2 and TNF-alpha are currently stale.",
                "recommended_fix_now_next": "Now: deploy AlphaEvolve JIT script healer to restore sequence format fields. Next: implement pre-prediction contract checks in bioinformatics ingest jobs.",
                "confidence_and_evidence": "High confidence based on temporal sequence drift logs, missing PDB coordinate alerts, and failed RDKit docking targets."
            }
            return json.dumps(res)
            
        elif "trust-scoring" in prompt:
            return json.dumps({"score": 58, "rationale": "Degraded due to active sequence drift and broken downstream docking endpoints."})
            
        return "Offline mock response generated successfully."
