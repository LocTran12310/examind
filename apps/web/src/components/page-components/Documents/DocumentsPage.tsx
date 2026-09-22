"use client";

import { FileUp } from "lucide-react";
import { FormDialog } from "@/components/common/FormDialog/FormDialog";
import { ListLayout } from "@/components/common/ListLayout/ListLayout";
import { PageHeader } from "@/components/common/PageHeader/PageHeader";
import { DataTable } from "@/components/common/DataTable/DataTable";
import { ToolbarButton } from "@/components/common/DataTable/Toolbar";
import { ProcessingConfigPanel } from "@/components/common/ProcessingConfig/ProcessingConfig";
import { inFlight, useDocumentsPage } from "@/hooks/page-hooks/documents/use-documents-page";
import { useDocumentSearchQuery } from "@/hooks/react-query/use-query-document";
import { UploadForm } from "./UploadForm/UploadForm";

export function DocumentsPage() {
  const p = useDocumentsPage();
  return (
    <>
      <ListLayout header={<PageHeader title="Đề đã tải lên" description="Tải file Word/PDF/ảnh; hệ thống tự tách từng câu với đáp án, lời giải và hình" />}>
        <DataTable
          useRows={useDocumentSearchQuery}
          refetchWhile={inFlight}
          columns={p.columns}
          getRowId={(d) => d.id}
          actions={() => (
            <ToolbarButton onClick={() => p.setUploading(true)}>
              <FileUp /> Tải đề lên
            </ToolbarButton>
          )}
          onDelete={p.removeDocuments}
          deleteLabel={(rows) => `Xóa ${rows.length} đề? Câu hỏi chưa dùng trong đề thi sẽ bị xóa theo.`}
          onRowActivate={p.open}
          emptyText="Chưa có đề nào. Bấm “Tải đề lên” để bắt đầu."
        />
      </ListLayout>
      <FormDialog open={p.uploading} onOpenChange={p.setUploading} title="Tải đề lên" description="Word (.docx), PDF hoặc ảnh chụp đề" wide>
        {p.taxonomy && (
          <UploadForm
            taxonomy={p.taxonomy}
            onFinished={p.uploaded}
            config={p.config ?? undefined}
            configSlot={p.config && <ProcessingConfigPanel value={p.config} onChange={p.setConfig} models={p.models} />}
          />
        )}
      </FormDialog>
    </>
  );
}
