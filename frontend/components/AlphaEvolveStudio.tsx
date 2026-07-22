// Lead Researcher: Nikhil Chapkanade | PRN: 20230802111
// Chronos-Rx & AlphaEvolve Studio Workstation Component

"use client";

import { useEffect, useState } from "react";
import { Protein3DViewer } from "./Protein3DViewer";

type TargetInfo = {
  id: string;
  name: string;
  pdb_id: string;
  target_disease: string;
};

type SimulationData = {
  target_id: string;
  target_name: string;
  pdb_id: string;
  target_disease: string;
  generation: number;
  wildtype_sequence: string;
  mutated_sequence: string;
  active_mutations: Array<{ generation: number; pos: number; from_aa: string; to_aa: string; code: string; impact: string; delta_g: number; pocket: string }>;
  cumulative_delta_g_kcal: number;
  rmsd_angstrom: number;
  plddt_confidence: number;
  invalidated_candidates: number;
  wildtype_pdb: string;
  mutated_pdb: string;
  evolution_timeline: Array<{ generation: number; active_mutations_count: number; latest_mutation: string; delta_g: number; plddt: number }>;
  conserved_allosteric_pockets: Array<{ pocket_id: string; residues: string; conserved_score: number; status: string }>;
};

type Candidate = {
  id: string;
  type: string;
  sequence: string;
  smiles: string;
  predicted_kd_nm: number;
  binding_affinity_kcal: number;
  lipinski_score: number;
  target_pocket: string;
  mechanism: string;
  synthesis_feasibility: string;
};

