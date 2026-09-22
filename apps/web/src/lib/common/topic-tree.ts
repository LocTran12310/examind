import type { Topic } from "@/interfaces/topic.interface";

export interface TopicNode extends Topic {
  children: TopicNode[];
}

export function buildTree(topics: Topic[]): TopicNode[] {
  const byId = new Map<string, TopicNode>(topics.map((t) => [t.id, { ...t, children: [] }]));
  const roots: TopicNode[] = [];
  for (const n of byId.values()) {
    const parent = n.parent_id ? byId.get(n.parent_id) : undefined;
    (parent ? parent.children : roots).push(n);
  }
  const sort = (xs: TopicNode[]) => {
    xs.sort((a, b) => a.sort - b.sort || a.name.localeCompare(b.name, "vi"));
    xs.forEach((x) => sort(x.children));
  };
  sort(roots);
  return roots;
}

/** Depth-first flat list with indentation depth, for pickers. */
export function flatten(nodes: TopicNode[], depth = 0, out: { node: TopicNode; depth: number }[] = []) {
  for (const n of nodes) {
    out.push({ node: n, depth });
    flatten(n.children, depth + 1, out);
  }
  return out;
}

export function isInSubtree(candidate: Topic, root: Topic): boolean {
  return candidate.path === root.path || candidate.path.startsWith(root.path + ".");
}

/** "Giải tích › Nguyên hàm": the names from the strand down to the topic. */
export function topicLabel(t: Topic, byId: Map<string, Topic>): string {
  const names: string[] = [];
  let cur: Topic | undefined = t;
  while (cur) {
    names.unshift(cur.name);
    cur = cur.parent_id ? byId.get(cur.parent_id) : undefined;
  }
  return names.join(" › ");
}
