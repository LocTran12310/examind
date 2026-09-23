"use client";

import { DataTable } from "@/components/common/DataTable/DataTable";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { eventRowId, useRecentChanges } from "@/hooks/page-hooks/bank/use-recent-changes";
import { useQuestionEventSearchQuery } from "@/hooks/react-query/use-query-question";

/** "Thay đổi gần đây": every change made to the bank, newest first, one row per request — when, who, what it
 *  moved and how many câu — with the way back on the row itself (bulk-safety AC-03, AC-04, AC-05). It opens
 *  from the bank's toolbar because that is where the change was made; a mistake found an hour later is looked
 *  for where it was committed, not on a page of its own. */
export function RecentChanges({ open, onOpenChange }: { open: boolean; onOpenChange: (o: boolean) => void }) {
  const { columns } = useRecentChanges();
  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="gap-0 p-0 data-[side=right]:w-full data-[side=right]:sm:max-w-5xl" data-testid="recent-changes">
        <SheetHeader className="border-b">
          <SheetTitle>Thay đổi gần đây</SheetTitle>
          <SheetDescription>Mỗi dòng là một lượt sửa của cả tổ chức. Hoàn tác đưa mọi câu của lượt đó về đúng như trước.</SheetDescription>
        </SheetHeader>
        <div className="min-h-0 flex-1 overflow-hidden p-3">
          {/* its own URL prefix: the sheet's page and date filter never disturb the bank underneath it */}
          <DataTable useRows={useQuestionEventSearchQuery} prefix="ch." columns={columns} getRowId={eventRowId} selectable={false} emptyText="Chưa có thay đổi nào." />
        </div>
      </SheetContent>
    </Sheet>
  );
}
