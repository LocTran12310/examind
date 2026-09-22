"use client";

import { DataTable } from "@/components/common/DataTable/DataTable";
import { FormDialog } from "@/components/common/FormDialog/FormDialog";
import { ListLayout } from "@/components/common/ListLayout/ListLayout";
import { PageHeader } from "@/components/common/PageHeader/PageHeader";
import { useTagsPage } from "@/hooks/page-hooks/tags/use-tags-page";
import { useTagSearchQuery } from "@/hooks/react-query/use-query-tag";
import { TagForm } from "./TagForm/TagForm";

export function TagsPage() {
  const p = useTagsPage();
  return (
    <>
      <ListLayout header={<PageHeader title="Tags" description="Nhãn tự do, gắn nhiều nhãn cho một câu hỏi (phương pháp, kỹ năng, nguồn đề…)" />}>
        <DataTable
          useRows={useTagSearchQuery}
          params={p.params}
          columns={p.columns}
          getRowId={(t) => t.id}
          onAdd={() => p.setCreating(true)}
          addLabel="Thêm tag"
          onEdit={p.setEditing}
          onDelete={p.removeTags}
          deleteLabel={(rows) => `Xóa ${rows.length} tag? Câu hỏi sẽ bỏ các tag này.`}
        />
      </ListLayout>
      <FormDialog open={p.creating} onOpenChange={p.setCreating} title="Thêm tag">
        <TagForm subjectId={p.newTagSubject} onDone={() => p.setCreating(false)} />
      </FormDialog>
      <FormDialog open={!!p.editing} onOpenChange={(o) => !o && p.setEditing(null)} title="Sửa tag">
        {p.editing && <TagForm tag={p.editing} onDone={() => p.setEditing(null)} />}
      </FormDialog>
    </>
  );
}
