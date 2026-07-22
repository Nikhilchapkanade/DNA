# Lead Researcher: Nikhil Chapkanade | PRN: 20230802111
# Bio-DNA OS AlphaEvolve Evolutionary Mutation Engine

from __future__ import annotations

import math
from typing import Dict, List, Any


TARGET_PROTEINS: Dict[str, Dict[str, Any]] = {
    "egfr_kinase": {
        "name": "EGFR Kinase Domain (Oncology Target)",
        "pdb_id": "2ITN",
        "wildtype_sequence": (
            "LVKITDFGLAKLLGAEEKEYHAEGGKVPIKWMALESILHRIYTHQSDVWSYGVTVWELMT"
            "FGSKPYDGIPASEISSILEKGERLPQPPICTIDVYMIMVKCWMIDADSRPKFRELIIEFSKMARDPQ"
        ),
        "target_disease": "Non-Small Cell Lung Cancer (NSCLC)",
        "mutations_timeline": [
            {"generation": 1, "pos": 21, "from_aa": "L", "to_aa": "R", "code": "L858R", "impact": "Constitutive kinase activation", "delta_g": -1.2, "pocket": "ATP binding cleft"},
            {"generation": 3, "pos": 52, "from_aa": "T", "to_aa": "M", "code": "T790M", "impact": "Gatekeeper mutation causing steric hindrance to 1st/2nd gen TKIs", "delta_g": -3.8, "pocket": "Gatekeeper residue"},
            {"generation": 6, "pos": 59, "from_aa": "C", "to_aa": "S", "code": "C797S", "impact": "Loss of covalent binding site for Osimertinib (3rd gen TKI)", "delta_g": -5.4, "pocket": "Covalent cysteinyl pocket"},
            {"generation": 9, "pos": 58, "from_aa": "G", "to_aa": "R", "code": "G796R", "impact": "Solvent front mutation blocking 4th gen TKI engagement", "delta_g": -7.1, "pocket": "Solvent front interface"},
        ],
    },
    "spike_rbd": {
        "name": "SARS-CoV-2 Spike Receptor Binding Domain",
        "pdb_id": "6M0J",
        "wildtype_sequence": (
            "RVQPTESIVRFPNITNLCPFGEVFNATRFASVYAWNRKRISNCVADYSVLYNSASFSTFKCYGVSPTKLNDLCFTNVYADSFVIRGDEVRQIAPGQTGKIAD"
            "YNYKLPDDFTGCVIAWNSNNLDSKVGGNYNYLYRLFRKSNLKPFERDISTEIYQAGSTPCNGVEGFNCYFPLQSYGFQPTNGVGYQPYRVVVLSFELLHAPATVCGP"
        ),
        "target_disease": "Viral Immune Evasion & Resistance",
        "mutations_timeline": [
            {"generation": 2, "pos": 48, "from_aa": "N", "to_aa": "Y", "code": "N501Y", "impact": "Enhanced hACE2 receptor affinity (+35%)", "delta_g": -1.8, "pocket": "ACE2 contact loop 1"},
            {"generation": 5, "pos": 31, "from_aa": "E", "to_aa": "K", "code": "E484K", "impact": "Major neutralizing mAb immune escape charge flip", "delta_g": -4.2, "pocket": "Flexible ridge loop"},
            {"generation": 8, "pos": 64, "from_aa": "K", "to_aa": "N", "code": "K417N", "impact": "Class 1/2 antibody neutralization failure", "delta_g": -6.5, "pocket": "Core binding epitope"},
        ],
    },
    "dopamine_drd2": {
        "name": "Dopamine D2 Receptor (Neurological Target)",
        "pdb_id": "6CM4",
        "wildtype_sequence": (
            "MDPLNLSWYDDDLERQNWSRPFNGSDGKADRPHYNYYATLLTLLIAVIVFGNVLVCMAVSREKALQTTTNYLIVSLAVADLLVATLVMPWVVYLEVVGEWKFSRIHC"
            "DIFVTLDVMMCTASILNLCAISIDRYTAVAMPMLYNTRYSSKRRVTVMISIVWVLSFTISCPLLFGLNNTDQNECIIANPAFVVYSSIVSFYVPFIVTLLVYIKIYIV"
        ),
        "target_disease": "Parkinson's & Schizophrenia Drug Resistance",
        "mutations_timeline": [
            {"generation": 3, "pos": 72, "from_aa": "S", "to_aa": "A", "code": "S197A", "impact": "Agonist binding pocket hydrogen bond disruption", "delta_g": -2.4, "pocket": "Orthosteric binding pocket"},
            {"generation": 7, "pos": 115, "from_aa": "F", "to_aa": "V", "code": "F389V", "impact": "G-protein transducer uncoupling & signaling bias", "delta_g": -5.1, "pocket": "Allosteric intracellular loop 3"},
        ],
    },
}


