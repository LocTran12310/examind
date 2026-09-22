"use client";

import { ListLayout } from "@/components/app/ListLayout";
import { FileUp } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { FormDialog } from "@/components/app/FormDialog";
import { PageHeader } from "@/components/app/PageHeader";
import { DataTable } from "@/components/data-table/DataTable";
import { ToolbarButton } from "@/components/data-table/Toolbar";
import { documentColumns } from "@/components/documents/DocumentList";
import { ProcessingConfigPanel } from "@/components/documents/ProcessingConfig";
import { UploadForm } from "@/components/documents/UploadForm";
import { api } from "@/lib/api";
import { useApi } from "@/lib/hooks";
import type { AiModel, Page, ProcessingConfig, SourceDocument, Taxonomy } from "@/lib/types";

const inFlight = (docs: SourceDocument[]) => docs.some((d) => d.status === "queued" || d.status === "processing");

export default function DocumentsPage() {
  const router = useRouter();
  const { data: taxonomy } = useApi<Taxonomy>("/taxonomy");
  const { data: defaults } = useApi<ProcessingConfig>("/org/settings/ingestion");
  const { data: models } = useApi<Page<AiModel>>("/ai-models?enabled=true&page_size=all");
  const [config, setConfig] = useState<ProcessingConfig | null>(null);
  const [uploading, setUploading] = useState(false);
  const [reloadKey, setReloadKey] = useState(0);
  useEffect(() => {
    if (defaults && !config) setConfig(defaults);
  }, [defaults, config]);
  const columns = useMemo(() => documentColumns(taxonomy), [taxonomy]);

  return (
    <>
      <ListLayout header={<PageHeader title="Đề đã tải lên" description="Tải file Word/PDF/ảnh; hệ thống tự tách từng câu với đáp án, lời giải và hình" />}>
        <DataTable
          path="/documents"
          columns={columns}
          getRowId={(d) => d.id}
          pollWhile={inFlight}
          reloadKey={reloadKey}
          actions={() => (
            <ToolbarButton onClick={() => setUploading(true)}>
              <FileUp /> Tải đề lên
            </ToolbarButton>
          )}
          onDelete={async (rows) => {
            for (const d of rows) await api(`/documents/${d.id}`, { method: "DELETE" });
          }}
          deleteLabel={(rows) => `Xóa ${rows.length} đề? Câu hỏi chưa dùng trong đề thi sẽ bị xóa theo.`}
          onRowActivate={(d) => router.push(`/org/documents/${d.id}`)}
          emptyText="Chưa có đề nào. Bấm “Tải đề lên” để bắt đầu."
        />
      </ListLayout>
      <FormDialog open={uploading} onOpenChange={setUploading} title="Tải đề lên" description="Word (.docx), PDF hoặc ảnh chụp đề" wide>
        {taxonomy && (
          <UploadForm
            taxonomy={taxonomy}
            onFinished={(done) => {
              // one file: open it; a batch: stay here, the list shows every file's progress
              if (done.length === 1) router.push(`/org/documents/${done[0].doc.id}${done[0].duplicate ? "?dup=1" : ""}`);
              else setReloadKey((k) => k + 1);
            }}
            config={config ?? undefined}
            configSlot={config && <ProcessingConfigPanel value={config} onChange={setConfig} models={models?.items ?? []} />}
          />
        )}
      </FormDialog>
    </>
  );
}
