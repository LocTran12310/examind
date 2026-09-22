"use client";

import { ConfirmDialog } from "@/components/app/ConfirmDialog";
import { cn } from "@/lib/utils";
import { useState } from "react";
import { FormAlert } from "@/components/app/FormAlert";
import { ToneBadge } from "@/components/app/ToneBadge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { FormDialog } from "@/components/app/FormDialog";
import { OptionSelect } from "@/components/app/OptionSelect";
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
  const [deleting, setDeleting] = useState<TopicNode | null>(null);
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
        <div className={cn("group flex items-center gap-2 rounded-md py-1 pr-2 hover:bg-muted/50")} style={{ paddingLeft: depth * 20 + 4 }} data-testid={`topic-${node.name}`}>
          <Button
            type="button"
            variant="ghost"
            size="icon-xs"
            aria-label={expanded ? "Thu gọn" : "Mở rộng"}
            className={cn("size-5 font-normal text-muted-foreground", !node.children.length && "invisible")}
            onClick={() => toggle(node.id)}
          >
            {expanded ? "▾" : "▸"}
          </Button>
          {editing === node.id ? (
            <InlineName
              initial={node.name}
              onCancel={() => setEditing(null)}
              onSave={(name) => run(() => api(`/topics/${node.id}`, { method: "PATCH", body: { name } })).then((ok) => ok && setEditing(null))}
            />
          ) : (
            <span className={cn(depth === 0 && "font-semibold")} onDoubleClick={() => !readOnly && setEditing(node.id)}>
              {node.name}
            </span>
          )}
          <ToneBadge>{LEVEL_LABEL[node.level_kind]}</ToneBadge>
          {node.grade && <span className="text-xs text-muted-foreground/70">Lớp {node.grade}</span>}
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
                className="text-destructive"
                onClick={() => setDeleting(node)}
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
      {error && <div className="mb-3"><FormAlert>{error}</FormAlert></div>}
      <ul className="rounded-xl border border-border bg-card p-2">
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
        <Button variant="outline" className="mt-3" onClick={() => setAdding("root")}>
          + Mạch kiến thức
        </Button>
      )}
      <ConfirmDialog
        open={!!deleting}
        onOpenChange={(o) => !o && setDeleting(null)}
        destructive
        title={`Xóa "${deleting?.name ?? ""}"?`}
        description="Chỉ xóa được nhánh chưa có câu hỏi và nhánh con."
        confirmLabel="Xóa"
        onConfirm={async () => {
          const node = deleting!;
          setDeleting(null);
          await run(() => api(`/topics/${node.id}`, { method: "DELETE" }));
        }}
      />
      <FormDialog open={!!dialog} title={dialog?.kind === "move" ? "Di chuyển chuyên đề" : "Gộp chuyên đề"} onOpenChange={(o) => !o && setDialog(null)}>
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
      </FormDialog>
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
      <Button size="sm" type="submit">
        Lưu
      </Button>
      <Button variant="outline" size="sm" type="button" onClick={onCancel}>
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
      {note && <FormAlert kind="warning">{note}</FormAlert>}
      <OptionSelect
        value={target}
        onValueChange={setTarget}
        aria-label="Chuyên đề đích"
        emptyLabel={allowRoot ? "— Cấp gốc —" : undefined}
        options={options.map(({ node, depth }) => ({ value: node.id, label: "  ".repeat(depth) + (depth ? "└ " : "") + node.name }))}
      />
      <div className="flex justify-end">
        <Button onClick={() => onPick(target || null)} disabled={!allowRoot && !target}>
          {action}
        </Button>
      </div>
    </div>
  );
}
