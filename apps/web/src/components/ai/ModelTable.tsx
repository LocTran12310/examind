"use client";

import { ToneBadge } from "@/components/app/ToneBadge";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { PROVIDER_LABEL, type AiModel } from "@/lib/types";

export type TestState = Record<string, { ok: boolean; latency_ms?: number | null; error?: string | null } | "running">;

export function ModelTable({
  models,
  tests,
  onTest,
  onEdit,
  onToggle,
  onDelete,
}: {
  models: AiModel[];
  tests: TestState;
  onTest: (m: AiModel) => void;
  onEdit: (m: AiModel) => void;
  onToggle: (m: AiModel) => void;
  onDelete: (m: AiModel) => void;
}) {
  return (
    <div className="rounded-lg border bg-card">
<Table>
      <TableHeader>
        <TableRow>
          <TableHead>Model</TableHead>
          <TableHead>Nhà cung cấp</TableHead>
          <TableHead>Khả năng</TableHead>
          <TableHead>Trạng thái</TableHead>
          <TableHead />
        </TableRow>
      </TableHeader>
      <TableBody>
        {models.map((m) => {
          const t = tests[m.id];
          return (
            <TableRow key={m.id} data-testid={`model-${m.name}`} className={m.enabled ? "" : "opacity-60"}>
              <TableCell>
                <div className="font-medium">{m.name}</div>
                <div className="font-mono text-xs text-muted-foreground">{m.model}</div>
              </TableCell>
              <TableCell>
                <div>{PROVIDER_LABEL[m.provider]}</div>
                <div className="text-xs text-muted-foreground">{m.base_url}</div>
              </TableCell>
              <TableCell className="space-x-1">
                {m.capabilities.map((c) => (
                  <ToneBadge key={c}>{c === "vision" ? "Đọc ảnh" : "Văn bản"}</ToneBadge>
                ))}
              </TableCell>
              <TableCell className="space-x-1">
                <ToneBadge tone={m.is_free ? "green" : "amber"}>{m.is_free ? "Free" : "Trả phí"}</ToneBadge>
                {m.system && <ToneBadge tone="blue">Hệ thống</ToneBadge>}
                {m.has_key && <ToneBadge>Có khóa</ToneBadge>}
                {!m.enabled && <ToneBadge tone="red">Đã tắt</ToneBadge>}
                {t && t !== "running" && (
                  <ToneBadge tone={t.ok ? "green" : "red"}>{t.ok ? `OK · ${t.latency_ms} ms` : t.error}</ToneBadge>
                )}
              </TableCell>
              <TableCell className="whitespace-nowrap text-right">
                <div className="flex justify-end gap-1">
                  <Button variant="outline" size="sm" onClick={() => onTest(m)} disabled={t === "running"}>
                    {t === "running" ? "Đang kiểm tra…" : "Kiểm tra"}
                  </Button>
                  {m.editable && (
                    <>
                      <Button variant="outline" size="sm" onClick={() => onEdit(m)}>
                        Sửa
                      </Button>
                      <Button variant="outline" size="sm" onClick={() => onToggle(m)}>
                        {m.enabled ? "Tắt" : "Bật"}
                      </Button>
                      <Button size="sm" variant="destructive" onClick={() => onDelete(m)}>
                        Xóa
                      </Button>
                    </>
                  )}
                </div>
              </TableCell>
            </TableRow>
          );
        })}
      </TableBody>
    </Table>
</div>
  );
}
