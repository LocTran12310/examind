"use client";

import { FormAlert } from "@/components/app/FormAlert";
import { PageHeader } from "@/components/app/PageHeader";
import { Panel } from "@/components/app/Panel";
import { ProcessingConfigFields } from "@/components/common/ProcessingConfig/ProcessingConfig";
import { Button } from "@/components/ui/button";
import { useIngestionSettingsPage } from "@/hooks/page-hooks/ingestion-settings/use-ingestion-settings-page";

export function IngestionSettingsPage() {
  const p = useIngestionSettingsPage();
  if (!p.value) return null;
  return (
    <>
      <PageHeader title="Cấu hình tách đề" description="Mặc định cho mọi lần tải đề của trung tâm; giáo viên vẫn đổi được khi tải lên" />
      <Panel className="max-w-3xl space-y-4">
        <ProcessingConfigFields value={p.value} onChange={p.change} models={p.models} showThreshold />
        {p.message && <FormAlert>{p.message}</FormAlert>}
        {p.saved && <FormAlert kind="success">Đã lưu.</FormAlert>}
        <div className="flex justify-end">
          <Button disabled={p.busy} onClick={p.submit}>
            Lưu
          </Button>
        </div>
      </Panel>
    </>
  );
}
