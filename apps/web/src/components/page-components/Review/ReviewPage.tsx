"use client";

import { ListLayout } from "@/components/common/ListLayout/ListLayout";
import { PageHeader } from "@/components/common/PageHeader/PageHeader";
import { DataTable } from "@/components/common/DataTable/DataTable";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { SPOT_NOTE } from "@/constants/review.constant";
import { useReviewPage } from "@/hooks/page-hooks/review/use-review-page";
import { useReviewDocumentSearchQuery } from "@/hooks/react-query/use-query-review";
import type { ReviewDocument } from "@/interfaces/review.interface";

export function ReviewPage() {
  const p = useReviewPage();
  return (
    <ListLayout
      header={
        <PageHeader
          title="Duyệt câu hỏi"
          description={`Chỉ những câu cần mắt người mới vào hàng đợi. ${SPOT_NOTE}`}
          actions={
            <div className="flex items-center gap-2">
              <Switch id="mine" checked={p.mine} onCheckedChange={p.setMine} />
              <Label htmlFor="mine">Của tôi</Label>
            </div>
          }
        />
      }
    >
      <DataTable<ReviewDocument>
        useRows={useReviewDocumentSearchQuery}
        params={p.params}
        columns={p.columns}
        getRowId={(r) => r.document.id}
        selectable={false}
        emptyText="Không có đề nào cần duyệt."
      />
    </ListLayout>
  );
}
