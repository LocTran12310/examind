import type { ColumnDef } from "@tanstack/react-table";
import { useMemo, useState } from "react";
import { toast } from "sonner";
import { ToneBadge } from "@/components/app/ToneBadge";
import { MODEL_ENABLED_OPTIONS, PROVIDER_LABEL, PROVIDER_OPTIONS } from "@/constants/ai-model.constant";
import { useMe } from "@/hooks/common/use-me";
import { useDeleteAiModelsMutation, useTestAiModelMutation, useToggleAiModelsMutation } from "@/hooks/react-query/use-query-ai-model";
import type { AiModel, ModelDraft, ModelTestState } from "@/interfaces/ai-model.interface";
import { ApiError } from "@/lib/common/http";

function modelColumns(tests: ModelTestState): ColumnDef<AiModel, unknown>[] {
  return [
    {
      accessorKey: "name",
      header: "Model",
      cell: ({ row }) => (
        <div data-testid={`model-${row.original.name}`}>
          <div className="font-medium">{row.original.name}</div>
          <div className="font-mono text-xs text-muted-foreground">{row.original.model}</div>
        </div>
      ),
      meta: { filter: { kind: "text" }, sort: "name" },
    },
    {
      accessorKey: "provider",
      header: "Nhà cung cấp",
      cell: ({ row }) => (
        <div>
          <div>{PROVIDER_LABEL[row.original.provider]}</div>
          <div className="text-xs text-muted-foreground">{row.original.base_url}</div>
        </div>
      ),
      meta: { filter: { kind: "select", options: PROVIDER_OPTIONS }, sort: "provider" },
    },
    {
      id: "capabilities",
      header: "Khả năng",
      cell: ({ row }) => (
        <div className="flex gap-1">
          {row.original.capabilities.map((c) => (
            <ToneBadge key={c}>{c === "vision" ? "Đọc ảnh" : "Văn bản"}</ToneBadge>
          ))}
        </div>
      ),
    },
    {
      accessorKey: "enabled",
      header: "Trạng thái",
      cell: ({ row }) => {
        const m = row.original;
        const t = tests[m.id];
        return (
          <div className="flex flex-wrap gap-1">
            <ToneBadge tone={m.is_free ? "green" : "amber"}>{m.is_free ? "Free" : "Trả phí"}</ToneBadge>
            {m.system && <ToneBadge tone="blue">Hệ thống</ToneBadge>}
            {m.has_key && <ToneBadge>Có khóa</ToneBadge>}
            {!m.enabled && <ToneBadge tone="red">Đã tắt</ToneBadge>}
            {t === "running" && <ToneBadge>Đang kiểm tra…</ToneBadge>}
            {t && t !== "running" && <ToneBadge tone={t.ok ? "green" : "red"}>{t.ok ? `OK · ${t.latency_ms} ms` : t.error}</ToneBadge>}
          </div>
        );
      },
      meta: { filter: { kind: "select", options: MODEL_ENABLED_OPTIONS } },
    },
  ];
}

/** Columns, dialogs and toolbar actions (test, on/off, Ollama discovery) of the AI models page. */
export function useAiModelsPage() {
  const me = useMe();
  const [adding, setAdding] = useState<ModelDraft | null>(null);
  const [editing, setEditing] = useState<AiModel | null>(null);
  const [discovering, setDiscovering] = useState(false);
  const [tests, setTests] = useState<ModelTestState>({});
  const columns = useMemo(() => modelColumns(tests), [tests]);
  const test = useTestAiModelMutation();
  const toggle = useToggleAiModelsMutation();
  const remove = useDeleteAiModelsMutation();

  return {
    description: me.role === "super_admin" ? "Model hệ thống — mọi trung tâm đều thấy" : "Model trung tâm dùng để tách câu, gắn chuyên đề và đọc ảnh",
    columns,
    adding,
    setAdding,
    editing,
    setEditing,
    discovering,
    setDiscovering,
    edit: (m: AiModel) => (m.editable ? setEditing(m) : toast.info("Model hệ thống chỉ quản trị hệ thống sửa được")),
    removeModels: (rows: AiModel[]) => remove.mutateAsync(rows.filter((m) => m.editable).map((m) => m.id)),
    testModels: async (models: AiModel[]) => {
      await Promise.all(
        models.map(async (m) => {
          setTests((t) => ({ ...t, [m.id]: "running" }));
          const r = await test.mutateAsync(m.id).catch((e) => ({ ok: false, error: e instanceof ApiError ? e.message : "Lỗi" }));
          setTests((t) => ({ ...t, [m.id]: r }));
        }),
      );
    },
    toggleModels: (models: AiModel[]) =>
      toggle.mutate(
        models.filter((m) => m.editable),
        { onError: (e) => toast.error(e instanceof ApiError ? e.message : "Có lỗi xảy ra") },
      ),
    picked: (d: ModelDraft) => {
      setDiscovering(false);
      setAdding(d);
    },
  };
}
