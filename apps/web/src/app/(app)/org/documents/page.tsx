"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { DocumentList } from "@/components/documents/DocumentList";
import { ProcessingConfigPanel } from "@/components/documents/ProcessingConfig";
import { UploadForm } from "@/components/documents/UploadForm";
import { Card, Empty, PageHeader } from "@/components/ui";
import { useApi } from "@/lib/hooks";
import type { AiModel, Page, ProcessingConfig, SourceDocument, Taxonomy } from "@/lib/types";

export default function DocumentsPage() {
  const router = useRouter();
  const { data: taxonomy } = useApi<Taxonomy>("/taxonomy");
  const { data, reload } = useApi<Page<SourceDocument>>("/documents?page_size=100");
  const { data: defaults } = useApi<ProcessingConfig>("/org/settings/ingestion");
  const { data: models } = useApi<AiModel[]>("/ai-models?enabled=true");
  const [config, setConfig] = useState<ProcessingConfig | null>(null);
  useEffect(() => {
    if (defaults && !config) setConfig(defaults);
  }, [defaults, config]);
  const busy = data?.items.some((d) => d.status === "queued" || d.status === "processing");
  useEffect(() => {
    if (!busy) return;
    const t = setInterval(reload, 2000);
    return () => clearInterval(t);
  }, [busy, reload]);

  return (
    <>
      <PageHeader title="Đề đã tải lên" subtitle="Tải file Word/PDF/ảnh; hệ thống tự tách từng câu với đáp án, lời giải và hình" />
      <Card className="mb-6">
        {taxonomy && (
          <UploadForm
            taxonomy={taxonomy}
            onUploaded={(doc, duplicate) => router.push(`/org/documents/${doc.id}${duplicate ? "?dup=1" : ""}`)}
            config={config ?? undefined}
            configSlot={config && <ProcessingConfigPanel value={config} onChange={setConfig} models={models ?? []} />}
          />
        )}
      </Card>
      {data && data.items.length === 0 && <Empty>Chưa có đề nào. Tải lên file đầu tiên ở trên.</Empty>}
      {data && data.items.length > 0 && <DocumentList docs={data.items} taxonomy={taxonomy} />}
    </>
  );
}
