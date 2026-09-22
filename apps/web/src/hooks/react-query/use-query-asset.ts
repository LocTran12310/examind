import { useMutation, type UseMutationResult } from "@tanstack/react-query";
import type { UploadedAsset } from "@/interfaces/asset.interface";
import { assetService } from "@/services/asset.service";

/** Upload a pasted / dropped image; nothing cached depends on it. */
export function useUploadAssetMutation(): UseMutationResult<UploadedAsset, Error, File> {
  return useMutation<UploadedAsset, Error, File>({ mutationFn: assetService.upload });
}
