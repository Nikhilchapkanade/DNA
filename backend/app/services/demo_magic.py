# Lead Researcher: Nikhil Chapkanade | PRN: 20230802111
# Bio-DNA OS Demo Simulation Engine (Dual-Track Polypharmacological Storyline)

from __future__ import annotations

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models import Dataset, DnaSnapshot, LineageEdge


SEVERITY_BANDS = (
    (24, "low"),
    (49, "medium"),
    (74, "high"),
    (100, "critical"),
)


def severity_from_score(risk_score: float) -> str:
    for cap, label in SEVERITY_BANDS:
        if risk_score <= cap:
            return label
    return "critical"


def compute_risk_score(schema_break: int, downstream_breaks: int, mutation_frequency_24h: int) -> float:
    return min(100.0, float(40 + 20 * schema_break + 15 * downstream_breaks + 5 * mutation_frequency_24h))


def _downstream_map(edges: list[LineageEdge]) -> dict[str, set[str]]:
    mapping: dict[str, set[str]] = {}
    for edge in edges:
        mapping.setdefault(edge.source, set()).add(edge.target)
    return mapping


def compute_blast_radius(edges: list[LineageEdge], root_dataset: str) -> int:
    mapping = _downstream_map(edges)
    visited: set[str] = set()
    stack = [root_dataset]
    while stack:
        source = stack.pop()
        for target in mapping.get(source, set()):
            if target in visited:
                continue
            visited.add(target)
            stack.append(target)
    return len(visited)


def mutation_frequency_24h(db: Session, dataset_id: int, now: datetime | None = None) -> int:
    current = now or datetime.utcnow()
    window_start = current - timedelta(hours=24)
    snaps = (
        db.query(DnaSnapshot)
        .filter(DnaSnapshot.dataset_id == dataset_id, DnaSnapshot.captured_at >= window_start, DnaSnapshot.mutation_type.is_not(None))
        .all()
    )
    return len(snaps)


def current_metrics(db: Session, dataset: Dataset, edges: list[LineageEdge], latest: DnaSnapshot | None = None) -> dict:
    latest_snap = latest or (
        db.query(DnaSnapshot)
        .filter(DnaSnapshot.dataset_id == dataset.id)
        .order_by(DnaSnapshot.captured_at.desc())
        .first()
    )
    if not latest_snap:
        return {
            "risk_score": 0.0,
            "mutation_frequency_24h": 0,
            "blast_radius": 0,
            "severity_level": "low",
        }

    freq = mutation_frequency_24h(db, dataset.id)
    schema_break = 1 if latest_snap.mutation_type == "sequence_drift" else 0
    downstream_breaks = len([e for e in edges if e.source == dataset.name and not e.is_active])
    blast_radius = compute_blast_radius(edges, dataset.name)
    risk_score = compute_risk_score(schema_break, downstream_breaks, freq)

    return {
        "risk_score": risk_score,
        "mutation_frequency_24h": freq,
        "blast_radius": blast_radius,
        "severity_level": severity_from_score(risk_score),
    }


def persist_metrics_in_genes(snapshot: DnaSnapshot, metrics: dict) -> None:
    genes = dict(snapshot.genes or {})
    genes["metrics"] = {
        "risk_score": metrics["risk_score"],
        "mutation_frequency_24h": metrics["mutation_frequency_24h"],
        "blast_radius": metrics["blast_radius"],
        "severity_level": metrics["severity_level"],
    }
    snapshot.genes = genes


def _ensure_dataset(db: Session, name: str, owner: str, description: str) -> Dataset:
    dataset = db.query(Dataset).filter(Dataset.name == name).first()
    if dataset:
        dataset.owner = owner
        dataset.description = description
        return dataset
    dataset = Dataset(name=name, owner=owner, description=description)
    db.add(dataset)
    db.flush()
    return dataset


def _upsert_lineage_edge(db: Session, source: str, target: str, is_active: bool, broken_reason: str | None = None) -> LineageEdge:
    edge = db.query(LineageEdge).filter(LineageEdge.source == source, LineageEdge.target == target).first()
    if edge:
        edge.is_active = is_active
        edge.broken_reason = broken_reason
        return edge
    edge = LineageEdge(source=source, target=target, is_active=is_active, broken_reason=broken_reason)
    db.add(edge)
    return edge


