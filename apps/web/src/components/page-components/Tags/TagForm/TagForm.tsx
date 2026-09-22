"use client";

import { useState } from "react";
import { FormAlert } from "@/components/common/FormAlert/FormAlert";
import { FormField } from "@/components/common/FormField/FormField";
import { OptionSelect } from "@/components/common/OptionSelect/OptionSelect";
import { Button } from "@/components/ui/button";
import { DialogFooter } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { SHARED_SUBJECT, TAG_GROUP_OPTIONS } from "@/constants/tag.constant";
import { useTagForm } from "@/hooks/page-hooks/tags/use-tag-form";
import type { Tag, TagGroup } from "@/interfaces/tag.interface";

export interface TagFormProps {
  tag?: Tag;
  onDone: () => void;
  /** pre-selects the subject of a new tag (e.g. the one filtered on the Tags page) */
  subjectId?: string | null;
}

export function TagForm({ tag, onDone, subjectId }: TagFormProps) {
  const [group, setGroup] = useState<TagGroup>(tag?.group ?? "method");
  const [name, setName] = useState(tag?.name ?? "");
  const [subject, setSubject] = useState<string>((tag ? tag.subject_id : subjectId) ?? SHARED_SUBJECT);
  const { subjects, save, busy, fields, message } = useTagForm(tag, onDone);
  const source = group === "source"; // nguồn đề is shared by every subject
  return (
    <form
      className="grid gap-4"
      onSubmit={(e) => {
        e.preventDefault();
        save({ group, name, subject_id: source || subject === SHARED_SUBJECT ? null : subject });
      }}
    >
      {message && !Object.keys(fields).length && <FormAlert>{message}</FormAlert>}
      <FormField label="Nhóm">{(f) => <OptionSelect {...f} value={group} onValueChange={(v) => setGroup(v as TagGroup)} options={TAG_GROUP_OPTIONS} />}</FormField>
      <FormField label="Môn" error={fields.subject_id} hint={source ? "Nguồn đề luôn dùng chung cho mọi môn" : "Tag của một môn chỉ hiện trong bộ lọc của môn đó"}>
        {(f) => (
          <OptionSelect
            {...f}
            disabled={source}
            value={source ? SHARED_SUBJECT : subject}
            onValueChange={setSubject}
            options={[{ value: SHARED_SUBJECT, label: "Dùng chung mọi môn" }, ...subjects.map((s) => ({ value: s.id, label: s.name }))]}
          />
        )}
      </FormField>
      <FormField label="Tên tag" error={fields.name}>
        <Input value={name} onChange={(e) => setName(e.target.value)} required autoFocus />
      </FormField>
      <DialogFooter>
        <Button type="submit" disabled={busy}>
          {tag ? "Lưu" : "Thêm tag"}
        </Button>
      </DialogFooter>
    </form>
  );
}
