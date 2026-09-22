"use client";

import { ListLayout } from "@/components/app/ListLayout";
import { Activity, Power, Radar } from "lucide-react";
import { useMemo, useState } from "react";
import { toast } from "sonner";
import { useMe } from "@/app/(app)/AppShell";
import { modelColumns, type TestState } from "@/components/ai/ModelColumns";
import { emptyDraft, ModelForm } from "@/components/ai/ModelForm";
import { FormAlert } from "@/components/app/FormAlert";
import { FormDialog } from "@/components/app/FormDialog";
import { FormField } from "@/components/app/FormField";
import { PageHeader } from "@/components/app/PageHeader";
import { DataTable } from "@/components/data-table/DataTable";
import { ToolbarButton } from "@/components/data-table/Toolbar";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api, ApiError } from "@/lib/api";
import type { AiModel } from "@/lib/types";

interface Discovered {
  model: string;
  parameter_size?: string;
  capabilities: ("text" | "vision")[];
}

function Discover({ onPick }: { onPick: (draft: ReturnType<typeof emptyDraft>) => void }) {
  const [url, setUrl] = useState("");
  const [busy, setBusy] = useState(false);
  const [found, setFound] = useState<{ base_url: string; models: Discovered[]; error?: string } | null>(null);
  return (
    <div className="grid gap-3">
      <div className="flex items-end gap-2">
        <FormField label="Máy chủ Ollama" className="flex-1">
          <Input placeholder="Mặc định theo cấu hình máy chủ (OLLAMA_URL)" value={url} onChange={(e) => setUrl(e.target.value)} />
        </FormField>
        <Button
          disabled={busy}
          onClick={async () => {
            setBusy(true);
            try {
              setFound(await api("/ai-models/discover", { body: { base_url: url || null } }));
            } catch (e) {
              toast.error(e instanceof ApiError ? e.message : "Có lỗi xảy ra");
            } finally {
              setBusy(false);
            }
          }}
        >
          <Radar /> Phát hiện
        </Button>
      </div>
      {found?.error && <FormAlert kind="warning">{found.error}</FormAlert>}
      {found && !found.error && found.models.length === 0 && <p className="text-sm text-muted-foreground">Ollama chưa có model nào — chạy `ollama pull qwen2.5:7b`.</p>}
      {found && found.models.length > 0 && (
        <ul className="divide-y text-sm" data-testid="discovered">
          {found.models.map((d) => (
            <li key={d.model} className="flex items-center justify-between py-2">
              <span>
                <span className="font-mono">{d.model}</span> <span className="text-muted-foreground">{d.parameter_size}</span>
                {d.capabilities.includes("vision") && <span className="ml-2 text-xs text-primary">đọc ảnh</span>}
              </span>
              <Button variant="outline" size="sm" onClick={() => onPick(emptyDraft({ name: d.model, model: d.model, base_url: found.base_url, capabilities: d.capabilities }))}>
                Thêm
              </Button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default function AiModelsPage() {
  const me = useMe();
  const [adding, setAdding] = useState<ReturnType<typeof emptyDraft> | null>(null);
  const [editing, setEditing] = useState<AiModel | null>(null);
  const [discovering, setDiscovering] = useState(false);
  const [tests, setTests] = useState<TestState>({});
  const [version, setVersion] = useState(0);
  const refresh = () => setVersion((v) => v + 1);
  const columns = useMemo(() => modelColumns(tests), [tests]);

  async function test(models: AiModel[]) {
    await Promise.all(
      models.map(async (m) => {
        setTests((t) => ({ ...t, [m.id]: "running" }));
        const r = await api<{ ok: boolean; latency_ms?: number; error?: string }>(`/ai-models/${m.id}/test`, { method: "POST" }).catch((e) => ({
          ok: false,
          error: e instanceof ApiError ? e.message : "Lỗi",
        }));
        setTests((t) => ({ ...t, [m.id]: r }));
      }),
    );
  }

  async function toggle(models: AiModel[]) {
    try {
      for (const m of models.filter((m) => m.editable)) await api(`/ai-models/${m.id}`, { method: "PATCH", body: { enabled: !m.enabled } });
      refresh();
    } catch (e) {
      toast.error(e instanceof ApiError ? e.message : "Có lỗi xảy ra");
    }
  }

  return (
    <>
      <ListLayout header={<PageHeader
        title="Model AI"
        description={me.role === "super_admin" ? "Model hệ thống — mọi trung tâm đều thấy" : "Model trung tâm dùng để tách câu, gắn chuyên đề và đọc ảnh"}
      />}>
        <DataTable
          path="/ai-models"
          columns={columns}
          getRowId={(m) => m.id}
          reloadKey={version}
          onAdd={() => setAdding(emptyDraft())}
          addLabel="Thêm model"
          onEdit={(m) => (m.editable ? setEditing(m) : toast.info("Model hệ thống chỉ quản trị hệ thống sửa được"))}
          onDelete={async (rows) => {
            for (const m of rows.filter((m) => m.editable)) await api(`/ai-models/${m.id}`, { method: "DELETE" });
          }}
          deleteLabel={(rows) => `Xóa ${rows.filter((m) => m.editable).length} model?`}
          rowClassName={(m) => (m.enabled ? undefined : "opacity-60")}
          actions={({ selected }) => (
            <>
              <ToolbarButton disabled={!selected.length} onClick={() => void test(selected)}>
                <Activity /> Kiểm tra
              </ToolbarButton>
              <ToolbarButton disabled={!selected.some((m) => m.editable)} onClick={() => void toggle(selected)}>
                <Power /> Bật/Tắt
              </ToolbarButton>
              <ToolbarButton onClick={() => setDiscovering(true)}>
                <Radar /> Phát hiện Ollama
              </ToolbarButton>
            </>
          )}
          emptyText="Chưa có model nào. Hệ thống vẫn tách đề bằng quy tắc; thêm model để bật AI."
        />
      </ListLayout>
      <FormDialog open={discovering} onOpenChange={setDiscovering} title="Phát hiện model Ollama" wide>
        <Discover onPick={(d) => (setDiscovering(false), setAdding(d))} />
      </FormDialog>
      <FormDialog open={!!adding} title="Thêm model" wide onOpenChange={(o) => !o && setAdding(null)}>
        {adding && <ModelForm initial={adding} onDone={() => (setAdding(null), refresh())} />}
      </FormDialog>
      <FormDialog open={!!editing} title="Sửa model" wide onOpenChange={(o) => !o && setEditing(null)}>
        {editing && <ModelForm existing={editing} initial={emptyDraft({ ...editing, base_url: editing.base_url ?? "", api_key: "" })} onDone={() => (setEditing(null), refresh())} />}
      </FormDialog>
    </>
  );
}
