"use client";

import { Badge, Button, Table, td, th } from "@/components/ui";
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
    <Table>
      <thead className="bg-gray-50">
        <tr>
          <th className={th}>Model</th>
          <th className={th}>Nhà cung cấp</th>
          <th className={th}>Khả năng</th>
          <th className={th}>Trạng thái</th>
          <th className={th} />
        </tr>
      </thead>
      <tbody className="divide-y divide-gray-100">
        {models.map((m) => {
          const t = tests[m.id];
          return (
            <tr key={m.id} data-testid={`model-${m.name}`} className={m.enabled ? "" : "opacity-60"}>
              <td className={td}>
                <div className="font-medium">{m.name}</div>
                <div className="font-mono text-xs text-gray-500">{m.model}</div>
              </td>
              <td className={td}>
                <div>{PROVIDER_LABEL[m.provider]}</div>
                <div className="text-xs text-gray-500">{m.base_url}</div>
              </td>
              <td className={`${td} space-x-1`}>
                {m.capabilities.map((c) => (
                  <Badge key={c}>{c === "vision" ? "Đọc ảnh" : "Văn bản"}</Badge>
                ))}
              </td>
              <td className={`${td} space-x-1`}>
                <Badge tone={m.is_free ? "green" : "amber"}>{m.is_free ? "Free" : "Trả phí"}</Badge>
                {m.system && <Badge tone="blue">Hệ thống</Badge>}
                {m.has_key && <Badge>Có khóa</Badge>}
                {!m.enabled && <Badge tone="red">Đã tắt</Badge>}
                {t && t !== "running" && (
                  <Badge tone={t.ok ? "green" : "red"}>{t.ok ? `OK · ${t.latency_ms} ms` : t.error}</Badge>
                )}
              </td>
              <td className={`${td} whitespace-nowrap text-right`}>
                <div className="flex justify-end gap-1">
                  <Button size="sm" onClick={() => onTest(m)} disabled={t === "running"}>
                    {t === "running" ? "Đang kiểm tra…" : "Kiểm tra"}
                  </Button>
                  {m.editable && (
                    <>
                      <Button size="sm" onClick={() => onEdit(m)}>
                        Sửa
                      </Button>
                      <Button size="sm" onClick={() => onToggle(m)}>
                        {m.enabled ? "Tắt" : "Bật"}
                      </Button>
                      <Button size="sm" variant="danger" onClick={() => onDelete(m)}>
                        Xóa
                      </Button>
                    </>
                  )}
                </div>
              </td>
            </tr>
          );
        })}
      </tbody>
    </Table>
  );
}
