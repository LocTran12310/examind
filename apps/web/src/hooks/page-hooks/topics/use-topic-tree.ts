import { useState } from "react";
import {
  useCreateTopicMutation, useDeleteTopicMutation, useMergeTopicMutation, useMoveTopicMutation, useUpdateTopicMutation,
} from "@/hooks/react-query/use-query-topic";
import { ApiError } from "@/lib/common/http";

/** Tree edits (add, rename, move, merge, delete); the tree refetches by itself, a refusal is shown above it. */
export function useTopicTree(subjectId: string) {
  const [error, setError] = useState<string | null>(null);
  const create = useCreateTopicMutation();
  const update = useUpdateTopicMutation();
  const move = useMoveTopicMutation();
  const merge = useMergeTopicMutation();
  const remove = useDeleteTopicMutation();

  async function run(fn: () => Promise<unknown>): Promise<boolean> {
    setError(null);
    try {
      await fn();
      return true;
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Có lỗi xảy ra");
      return false;
    }
  }

  return {
    error,
    addStrand: (name: string) => run(() => create.mutateAsync({ name, subject_id: subjectId })),
    addChild: (parentId: string, name: string) => run(() => create.mutateAsync({ name, parent_id: parentId })),
    rename: (id: string, name: string) => run(() => update.mutateAsync({ id, body: { name } })),
    moveTo: (id: string, parentId: string | null) => run(() => move.mutateAsync({ id, parentId })),
    mergeInto: (id: string, targetId: string) => run(() => merge.mutateAsync({ id, targetId })),
    remove: (id: string) => run(() => remove.mutateAsync(id)),
  };
}
