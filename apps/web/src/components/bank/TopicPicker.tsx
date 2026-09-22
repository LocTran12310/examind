"use client";

import { useMemo, useState } from "react";
import { Input } from "@/components/ui/input";
import type { Topic } from "@/lib/types";

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

/** Searchable topic list: type to filter (accent-insensitive), ↑/↓ to move, Enter to pick, Esc to close. */
export function TopicPicker({ topics, onPick, onClose, autoFocus = true }: { topics: Topic[]; onPick: (t: Topic) => void; onClose?: () => void; autoFocus?: boolean }) {
  const [q, setQ] = useState("");
  const [active, setActive] = useState(0);
  const byId = useMemo(() => new Map(topics.map((t) => [t.id, t])), [topics]);
  const items = useMemo(() => {
    const needle = fold(q.trim());
    return topics
      .map((t) => ({ t, label: topicLabel(t, byId) }))
      .filter((x) => !needle || fold(x.label).includes(needle))
      .slice(0, 50);
  }, [q, topics, byId]);
  return (
    <div className="space-y-2" data-testid="topic-picker">
      <Input
        autoFocus={autoFocus}
        placeholder="Tìm chuyên đề… (ví dụ: nguyen ham)"
        value={q}
        onChange={(e) => (setQ(e.target.value), setActive(0))}
        onKeyDown={(e) => {
          if (e.key === "ArrowDown") {
            e.preventDefault();
            setActive((a) => Math.min(a + 1, items.length - 1));
          } else if (e.key === "ArrowUp") {
            e.preventDefault();
            setActive((a) => Math.max(a - 1, 0));
          } else if (e.key === "Enter" && items[active]) {
            e.preventDefault();
            onPick(items[active].t);
          } else if (e.key === "Escape") {
            onClose?.();
          }
        }}
      />
      <ul className="max-h-72 overflow-y-auto rounded-md border border-border text-sm" role="listbox">
        {items.map((x, i) => (
          <li
            key={x.t.id}
            role="option"
            aria-selected={i === active}
            className={i === active ? "cursor-pointer bg-primary/10 px-3 py-1.5 text-primary" : "cursor-pointer px-3 py-1.5 hover:bg-muted/50"}
            onMouseEnter={() => setActive(i)}
            onClick={() => onPick(x.t)}
          >
            {x.label}
          </li>
        ))}
        {items.length === 0 && <li className="px-3 py-2 text-muted-foreground">Không tìm thấy</li>}
      </ul>
    </div>
  );
}