class AlphaEvolveEngine:
    def list_targets(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": target_id,
                "name": data["name"],
                "pdb_id": data["pdb_id"],
                "target_disease": data["target_disease"],
                "sequence_length": len(data["wildtype_sequence"]),
            }
            for target_id, data in TARGET_PROTEINS.items()
        ]

    def simulate_evolution(self, target_id: str, max_generation: int = 10) -> Dict[str, Any]:
        target = TARGET_PROTEINS.get(target_id)
        if not target:
            target_id = "egfr_kinase"
            target = TARGET_PROTEINS["egfr_kinase"]

        wt_seq = target["wildtype_sequence"]
        mutated_seq_chars = list(wt_seq)
        
        active_mutations = []
        cumulative_delta_g = 0.0
        
        # Apply mutations up to max_generation
        for mut in target["mutations_timeline"]:
            if mut["generation"] <= max_generation:
                pos = mut["pos"]
                if pos < len(mutated_seq_chars):
                    mutated_seq_chars[pos] = mut["to_aa"]
                    active_mutations.append(mut)
                    cumulative_delta_g += mut["delta_g"]

        mutated_seq = "".join(mutated_seq_chars)
        
        # Calculate structural metrics
        rmsd = round(0.45 * len(active_mutations) + 0.12 * (max_generation / 2.0), 2)
        plddt_confidence = round(max(55.0, 94.5 - 3.2 * len(active_mutations) - 0.5 * max_generation), 1)
        invalidation_scale = len(active_mutations) * 350 + (max_generation * 40)
        
        # Generate PDB coordinates for Wild-Type and Mutated Variant
        wt_pdb = self._generate_pdb(target["pdb_id"], wt_seq, "WILDTYPE", active_mutations=[])
        var_pdb = self._generate_pdb(target["pdb_id"], mutated_seq, f"GEN_{max_generation}_VARIANT", active_mutations=active_mutations)

        # Build evolutionary timeline steps
        timeline = []
        for g in range(1, max_generation + 1):
            g_muts = [m for m in target["mutations_timeline"] if m["generation"] <= g]
            timeline.append({
                "generation": g,
                "active_mutations_count": len(g_muts),
                "latest_mutation": g_muts[-1]["code"] if g_muts else "None",
                "delta_g": round(sum(m["delta_g"] for m in g_muts), 2),
                "plddt": round(max(55.0, 94.5 - 3.2 * len(g_muts) - 0.5 * g), 1),
            })

        return {
            "target_id": target_id,
            "target_name": target["name"],
            "pdb_id": target["pdb_id"],
            "target_disease": target["target_disease"],
            "generation": max_generation,
            "wildtype_sequence": wt_seq,
            "mutated_sequence": mutated_seq,
            "active_mutations": active_mutations,
            "cumulative_delta_g_kcal": round(cumulative_delta_g, 2),
            "rmsd_angstrom": rmsd,
            "plddt_confidence": plddt_confidence,
            "invalidated_candidates": invalidation_scale,
            "wildtype_pdb": wt_pdb,
            "mutated_pdb": var_pdb,
            "evolution_timeline": timeline,
            "conserved_allosteric_pockets": [
                {"pocket_id": "POCKET_ALPHA", "residues": "Res 45-58", "conserved_score": 0.94, "status": "accessible"},
                {"pocket_id": "POCKET_BETA", "residues": "Res 102-118", "conserved_score": 0.88, "status": "partially_occluded" if max_generation >= 6 else "accessible"},
            ],
        }

    def _generate_pdb(self, pdb_id: str, sequence: str, title: str, active_mutations: List[Dict[str, Any]]) -> str:
        lines = [
            f"HEADER    ALPHAEVOLVE 3D MODEL FOR {title}",
            f"REMARK    RESEARCHER: NIKHIL CHAPKANADE | PRN: 20230802111",
            f"REMARK    PDB SOURCE TEMPLATE: {pdb_id}",
            "MODEL        1",
        ]
        
        mut_positions = {m["pos"]: m["code"] for m in active_mutations}
        
        for idx, aa in enumerate(sequence):
            res_num = idx + 1
            # Add spatial coordinates forming an alpha helix structure
            angle = idx * 1.5
            x = round(5.0 * math.cos(angle), 3)
            y = round(5.0 * math.sin(angle), 3)
            z = round(1.5 * idx, 3)
            
            is_mutated = idx in mut_positions
            b_factor = 99.00 if is_mutated else 20.00
            
            lines.append(
                f"ATOM   {res_num:4d}  CA  {aa:3s} A{res_num:4d}    {x:8.3f}{y:8.3f}{z:8.3f}  1.00{b_factor:6.2f}           C"
            )
            
        lines.append("ENDMDL")
        lines.append("END")
        return "\n".join(lines)
