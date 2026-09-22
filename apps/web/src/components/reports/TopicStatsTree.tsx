"use client";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useMemo, useState } from "react";
import { ScoreBar } from "@/components/common/ScoreBar/ScoreBar";
import type { TopicStat } from "@/lib/types";

interface Node extends TopicStat {
  children: Node[];
}

export function statTree(rows: TopicStat[]): Node[] {
  const byId = new Map<string, Node>();
  rows.forEach((r) => byId.set(r.id ?? `none-${r.name}`, { ...r, children: [] }));
  const roots: Node[] = [];
  for (const n of byId.values()) {
    const parent = n.parent_id ? byId.get(n.parent_id) : undefined;
    (parent ? parent.children : roots).push(n);
  }
  const sort = (xs: Node[]) => {
    xs.sort((a, b) => a.path.localeCompare(b.path));
    xs.forEach((x) => sort(x.children));
  };
  sort(roots);
  return roots;
}

export function TopicStatsTree({ rows }: { rows: TopicStat[] }) {
  const roots = useMemo(() => statTree(rows), [rows]);
  const [open, setOpen] = useState<Set<string>>(() => new Set(roots.map((r) => r.path)));
  const toggle = (p: string) =>
    setOpen((s) => {
      const n = new Set(s);
      if (n.has(p)) n.delete(p);
      else n.add(p);
      return n;
    });

  function row(n: Node, depth: number): React.ReactNode {
    const expanded = open.has(n.path);
    return (
      <li key={n.path || n.name}>
        <div className="grid grid-cols-[1fr_120px_48px_60px] items-center gap-2 py-1 text-sm" style={{ paddingLeft: depth * 18 }} data-testid={`ts-${n.name}`}>
          <Button type="button" variant="ghost" className={cn("block h-auto truncate rounded-sm p-0 text-left font-normal hover:bg-transparent", depth === 0 && "font-semibold")} onClick={() => n.children.length && toggle(n.path)} aria-expanded={n.children.length ? expanded : undefined}>
            <span className={cn("mr-1 inline-block w-4 text-muted-foreground/70", !n.children.length && "invisible")}>{expanded ? "▾" : "▸"}</span>
            {n.name}
          </Button>
          <ScoreBar ratio={n.ratio ?? 0} />
          <span className="text-right font-medium">{n.ratio === null ? "—" : `${Math.round(n.ratio * 100)}%`}</span>
          <span className="text-right text-xs text-muted-foreground">{n.answered} lượt</span>
        </div>
        {expanded && n.children.length > 0 && <ul>{n.children.map((c) => row(c, depth + 1))}</ul>}
      </li>
    );
  }

  if (!rows.length) return <p className="text-sm text-muted-foreground">Chưa có dữ liệu làm bài.</p>;
  return <ul data-testid="topic-stats">{roots.map((r) => row(r, 0))}</ul>;
}

export function weakest(rows: TopicStat[], n = 5): TopicStat[] {
  const leaves = rows.filter((r) => r.id && !rows.some((c) => c.parent_id === r.id) && r.answered >= 1 && r.ratio !== null);
  return [...leaves].sort((a, b) => (a.ratio ?? 1) - (b.ratio ?? 1)).slice(0, n);
}
