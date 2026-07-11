// Lead Researcher: Nikhil Chapkanade | PRN: 20230802111
// Bio-DNA OS GraphView Component (React Flow Parallel Layout)

"use client";

import "reactflow/dist/style.css";
import ReactFlow, { Background, Controls, MarkerType } from "reactflow";

type Props = {
  data: {
    nodes: Array<{
      id: string;
      label: string;
      trust_score: number;
      mutation?: string | null;
      risk_score: number;
      blast_radius: number;
      severity_level: "low" | "medium" | "high" | "critical";
    }>;
    edges: Array<{ id: string; source: string; target: string; is_active: boolean; severity_level?: string }>;
  };
};

function trustTone(score: number): string {
  if (score > 80) return "#10b981"; // healthy green
  if (score > 65) return "#f59e0b"; // warning orange
  return "#ef4444"; // critical red
}

function severityTone(level: string): string {
  if (level === "critical") return "#ef4444";
  if (level === "high") return "#f59e0b";
  if (level === "medium") return "#3b82f6";
  return "#10b981";
}

function compactLabel(input: string): string {
  return input;
}

export function GraphView({ data }: Props) {
  const nodes = data.nodes.map((n) => {
    const severity = severityTone(n.severity_level);
    const tone = trustTone(n.trust_score);
    
    // Deterministic layout coordinates for the parallel bi-branch architecture
    let x = 100;
    let y = 100;
    
    if (n.id === "neuro_fasta_sequences") { x = 80; y = 100; }
    else if (n.id === "neuro_alphafold_structures") { x = 360; y = 100; }
    else if (n.id === "neuro_dopamine_docking_matrix") { x = 640; y = 100; }
    else if (n.id === "peptide_fasta_sequences") { x = 80; y = 350; }
    else if (n.id === "peptide_alphafold_structures") { x = 360; y = 350; }
    else if (n.id === "peptide_cox2_docking_matrix") { x = 640; y = 260; }
    else if (n.id === "peptide_tnf_docking_matrix") { x = 640; y = 440; }
    
    const invalidatedCandidates = n.blast_radius * 250;
    
    return {
      id: n.id,
      position: { x, y },
      data: {
        label: `${compactLabel(n.label)}\nIntegrity ${n.trust_score.toFixed(0)} • Drift ${n.risk_score.toFixed(0)}\nInvalidated ${invalidatedCandidates}`,
      },
      style: {
        border: `2px solid ${severity}`,
        background: "#0c0d12",
        color: "#f3f4f6",
        borderRadius: 14,
        padding: 14,
        width: 230,
        fontSize: 12,
        fontFamily: "monospace",
        whiteSpace: "pre-wrap",
        textAlign: "center" as const,
        boxShadow: `0 0 10px ${tone}44`,
      },
    };
  });

  const edges = data.edges.map((e) => {
    const isBroken = !e.is_active;
    return {
      id: e.id,
      source: e.source,
      target: e.target,
      animated: isBroken, // animated cascade for broken flows
      markerEnd: { type: MarkerType.ArrowClosed, color: isBroken ? "#ef4444" : "#10b981" },
      style: {
        stroke: isBroken ? "#ef4444" : "#10b981", // red for broken, green for active
        strokeWidth: isBroken ? 3.5 : 2.5,
        strokeDasharray: isBroken ? "6,6" : "none",
      },
    };
  });

  return (
    <div className="card graph-shell" style={{ height: 550, background: "#06070a", border: "1px solid #1f2937" }}>
      <ReactFlow
        fitView
        proOptions={{ hideAttribution: true }}
        nodes={nodes}
        edges={edges}
        defaultViewport={{ x: 0, y: 0, zoom: 0.85 }}
      >
        <Controls />
        <Background color="#1f2937" gap={25} size={1} />
      </ReactFlow>
    </div>
  );
}
