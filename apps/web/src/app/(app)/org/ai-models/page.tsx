"use client";

import { useState } from "react";
import { useMe } from "@/app/(app)/AppShell";
import { emptyDraft, ModelForm } from "@/components/ai/ModelForm";
import { ModelTable, type TestState } from "@/components/ai/ModelTable";
import { Alert, Button, Card, Empty, Input, Modal, PageHeader } from "@/components/ui";
import { api, ApiError } from "@/lib/api";
import { useApi } from "@/lib/hooks";
import type { AiModel } from "@/lib/types";

interface Discovered {
  model: string;
  parameter_size?: string;
  capabilities: ("text" | "vision")[];
}

export default function AiModelsPage() {
  const me = useMe();
  const { data, reload } = useApi<AiModel[]>("/ai-models");
  const [adding, setAdding] = useState<ReturnType<typeof emptyDraft> | null>(null);
  const [editing, setEditing] = useState<AiModel | null>(null);
  const [tests, setTests] = useState<TestState>({});
  const [ollamaUrl, setOllamaUrl] = useState("");
  const [found, setFound] = useState<{ base_url: string; models: Discovered[]; error?: string } | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function act(fn: () => Promise<unknown>) {
    setError(null);
    try {
      await fn();
      await reload();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Có lỗi xảy ra");
    }
  }

  async function test(m: AiModel) {
    setTests((t) => ({ ...t, [m.id]: "running" }));
    const r = await api<{ ok: boolean; latency_ms?: number; error?: string }>(`/ai-models/${m.id}/test`, { method: "POST" }).catch(
      (e) => ({ ok: false, error: e instanceof ApiError ? e.message : "Lỗi" }),
    );
    setTests((t) => ({ ...t, [m.id]: r }));
  }

  return (
    <>
      <PageHeader
        title="Model AI"
        subtitle={me.role === "super_admin" ? "Model hệ thống — mọi trung tâm đều thấy" : "Model trung tâm dùng để tách câu, gắn chuyên đề và đọc ảnh"}
        actions={
          <Button variant="primary" onClick={() => setAdding(emptyDraft())}>
            Thêm model
          </Button>
        }
      />
      <Card className="mb-4">
        <div className="flex flex-wrap items-end gap-2">
          <div className="min-w-64 flex-1">
            <label className="text-sm font-medium text-gray-700">Máy chủ Ollama</label>
            <Input placeholder="Mặc định theo cấu hình máy chủ (OLLAMA_URL)" value={ollamaUrl} onChange={(e) => setOllamaUrl(e.target.value)} />
          </div>
          <Button
            onClick={() =>
              act(async () => setFound(await api("/ai-models/discover", { body: { base_url: ollamaUrl || null } })))
            }
          >
            Phát hiện model Ollama
          </Button>
        </div>
        {found?.error && <div className="mt-3"><Alert tone="amber">{found.error}</Alert></div>}
        {found && !found.error && found.models.length === 0 && <p className="mt-3 text-sm text-gray-500">Ollama chưa có model nào — chạy `ollama pull qwen2.5:7b`.</p>}
        {found && found.models.length > 0 && (
          <ul className="mt-3 divide-y divide-gray-100 text-sm" data-testid="discovered">
            {found.models.map((d) => (
              <li key={d.model} className="flex items-center justify-between py-2">
                <span>
                  <span className="font-mono">{d.model}</span> <span className="text-gray-500">{d.parameter_size}</span>
                  {d.capabilities.includes("vision") && <span className="ml-2 text-xs text-brand-700">đọc ảnh</span>}
                </span>
                <Button size="sm" onClick={() => setAdding(emptyDraft({ name: d.model, model: d.model, base_url: found.base_url, capabilities: d.capabilities }))}>
                  Thêm
                </Button>
              </li>
            ))}
          </ul>
        )}
      </Card>
      {error && <div className="mb-3"><Alert>{error}</Alert></div>}
      {data && data.length === 0 && <Empty>Chưa có model nào. Hệ thống vẫn tách đề bằng quy tắc; thêm model để bật AI.</Empty>}
      {data && data.length > 0 && (
        <ModelTable
          models={data}
          tests={tests}
          onTest={test}
          onEdit={setEditing}
          onToggle={(m) => act(() => api(`/ai-models/${m.id}`, { method: "PATCH", body: { enabled: !m.enabled } }))}
          onDelete={(m) => window.confirm(`Xóa model ${m.name}?`) && act(() => api(`/ai-models/${m.id}`, { method: "DELETE" }))}
        />
      )}
      <Modal open={!!adding} title="Thêm model" wide onClose={() => setAdding(null)}>
        {adding && <ModelForm initial={adding} onDone={() => (setAdding(null), void reload())} />}
      </Modal>
      <Modal open={!!editing} title="Sửa model" wide onClose={() => setEditing(null)}>
        {editing && (
          <ModelForm
            existing={editing}
            initial={emptyDraft({ ...editing, base_url: editing.base_url ?? "", api_key: "" })}
            onDone={() => (setEditing(null), void reload())}
          />
        )}
      </Modal>
    </>
  );
}
