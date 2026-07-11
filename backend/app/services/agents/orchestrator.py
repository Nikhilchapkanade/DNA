# Lead Researcher: Nikhil Chapkanade | PRN: 20230802111
# Bio-DNA OS Agent Orchestrator

from __future__ import annotations

from contextlib import asynccontextmanager
from sqlalchemy.orm import Session

from app.models import Dataset, DnaSnapshot, Issue, LineageEdge
from app.services.agents.analyst import AnalystAgent
from app.services.agents.explainer import ExplainerAgent
from app.services.agents.fixer import FixerAgent
from app.services.agents.observer import ObserverAgent
from app.services.external_apis import ExternalContextService


class AgentOrchestrator:
    def __init__(self) -> None:
        self.observer = ObserverAgent()
        self.analyst = AnalystAgent()
        self.fixer = FixerAgent()
        self.explainer = ExplainerAgent()
        self.external_context = ExternalContextService()

    async def run(self, db: Session, dataset_name: str, user_question: str | None = None) -> dict:
        dataset = db.query(Dataset).filter(Dataset.name == dataset_name).first()
        if not dataset:
            raise ValueError(f"Biological asset not found: {dataset_name}")

        snaps = (
            db.query(DnaSnapshot)
            .filter(DnaSnapshot.dataset_id == dataset.id)
            .order_by(DnaSnapshot.captured_at.desc())
            .limit(2)
            .all()
        )
        latest = snaps[0] if snaps else None
        previous = snaps[1] if len(snaps) > 1 else None
        if not latest:
            raise ValueError(f"No DNA snapshots for biological asset: {dataset_name}")

        edges = db.query(LineageEdge).all()
        issues = self.observer.detect_issues(dataset_name, latest, previous, edges)
        brightdata_validation = await self.external_context.brightdata_validate(dataset_name)

        # Classification of Track A (Neuro-Therapeutics) vs Track B (Nutritional Peptides)
        is_track_a = "neuro" in dataset_name or "dopamine" in dataset_name
        is_track_b = "peptide" in dataset_name or "cox2" in dataset_name or "tnf" in dataset_name
        track_label = "Track A (Small-Molecule Neuro-Therapeutics)" if is_track_a else ("Track B (Nutritional Bioactive Peptides)" if is_track_b else "Shared/Core")
        
        # Polypharmacological Receptor Mappings
        if is_track_a:
            receptors = ["Dopamine D2 Receptor (DRD2)"]
        elif is_track_b:
            receptors = ["Cyclooxygenase-2 (COX-2)", "Tumor Necrosis Factor alpha (TNF-alpha)"]
        else:
            receptors = ["Dopamine D2 Receptor (DRD2)", "Cyclooxygenase-2 (COX-2)", "Tumor Necrosis Factor alpha (TNF-alpha)"]

        for issue in issues:
            issue["details"]["external_validation"] = brightdata_validation
            issue["details"]["track"] = track_label
            issue["details"]["associated_receptors"] = receptors
            
            db_issue = Issue(
                dataset=dataset_name,
                issue_type=issue["issue_type"],
                severity=issue["severity"],
                details=issue["details"],
            )
            db.add(db_issue)
        db.commit()

        analyses = []
        fixes = []
        for issue in issues:
            analysis = await self.analyst.analyze_issue(
                issue,
                lineage_context=[{"source": e.source, "target": e.target, "is_active": e.is_active} for e in edges],
                schema_context={
                    "latest": latest.genes.get("structural_conformation_gene", []),
                    "previous": previous.genes.get("structural_conformation_gene", []) if previous else [],
                },
            )
            analysis["track"] = track_label
            analysis["associated_receptors"] = receptors
            
            analyses.append(analysis)
            fixes.append(self.fixer.suggest_fix(issue, analysis))

        narrative, sections = await self.explainer.explain(dataset_name, issues, analyses, fixes, user_question)
        return {
            "dataset": dataset_name,
            "track": track_label,
            "associated_receptors": receptors,
            "issues": issues,
            "analysis": analyses,
            "fixes": fixes,
            "narrative": narrative,
            "sections": sections,
        }
