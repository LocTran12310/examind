"use client";

import { ChevronRight } from "lucide-react";
import { useMemo, useState } from "react";
import { buildTree, type TopicNode } from "@/components/topics/tree";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import type { Topic } from "@/lib/types";
import { cn } from "@/lib/utils";

export function topicLabel(t: Topic, byId: Map<string, Topic>): string {
  const names: string[] = [];
  let cur: Topic | undefined = t;
  while (cur) {
    names.unshift(cur.name);
    cur = cur.parent_id ? byId.get(cur.parent_id) : undefined;
  }
  return names.join(" › ");
}

const fold = (s: string) => s.normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/đ/g, "d").replace(/Đ/g, "D").toLowerCase();

type Row = { node: TopicNode; depth: number; hit: boolean };

/** Topic tree to pick one node (ui-polish AC-04): type to search (accent-insensitive, matches keep
 *  their ancestors), ▸ to open a branch, ↑/↓ to move, Enter or click to pick, Esc to close. */
export function TopicPicker({ topics, onPick, onClose, autoFocus = true }: { topics: Topic[]; onPick: (t: Topic) => void; onClose?: () => void; autoFocus?: boolean }) {
  const [q, setQ] = useState("");
  const [active, setActive] = useState(0);
  const [open, setOpen] = useState<Set<string>>(new Set());
  const roots = useMemo(() => buildTree(topics), [topics]);
  const byId = useMemo(() => new Map(topics.map((t) => [t.id, t])), [topics]);
  const rows = useMemo(() => {
    const needle = fold(q.trim());
    const out: Row[] = [];
    const walk = (n: TopicNode, depth: number): Row[] => {
      const hit = !!needle && fold(n.name).includes(needle);
      const kids = n.children.flatMap((c) => walk(c, depth + 1));
      if (needle) return hit || kids.length ? [{ node: n, depth, hit }, ...kids] : [];
      return [{ node: n, depth, hit: false }, ...(open.has(n.id) ? kids : [])];
    };
    for (const r of roots) out.push(...walk(r, 0));
    return out;
  }, [q, roots, open]);
  const first = Math.max(0, rows.findIndex((r) => r.hit));
  const toggle = (id: string) => setOpen((s) => (s.has(id) ? (s.delete(id), new Set(s)) : new Set(s).add(id)));

  return (
    <div className="space-y-2" data-testid="topic-picker">
      <Input
        autoFocus={autoFocus}
        placeholder="Tìm chuyên đề… (ví dụ: nguyen ham)"
        value={q}
        aria-label="Tìm chuyên đề"
        onChange={(e) => {
          setQ(e.target.value);
          setActive(-1);
        }}
        onKeyDown={(e) => {
          const cur = active < 0 ? first : active;
          if (e.key === "ArrowDown") {
            e.preventDefault();
            setActive(Math.min(cur + 1, rows.length - 1));
          } else if (e.key === "ArrowUp") {
            e.preventDefault();
            setActive(Math.max(cur - 1, 0));
          } else if (e.key === "ArrowRight" && rows[cur]?.node.children.length && !q) {
            e.preventDefault();
            toggle(rows[cur].node.id);
          } else if (e.key === "Enter" && rows[cur]) {
            e.preventDefault();
            onPick(byId.get(rows[cur].node.id)!);
          } else if (e.key === "Escape") {
            onClose?.();
          }
        }}
      />
      <ul className="max-h-[55svh] overflow-y-auto rounded-md border border-border p-1 text-sm" role="tree" aria-label="Cây chuyên đề">
        {rows.map((r, i) => {
          const on = i === (active < 0 ? first : active);
          const expanded = !!q || open.has(r.node.id);
          return (
            <li
              key={r.node.id}
              role="treeitem"
              aria-selected={on}
              aria-expanded={r.node.children.length ? expanded : undefined}
              className={cn("flex cursor-pointer items-center gap-1 rounded-md py-1 pr-2", on ? "bg-primary/10 text-primary" : "hover:bg-muted/60")}
              style={{ paddingLeft: 4 + r.depth * 18 }}
              onMouseEnter={() => setActive(i)}
              onClick={() => onPick(byId.get(r.node.id)!)}
            >
              <Button
                variant="ghost"
                size="icon-xs"
                aria-label={expanded ? `Thu gọn ${r.node.name}` : `Mở rộng ${r.node.name}`}
                className={cn(!r.node.children.length && "invisible")}
                onClick={(e) => {
                  e.stopPropagation();
                  toggle(r.node.id);
                }}
              >
                <ChevronRight className={cn("transition-transform", expanded && "rotate-90")} />
              </Button>
              <span className={cn("truncate", r.depth === 0 && "font-medium", q && !r.hit && "text-muted-foreground")}>{r.node.name}</span>
              {r.node.children.length > 0 && <span className="ml-auto text-xs text-muted-foreground">{r.node.children.length}</span>}
            </li>
          );
        })}
        {rows.length === 0 && <li className="px-3 py-2 text-muted-foreground">Không tìm thấy</li>}
      </ul>
    </div>
  );
}
