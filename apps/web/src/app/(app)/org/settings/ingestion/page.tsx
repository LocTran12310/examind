"use client";

import { useEffect, useState } from "react";
import { ProcessingConfigFields } from "@/components/documents/ProcessingConfig";
import { FormAlert } from "@/components/app/FormAlert";
import { Button } from "@/components/ui/button";
import { Panel } from "@/components/app/Panel";
import { PageHeader } from "@/components/app/PageHeader";
import { api } from "@/lib/api";
import { useApi, useMutation } from "@/lib/hooks";
import type { AiModel, Page, ProcessingConfig } from "@/lib/types";

export default function IngestionSettingsPage() {
  const { data } = useApi<ProcessingConfig>("/org/settings/ingestion");
  const { data: modelsPage } = useApi<Page<AiModel>>("/ai-models?enabled=true&page_size=all");
  const models = modelsPage?.items;
  const [value, setValue] = useState<ProcessingConfig | null>(null);
  const [saved, setSaved] = useState(false);
  const m = useMutation();
  useEffect(() => {
    if (data) setValue(data);
  }, [data]);
  if (!value) return null;
  return (
    <>
      <PageHeader title="Cấu hình tách đề" description="Mặc định cho mọi lần tải đề của trung tâm; giáo viên vẫn đổi được khi tải lên" />
      <Panel className="max-w-3xl space-y-4">
        <ProcessingConfigFields value={value} onChange={(v) => (setValue(v), setSaved(false))} models={models ?? []} showThreshold />
        {m.message && <FormAlert>{m.message}</FormAlert>}
        {saved && <FormAlert kind="success">Đã lưu.</FormAlert>}
        <div className="flex justify-end">
          <Button
           
            disabled={m.busy}
            onClick={async () => {
              const r = await m.run(() => api<ProcessingConfig>("/org/settings/ingestion", { method: "PUT", body: value }));
              if (r) {
                setValue(r);
                setSaved(true);
              }
            }}
          >
            Lưu
          </Button>
        </div>
      </Panel>
    </>
  );
}
