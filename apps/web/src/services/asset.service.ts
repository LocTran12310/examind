import type { UploadedAsset } from "@/interfaces/asset.interface";
import { http } from "@/lib/common/http";

export const assetService = {
  upload: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return http<UploadedAsset>("/assets", { form });
  },
};
