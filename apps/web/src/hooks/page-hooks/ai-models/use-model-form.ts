import { useState } from "react";
import type { CreateAiModelBody } from "@/dtos/ai-model.dto";
import { useCreateAiModelMutation, useUpdateAiModelMutation } from "@/hooks/react-query/use-query-ai-model";
import type { AiModel, ModelCapability, ModelDraft } from "@/interfaces/ai-model.interface";
import { formErrors } from "@/lib/common/form-errors";
import { draftBody } from "@/lib/page-libs/ai-models/model-draft";

/** Add a model or edit one; `onDone` after the server accepted it. */
export function useModelForm(initial: ModelDraft, existing: AiModel | undefined, onDone: () => void) {
  const [draft, setDraft] = useState<ModelDraft>(initial);
  const create = useCreateAiModelMutation();
  const update = useUpdateAiModelMutation();
  const active = existing ? update : create;
  const { fields, message } = formErrors(active.error);
  const set = <K extends keyof ModelDraft>(k: K, v: ModelDraft[K]) => setDraft((x) => ({ ...x, [k]: v }));
  return {
    draft,
    set,
    toggleCap: (c: ModelCapability) => set("capabilities", draft.capabilities.includes(c) ? draft.capabilities.filter((x) => x !== c) : [...draft.capabilities, c]),
    busy: active.isPending,
    fields,
    message,
    submit: () => {
      const body = draftBody(draft, !!existing);
      if (existing) update.mutate({ id: existing.id, body }, { onSuccess: onDone });
      else create.mutate(body as CreateAiModelBody, { onSuccess: onDone });
    },
  };
}
