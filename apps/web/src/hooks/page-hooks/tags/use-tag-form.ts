import type { CreateTagBody } from "@/dtos/tag.dto";
import { useCreateTagMutation, useUpdateTagMutation } from "@/hooks/react-query/use-query-tag";
import { useTaxonomyQuery } from "@/hooks/react-query/use-query-taxonomy";
import type { Tag } from "@/interfaces/tag.interface";
import { formErrors } from "@/lib/common/form-errors";

/** Create or edit a tag; `onDone` after the server accepted it. */
export function useTagForm(tag: Tag | undefined, onDone: () => void) {
  const { data: taxonomy } = useTaxonomyQuery();
  const create = useCreateTagMutation();
  const update = useUpdateTagMutation();
  const active = tag ? update : create;
  const { fields, message } = formErrors(active.error);
  return {
    subjects: taxonomy?.subjects ?? [],
    busy: active.isPending,
    fields,
    message,
    save: (body: CreateTagBody) =>
      tag ? update.mutate({ id: tag.id, body }, { onSuccess: onDone }) : create.mutate(body, { onSuccess: onDone }),
  };
}
