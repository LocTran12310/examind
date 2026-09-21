"use client";

import clsx from "clsx";
import { useState } from "react";
import { Alert, Badge, Button, Input, Modal, Select } from "@/components/ui";
import { api, ApiError } from "@/lib/api";
import { LEVEL_LABEL, type Topic } from "@/lib/types";
import { buildTree, flatten, isInSubtree, type TopicNode } from "./tree";

type Dialog = { kind: "move" | "merge"; topic: Topic } | null;

export function TopicTree({ topics, subjectId, onChange, readOnly }: { topics: Topic[]; subjectId: string; onChange: () => void; readOnly?: boolean }) {
  const roots = buildTree(topics);
  const [open, setOpen] = useState<Set<string>>(() => new Set(roots.map((r) => r.id)));
  const [editing, setEditing] = useState<string | null>(null);
  const [adding, setAdding] = useState<string | null>(null); // parent id, or "root"
  const [dialog, setDialog] = useState<Dialog>(null);
  const [error, setError] = useState<string | null>(null);

  const toggle = (id: string) => setOpen((s) => {
    const n = new Set(s);
    if (n.has(id)) n.delete(id);
    else n.add(id);
    return n;
  });

  async function run(fn: () => Promise<unknown>): Promise<boolean> {
    setError(null);
    try {
      await fn();
      onChange();
      return true;
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Có lỗi xảy ra");
      return false;
    }
  }

  // A render function rather than a nested component, so rows are not remounted on every render.
  function renderRow(node: TopicNode, depth: number): React.ReactNode {
    const expanded = open.has(node.id);
    return (
      <li key={node.id}>
        <div className={clsx("group flex items-center gap-2 rounded-md py-1 pr-2 hover:bg-gray-50")} style={{ paddingLeft: depth * 20 + 4 }} data-testid={`topic-${node.name}`}>
          <button
            type="button"
            aria-label={expanded ? "Thu gọn" : "Mở rộng"}
            className={clsx("w-5 text-gray-500", !node.children.length && "invisible")}
            onClick={() => toggle(node.id)}
          >
            {expanded ? "▾" : "▸"}
          </button>
          {editing === node.id ? (
            <InlineName
              initial={node.name}
              onCancel={() => setEditing(null)}
              onSave={(name) => run(() => api(`/topics/${node.id}`, { method: "PATCH", body: { name } })).then((ok) => ok && setEditing(null))}
            />
          ) : (
            <span className={clsx(depth === 0 && "font-semibold")} onDoubleClick={() => !readOnly && setEditing(node.id)}>
              {node.name}
            </span>
          )}
          <Badge>{LEVEL_LABEL[node.level_kind]}</Badge>
          {node.grade && <span className="text-xs text-gray-400">Lớp {node.grade}</span>}
          {!readOnly && editing !== node.id && (
            <div className="ml-auto flex gap-1 opacity-0 transition group-hover:opacity-100 group-focus-within:opacity-100">
              <Button size="sm" variant="ghost" onClick={() => (setAdding(node.id), setOpen((s) => new Set(s).add(node.id)))}>
                + Con
              </Button>
              <Button size="sm" variant="ghost" onClick={() => setEditing(node.id)}>
                Đổi tên
              </Button>
              <Button size="sm" variant="ghost" onClick={() => setDialog({ kind: "move", topic: node })}>
                Di chuyển
              </Button>
              <Button size="sm" variant="ghost" onClick={() => setDialog({ kind: "merge", topic: node })}>
                Gộp
              </Button>
              <Button
                size="sm"
                variant="ghost"
                className="text-red-700"
                onClick={() => window.confirm(`Xóa "${node.name}"?`) && run(() => api(`/topics/${node.id}`, { method: "DELETE" }))}
              >
                Xóa
              </Button>
            </div>
          )}
        </div>
        {expanded && (
          <ul>
            {node.children.map((c) => renderRow(c, depth + 1))}
            {adding === node.id && (
              <li style={{ paddingLeft: (depth + 1) * 20 + 28 }} className="py-1">
                <InlineName
                  initial=""
                  placeholder="Tên nhánh mới"
                  onCancel={() => setAdding(null)}
                  onSave={(name) => run(() => api("/topics", { body: { name, parent_id: node.id } })).then((ok) => ok && setAdding(null))}
                />
              </li>
            )}
          </ul>
        )}
      </li>
    );
  }

  return (
    <div>
      {error && <div className="mb-3"><Alert>{error}</Alert></div>}
      <ul className="rounded-xl border border-gray-200 bg-white p-2">
        {roots.map((r) => renderRow(r, 0))}
        {adding === "root" && (
          <li className="py-1 pl-7">
            <InlineName
              initial=""
              placeholder="Tên mạch kiến thức mới"
              onCancel={() => setAdding(null)}
              onSave={(name) => run(() => api("/topics", { body: { name, subject_id: subjectId } })).then((ok) => ok && setAdding(null))}
            />
          </li>
        )}
      </ul>
      {!readOnly && (
        <Button className="mt-3" onClick={() => setAdding("root")}>
          + Mạch kiến thức
        </Button>
      )}
      <Modal open={!!dialog} title={dialog?.kind === "move" ? "Di chuyển chuyên đề" : "Gộp chuyên đề"} onClose={() => setDialog(null)}>
        {dialog && (
          <TargetPicker
            topics={topics}
            source={dialog.topic}
            allowRoot={dialog.kind === "move"}
            action={dialog.kind === "move" ? "Di chuyển" : "Gộp vào"}
            note={dialog.kind === "merge" ? `Các nhánh con và câu hỏi của "${dialog.topic.name}" sẽ chuyển sang chuyên đề đích, sau đó "${dialog.topic.name}" bị xóa.` : undefined}
            onPick={async (targetId) => {
              const ok = await run(() =>
                dialog.kind === "move"
                  ? api(`/topics/${dialog.topic.id}/move`, { body: { parent_id: targetId } })
                  : api(`/topics/${dialog.topic.id}/merge`, { body: { target_id: targetId } }),
              );
              if (ok) setDialog(null);
            }}
          />
        )}
      </Modal>
    </div>
  );
}

