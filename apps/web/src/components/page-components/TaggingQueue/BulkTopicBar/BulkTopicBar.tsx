"use client";

import { Network, X } from "lucide-react";
import { ToolbarButton } from "@/components/common/DataTable/Toolbar";

/** Bulk apply of the tagging queue (AC-03): one topic for every selected question, in one request.
 *  A topic belongs to one subject, so a selection spanning subjects is refused before it is sent. */
export function BulkTopicBar({ count, mixed, onPick, onClear }: { count: number; mixed: boolean; onPick: () => void; onClear: () => void }) {
  return (
    <>
      <ToolbarButton disabled={count === 0 || mixed} onClick={onPick}>
        <Network /> Gán chuyên đề cho {count} câu
      </ToolbarButton>
      <ToolbarButton disabled={count === 0} onClick={onClear}>
        <X /> Bỏ chọn
      </ToolbarButton>
      {mixed && <span className="px-2 text-xs opacity-80">Chọn các câu cùng môn để gán một lượt</span>}
    </>
  );
}
