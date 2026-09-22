/** The tree node selected on the structure page, kept in the URL as `node=<kind>:<id>`. */
export type NodeRef = { kind: "level" | "grade" | "class"; id: string } | null;

export const nodeKey = (n: NodeRef) => (n ? `${n.kind}:${n.id}` : "");
export function parseNode(v: string | null | undefined): NodeRef {
  const m = /^(level|grade|class):(.+)$/.exec(v ?? "");
  return m ? { kind: m[1] as "level" | "grade" | "class", id: m[2] } : null;
}
