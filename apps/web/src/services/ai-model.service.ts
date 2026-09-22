import type { CreateAiModelBody, DiscoverModelsBody, UpdateAiModelBody } from "@/dtos/ai-model.dto";
import type { SearchBody } from "@/dtos/search.dto";
import type { AiModel, DiscoverResult, ModelTestResult } from "@/interfaces/ai-model.interface";
import type { SearchPage } from "@/interfaces/search-page.interface";
import { http } from "@/lib/common/http";

export const aiModelService = {
  search: (body: SearchBody) => http<SearchPage<AiModel>>("/ai-models/search", { body }),
  create: (body: CreateAiModelBody) => http<AiModel>("/ai-models", { body }),
  update: (id: string, body: UpdateAiModelBody) => http<AiModel>(`/ai-models/${id}`, { method: "PATCH", body }),
  remove: (id: string) => http<void>(`/ai-models/${id}`, { method: "DELETE" }),
  /** Models an Ollama server offers (the server's default when `base_url` is null). */
  discover: (body: DiscoverModelsBody) => http<DiscoverResult>("/ai-models/discover", { body }),
  test: (id: string) => http<ModelTestResult>(`/ai-models/${id}/test`, { method: "POST" }),
};
