"use client";

import { ChevronRight } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { Topic } from "@/interfaces/topic.interface";
import { cn } from "@/lib/utils";
import { expand, indexTree, state, toggle, topMost } from "@/lib/common/topic-selection";
import { buildTree, type TopicNode } from "@/lib/common/topic-tree";

const fold = (s: string) => s.normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/đ/g, "d").replace(/Đ/g, "D").toLowerCase();

/** Checkbox tree of topics; choosing a parent includes all its children. `value`/`onApply` use top-most ids.
 *  With `onChange` instead of `onApply` it is embedded (no buttons, every tick reported); `counts`
 *  shows the number of questions in each subtree (pickers-builder ADR-01) and is the only number shown.
 *  `initial` is where a suggestion points: its branch opens and the row is scrolled to and marked, still
 *  unticked — the teacher confirms (A-01). */
export function TopicTreeSelect({
  topics,
  value,
  onApply,
  onChange,
  onCancel,
  counts,
  initial,
}: {
  topics: Topic[];
  value: string[];
  onApply?: (ids: string[]) => void;
  onChange?: (ids: string[]) => void;
  onCancel?: () => void;
  counts?: Record<string, number>;
  initial?: string | null;
}) {
  const roots = useMemo(() => buildTree(topics), [topics]);
  const ix = useMemo(() => indexTree(roots), [roots]);
  const [checked, setChecked] = useState<Set<string>>(() => expand(ix, value));
  const [q, setQ] = useState("");
  const [open, setOpen] = useState<Set<string>>(() => {
    // open the path to every selected node, and the first level
    const s = new Set<string>(roots.map((r) => r.id));
    for (const id of value) for (let p = ix.parent.get(id); p; p = ix.parent.get(p)) s.add(p);
    return s;
  });

  // the branch of the suggestion, opened and scrolled to as soon as the tree holds it — nothing is ticked
  const rows = useRef(new Map<string, HTMLDivElement>());
  const landed = useRef<string | null>(null);
  useEffect(() => {
    if (!initial || landed.current === initial || !ix.parent.has(initial)) return;
    landed.current = initial;
    setOpen((s) => {
      const n = new Set(s);
      for (let p = ix.parent.get(initial); p; p = ix.parent.get(p)) n.add(p);
      return n;
    });
  }, [initial, ix]);
  useEffect(() => {
    if (initial) rows.current.get(initial)?.scrollIntoView?.({ block: "center" });
  }, [initial, open]);

  // search keeps matches and their ancestors, opened
  const visible = useMemo(() => {
    const needle = fold(q.trim());
    if (!needle) return null;
    const keep = new Set<string>();
    const walk = (n: TopicNode): boolean => {
      const hit = fold(n.name).includes(needle);
      const kid = n.children.map(walk).some(Boolean);
      if (hit || kid) keep.add(n.id);
      return hit || kid;
    };
    roots.forEach(walk);
    return keep;
  }, [q, roots]);

  const row = (n: TopicNode, depth: number): React.ReactNode => {
    if (visible && !visible.has(n.id)) return null;
    const expanded = visible ? true : open.has(n.id);
    const st = state(ix, checked, n.id);
    const empty = !!counts && !counts[n.id];
    return (
      <li key={n.id}>
        <div
          ref={(el) => {
            if (el) rows.current.set(n.id, el);
            else rows.current.delete(n.id);
          }}
          data-suggested={n.id === initial ? "true" : undefined}
          className={cn("flex items-center gap-1 rounded-md py-0.5 pr-2 hover:bg-muted/60", n.id === initial && "bg-primary/10 ring-1 ring-primary/30 ring-inset")}
          style={{ paddingLeft: depth * 18 }}
        >
          <Button
            variant="ghost"
            size="icon-xs"
            aria-label={expanded ? `Thu gọn ${n.name}` : `Mở rộng ${n.name}`}
            className={cn(!n.children.length && "invisible")}
            onClick={() => setOpen((s) => (s.has(n.id) ? (s.delete(n.id), new Set(s)) : new Set(s).add(n.id)))}
          >
            <ChevronRight className={cn("transition-transform", expanded && "rotate-90")} />
          </Button>
          <Label className="min-w-0 flex-1 cursor-pointer font-normal leading-normal">
            <Checkbox
              checked={st}
              onCheckedChange={() => {
                const next = toggle(ix, checked, n.id);
                setChecked(next);
                onChange?.(topMost(ix, next));
              }}
              aria-label={n.name}
            />
            <span className={cn("truncate", depth === 0 && "font-medium", empty && "text-muted-foreground")}>{n.name}</span>
            {counts && (
              <span className={cn("ml-auto text-xs tabular-nums", empty ? "text-muted-foreground/60" : "text-muted-foreground")} title={`${counts[n.id] ?? 0} câu hỏi`}>
                {counts[n.id] ?? 0}
              </span>
            )}
          </Label>
        </div>
        {expanded && n.children.length > 0 && <ul>{n.children.map((c) => row(c, depth + 1))}</ul>}
      </li>
    );
  };

  const count = topMost(ix, checked).length;
  return (
    <div className="grid gap-2" data-testid="topic-tree-select">
      <Input autoFocus={!onChange} placeholder="Tìm chuyên đề… (ví dụ: nguyen ham)" value={q} onChange={(e) => setQ(e.target.value)} aria-label="Tìm chuyên đề" />
      <ul className="max-h-[50svh] overflow-y-auto rounded-md border p-1" role="tree" aria-label="Cây chuyên đề">
        {roots.map((r) => row(r, 0))}
        {visible && visible.size === 0 && <li className="px-3 py-2 text-sm text-muted-foreground">Không tìm thấy</li>}
      </ul>
      <p className="text-xs text-muted-foreground">Chọn một nhánh là chọn cả các nhánh con.</p>
      {onApply && <div className="flex justify-between gap-2">
        <Button variant="ghost" size="sm" onClick={() => setChecked(new Set())} disabled={!checked.size}>
          Bỏ chọn tất cả
        </Button>
        <div className="flex gap-2">
          {onCancel && (
            <Button variant="outline" size="sm" onClick={onCancel}>
              Hủy
            </Button>
          )}
          <Button size="sm" onClick={() => onApply(topMost(ix, checked))}>
            Áp dụng{count ? ` (${count})` : ""}
          </Button>
        </div>
      </div>}
    </div>
  );
}
