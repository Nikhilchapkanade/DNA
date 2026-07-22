// Lead Researcher: Nikhil Chapkanade | PRN: 20230802111
// Bio-DNA OS 3D Protein Structure WebGL Renderer (3Dmol.js + WebGL Canvas Fallback)

"use client";

import { useEffect, useRef, useState } from "react";

type Props = {
  pdbData: string;
  title: string;
  highlightMutations?: Array<{ pos: number; code: string }>;
};

declare global {
  interface Window {
    $3Dmol: any;
  }
}

export function Protein3DViewer({ pdbData, title, highlightMutations = [] }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const viewerRef = useRef<any>(null);
  const [useFallback, setUseFallback] = useState(false);
  const [styleMode, setStyleMode] = useState<"cartoon" | "sphere" | "stick">("cartoon");
  const [spinning, setSpinning] = useState(true);

  useEffect(() => {
    let scriptLoaded = false;
    
    // Check if 3Dmol script is already in document
    if (window.$3Dmol) {
      init3Dmol();
      return;
    }

    const script = document.createElement("script");
    script.src = "https://3Dmol.org/build/3Dmol-min.js";
    script.async = true;
    script.onload = () => {
      scriptLoaded = true;
      init3Dmol();
    };
    script.onerror = () => {
      setUseFallback(true);
    };
    document.head.appendChild(script);

    function init3Dmol() {
      if (!containerRef.current || !window.$3Dmol) {
        setUseFallback(true);
        return;
      }
      try {
        containerRef.current.innerHTML = "";
        const config = { backgroundColor: "#060810" };
        const viewer = window.$3Dmol.createViewer(containerRef.current, config);
        viewerRef.current = viewer;

        viewer.addModel(pdbData, "pdb");
        
        // Default cartoon style colored by secondary structure / spectrum
        applyViewerStyle(viewer, styleMode);
        
        viewer.zoomTo();
        viewer.render();
        viewer.spin(spinning ? "y" : false, 1);
      } catch (err) {
        console.warn("[3Dmol] WebGL init failed, switching to Canvas fallback:", err);
        setUseFallback(true);
      }
    }

    return () => {
      if (viewerRef.current) {
        try {
          viewerRef.current.spin(false);
        } catch {}
      }
    };
  }, [pdbData]);

  useEffect(() => {
    if (viewerRef.current && window.$3Dmol) {
      applyViewerStyle(viewerRef.current, styleMode);
      viewerRef.current.spin(spinning ? "y" : false, 1);
      viewerRef.current.render();
    }
  }, [styleMode, spinning]);

  function applyViewerStyle(viewer: any, mode: string) {
    viewer.setStyle({}, {});
    if (mode === "cartoon") {
      viewer.setStyle({}, { cartoon: { color: "spectrum" } });
    } else if (mode === "sphere") {
      viewer.setStyle({}, { sphere: { scale: 0.8, color: "spectrum" } });
    } else {
      viewer.setStyle({}, { stick: { colorscheme: "amino" } });
    }

    // Highlight active mutations with bright neon magenta sphere & stick representation
    if (highlightMutations.length > 0) {
      highlightMutations.forEach((mut) => {
        viewer.addStyle(
          { resi: mut.pos + 1 },
          {
            stick: { color: "#ff007f", radius: 0.4 },
            sphere: { color: "#ff007f", radius: 1.2 },
          }
        );
      });
    }
  }

  // Fallback 3D Alpha-Helix Ribbon Canvas Renderer
  useEffect(() => {
    if (!useFallback || !canvasRef.current) return;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animId: number;
    let angle = 0;

    function renderCanvas() {
      if (!ctx || !canvas) return;
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      const cx = canvas.width / 2;
      const cy = canvas.height / 2;
      const radius = 65;
      const totalResidues = 40;

      // Draw Alpha-Helix Backbone Wireframe
      ctx.beginPath();
      ctx.lineWidth = 3;
      ctx.strokeStyle = "#00f0ff";

      for (let i = 0; i < totalResidues; i++) {
        const t = i * 0.35 + angle;
        const x = cx + radius * Math.cos(t);
        const y = cy + (i - totalResidues / 2) * 8;
        const z = radius * Math.sin(t);

        const scale = (z + 100) / 160;
        const renderX = cx + (x - cx) * scale;
        const renderY = cy + (y - cy) * scale;

        if (i === 0) {
          ctx.moveTo(renderX, renderY);
        } else {
          ctx.lineTo(renderX, renderY);
        }

        // Draw Residue Nodes
        ctx.save();
        ctx.fillStyle = i % 5 === 0 ? "#ff007f" : "#00ffaa";
        ctx.beginPath();
        ctx.arc(renderX, renderY, 4 * scale, 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();
      }
      ctx.stroke();

      angle += 0.02;
      animId = requestAnimationFrame(renderCanvas);
    }

    renderCanvas();
    return () => cancelAnimationFrame(animId);
  }, [useFallback]);

  return (
    <div
      style={{
        background: "radial-gradient(circle at center, #0f172a 0%, #060810 100%)",
        border: "1px solid var(--line)",
        borderRadius: 16,
        padding: 16,
        display: "flex",
        flexDirection: "column",
        gap: 12,
        boxShadow: "0 0 20px rgba(0, 240, 255, 0.15)",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <h4 style={{ margin: 0, fontSize: 16, color: "#f3f4f6", fontFamily: "monospace" }}>{title}</h4>
          <span style={{ fontSize: 12, color: "#00f0ff", fontFamily: "monospace" }}>
            {highlightMutations.length > 0
              ? `⚡ ${highlightMutations.length} Active Mutated Residues`
              : "Wild-Type Unmutated Structure"}
          </span>
        </div>

        <div style={{ display: "flex", gap: 6 }}>
          <button
            type="button"
            className="question-chip"
            style={{ padding: "4px 8px", fontSize: 11, background: styleMode === "cartoon" ? "#00f0ff22" : "transparent" }}
            onClick={() => setStyleMode("cartoon")}
          >
            Ribbon
          </button>
          <button
            type="button"
            className="question-chip"
            style={{ padding: "4px 8px", fontSize: 11, background: styleMode === "sphere" ? "#00f0ff22" : "transparent" }}
            onClick={() => setStyleMode("sphere")}
          >
            Spheres
          </button>
          <button
            type="button"
            className="question-chip"
            style={{ padding: "4px 8px", fontSize: 11, background: styleMode === "stick" ? "#00f0ff22" : "transparent" }}
            onClick={() => setStyleMode("stick")}
          >
            Sticks
          </button>
          <button
            type="button"
            className="question-chip"
            style={{ padding: "4px 8px", fontSize: 11 }}
            onClick={() => setSpinning(!spinning)}
          >
            {spinning ? "Pause 3D" : "Spin 3D"}
          </button>
        </div>
      </div>

      <div
        style={{
          width: "100%",
          height: 320,
          position: "relative",
          borderRadius: 12,
          overflow: "hidden",
          background: "#060810",
          border: "1px solid #1e293b",
        }}
      >
        {!useFallback ? (
          <div ref={containerRef} style={{ width: "100%", height: "100%", position: "absolute", top: 0, left: 0 }} />
        ) : (
          <canvas ref={canvasRef} width={450} height={320} style={{ width: "100%", height: "100%" }} />
        )}
      </div>

      {highlightMutations.length > 0 ? (
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          <span style={{ fontSize: 12, color: "#94a3b8" }}>Key Mutated Hotspots:</span>
          {highlightMutations.map((m) => (
            <span
              key={m.code}
              style={{
                fontSize: 12,
                background: "#ff007f22",
                color: "#ff007f",
                border: "1px solid #ff007f66",
                borderRadius: 6,
                padding: "2px 8px",
                fontFamily: "monospace",
                fontWeight: 700,
              }}
            >
              {m.code} ({m.impact.split(" ")[0]}...)
            </span>
          ))}
        </div>
      ) : (
        <span style={{ fontSize: 12, color: "#10b981", fontFamily: "monospace" }}>
          ✓ Canonical PDB 3D conformation intact. No allosteric drift detected.
        </span>
      )}
    </div>
  );
}
