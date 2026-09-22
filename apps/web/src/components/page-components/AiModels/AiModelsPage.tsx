"use client";

import { Activity, Power, Radar } from "lucide-react";
import { FormDialog } from "@/components/common/FormDialog/FormDialog";
import { ListLayout } from "@/components/common/ListLayout/ListLayout";
import { PageHeader } from "@/components/common/PageHeader/PageHeader";
import { DataTable } from "@/components/common/DataTable/DataTable";
import { ToolbarButton } from "@/components/common/DataTable/Toolbar";
import { useAiModelsPage } from "@/hooks/page-hooks/ai-models/use-ai-models-page";
import { useAiModelSearchQuery } from "@/hooks/react-query/use-query-ai-model";
import { draftOf, emptyDraft } from "@/lib/page-libs/ai-models/model-draft";
import { DiscoverModels } from "./DiscoverModels/DiscoverModels";
import { ModelForm } from "./ModelForm/ModelForm";

export function AiModelsPage() {
  const p = useAiModelsPage();
  return (
    <>
      <ListLayout header={<PageHeader title="Model AI" description={p.description} />}>
        <DataTable
          useRows={useAiModelSearchQuery}
          columns={p.columns}
          getRowId={(m) => m.id}
          onAdd={() => p.setAdding(emptyDraft())}
          addLabel="Thêm model"
          onEdit={p.edit}
          onDelete={p.removeModels}
          deleteLabel={(rows) => `Xóa ${rows.filter((m) => m.editable).length} model?`}
          rowClassName={(m) => (m.enabled ? undefined : "opacity-60")}
          actions={({ selected }) => (
            <>
              <ToolbarButton disabled={!selected.length} onClick={() => void p.testModels(selected)}>
                <Activity /> Kiểm tra
              </ToolbarButton>
              <ToolbarButton disabled={!selected.some((m) => m.editable)} onClick={() => p.toggleModels(selected)}>
                <Power /> Bật/Tắt
              </ToolbarButton>
              <ToolbarButton onClick={() => p.setDiscovering(true)}>
                <Radar /> Phát hiện Ollama
              </ToolbarButton>
            </>
          )}
          emptyText="Chưa có model nào. Hệ thống vẫn tách đề bằng quy tắc; thêm model để bật AI."
        />
      </ListLayout>
      <FormDialog open={p.discovering} onOpenChange={p.setDiscovering} title="Phát hiện model Ollama" wide>
        <DiscoverModels onPick={p.picked} />
      </FormDialog>
      <FormDialog open={!!p.adding} title="Thêm model" wide onOpenChange={(o) => !o && p.setAdding(null)}>
        {p.adding && <ModelForm initial={p.adding} onDone={() => p.setAdding(null)} />}
      </FormDialog>
      <FormDialog open={!!p.editing} title="Sửa model" wide onOpenChange={(o) => !o && p.setEditing(null)}>
        {p.editing && <ModelForm existing={p.editing} initial={draftOf(p.editing)} onDone={() => p.setEditing(null)} />}
      </FormDialog>
    </>
  );
}
