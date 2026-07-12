# Lead Researcher: Nikhil Chapkanade | PRN: 20230802111
# Bio-DNA OS ESMFold Client

from __future__ import annotations

import httpx


class ESMFoldClient:
    def __init__(self) -> None:
        self.api_url = "https://api.esmatlas.com/fold/v1/pdb/"

    async def fold_sequence(self, sequence: str) -> str:
        """
        POSTs raw amino acid sequence to Meta's ESMFold API and returns the PDB text content.
        Includes a fallback PDB model if offline or rate-limited.
        """
        clean_seq = "".join(sequence.split()).replace("-", "").upper()
        if not clean_seq:
            raise ValueError("Empty peptide sequence provided")

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(self.api_url, content=clean_seq)
                resp.raise_for_status()
                return resp.text
        except Exception as exc:
            # Fallback PDB content if offline
            print(f"[ESMFold] API query failed: {exc}. Using fallback PDB generator.")
            return self._generate_fallback_pdb(clean_seq)

    def _generate_fallback_pdb(self, sequence: str) -> str:
        lines = [
            f"HEADER    OFFLINE FALLBACK 3D COORDINATES GENERATED FOR: {sequence[:30]}",
            f"TITLE     RESEARCHER: NIKHIL CHAPKANADE | PRN: 20230802111",
            "MODEL        1",
        ]
        for idx, aa in enumerate(sequence):
            x = 1.25 * idx
            y = 0.5 * (idx % 2)
            z = -0.75 * (idx % 3)
            lines.append(
                f"ATOM   {idx+1:4d}  CA  {aa:3s} A{idx+1:4d}    {x:8.3f}{y:8.3f}{z:8.3f}  1.00 20.00           C"
            )
        lines.append("ENDMDL")
        lines.append("END")
        return "\n".join(lines)
