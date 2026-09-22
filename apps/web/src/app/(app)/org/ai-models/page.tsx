"use client";

import { useState } from "react";
import { useMe } from "@/app/(app)/AppShell";
import { emptyDraft, ModelForm } from "@/components/ai/ModelForm";
import { ModelTable, type TestState } from "@/components/ai/ModelTable";
import { FormAlert } from "@/components/app/FormAlert";
import { Button } from "@/components/ui/button";
import { Panel } from "@/components/app/Panel";
import { EmptyState } from "@/components/app/EmptyState";
import { Input } from "@/components/ui/input";
import { FormDialog } from "@/components/app/FormDialog";
import { PageHeader } from "@/components/app/PageHeader";
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
        description={me.role === "super_admin" ? "Model hệ thống — mọi trung tâm đều thấy" : "Model trung tâm dùng để tách câu, gắn chuyên đề và đọc ảnh"}
        actions={
          <Button onClick={() => setAdding(emptyDraft())}>
            Thêm model
          </Button>
        }
      />
      <Panel className="mb-4">
        <div className="flex flex-wrap items-end gap-2">
          <div className="min-w-64 flex-1">
            <label className="text-sm font-medium text-foreground/80">Máy chủ Ollama</label>
            <Input placeholder="Mặc định theo cấu hình máy chủ (OLLAMA_URL)" value={ollamaUrl} onChange={(e) => setOllamaUrl(e.target.value)} />
          </div>
          <Button variant="outline"
            onClick={() =>
              act(async () => setFound(await api("/ai-models/discover", { body: { base_url: ollamaUrl || null } })))
            }
          >
            Phát hiện model Ollama
          </Button>
        </div>
        {found?.error && <div className="mt-3"><FormAlert kind="warning">{found.error}</FormAlert></div>}
        {found && !found.error && found.models.length === 0 && <p className="mt-3 text-sm text-muted-foreground">Ollama chưa có model nào — chạy `ollama pull qwen2.5:7b`.</p>}
        {found && found.models.length > 0 && (
          <ul className="mt-3 divide-y divide-border text-sm" data-testid="discovered">
            {found.models.map((d) => (
              <li key={d.model} className="flex items-center justify-between py-2">
                <span>
                  <span className="font-mono">{d.model}</span> <span className="text-muted-foreground">{d.parameter_size}</span>
                  {d.capabilities.includes("vision") && <span className="ml-2 text-xs text-primary">đọc ảnh</span>}
                </span>
                <Button variant="outline" size="sm" onClick={() => setAdding(emptyDraft({ name: d.model, model: d.model, base_url: found.base_url, capabilities: d.capabilities }))}>
                  Thêm
                </Button>
              </li>
            ))}
          </ul>
        )}
      </Panel>
      {error && <div className="mb-3"><FormAlert>{error}</FormAlert></div>}
      {data && data.length === 0 && <EmptyState>Chưa có model nào. Hệ thống vẫn tách đề bằng quy tắc; thêm model để bật AI.</EmptyState>}
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
      <FormDialog open={!!adding} title="Thêm model" wide onOpenChange={(o) => !o && setAdding(null)}>
        {adding && <ModelForm initial={adding} onDone={() => (setAdding(null), void reload())} />}
      </FormDialog>
      <FormDialog open={!!editing} title="Sửa model" wide onOpenChange={(o) => !o && setEditing(null)}>
        {editing && (
          <ModelForm
            existing={editing}
            initial={emptyDraft({ ...editing, base_url: editing.base_url ?? "", api_key: "" })}
            onDone={() => (setEditing(null), void reload())}
          />
        )}
      </FormDialog>
    </>
  );
}
