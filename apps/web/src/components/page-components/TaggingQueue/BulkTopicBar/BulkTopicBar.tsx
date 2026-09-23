"use client";

import { Network, Sparkles, X } from "lucide-react";
import { ToolbarButton } from "@/components/common/DataTable/Toolbar";

/** Bulk apply of the tagging queue: "Gán theo gợi ý" gives every selected question its own top suggestion
 *  in one request (AC-03), "Gán chuyên đề" gives them all the same one. A topic belongs to one subject, so
 *  a selection spanning subjects is refused for the second — the first is per question and never is. */
export function BulkTopicBar({
  count,
  suggestable,
  mixed,
  onApplySuggestions,
  onPick,
  onClear,
}: {
  count: number;
  suggestable: number;
  mixed: boolean;
  onApplySuggestions: () => void;
  onPick: () => void;
  onClear: () => void;
}) {
  return (
    <>
      <ToolbarButton disabled={count === 0 || suggestable === 0} onClick={onApplySuggestions}>
        <Sparkles /> Gán theo gợi ý ({suggestable})
      </ToolbarButton>
      <ToolbarButton disabled={count === 0 || mixed} onClick={onPick}>
        <Network /> Gán chuyên đề cho {count} câu
      </ToolbarButton>
      <ToolbarButton disabled={count === 0} onClick={onClear}>
        <X /> Bỏ chọn
      </ToolbarButton>
      {mixed && <span className="px-2 text-xs opacity-80">Chọn các câu cùng môn để gán một lượt</span>}
      {count > 0 && suggestable < count && <span className="px-2 text-xs opacity-80">{count - suggestable} câu chưa có gợi ý</span>}
    </>
  );
}