def _snapshot(
    dataset_id: int,
    captured_at: datetime,
    trust_score: float,
    schema_gene: list[dict],
    lineage_gene: list[dict],
    usage_gene: dict,
    owner: str,
    description: str,
    mutation_type: str | None = None,
    incident: str | None = None,
) -> DnaSnapshot:
    return DnaSnapshot(
        dataset_id=dataset_id,
        captured_at=captured_at,
        trust_score=trust_score,
        mutation_type=mutation_type,
        incident=incident,
        genes={
            "structural_conformation_gene": schema_gene,
            "bio_pathway_lineage_gene": lineage_gene,
            "target_usage_gene": usage_gene,
            "ownership_gene": {"owner": owner, "description": description},
            "computed_at": captured_at.isoformat(),
        },
    )


def run_magic_demo(db: Session) -> dict:
    now = datetime.utcnow()
    baseline_time = now - timedelta(minutes=1)
    event_time = now

    # Seeding Track A (Neuro-Therapeutics)
    neuro_seq = _ensure_dataset(
        db, 
        "neuro_fasta_sequences", 
        "neuro-discovery-lab", 
        "Small-molecule FASTA target sequences for neurodegenerative receptor binding"
    )
    neuro_struct = _ensure_dataset(
        db,
        "neuro_alphafold_structures",
        "structural-bioinformatics",
        "AlphaFold predicted 3D structures for dopamine pathway models",
    )
    dopamine_matrix = _ensure_dataset(
        db,
        "neuro_dopamine_docking_matrix",
        "computational-docking",
        "RDKit virtual screening affinity matrix targeting Dopamine D2 receptors",
    )

    # Seeding Track B (Nutritional Peptides)
    peptide_seq = _ensure_dataset(
        db,
        "peptide_fasta_sequences",
        "nutri-proteomics-lab",
        "Bioactive nutritional peptide sequences screened for anti-inflammatory efficacy",
    )
    peptide_struct = _ensure_dataset(
        db,
        "peptide_alphafold_structures",
        "structural-bioinformatics",
        "AlphaFold predicted 3D structures for bioactive peptides",
    )
    cox2_matrix = _ensure_dataset(
        db,
        "peptide_cox2_docking_matrix",
        "computational-docking",
        "RDKit virtual screening docking matrix targeting COX-2 receptors",
    )
    tnf_matrix = _ensure_dataset(
        db,
        "peptide_tnf_docking_matrix",
        "computational-docking",
        "RDKit virtual screening docking matrix targeting TNF-alpha receptors",
    )

    all_ids = [neuro_seq.id, neuro_struct.id, dopamine_matrix.id, peptide_seq.id, peptide_struct.id, cox2_matrix.id, tnf_matrix.id]
    db.query(DnaSnapshot).filter(DnaSnapshot.dataset_id.in_(all_ids)).delete(synchronize_session=False)
    
    db.query(LineageEdge).filter(
        (LineageEdge.source.in_([neuro_seq.name, neuro_struct.name, peptide_seq.name, peptide_struct.name])) |
        (LineageEdge.target.in_([neuro_struct.name, dopamine_matrix.name, peptide_struct.name, cox2_matrix.name, tnf_matrix.name]))
    ).delete(synchronize_session=False)
    db.flush()

    # Track A remains healthy
    _upsert_lineage_edge(db, neuro_seq.name, neuro_struct.name, True, None)
    _upsert_lineage_edge(db, neuro_struct.name, dopamine_matrix.name, True, None)

    # Track B undergoes mutation event
    _upsert_lineage_edge(db, peptide_seq.name, peptide_struct.name, False, "Sequence drift: peptide format column mismatch in upstream database revision")
    _upsert_lineage_edge(db, peptide_struct.name, cox2_matrix.name, False, "Molecular docking simulation endpoint blocked by missing 3D coordinate inputs")
    _upsert_lineage_edge(db, peptide_struct.name, tnf_matrix.name, False, "Molecular docking simulation endpoint blocked by missing 3D coordinate inputs")
    db.flush()

    # Gene schemas
    fasta_base_schema = [
        {"name": "sequence_id", "type": "string", "nullable": False},
        {"name": "peptide_sequence", "type": "string", "nullable": False},
        {"name": "format", "type": "string", "nullable": False},
        {"name": "residue_count", "type": "integer", "nullable": False},
        {"name": "source_organism", "type": "string", "nullable": False},
    ]
    fasta_mutated_schema = [
        {"name": "sequence_id", "type": "string", "nullable": False},
        {"name": "peptide_sequence", "type": "string", "nullable": False},
        {"name": "conformation_format", "type": "string", "nullable": False},
        {"name": "residue_count", "type": "integer", "nullable": False},
        {"name": "source_organism", "type": "string", "nullable": False},
    ]
    alphafold_schema = [
        {"name": "coordinate_id", "type": "string", "nullable": False},
        {"name": "pdb_raw_content", "type": "string", "nullable": False},
        {"name": "plddt_confidence", "type": "double", "nullable": False},
    ]
    docking_schema = [
        {"name": "ligand_id", "type": "string", "nullable": False},
        {"name": "target_receptor", "type": "string", "nullable": False},
        {"name": "binding_affinity_kcal", "type": "double", "nullable": False},
    ]

    snapshots = [
        # Track A: Healthy snapshots
        _snapshot(
            dataset_id=neuro_seq.id,
            captured_at=event_time,
            trust_score=95.0,
            schema_gene=fasta_base_schema,
            lineage_gene=[{"source": neuro_seq.name, "target": neuro_struct.name, "is_active": True}],
            usage_gene={"weekly_queries": 3200, "consumers": 18, "last_accessed": event_time.isoformat()},
            owner=neuro_seq.owner,
            description=neuro_seq.description,
        ),
        _snapshot(
            dataset_id=neuro_struct.id,
            captured_at=event_time,
            trust_score=92.0,
            schema_gene=alphafold_schema,
            lineage_gene=[{"source": neuro_struct.name, "target": dopamine_matrix.name, "is_active": True}],
            usage_gene={"weekly_queries": 1800, "consumers": 12, "last_accessed": event_time.isoformat()},
            owner=neuro_struct.owner,
            description=neuro_struct.description,
        ),
        _snapshot(
            dataset_id=dopamine_matrix.id,
            captured_at=event_time,
            trust_score=90.0,
            schema_gene=docking_schema,
            lineage_gene=[],
            usage_gene={"weekly_queries": 950, "consumers": 8, "last_accessed": event_time.isoformat()},
            owner=dopamine_matrix.owner,
            description=dopamine_matrix.description,
        ),
        
        # Track B: Mutating snapshots
        _snapshot(
            dataset_id=peptide_seq.id,
            captured_at=baseline_time,
            trust_score=94.0,
            schema_gene=fasta_base_schema,
            lineage_gene=[{"source": peptide_seq.name, "target": peptide_struct.name, "is_active": True}],
            usage_gene={"weekly_queries": 2800, "consumers": 24, "last_accessed": baseline_time.isoformat()},
            owner=peptide_seq.owner,
            description=peptide_seq.description,
        ),
        _snapshot(
            dataset_id=peptide_seq.id,
            captured_at=event_time,
            trust_score=58.0,
            schema_gene=fasta_mutated_schema,
            lineage_gene=[{"source": peptide_seq.name, "target": peptide_struct.name, "is_active": False}],
            usage_gene={"weekly_queries": 2700, "consumers": 24, "last_accessed": event_time.isoformat()},
            owner=peptide_seq.owner,
            description=peptide_seq.description,
            mutation_type="sequence_drift",
            incident="Sequence database revision: format renamed to conformation_format, breaking alignment inputs.",
        ),
        _snapshot(
            dataset_id=peptide_struct.id,
            captured_at=event_time,
            trust_score=48.0,
            schema_gene=alphafold_schema,
            lineage_gene=[
                {"source": peptide_struct.name, "target": cox2_matrix.name, "is_active": False},
                {"source": peptide_struct.name, "target": tnf_matrix.name, "is_active": False}
            ],
            usage_gene={"weekly_queries": 1500, "consumers": 14, "last_accessed": event_time.isoformat()},
            owner=peptide_struct.owner,
            description=peptide_struct.description,
            mutation_type="missing_pdb_coordinates",
            incident="AlphaFold modeling failed: cannot resolve structural coordinates due to upstream sequence drift.",
        ),
        _snapshot(
            dataset_id=cox2_matrix.id,
            captured_at=event_time,
            trust_score=39.0,
            schema_gene=docking_schema,
            lineage_gene=[],
            usage_gene={"weekly_queries": 800, "consumers": 9, "last_accessed": event_time.isoformat()},
            owner=cox2_matrix.owner,
            description=cox2_matrix.description,
            mutation_type="broken_docking_endpoint",
            incident="RDKit virtual screening blocked targeting COX-2: missing PDB coordinate files from AlphaFold.",
        ),
        _snapshot(
            dataset_id=tnf_matrix.id,
            captured_at=event_time,
            trust_score=39.0,
            schema_gene=docking_schema,
            lineage_gene=[],
            usage_gene={"weekly_queries": 600, "consumers": 9, "last_accessed": event_time.isoformat()},
            owner=tnf_matrix.owner,
            description=tnf_matrix.description,
            mutation_type="broken_docking_endpoint",
            incident="RDKit virtual screening blocked targeting TNF-alpha: missing PDB coordinate files from AlphaFold.",
        ),
    ]
    db.add_all(snapshots)
    db.flush()

    edges = db.query(LineageEdge).all()
    latest_by_dataset: dict[str, DnaSnapshot] = {}
    for ds_name in [neuro_seq.name, neuro_struct.name, dopamine_matrix.name, peptide_seq.name, peptide_struct.name, cox2_matrix.name, tnf_matrix.name]:
        ds = db.query(Dataset).filter(Dataset.name == ds_name).first()
        latest_by_dataset[ds_name] = (
            db.query(DnaSnapshot).filter(DnaSnapshot.dataset_id == ds.id).order_by(DnaSnapshot.captured_at.desc()).first()
        )

    metrics_by_dataset = {}
    for ds_name in latest_by_dataset.keys():
        ds = db.query(Dataset).filter(Dataset.name == ds_name).first()
        latest = latest_by_dataset[ds_name]
        metrics = current_metrics(db, ds, edges, latest=latest)
        persist_metrics_in_genes(latest, metrics)
        metrics_by_dataset[ds_name] = metrics

    db.commit()

    incident = {
        "dataset": peptide_seq.name,
        "type": "sequence_drift",
        "started_at": event_time.isoformat(),
        "downstream_failed": peptide_struct.name,
        "propagated_to": cox2_matrix.name,
        "status": "active",
    }
    
    timeline_events = [
        {
            "at": baseline_time.isoformat(),
            "dataset": peptide_seq.name,
            "event_type": "baseline_snapshot",
            "message": "Baseline FASTA schema active with standard format column.",
        },
        {
            "at": event_time.isoformat(),
            "dataset": peptide_seq.name,
            "event_type": "sequence_drift",
            "message": "Sequence format column renamed to conformation_format.",
        },
        {
            "at": event_time.isoformat(),
            "dataset": peptide_struct.name,
            "event_type": "missing_pdb_coordinates",
            "message": "AlphaFold run failed: coordinate resolution blocked.",
        },
        {
            "at": event_time.isoformat(),
            "dataset": cox2_matrix.name,
            "event_type": "broken_docking_endpoint",
            "message": "RDKit virtual screening targeting COX-2 docking matrix invalidated.",
        },
        {
            "at": event_time.isoformat(),
            "dataset": tnf_matrix.name,
            "event_type": "broken_docking_endpoint",
            "message": "RDKit virtual screening targeting TNF-alpha docking matrix invalidated.",
        },
    ]

    root_metrics = metrics_by_dataset[peptide_seq.name]
    candidates_invalidated = int(root_metrics['blast_radius'] * 250)
    
    boardroom_brief = {
        "Executive Summary": "A sequence database formatting revision in peptide_fasta_sequences broke the downstream AlphaFold prediction pipeline.",
        "Root Cause": "Upstream sequence format column was renamed to conformation_format, creating a contract drift.",
        "Business Impact": (
            f"Downstream Target Invalidation Scale is {candidates_invalidated} virtual drug screening candidates "
            f"({root_metrics['severity_level']}). virtual screening docking matrices targeting COX-2 and TNF-alpha are currently stale."
        ),
        "Recommended Fix (Now/Next)": (
            "Now: deploy AlphaEvolve JIT script healer to restore sequence format fields. "
            "Next: implement pre-prediction contract checks in bioinformatics ingest jobs."
        ),
        "Confidence + Evidence": (
            "High confidence based on temporal sequence drift logs, missing PDB coordinate alerts, and failed RDKit docking targets."
        ),
    }

    return {
        "datasets": [neuro_seq.name, neuro_struct.name, dopamine_matrix.name, peptide_seq.name, peptide_struct.name, cox2_matrix.name, tnf_matrix.name],
        "lineage": [
            {"source": neuro_seq.name, "target": neuro_struct.name, "is_active": True},
            {"source": neuro_struct.name, "target": dopamine_matrix.name, "is_active": True},
            {"source": peptide_seq.name, "target": peptide_struct.name, "is_active": False},
            {"source": peptide_struct.name, "target": cox2_matrix.name, "is_active": False},
            {"source": peptide_struct.name, "target": tnf_matrix.name, "is_active": False},
        ],
        "incident": incident,
        "metrics": root_metrics,
        "boardroom_brief": boardroom_brief,
        "timeline_events": timeline_events,
    }
