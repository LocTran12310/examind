import { useState } from "react";
import { useAiModelOptionsQuery } from "@/hooks/react-query/use-query-ai-model";
import { useIngestionSettingsQuery, useSaveIngestionSettingsMutation } from "@/hooks/react-query/use-query-ingestion-settings";
import type { ProcessingConfig } from "@/interfaces/document.interface";
import { formErrors } from "@/lib/common/form-errors";

/** The org's default processing config: edited locally, saved with "Lưu". */
export function useIngestionSettingsPage() {
  const { data } = useIngestionSettingsQuery();
  const { data: models } = useAiModelOptionsQuery();
  const save = useSaveIngestionSettingsMutation();
  const [edited, setEdited] = useState<ProcessingConfig | null>(null);
  const [saved, setSaved] = useState(false);
  return {
    value: edited ?? data ?? null,
    models: models ?? [],
    saved,
    busy: save.isPending,
    message: formErrors(save.error).message,
    change: (v: ProcessingConfig) => {
      setEdited(v);
      setSaved(false);
    },
    submit: () => {
      const value = edited ?? data;
      if (!value) return;
      save.mutate(value, {
        onSuccess: (r) => {
          setEdited(r);
          setSaved(true);
        },
      });
    },
  };
}
