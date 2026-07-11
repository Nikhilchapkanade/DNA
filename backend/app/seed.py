# Lead Researcher: Nikhil Chapkanade | PRN: 20230802111
# Bio-DNA OS Database Seeding Script (Dual-Track)

from __future__ import annotations

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models import Dataset, DnaSnapshot, LineageEdge


def seed_demo_data(db: Session) -> None:
    if db.query(Dataset).count() > 0:
        return

    # Track A
    neuro_seq = Dataset(
        name="neuro_fasta_sequences",
        owner="neuro-discovery-lab",
        description="Small-molecule FASTA target sequences for neurodegenerative receptor binding",
    )
    neuro_struct = Dataset(
        name="neuro_alphafold_structures",
        owner="structural-bioinformatics",
        description="AlphaFold predicted 3D structures for dopamine pathway models",
    )
    dopamine_matrix = Dataset(
        name="neuro_dopamine_docking_matrix",
        owner="computational-docking",
        description="RDKit virtual screening affinity matrix targeting Dopamine D2 receptors",
    )

    # Track B
    peptide_seq = Dataset(
        name="peptide_fasta_sequences",
        owner="nutri-proteomics-lab",
        description="Bioactive nutritional peptide sequences screened for anti-inflammatory efficacy",
    )
    peptide_struct = Dataset(
        name="peptide_alphafold_structures",
        owner="structural-bioinformatics",
        description="AlphaFold predicted 3D structures for bioactive peptides",
    )
    cox2_matrix = Dataset(
        name="peptide_cox2_docking_matrix",
        owner="computational-docking",
        description="RDKit virtual screening docking matrix targeting COX-2 receptors",
    )
    tnf_matrix = Dataset(
        name="peptide_tnf_docking_matrix",
        owner="computational-docking",
        description="RDKit virtual screening docking matrix targeting TNF-alpha receptors",
    )

    db.add_all([neuro_seq, neuro_struct, dopamine_matrix, peptide_seq, peptide_struct, cox2_matrix, tnf_matrix])
    db.flush()

    t0 = datetime.utcnow() - timedelta(hours=4)
    t1 = datetime.utcnow() - timedelta(hours=1)

    # Base genes for Track B
    baseline_genes = {
        "structural_conformation_gene": [
            {"name": "sequence_id", "type": "string", "nullable": False},
            {"name": "peptide_sequence", "type": "string", "nullable": False},
            {"name": "format", "type": "string", "nullable": False},
            {"name": "residue_count", "type": "integer", "nullable": False},
            {"name": "source_organism", "type": "string", "nullable": False},
        ],
        "bio_pathway_lineage_gene": [
            {"source": "peptide_fasta_sequences", "target": "peptide_alphafold_structures", "is_active": True},
        ],
        "target_usage_gene": {"weekly_queries": 2800, "consumers": 24, "last_accessed": t0.isoformat()},
        "ownership_gene": {"owner": "nutri-proteomics-lab", "description": "Bioactive nutritional peptide sequences screened for anti-inflammatory efficacy"},
        "computed_at": t0.isoformat(),
    }

    mutated_genes = {
        "structural_conformation_gene": [
            {"name": "sequence_id", "type": "string", "nullable": False},
            {"name": "peptide_sequence", "type": "string", "nullable": False},
            {"name": "conformation_format", "type": "string", "nullable": False},
            {"name": "residue_count", "type": "integer", "nullable": False},
            {"name": "source_organism", "type": "string", "nullable": False},
        ],
        "bio_pathway_lineage_gene": [
            {"source": "peptide_fasta_sequences", "target": "peptide_alphafold_structures", "is_active": False},
        ],
        "target_usage_gene": {"weekly_queries": 2700, "consumers": 24, "last_accessed": t1.isoformat()},
        "ownership_gene": {"owner": "nutri-proteomics-lab", "description": "Bioactive nutritional peptide sequences screened for anti-inflammatory efficacy"},
        "computed_at": t1.isoformat(),
    }

    db.add_all(
        [
            # Track A: Healthy snapshots
            DnaSnapshot(
                dataset_id=neuro_seq.id,
                captured_at=t0,
                trust_score=95.0,
                genes={
                    "structural_conformation_gene": [
                        {"name": "sequence_id", "type": "string", "nullable": False},
                        {"name": "peptide_sequence", "type": "string", "nullable": False},
                        {"name": "format", "type": "string", "nullable": False},
                    ],
                    "bio_pathway_lineage_gene": [{"source": "neuro_fasta_sequences", "target": "neuro_alphafold_structures", "is_active": True}],
                    "target_usage_gene": {"weekly_queries": 3200, "consumers": 18, "last_accessed": t0.isoformat()},
                    "ownership_gene": {"owner": "neuro-discovery-lab", "description": "Small-molecule FASTA target sequences for neurodegenerative receptor binding"},
                    "computed_at": t0.isoformat(),
                },
                mutation_type=None,
                incident=None,
            ),
            
            # Track B: Mutated snapshots
            DnaSnapshot(dataset_id=peptide_seq.id, captured_at=t0, trust_score=94.0, genes=baseline_genes, mutation_type=None, incident=None),
            DnaSnapshot(
                dataset_id=peptide_seq.id,
                captured_at=t1,
                trust_score=58.0,
                genes=mutated_genes,
                mutation_type="sequence_drift",
                incident="Sequence database revision: format renamed to conformation_format, breaking alignment inputs.",
            ),
            DnaSnapshot(
                dataset_id=peptide_struct.id,
                captured_at=t1,
                trust_score=48.0,
                genes={
                    "structural_conformation_gene": [
                        {"name": "coordinate_id", "type": "string", "nullable": False},
                        {"name": "pdb_raw_content", "type": "string", "nullable": False},
                        {"name": "plddt_confidence", "type": "double", "nullable": False},
                    ],
                    "bio_pathway_lineage_gene": [
                        {"source": "peptide_alphafold_structures", "target": "peptide_cox2_docking_matrix", "is_active": False},
                        {"source": "peptide_alphafold_structures", "target": "peptide_tnf_docking_matrix", "is_active": False}
                    ],
                    "target_usage_gene": {"weekly_queries": 1500, "consumers": 14, "last_accessed": t1.isoformat()},
                    "ownership_gene": {"owner": "structural-bioinformatics", "description": "AlphaFold predicted 3D structures for bioactive peptides"},
                    "computed_at": t1.isoformat(),
                },
                mutation_type="missing_pdb_coordinates",
                incident="AlphaFold modeling failed: cannot resolve structural coordinates due to upstream sequence drift.",
            ),
            DnaSnapshot(
                dataset_id=cox2_matrix.id,
                captured_at=t1,
                trust_score=39.0,
                genes={
                    "structural_conformation_gene": [
                        {"name": "ligand_id", "type": "string", "nullable": False},
                        {"name": "target_receptor", "type": "string", "nullable": False},
                        {"name": "binding_affinity_kcal", "type": "double", "nullable": False},
                    ],
                    "bio_pathway_lineage_gene": [],
                    "target_usage_gene": {"weekly_queries": 800, "consumers": 9, "last_accessed": t1.isoformat()},
                    "ownership_gene": {"owner": "computational-docking", "description": "RDKit virtual screening docking matrix targeting COX-2 receptors"},
                    "computed_at": t1.isoformat(),
                },
                mutation_type="broken_docking_endpoint",
                incident="RDKit virtual screening blocked targeting COX-2: missing PDB coordinate files from AlphaFold.",
            ),
        ]
    )

    db.add_all(
        [
            LineageEdge(source="neuro_fasta_sequences", target="neuro_alphafold_structures", is_active=True, broken_reason=None),
            LineageEdge(source="neuro_alphafold_structures", target="neuro_dopamine_docking_matrix", is_active=True, broken_reason=None),
            LineageEdge(
                source="peptide_fasta_sequences",
                target="peptide_alphafold_structures",
                is_active=False,
                broken_reason="Sequence drift: peptide format column mismatch in upstream database revision",
            ),
            LineageEdge(
                source="peptide_alphafold_structures",
                target="peptide_cox2_docking_matrix",
                is_active=False,
                broken_reason="Molecular docking simulation endpoint blocked by missing 3D coordinate inputs",
            ),
            LineageEdge(
                source="peptide_alphafold_structures",
                target="peptide_tnf_docking_matrix",
                is_active=False,
                broken_reason="Molecular docking simulation endpoint blocked by missing 3D coordinate inputs",
            ),
        ]
    )

    db.commit()
