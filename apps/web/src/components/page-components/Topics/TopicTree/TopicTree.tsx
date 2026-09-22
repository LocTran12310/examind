"use client";

import { ConfirmDialog } from "@/components/common/ConfirmDialog/ConfirmDialog";
import { cn } from "@/lib/utils";
import { useState } from "react";
import { FormAlert } from "@/components/common/FormAlert/FormAlert";
import { ToneBadge } from "@/components/common/ToneBadge/ToneBadge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { FormDialog } from "@/components/common/FormDialog/FormDialog";
import { OptionSelect } from "@/components/common/OptionSelect/OptionSelect";
import { buildTree, flatten, isInSubtree, type TopicNode } from "@/lib/common/topic-tree";
import { LEVEL_LABEL } from "@/constants/topic.constant";
import { useTopicTree } from "@/hooks/page-hooks/topics/use-topic-tree";
import type { Topic } from "@/interfaces/topic.interface";

type Dialog = { kind: "move" | "merge"; topic: Topic } | null;

export interface TopicTreeProps {
  topics: Topic[];
  subjectId: string;
  readOnly?: boolean;
}

export function TopicTree({ topics, subjectId, readOnly }: TopicTreeProps) {
  const roots = buildTree(topics);
  const [open, setOpen] = useState<Set<string>>(() => new Set(roots.map((r) => r.id)));
  const [editing, setEditing] = useState<string | null>(null);
  const [adding, setAdding] = useState<string | null>(null); // parent id, or "root"
  const [dialog, setDialog] = useState<Dialog>(null);
  const [deleting, setDeleting] = useState<TopicNode | null>(null);
  const t = useTopicTree(subjectId);

  const toggle = (id: string) => setOpen((s) => {
    const n = new Set(s);
    if (n.has(id)) n.delete(id);
    else n.add(id);
    return n;
  });

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
              onSave={(name) => t.rename(node.id, name).then((ok) => ok && setEditing(null))}
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
                  onSave={(name) => t.addChild(node.id, name).then((ok) => ok && setAdding(null))}
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
      {t.error && <div className="mb-3"><FormAlert>{t.error}</FormAlert></div>}
      <ul className="rounded-xl border border-border bg-card p-2">
        {roots.map((r) => renderRow(r, 0))}
        {adding === "root" && (
          <li className="py-1 pl-7">
            <InlineName
              initial=""
              placeholder="Tên mạch kiến thức mới"
              onCancel={() => setAdding(null)}
              onSave={(name) => t.addStrand(name).then((ok) => ok && setAdding(null))}
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
          await t.remove(node.id);
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
              const ok = dialog.kind === "move" ? await t.moveTo(dialog.topic.id, targetId) : await t.mergeInto(dialog.topic.id, targetId!);
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
