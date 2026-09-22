"use client";

import { useState } from "react";
import { FormAlert } from "@/components/app/FormAlert";
import { FormField } from "@/components/app/FormField";
import { OptionSelect } from "@/components/app/OptionSelect";
import { Button } from "@/components/ui/button";
import { DialogFooter } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";
import { useApi, useMutation } from "@/lib/hooks";
import { type Tag, TAG_GROUP_LABEL, type Taxonomy } from "@/lib/types";

export const GROUPS = Object.entries(TAG_GROUP_LABEL).map(([value, label]) => ({ value, label }));

const SHARED = "shared";

/** `subjectId` pre-selects the subject for a new tag (e.g. the one filtered on the Tags page). */
export function TagForm({ tag, onDone, subjectId }: { tag?: Tag; onDone: () => void; subjectId?: string | null }) {
  const [group, setGroup] = useState<string>(tag?.group ?? "method");
  const [name, setName] = useState(tag?.name ?? "");
  const [subject, setSubject] = useState<string>((tag ? tag.subject_id : subjectId) ?? SHARED);
  const { data: taxonomy } = useApi<Taxonomy>("/taxonomy");
  const m = useMutation();
  const source = group === "source"; // nguồn đề is shared by every subject
  const subject_id = source || subject === SHARED ? null : subject;
  return (
    <form
      className="grid gap-4"
      onSubmit={async (e) => {
        e.preventDefault();
        const r = await m.run(() => (tag ? api(`/tags/${tag.id}`, { method: "PATCH", body: { name, group, subject_id } }) : api("/tags", { body: { group, name, subject_id } })));
        if (r !== undefined) onDone();
      }}
    >
      {m.message && !Object.keys(m.fields).length && <FormAlert>{m.message}</FormAlert>}
      <FormField label="Nhóm">{(f) => <OptionSelect {...f} value={group} onValueChange={setGroup} options={GROUPS} />}</FormField>
      <FormField label="Môn" error={m.fields.subject_id} hint={source ? "Nguồn đề luôn dùng chung cho mọi môn" : "Tag của một môn chỉ hiện trong bộ lọc của môn đó"}>
        {(f) => (
          <OptionSelect
            {...f}
            disabled={source}
            value={source ? SHARED : subject}
            onValueChange={setSubject}
            options={[{ value: SHARED, label: "Dùng chung mọi môn" }, ...(taxonomy?.subjects ?? []).map((s) => ({ value: s.id, label: s.name }))]}
          />
        )}
      </FormField>
      <FormField label="Tên tag" error={m.fields.name}>
        <Input value={name} onChange={(e) => setName(e.target.value)} required autoFocus />
      </FormField>
      <DialogFooter>
        <Button type="submit" disabled={m.busy}>
          {tag ? "Lưu" : "Thêm tag"}
        </Button>
      </DialogFooter>
    </form>
  );
}
