# Lead Researcher: Nikhil Chapkanade | PRN: 20230802111
# Bio-DNA OS Biological Mutation Tracking Engine

from __future__ import annotations


def compute_schema_diff(previous_genes: dict, current_genes: dict) -> dict:
    """
    Computes structural conformation diffs (substitutions, deletions, insertions)
    on target biological residue datasets.
    """
    prev_list = previous_genes.get("structural_conformation_gene", [])
    curr_list = current_genes.get("structural_conformation_gene", [])
    
    prev_dict = {col["name"]: col["type"] for col in prev_list if "name" in col}
    curr_dict = {col["name"]: col["type"] for col in curr_list if "name" in col}
    
    substitutions = []
    deletions = []
    insertions = []
    
    for name, prev_type in prev_dict.items():
        if name not in curr_dict:
            deletions.append({"residue": name, "original_type": prev_type})
        elif curr_dict[name] != prev_type:
            substitutions.append({"residue": name, "from_type": prev_type, "to_type": curr_dict[name]})
            
    for name, curr_type in curr_dict.items():
        if name not in prev_dict:
            insertions.append({"residue": name, "new_type": curr_type})
            
    return {
        "added": sorted([{"name": c["residue"], "type": c["new_type"]} for c in insertions], key=lambda x: x["name"]),
        "removed": sorted([{"name": c["residue"], "type": c["original_type"]} for c in deletions], key=lambda x: x["name"]),
        "mutations": {
            "substitutions": substitutions,
            "deletions": deletions,
            "insertions": insertions
        }
    }


def compute_lineage_diff(previous_genes: dict, current_genes: dict) -> dict:
    prev = {(e["source"], e["target"], e.get("is_active", True)) for e in previous_genes.get("bio_pathway_lineage_gene", [])}
    curr = {(e["source"], e["target"], e.get("is_active", True)) for e in current_genes.get("bio_pathway_lineage_gene", [])}
    return {
        "activated": [{"source": e[0], "target": e[1]} for e in curr - prev if e[2]],
        "deactivated": [{"source": e[0], "target": e[1]} for e in curr - prev if not e[2]],
    }