function InlineName({ initial, onSave, onCancel, placeholder }: { initial: string; onSave: (name: string) => void; onCancel: () => void; placeholder?: string }) {
  const [value, setValue] = useState(initial);
  return (
    <form
      className="flex flex-1 items-center gap-2"
      onSubmit={(e) => {
        e.preventDefault();
        if (value.trim()) onSave(value.trim());
      }}
    >
      <Input autoFocus value={value} placeholder={placeholder} onChange={(e) => setValue(e.target.value)} onKeyDown={(e) => e.key === "Escape" && onCancel()} className="h-8 max-w-md" />
      <Button size="sm" variant="primary" type="submit">
        Lưu
      </Button>
      <Button size="sm" type="button" onClick={onCancel}>
        Hủy
      </Button>
    </form>
  );
}

function TargetPicker({
  topics,
  source,
  allowRoot,
  action,
  note,
  onPick,
}: {
  topics: Topic[];
  source: Topic;
  allowRoot: boolean;
  action: string;
  note?: string;
  onPick: (targetId: string | null) => void;
}) {
  const options = flatten(buildTree(topics)).filter(({ node }) => !isInSubtree(node, source));
  const [target, setTarget] = useState<string>(allowRoot ? "" : options[0]?.node.id ?? "");
  return (
    <div className="space-y-4">
      {note && <Alert tone="amber">{note}</Alert>}
      <Select className="w-full" value={target} onChange={(e) => setTarget(e.target.value)} aria-label="Chuyên đề đích">
        {allowRoot && <option value="">— Cấp gốc —</option>}
        {options.map(({ node, depth }) => (
          <option key={node.id} value={node.id}>
            {"  ".repeat(depth) + (depth ? "└ " : "") + node.name}
          </option>
        ))}
      </Select>
      <div className="flex justify-end">
        <Button variant="primary" onClick={() => onPick(target || null)} disabled={!allowRoot && !target}>
          {action}
        </Button>
      </div>
    </div>
  );
}
