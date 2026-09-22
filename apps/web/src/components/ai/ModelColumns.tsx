"use client";

import type { ColumnDef } from "@tanstack/react-table";
import { ToneBadge } from "@/components/app/ToneBadge";
import { type AiModel, PROVIDER_LABEL } from "@/lib/types";

export type TestState = Record<string, { ok: boolean; latency_ms?: number | null; error?: string | null } | "running">;

export function modelColumns(tests: TestState): ColumnDef<AiModel, unknown>[] {
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
      meta: { filter: { kind: "select", options: Object.entries(PROVIDER_LABEL).map(([value, label]) => ({ value, label })) }, sort: "provider" },
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
      meta: { filter: { kind: "select", options: [{ value: "true", label: "Đang bật" }, { value: "false", label: "Đã tắt" }] } },
    },
  ];
}