export function AlphaEvolveStudio() {
  const [targets, setTargets] = useState<TargetInfo[]>([]);
  const [selectedTarget, setSelectedTarget] = useState("egfr_kinase");
  const [generation, setGeneration] = useState(6);
  const [simulation, setSimulation] = useState<SimulationData | null>(null);
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [loadingSim, setLoadingSim] = useState(false);
  const [loadingDesign, setLoadingDesign] = useState(false);

  useEffect(() => {
    fetchTargets();
  }, []);

  useEffect(() => {
    runSimulation(selectedTarget, generation);
  }, [selectedTarget, generation]);

  async function fetchTargets() {
    try {
      const res = await fetch("http://localhost:8000/alphaevolve/targets");
      const data = await res.json();
      if (data?.targets) {
        setTargets(data.targets);
      }
    } catch (err) {
      console.warn("Failed to fetch targets:", err);
    }
  }

  async function runSimulation(targetId: str, gen: number) {
    setLoadingSim(true);
    setCandidates([]);
    try {
      const res = await fetch("http://localhost:8000/alphaevolve/simulate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ target_id: targetId, generation: gen }),
      });
      const data = await res.json();
      setSimulation(data);
    } catch (err) {
      console.error("Simulation failed:", err);
    } finally {
      setLoadingSim(false);
    }
  }

  async function triggerDeNovoDesign() {
    setLoadingDesign(true);
    try {
      const res = await fetch("http://localhost:8000/denovo/design", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ target_id: selectedTarget, generation }),
      });
      const data = await res.json();
      if (data?.candidates) {
        setCandidates(data.candidates);
      }
    } catch (err) {
      console.error("De Novo design failed:", err);
    } finally {
      setLoadingDesign(false);
    }
  }

  return (
    <div className="grid" style={{ gap: 20 }}>
      {/* Header Banner */}
      <section className="card" style={{ borderLeft: "4px solid #00f0ff" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 12 }}>
          <div>
            <h2 className="section-title" style={{ fontSize: 28, color: "#f3f4f6" }}>
              Chronos-Rx & AlphaEvolve Studio
            </h2>
            <p className="section-kicker" style={{ fontSize: 14 }}>
              Evolutionary GNN Infrastructure for De Novo Target Selection & Mutation-Resistant Drug Design
            </p>
          </div>
          <div style={{ textAlign: "right" }}>
            <span style={{ fontSize: 12, background: "#00f0ff22", color: "#00f0ff", border: "1px solid #00f0ff66", padding: "4px 10px", borderRadius: 8, fontFamily: "monospace" }}>
              Lead Researcher: Nikhil Chapkanade | PRN: 20230802111
            </span>
          </div>
        </div>
      </section>

      {/* Target Selector & Evolutionary Generation Slider */}
      <section className="card" style={{ background: "#0a0d18" }}>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
          <div>
            <label style={{ fontSize: 13, color: "#94a3b8", display: "block", marginBottom: 6, fontWeight: 700 }}>
              SELECT TARGET PROTEIN / RECEPTOR:
            </label>
            <select
              value={selectedTarget}
              onChange={(e) => setSelectedTarget(e.target.value)}
              style={{
                width: "100%",
                background: "#0f172a",
                color: "#00f0ff",
                border: "1px solid #00f0ff44",
                borderRadius: 10,
                padding: "10px 14px",
                fontSize: 15,
                fontWeight: 700,
                fontFamily: "monospace",
              }}
            >
              {targets.length > 0 ? (
                targets.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.name} (PDB: {t.pdb_id})
                  </option>
                ))
              ) : (
                <>
                  <option value="egfr_kinase">EGFR Kinase Domain (Oncology Target - 2ITN)</option>
                  <option value="spike_rbd">SARS-CoV-2 Spike RBD (Viral Evasion - 6M0J)</option>
                  <option value="dopamine_drd2">Dopamine D2 Receptor (Neurology - 6CM4)</option>
                </>
              )}
            </select>
          </div>

          <div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
              <label style={{ fontSize: 13, color: "#94a3b8", fontWeight: 700 }}>
                EVOLUTIONARY GENERATION TRAJECTORY:
              </label>
              <span style={{ fontSize: 15, color: "#ff007f", fontWeight: 900, fontFamily: "monospace" }}>
                Generation {generation} / 10
              </span>
            </div>
            <input
              type="range"
              min={1}
              max={10}
              value={generation}
              onChange={(e) => setGeneration(Number(e.target.value))}
              style={{
                width: "100%",
                accentColor: "#ff007f",
                height: 8,
                borderRadius: 4,
                cursor: "pointer",
                marginTop: 8,
              }}
            />
          </div>
        </div>
      </section>

      {/* KPI Metrics Strip */}
      {simulation ? (
        <section className="kpi-strip">
          <article className="card kpi-mini" style={{ borderTop: "3px solid #ff007f" }}>
            <h4>Affinity Shift (ΔΔG)</h4>
            <p style={{ color: "#ff007f" }}>
              {simulation.cumulative_delta_g_kcal} <span>kcal/mol</span>
            </p>
          </article>
          <article className="card kpi-mini" style={{ borderTop: "3px solid #00f0ff" }}>
            <h4>Structural RMSD</h4>
            <p style={{ color: "#00f0ff" }}>
              {simulation.rmsd_angstrom} <span>Å</span>
            </p>
          </article>
          <article className="card kpi-mini" style={{ borderTop: "3px solid #10b981" }}>
            <h4>pLDDT Confidence</h4>
            <p style={{ color: "#10b981" }}>
              {simulation.plddt_confidence}% <span>score</span>
            </p>
          </article>
          <article className="card kpi-mini" style={{ borderTop: "3px solid #f59e0b" }}>
            <h4>Target Invalidation</h4>
            <p style={{ color: "#f59e0b" }}>
              {simulation.invalidated_candidates} <span>candidates</span>
            </p>
          </article>
        </section>
      ) : null}

      {/* Side-by-Side 3D WebGL Protein Viewers */}
      {simulation ? (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
          <Protein3DViewer
            pdbData={simulation.wildtype_pdb}
            title={`Wild-Type Canonical Conformation (${simulation.pdb_id})`}
            highlightMutations={[]}
          />
          <Protein3DViewer
            pdbData={simulation.mutated_pdb}
            title={`AlphaEvolve Mutated Variant (Gen ${generation})`}
            highlightMutations={simulation.active_mutations}
          />
        </div>
      ) : null}

      {/* Active Mutations & Conserved Allosteric Pockets */}
      {simulation ? (
        <div style={{ display: "grid", gridTemplateColumns: "1.2fr 0.8fr", gap: 16 }}>
          <section className="card">
            <h3>Active Mutation Escape Profile (Gen {generation})</h3>
            {simulation.active_mutations.length === 0 ? (
              <p className="muted">No mutations introduced at Gen 1 baseline.</p>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: 10, marginTop: 12 }}>
                {simulation.active_mutations.map((m) => (
                  <div
                    key={m.code}
                    style={{
                      background: "#111827",
                      border: "1px solid #ff007f44",
                      borderRadius: 10,
                      padding: 12,
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                    }}
                  >
                    <div>
                      <span style={{ fontSize: 16, fontWeight: 900, color: "#ff007f", fontFamily: "monospace" }}>
                        {m.code}
                      </span>
                      <span style={{ fontSize: 12, color: "#94a3b8", marginLeft: 10 }}>[Gen {m.generation}]</span>
                      <p style={{ margin: "4px 0 0", fontSize: 13, color: "#e2e8f0" }}>{m.impact}</p>
                    </div>
                    <div style={{ textAlign: "right" }}>
                      <span style={{ fontSize: 13, fontWeight: 700, color: "#ff007f" }}>{m.delta_g} kcal/mol</span>
                      <p style={{ margin: "2px 0 0", fontSize: 11, color: "#00f0ff", fontFamily: "monospace" }}>{m.pocket}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>

          <section className="card">
            <h3>GNN Conserved Allosteric Pockets</h3>
            <p className="section-kicker">Alternative binding sites mapped by Graph Neural Network for de novo targeting.</p>
            <div style={{ display: "flex", flexDirection: "column", gap: 10, marginTop: 12 }}>
              {simulation.conserved_allosteric_pockets.map((p) => (
                <div key={p.pocket_id} style={{ background: "#0f172a", border: "1px solid #10b98144", borderRadius: 10, padding: 12 }}>
                  <div style={{ display: "flex", justifyContent: "space-between" }}>
                    <span style={{ fontWeight: 800, color: "#10b981", fontFamily: "monospace" }}>{p.pocket_id}</span>
                    <span className="data-pill good">{(p.conserved_score * 100).toFixed(0)}% conserved</span>
                  </div>
                  <p style={{ margin: "6px 0 0", fontSize: 12, color: "#94a3b8" }}>Residues: {p.residues}</p>
                </div>
              ))}
            </div>
          </section>
        </div>
      ) : null}

      {/* De Novo Counter-Therapeutic Designer Section */}
      <section className="card" style={{ border: "1px solid #00f0ff" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 12 }}>
          <div>
            <h3>De Novo Counter-Therapeutic Multi-Agent Designer</h3>
            <p className="section-kicker">Generate novel peptide and small-molecule candidates engineered to intercept the predicted mutation.</p>
          </div>
          <button
            type="button"
            className="button"
            style={{ background: "linear-gradient(135deg, #00f0ff 0%, #ff007f 100%)", color: "#ffffff", fontWeight: 800, padding: "12px 24px" }}
            onClick={triggerDeNovoDesign}
            disabled={loadingDesign}
          >
            {loadingDesign ? "Designing De Novo Candidates..." : "⚡ Run De Novo Ligand Designer"}
          </button>
        </div>

        {candidates.length > 0 ? (
          <div className="grid-3" style={{ marginTop: 16 }}>
            {candidates.map((c) => (
              <article key={c.id} className="card" style={{ background: "#0f172a", border: "1px solid #00f0ff44" }}>
                <span style={{ fontSize: 11, color: "#00f0ff", fontFamily: "monospace", fontWeight: 700 }}>{c.type}</span>
                <h4 style={{ margin: "4px 0 8px", fontSize: 16, color: "#ffffff" }}>{c.id}</h4>
                <div style={{ fontSize: 12, color: "#94a3b8", display: "flex", flexDirection: "column", gap: 4 }}>
                  <div><strong>Target Pocket:</strong> {c.target_pocket}</div>
                  <div><strong>Kd Affinity:</strong> <span style={{ color: "#10b981", fontWeight: 800 }}>{c.predicted_kd_nm} nM</span> ({c.binding_affinity_kcal} kcal/mol)</div>
                  <div><strong>Mechanism:</strong> {c.mechanism}</div>
                  <div style={{ wordBreak: "break-all", fontFamily: "monospace", fontSize: 11, color: "#00f0ff", marginTop: 6, background: "#060810", padding: 6, borderRadius: 6 }}>
                    SMILES: {c.smiles}
                  </div>
                </div>
              </article>
            ))}
          </div>
        ) : null}
      </section>
    </div>
  );
}
