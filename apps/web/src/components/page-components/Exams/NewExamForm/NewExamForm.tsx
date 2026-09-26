"use client";

import { FormAlert } from "@/components/common/FormAlert/FormAlert";
import { FormField } from "@/components/common/FormField/FormField";
import { OptionSelect } from "@/components/common/OptionSelect/OptionSelect";
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
      <div className="grid gap-4 sm:grid-cols-2">
        {/* the subject is what scopes the matrix: without one the topic picker opens every subject's tree */}
        <FormField label="Môn" error={f.fields.subject_id} hint="Ma trận của đề chỉ mở chuyên đề của môn này">
          <OptionSelect
            aria-label="Môn"
            value={f.subjectId}
            onValueChange={f.setSubjectId}
            emptyLabel="Chưa chọn"
            options={f.subjects.map((s) => ({ value: s.id, label: s.name }))}
          />
        </FormField>
        <FormField label="Lớp" error={f.fields.grade} hint="Khối đề này dùng cho">
          <OptionSelect
            aria-label="Lớp"
            value={f.grade}
            onValueChange={f.setGrade}
            emptyLabel="Chưa chọn"
            options={f.grades.map((g) => ({ value: String(g.level), label: g.name }))}
          />
        </FormField>
      </div>
      <DialogFooter>
        <Button type="submit" disabled={f.busy}>
          Tạo và soạn đề
        </Button>
      </DialogFooter>
    </form>
  );
}
