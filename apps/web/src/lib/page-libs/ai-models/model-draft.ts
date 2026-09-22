import type { CreateAiModelBody, UpdateAiModelBody } from "@/dtos/ai-model.dto";
import type { AiModel, ModelDraft } from "@/interfaces/ai-model.interface";

export const emptyDraft = (p: Partial<ModelDraft> = {}): ModelDraft => ({
  name: "", provider: "ollama", model: "", base_url: "", api_key: "", capabilities: ["text"], is_free: true, ...p,
});

/** The form of an existing model: its fields, never its key. */
export const draftOf = (m: AiModel): ModelDraft => emptyDraft({ ...m, base_url: m.base_url ?? "", api_key: "" });

/** Body sent for a draft: an empty key keeps the stored one on update, and means "no key" on create. */
export function draftBody(d: ModelDraft, existing: boolean): CreateAiModelBody | UpdateAiModelBody {
  const body: CreateAiModelBody = { ...d, base_url: d.base_url || null };
  if (existing && !d.api_key) delete body.api_key;
  if (!existing && !d.api_key) body.api_key = null;
  return body;
}
