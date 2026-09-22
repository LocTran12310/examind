import type { ModelCapability, Provider } from "@/interfaces/ai-model.interface";

export interface CreateAiModelBody {
  name: string;
  provider: Provider;
  model: string;
  base_url: string | null;
  /** null = no key; left out on update = keep the stored one */
  api_key?: string | null;
  capabilities: ModelCapability[];
  is_free: boolean;
}

export type UpdateAiModelBody = Partial<CreateAiModelBody> & { enabled?: boolean };

export interface DiscoverModelsBody {
  base_url: string | null;
}
