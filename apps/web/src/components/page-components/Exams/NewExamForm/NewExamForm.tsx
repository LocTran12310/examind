"use client";

import { FormAlert } from "@/components/common/FormAlert/FormAlert";
import { FormField } from "@/components/common/FormField/FormField";
import { Button } from "@/components/ui/button";
import { DialogFooter } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { useNewExamForm } from "@/hooks/page-hooks/exams/use-new-exam-form";

export function NewExamForm() {
  const f = useNewExamForm();
  return (
    <form
      className="grid gap-4"
      onSubmit={(e) => {
        e.preventDefault();
        f.submit();
      }}
    >
      {f.message && <FormAlert>{f.message}</FormAlert>}
      <FormField label="Tên đề" error={f.fields.title}>
        <Input placeholder="Kiểm tra 15 phút – Hàm số bậc hai" value={f.title} onChange={(e) => f.setTitle(e.target.value)} required autoFocus />
      </FormField>
      <DialogFooter>
        <Button type="submit" disabled={f.busy}>
          Tạo và soạn đề
        </Button>
      </DialogFooter>
    </form>
  );
}
