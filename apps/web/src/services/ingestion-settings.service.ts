import type { ProcessingConfig } from "@/interfaces/document.interface";
import { http } from "@/lib/common/http";

/** The organisation's default processing config for uploads. */
export const ingestionSettingsService = {
  get: () => http<ProcessingConfig>("/org/settings/ingestion"),
  save: (body: ProcessingConfig) => http<ProcessingConfig>("/org/settings/ingestion", { method: "PUT", body }),
};
