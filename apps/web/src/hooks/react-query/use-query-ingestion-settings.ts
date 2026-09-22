import { useMutation, useQuery, useQueryClient, type UseMutationResult, type UseQueryResult } from "@tanstack/react-query";
import { INGESTION_SETTINGS_KEYS } from "@/constants/react-query-key.constant";
import type { ProcessingConfig } from "@/interfaces/document.interface";
import { ingestionSettingsService } from "@/services/ingestion-settings.service";

/** The organisation's default processing config. */
export function useIngestionSettingsQuery(): UseQueryResult<ProcessingConfig, Error> {
  return useQuery<ProcessingConfig, Error>({ queryKey: INGESTION_SETTINGS_KEYS.ALL, queryFn: ingestionSettingsService.get });
}

export function useSaveIngestionSettingsMutation(): UseMutationResult<ProcessingConfig, Error, ProcessingConfig> {
  const qc = useQueryClient();
  return useMutation<ProcessingConfig, Error, ProcessingConfig>({
    mutationFn: ingestionSettingsService.save,
    onSuccess: (saved) => qc.setQueryData(INGESTION_SETTINGS_KEYS.ALL, saved),
  });
}
