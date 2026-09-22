import type { TopicNode } from "@/lib/common/topic-tree";

/**
 * Tree check state (bank filter): checking a node checks its whole subtree; a parent is checked
 * when all its children are; the filter sends only the top-most checked nodes (each includes its
 * subtree on the server).
 */
export interface Index {
  parent: Map<string, string | null>;
  children: Map<string, string[]>;
}

export function indexTree(roots: TopicNode[]): Index {
  const parent = new Map<string, string | null>();
  const children = new Map<string, string[]>();
  const walk = (n: TopicNode, p: string | null) => {
    parent.set(n.id, p);
    children.set(n.id, n.children.map((c) => c.id));
    n.children.forEach((c) => walk(c, n.id));
  };
  roots.forEach((r) => walk(r, null));
  return { parent, children };
}

function descendants(ix: Index, id: string, out: string[] = []): string[] {
  for (const c of ix.children.get(id) ?? []) {
    out.push(c);
    descendants(ix, c, out);
  }
  return out;
}

/** Expand top-most ids (URL form) to every checked node. */
export function expand(ix: Index, roots: string[]): Set<string> {
  const s = new Set<string>();
  for (const r of roots) if (ix.parent.has(r)) [r, ...descendants(ix, r)].forEach((x) => s.add(x));
  return s;
}

export function toggle(ix: Index, checked: Set<string>, id: string): Set<string> {
  const next = new Set(checked);
  const on = !checked.has(id);
  for (const x of [id, ...descendants(ix, id)]) {
    if (on) next.add(x);
    else next.delete(x);
  }
  // walk up: a parent is checked exactly when all its children are
  for (let p = ix.parent.get(id); p; p = ix.parent.get(p)) {
    const kids = ix.children.get(p) ?? [];
    if (kids.length && kids.every((k) => next.has(k))) next.add(p);
    else next.delete(p);
  }
  return next;
}

export function state(ix: Index, checked: Set<string>, id: string): boolean | "indeterminate" {
  if (checked.has(id)) return true;
  return descendants(ix, id).some((d) => checked.has(d)) ? "indeterminate" : false;
}

/** Minimal set sent to the API: checked nodes whose parent is not checked. */
export function topMost(ix: Index, checked: Set<string>): string[] {
  return [...checked].filter((id) => {
    const p = ix.parent.get(id);
    return !p || !checked.has(p);
  });
}
