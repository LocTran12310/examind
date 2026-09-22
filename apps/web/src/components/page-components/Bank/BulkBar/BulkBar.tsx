"use client";

import { Check, ChevronDown, Gauge, Network, Tag as TagIcon, Trash2, X } from "lucide-react";
import { ConfirmDialog } from "@/components/app/ConfirmDialog";
import { FormDialog } from "@/components/app/FormDialog";
import { ToolbarButton } from "@/components/common/DataTable/Toolbar";
import { TopicPicker } from "@/components/common/TopicPicker/TopicPicker";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { DIFFICULTY_LABEL } from "@/constants/question.constant";
import { useBulkActions } from "@/hooks/page-hooks/bank/use-bulk-actions";
import type { Tag } from "@/interfaces/tag.interface";
import type { Topic } from "@/interfaces/topic.interface";

/** Bulk actions for the selected questions, rendered inside the table toolbar. */
export function BulkActions({ ids, topics, tags, onDone, onClear }: { ids: string[]; topics: Topic[]; tags: Tag[]; onDone?: () => void; onClear: () => void }) {
  const b = useBulkActions({ ids, onDone, onClear });
  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <ToolbarButton disabled={b.none}>
            <Gauge /> Mức độ <ChevronDown />
          </ToolbarButton>
        </DropdownMenuTrigger>
        <DropdownMenuContent>
          {Object.entries(DIFFICULTY_LABEL).map(([k, v]) => (
            <DropdownMenuItem key={k} onSelect={() => void b.apply({ difficulty: k }, `Đã đặt mức độ ${v}`)}>
              {v}
            </DropdownMenuItem>
          ))}
        </DropdownMenuContent>
      </DropdownMenu>
      <ToolbarButton disabled={b.none} onClick={() => b.setPicking(true)}>
        <Network /> Chuyên đề
      </ToolbarButton>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <ToolbarButton disabled={b.none || !tags.length}>
            <TagIcon /> Thêm tag <ChevronDown />
          </ToolbarButton>
        </DropdownMenuTrigger>
        <DropdownMenuContent className="max-h-72 overflow-y-auto">
          {tags.map((t) => (
            <DropdownMenuItem key={t.id} onSelect={() => void b.apply({ add_tag_ids: [t.id] }, `Đã thêm tag ${t.name}`)}>
              {t.name}
            </DropdownMenuItem>
          ))}
        </DropdownMenuContent>
      </DropdownMenu>
      <ToolbarButton disabled={b.none} onClick={() => void b.apply({ status: "approved" }, "Đã duyệt")}>
        <Check /> Duyệt
      </ToolbarButton>
      <ToolbarButton disabled={b.none} onClick={() => void b.apply({ status: "rejected" }, "Đã loại")}>
        <X /> Loại
      </ToolbarButton>
      <ToolbarButton disabled={b.none} onClick={() => b.setConfirming(true)}>
        <Trash2 /> Xóa
      </ToolbarButton>
      <ConfirmDialog
        open={b.confirming}
        onOpenChange={b.setConfirming}
        destructive
        title={`Xóa vĩnh viễn ${ids.length} câu hỏi?`}
        description="Câu đang dùng trong đề thi sẽ không bị xóa."
        confirmLabel="Xóa"
        onConfirm={async () => {
          b.setConfirming(false);
          await b.remove();
        }}
      />
      <FormDialog open={b.picking} title="Đặt chuyên đề cho các câu đã chọn" onOpenChange={b.setPicking}>
        <TopicPicker
          topics={topics}
          onPick={(t) => {
            b.setPicking(false);
            void b.apply({ primary_topic_id: t.id }, `Đã đặt chuyên đề ${t.name}`);
          }}
          onClose={() => b.setPicking(false)}
        />
      </FormDialog>
    </>
  );
}
