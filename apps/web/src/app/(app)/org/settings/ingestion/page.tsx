"use client";

import { useEffect, useState } from "react";
import { ProcessingConfigFields } from "@/components/documents/ProcessingConfig";
import { Alert, Button, Card, PageHeader } from "@/components/ui";
import { api } from "@/lib/api";
import { useApi, useMutation } from "@/lib/hooks";
import type { AiModel, ProcessingConfig } from "@/lib/types";

export default function IngestionSettingsPage() {
  const { data } = useApi<ProcessingConfig>("/org/settings/ingestion");
  const { data: models } = useApi<AiModel[]>("/ai-models?enabled=true");
  const [value, setValue] = useState<ProcessingConfig | null>(null);
  const [saved, setSaved] = useState(false);
  const m = useMutation();
  useEffect(() => {
    if (data) setValue(data);
  }, [data]);
  if (!value) return null;
  return (
    <>
      <PageHeader title="Cấu hình tách đề" subtitle="Mặc định cho mọi lần tải đề của trung tâm; giáo viên vẫn đổi được khi tải lên" />
      <Card className="max-w-3xl space-y-4">
        <ProcessingConfigFields value={value} onChange={(v) => (setValue(v), setSaved(false))} models={models ?? []} showThreshold />
        {m.message && <Alert>{m.message}</Alert>}
        {saved && <Alert tone="green">Đã lưu.</Alert>}
        <div className="flex justify-end">
          <Button
            variant="primary"
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
      </Card>
    </>
  );
}
