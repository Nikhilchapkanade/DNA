// Lead Researcher: Nikhil Chapkanade | PRN: 20230802111
// Bio-DNA OS Navigation

"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  ["/", "AlphaEvolve Studio"],
  ["/graph", "Bio-DNA Graph"],
  ["/timeline", "Timeline"],
  ["/copilot", "Chat Copilot"],
] as const;

export function Nav() {
  const pathname = usePathname();

  return (
    <nav className="nav">
      {links.map(([href, label]) => {
        const active = pathname === href;
        return (
          <Link key={href} href={href} className={active ? "active" : ""}>
            {label}
          </Link>
        );
      })}
    </nav>
  );
}
