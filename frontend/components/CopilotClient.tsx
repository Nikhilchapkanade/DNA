// Lead Researcher: Nikhil Chapkanade | PRN: 20230802111
// Bio-DNA OS Copilot Client

"use client";

import { FormEvent, useEffect, useState } from "react";

const MAGIC_PAYLOAD_KEY = "dnaMagicDemoPayload";
const QUICK_QUESTIONS = [
  "Why did this biological pipeline fail?",
  "Can I trust this biological pipeline today?",
  "What structural conformation drift occurred?",
  "What is the downstream target invalidation scale?",
  "What is the safest sequence restoration strategy?",
];

type GraphNode = {
  id: string;
  label: string;
  risk_score: number;
};

export function CopilotClient() {
  const [question, setQuestion] = useState("Why did this biological pipeline fail?");
  const [dataset, setDataset] = useState("peptide_fasta_sequences");
  const [availableDatasets, setAvailableDatasets] = useState<GraphNode[]>([]);
  const [answer, setAnswer] = useState<string>("");
  const [sections, setSections] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const loadDatasets = async () => {
      try {
        const res = await fetch("/api/graph");
        const data = await res.json();
        if (data?.nodes && Array.isArray(data.nodes)) {
          setAvailableDatasets(data.nodes);
          // Pick the dataset with the highest risk score (most critical incident)
          const sorted = [...data.nodes].sort((a, b) => (b.risk_score || 0) - (a.risk_score || 0));
          if (sorted[0]?.id) {
            setDataset(sorted[0].id);
          }
        }
      } catch {
        // Keep default dataset value if graph fetch fails.
      }
    };
    loadDatasets();

    try {
      const raw = localStorage.getItem(MAGIC_PAYLOAD_KEY);
      if (raw) {
        const payload = JSON.parse(raw) as { boardroom_brief?: Record<string, string>; incident?: { dataset?: string } };
        if (payload.boardroom_brief) {
          setSections(payload.boardroom_brief);
          setAnswer(Object.entries(payload.boardroom_brief).map(([k, v]) => `${k}: ${v}`).join("\n\n"));
        }
        if (payload.incident?.dataset) {
          setDataset(payload.incident.dataset);
        }
      }
    } catch {
      // No magic payload available.
    }
  }, []);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setAnswer("");
    setSections({});
    try {
      const res = await fetch("/api/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ dataset, question }),
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data?.detail || `Request failed (${res.status})`);
      }
      if (data.sections && Object.keys(data.sections).length > 0) {
        setSections(data.sections);
      }
      setAnswer(data.narrative || "No narrative returned");
    } catch (err) {
      setAnswer(`Failed to call copilot: ${(err as Error).message}`);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="grid" style={{ gap: 16 }}>
      <section className="card">
        <h2 className="section-title">Copilot Console</h2>
        <p className="section-kicker">Generate a pipeline incident brief detailing root cause, target invalidation scale, and repair path.</p>
      </section>

      <section className="card">
        <h3>Live Assistant</h3>
        <div className="kv-row" style={{ alignItems: "center", marginTop: 8 }}>
          <span>Target Bio-Asset Scope</span>
          {availableDatasets.length > 0 ? (
            <select
              value={dataset}
              onChange={(e) => setDataset(e.target.value)}
              style={{
                background: "#111827",
                color: "#f3f4f6",
                border: "1px solid var(--line)",
                borderRadius: 8,
                padding: "6px 12px",
                fontSize: 14,
                fontFamily: "monospace",
              }}
            >
              {availableDatasets.map((node) => (
                <option key={node.id} value={node.id}>
                  {node.id} {node.risk_score > 0 ? `(Drift: ${node.risk_score.toFixed(0)})` : "(Healthy)"}
                </option>
              ))}
            </select>
          ) : (
            <span className="mono">{dataset}</span>
          )}
        </div>

        <p className="muted" style={{ marginTop: 16 }}>
          Quick prompt presets:
        </p>
        <div className="question-chips" style={{ marginBottom: 14 }}>
          {QUICK_QUESTIONS.map((item) => (
            <button key={item} type="button" className="question-chip" onClick={() => setQuestion(item)}>
              {item}
            </button>
          ))}
        </div>

        <form onSubmit={onSubmit} className="grid" style={{ gap: 10 }}>
          <textarea className="textarea" rows={3} value={question} onChange={(e) => setQuestion(e.target.value)} />
          <button className="button" type="submit" disabled={loading}>
            {loading ? "Analyzing Pipeline Incident & Building Brief..." : "Generate Executive Brief"}
          </button>
        </form>
      </section>

      <section className="card">
        <h3>Boardroom Brief Analysis</h3>
        {loading ? (
          <div style={{ padding: "20px 0", textAlign: "center", color: "var(--warn)" }}>
            <p style={{ fontWeight: 700, fontSize: 18 }}>⚡ Multi-Agent Reasoning Loop Active...</p>
            <p className="muted">Evaluating structural conformation genes, blast radius, and root cause analysis.</p>
          </div>
        ) : null}

        {!loading && !answer && Object.keys(sections).length === 0 ? (
          <p className="muted">No analysis generated yet. Click "Generate Executive Brief" above.</p>
        ) : null}

        {!loading && Object.keys(sections).length > 0 ? (
          <div className="grid boardroom-grid" style={{ marginTop: 10 }}>
            {Object.entries(sections).map(([title, text]) => (
              <article key={title} className="timeline-item">
                <p style={{ margin: 0, fontWeight: 800, color: "var(--accent)" }}>{title}</p>
                <p className="muted" style={{ marginTop: 6, lineHeight: 1.5 }}>{text}</p>
              </article>
            ))}
          </div>
        ) : null}

        {!loading && answer && Object.keys(sections).length === 0 ? (
          <pre
            style={{
              marginTop: 12,
              whiteSpace: "pre-wrap",
              background: "rgba(8, 15, 39, .82)",
              border: "1px solid var(--line)",
              borderRadius: 14,
              padding: 16,
              fontSize: 14,
              lineHeight: 1.5,
              color: "#f3f4f6",
            }}
          >
            {answer}
          </pre>
        ) : null}
      </section>
    </div>
  );
}
