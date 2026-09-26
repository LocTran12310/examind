"use client";

import { Search, X } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { DialogTable, type DialogTableColumn, DialogTableRow } from "@/components/common/DialogTable/DialogTable";
import { FormDialog } from "@/components/common/FormDialog/FormDialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { type StudentStaging, useStudentStaging } from "@/hooks/page-hooks/classes/use-member-manager";
import { StudentPicker } from "../StudentPicker/StudentPicker";

/** Below `sm` the username and the current class ride under the name instead of holding a column each: three text
 *  columns plus the remove button do not fit a 390 px phone, and the overflow used to cut the left off the name
 *  itself — "Học sinh 101" arrived as "c sinh 101". Nothing is dropped, only moved. */
const COLUMNS: DialogTableColumn[] = [
  { header: "Học sinh", className: "whitespace-normal" },
  { header: "Tên đăng nhập", className: "font-mono text-xs text-muted-foreground", hideOnPhone: true },
  { header: "Lớp hiện tại", className: "text-muted-foreground", hideOnPhone: true },
  { className: "w-8" },
];

/** The draft list of who is about to be added: the box on top takes a name at a time, the table under it holds
 *  whoever has been taken, and the footer sends the lot in one request. Typing two characters offers the matching
 *  students; picking one adds a row and empties the box, so a class can be filled by typing names one after
 *  another. The magnifier opens the picker for the other way round — whole old classes, ticked.
 *
 *  Three fixed parts, one height (`tall` on the dialog): only the table scrolls, so staging a student no longer
 *  grows the dialog and walks the footer button out from under the cursor.
 *
 *  This is not "Chuyển năm học" and does not replace it (ADR-04): that one moves a whole year by name rule
 *  (10A1 → 11A1) and records how each student left. This one is the small, pointed version — this new class, from
 *  those old classes, chosen by hand. The link below is there because the bigger door is easy to miss from in here,
 *  which is exactly how this screen came to be the only one anybody found. */
export function AddStudents({ classId, onAdd }: { classId: string; onAdd: (userIds: string[]) => Promise<boolean> }) {
  const s = useStudentStaging(classId);
  const [picking, setPicking] = useState(false);
  return (
    <div className="flex h-full min-h-0 flex-col gap-3">
      <div className="flex shrink-0 items-start gap-2">
        {/* the box used to be the last row of the table: it moved down with every name staged, and what it
            offered was clipped by the scroll box it sat in. Up here it stays put and the list opens over. */}
        <div className="relative flex-1">
          <Input
            aria-label="Tìm học sinh để thêm"
            placeholder="Nhập tên hoặc tên đăng nhập"
            value={s.q}
            onChange={(e) => s.setQ(e.target.value)}
            onKeyDown={(e) => {
              // Enter takes the first name that can be taken: filling a class is typing, not aiming
              if (e.key !== "Enter") return;
              e.preventDefault();
              const first = s.matches.find((u) => !s.note(u));
              if (first) pickOne(s, first.id);
            }}
          />
          {s.searching && <Suggestions s={s} />}
        </div>
        <Button type="button" variant="outline" size="icon" aria-label="Chọn học sinh từ lớp khác" title="Chọn học sinh từ lớp khác" onClick={() => setPicking(true)}>
          <Search />
        </Button>
      </div>
      <DialogTable columns={COLUMNS} testId="staged-students">
        {s.staged.map((u) => {
          // named, because a JSX element written straight into the cells array asks eslint for a key it has no use for
          const drop = (
            <Button type="button" variant="ghost" size="icon-sm" aria-label={`Bỏ ${u.full_name}`} onClick={() => s.unstage(u.id)}>
              <X />
            </Button>
          );
          return (
            <DialogTableRow
              key={u.id}
              cells={[
                <>
                  <span className="font-medium">{u.full_name}</span>
                  <div className="text-xs text-muted-foreground sm:hidden">
                    {u.username} · {s.classLabel(u)}
                  </div>
                </>,
                u.username,
                s.classLabel(u),
                drop,
              ]}
            />
          );
        })}
        {s.staged.length === 0 && <DialogTableRow span cells={["Chưa có em nào trong danh sách — gõ tên vào ô trên, hoặc chọn từ một lớp khác."]} />}
      </DialogTable>
      <div className="shrink-0 border-t pt-3">
        <Button className="w-full" disabled={s.staged.length === 0} onClick={() => void onAdd(s.staged.map((u) => u.id))}>
          Thêm {s.staged.length} học sinh
        </Button>
        <p className="mt-2 text-xs text-muted-foreground">
          Chuyển cả một năm học — mọi lớp, 10A1 lên 11A1, kèm ở lại và tốt nghiệp — thì dùng{" "}
          <Link href="/org/school-years" className="underline hover:text-primary">
            Năm học › Chuyển năm học
          </Link>
          .
        </p>
      </div>
      <FormDialog open={picking} onOpenChange={setPicking} title="Chọn học sinh" description="Tích cả lớp cũ hoặc từng em, rồi bấm chọn để đưa vào danh sách." wide tall>
        <StudentPicker
          classId={classId}
          staged={s.ids}
          onConfirm={(users) => {
            s.stage(users);
            setPicking(false);
          }}
          onCancel={() => setPicking(false)}
        />
      </FormDialog>
    </div>
  );
}

/** Stage one match and empty the box, so the next name can be typed straight away. */
function pickOne(s: StudentStaging, id: string) {
  const u = s.matches.find((m) => m.id === id);
  if (!u) return;
  s.stage([u]);
  s.clearQuery();
}

/** What the box matches, over the table rather than above it: a panel in flow would push the rows — and with them
 *  the footer — down a little on every keystroke. */
function Suggestions({ s }: { s: StudentStaging }) {
  return (
    <ul
      aria-label="Học sinh khớp"
      data-testid="student-suggestions"
      className="absolute inset-x-0 top-full z-20 mt-1 max-h-60 divide-y overflow-y-auto rounded-lg border bg-popover shadow-md"
    >
      {s.matches.length === 0 && <li className="px-2 py-1.5 text-sm text-muted-foreground">Không có học sinh nào khớp.</li>}
      {s.matches.map((u) => {
        const note = s.note(u);
        return (
          <li key={u.id}>
            {/* whoever cannot be taken stays on the list and says why, instead of the name seeming not to exist */}
            <button
              type="button"
              disabled={!!note}
              onClick={() => pickOne(s, u.id)}
              className="flex w-full items-center gap-2 px-2 py-1.5 text-left text-sm hover:bg-muted disabled:pointer-events-none disabled:opacity-60"
            >
              {u.full_name} <span className="font-mono text-xs text-muted-foreground">{u.username}</span>
              <span className="ml-auto text-xs text-muted-foreground">{note || s.classLabel(u)}</span>
            </button>
          </li>
        );
      })}
      {s.more > 0 && <li className="px-2 py-1.5 text-xs text-muted-foreground">Còn {s.more} kết quả nữa — lọc thêm để thấy.</li>}
    </ul>
  );
}
