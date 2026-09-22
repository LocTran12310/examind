import type { Taxonomy } from "@/interfaces/taxonomy.interface";
import { http } from "@/lib/common/http";

export const taxonomyService = {
  get: () => http<Taxonomy>("/taxonomy"),
};
