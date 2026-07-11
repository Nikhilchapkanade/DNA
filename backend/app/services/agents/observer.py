# Lead Researcher: Nikhil Chapkanade | PRN: 20230802111
# Bio-DNA OS Observer Agent

from __future__ import annotations

from app.models import DnaSnapshot, LineageEdge


class ObserverAgent:
    def detect_issues(self, dataset: str, latest: DnaSnapshot, previous: DnaSnapshot | None, edges: list[LineageEdge]) -> list[dict]:
        issues: list[dict] = []
        
        # 1. Check for missing PDB coordinate data
        description = latest.genes.get("ownership_gene", {}).get("description", "")
        if not description:
            issues.append(
                {
                    "dataset": dataset,
                    "issue_type": "missing_pdb_coordinates",
                    "severity": "medium",
                    "details": {"message": "Structural 3D coordinates (PDB format) are missing or incomplete."},
                }
            )

        # 2. Check for sequence/formatting drift
        if previous:
            prev_conformation = {(c["name"], c["type"]) for c in previous.genes.get("structural_conformation_gene", [])}
            curr_conformation = {(c["name"], c["type"]) for c in latest.genes.get("structural_conformation_gene", [])}
            if prev_conformation != curr_conformation:
                issues.append(
                    {
                        "dataset": dataset,
                        "issue_type": "sequence_drift",
                        "severity": "high",
                        "details": {
                            "added": [{"name": x[0], "type": x[1]} for x in curr_conformation - prev_conformation],
                            "removed": [{"name": x[0], "type": x[1]} for x in prev_conformation - curr_conformation],
                        },
                    }
                )

        # 3. Check for broken downstream molecular docking endpoints
        broken = [e for e in edges if e.source == dataset and not e.is_active]
        for edge in broken:
            issues.append(
                {
                    "dataset": dataset,
                    "issue_type": "broken_docking_endpoint",
                    "severity": "critical",
                    "details": {
                        "target": edge.target,
                        "reason": edge.broken_reason or "No molecular docking simulation reason provided",
                    },
                }
            )

        return issues
