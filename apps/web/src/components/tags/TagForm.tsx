"use client";

import { useState } from "react";
import { FormAlert } from "@/components/app/FormAlert";
import { FormField } from "@/components/app/FormField";
import { OptionSelect } from "@/components/app/OptionSelect";
import { Button } from "@/components/ui/button";
import { DialogFooter } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";
import { useMutation } from "@/lib/hooks";
import { type Tag, TAG_GROUP_LABEL } from "@/lib/types";

export const GROUPS = Object.entries(TAG_GROUP_LABEL).map(([value, label]) => ({ value, label }));

export function TagForm({ tag, onDone }: { tag?: Tag; onDone: () => void }) {
  const [group, setGroup] = useState<string>(tag?.group ?? "method");
  const [name, setName] = useState(tag?.name ?? "");
  const m = useMutation();
  return (
    <form
      className="grid gap-4"
      onSubmit={async (e) => {
        e.preventDefault();
        const r = await m.run(() => (tag ? api(`/tags/${tag.id}`, { method: "PATCH", body: { name, group } }) : api("/tags", { body: { group, name } })));
        if (r !== undefined) onDone();
      }}
    >
      {m.message && !Object.keys(m.fields).length && <FormAlert>{m.message}</FormAlert>}
      <FormField label="Nhóm">{(f) => <OptionSelect {...f} value={group} onValueChange={setGroup} options={GROUPS} />}</FormField>
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
