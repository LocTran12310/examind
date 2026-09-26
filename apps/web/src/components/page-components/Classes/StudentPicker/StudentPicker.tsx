"use client";

import { DialogTable, type DialogTableColumn, DialogTableRow } from "@/components/common/DialogTable/DialogTable";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { type ClassAdder, useClassAdder, useClassRoster } from "@/hooks/page-hooks/classes/use-member-manager";
import type { SchoolClass } from "@/interfaces/class.interface";
import type { User } from "@/interfaces/user.interface";

/** The school year moves under the class name on a phone; the count stays, because it is what makes one tick worth
 *  25 students. The checkbox and the fold arrow are the table's own two columns, not these. */
const COLUMNS: DialogTableColumn[] = [
  { header: "Lớp", className: "whitespace-normal" },
  { header: "Năm học", className: "text-muted-foreground", hideOnPhone: true },
  { header: "Học sinh", className: "text-right tabular-nums text-muted-foreground" },
];

/** Chọn học sinh: picking many at once. One table of every other class of the organisation, each row folded over
 *  its own roster, ticks on class rows and on student rows; the search box answers the other question — "em này
 *  đang ở đâu?" instead of "lớp nào?" — over the same selection.
 *
 *  The box on top and the two buttons at the bottom do not move: the middle is the only part that scrolls, whether
 *  it is showing the classes or the matches of a search.
 *
 *  Confirming hands what is ticked to the draft list of the dialog underneath. It saves nothing: that dialog's
 *  footer is the one request. Cancelling leaves the draft list as it was. */
export function StudentPicker({
  classId,
  staged,
  onConfirm,
  onCancel,
}: {
  classId: string;
  /** already on the draft list: offered, but not takeable a second time */
  staged: ReadonlySet<string>;
  onConfirm: (users: User[]) => void;
  onCancel: () => void;
}) {
  const a = useClassAdder(classId, staged);
  const addable = a.rows.filter((u) => !a.note(u));
  return (
    <div className="flex h-full min-h-0 flex-col gap-3">
      <Input autoFocus aria-label="Tìm học sinh" placeholder="Tên hoặc tên đăng nhập" value={a.q} onChange={(e) => a.setQ(e.target.value)} className="shrink-0" />
      {a.searching ? (
        <>
          <Label className="flex shrink-0 items-center gap-2 border-y py-2 text-sm font-normal">
            <Checkbox checked={addable.length > 0 && addable.every((u) => a.picked.has(u.id))} disabled={addable.length === 0} onCheckedChange={a.toggleAll} aria-label="Chọn tất cả" />
            Chọn tất cả ({addable.length})
          </Label>
          <ul className="min-h-0 flex-1 divide-y overflow-y-auto" data-testid="found-students">
            {a.rows.length === 0 && <li className="py-2 text-sm text-muted-foreground">Không có học sinh nào khớp.</li>}
            {a.rows.map((u) => {
              const note = a.note(u);
              return (
                <li key={u.id}>
                  <Label className="flex items-center gap-2 py-2 text-sm font-normal">
                    <Checkbox checked={a.picked.has(u.id)} disabled={!!note} onCheckedChange={() => a.toggle(u)} aria-label={`Chọn ${u.full_name}`} />
                    {u.full_name} <span className="font-mono text-xs text-muted-foreground">{u.username}</span>
                    {note && <span className="ml-auto text-xs text-muted-foreground">{note}</span>}
                  </Label>
                </li>
              );
            })}
          </ul>
          {/* a cut-off list that says nothing about being cut off is how a teacher concludes a student does not exist */}
          {a.more > 0 && <p className="shrink-0 text-xs text-muted-foreground">Còn {a.more} kết quả nữa — lọc thêm để thấy.</p>}
        </>
      ) : (
        <>
          <p className="shrink-0 text-sm text-muted-foreground">{a.short ? "Nhập ít nhất 2 ký tự để tìm theo tên." : "Tích cả lớp cũ, hoặc mở lớp ra để tích từng em."}</p>
          <DialogTable columns={COLUMNS} selectable foldable testId="source-classes">
            {a.sources.map((c) => (
              <ClassRows key={c.id} c={c} a={a} />
            ))}
            {a.sources.length === 0 && <DialogTableRow span cells={["Chưa có lớp nào khác."]} />}
          </DialogTable>
        </>
      )}
      <div className="flex shrink-0 justify-end gap-2 border-t pt-3">
        <Button type="button" variant="outline" onClick={onCancel}>
          Hủy
        </Button>
        <Button type="button" disabled={a.picked.size === 0} onClick={() => onConfirm([...a.picked.values()])}>
          Chọn {a.picked.size} học sinh
        </Button>
      </div>
    </div>
  );
}

/** One old class, and its students beneath it while the row is open. Ticking the class row takes whoever it can
 *  still offer, which is the usual job; the child rows are there for the exceptions. */
function ClassRows({ c, a }: { c: SchoolClass; a: ClassAdder }) {
  const r = useClassRoster(a, c.id);
  const open = a.isOpen(c.id);
  const whole = r.addable.length > 0 && r.addable.every((u) => a.picked.has(u.id));
  return (
    <DialogTableRow
      // a class with nothing left to offer: a tick that changed nothing would be a lie (A-07)
      select={{
        label: `Chọn lớp ${c.name}`,
        checked: whole,
        disabled: r.loaded ? r.addable.length === 0 : c.member_count === 0,
        onChange: () => (whole ? a.unpick(r.addable.map((u) => u.id)) : r.loaded ? a.pick(r.addable) : a.want(c.id)),
      }}
      fold={{ open, label: `Xem học sinh lớp ${c.name}`, onToggle: () => a.toggleOpen(c.id) }}
      cells={[
        <>
          <span className="font-medium">Lớp {c.name}</span>
          <div className="text-xs text-muted-foreground sm:hidden">{c.school_year}</div>
        </>,
        c.school_year,
        c.member_count,
      ]}
    >
      {r.loading && <DialogTableRow span cells={["Đang tải…"]} />}
      {r.loaded && r.students.length === 0 && <DialogTableRow span cells={["Lớp này chưa có học sinh."]} />}
      {r.students.map((u) => {
        const note = a.note(u);
        return (
          <DialogTableRow
            key={u.id}
            muted
            // already a member, or already on the list: nothing to take, and the row says so instead of vanishing (A-07)
            select={{ label: `Chọn ${u.full_name}`, checked: a.picked.has(u.id), disabled: !!note, onChange: () => a.toggle(u) }}
            cells={[
              <>
                {u.full_name} <span className="font-mono text-xs text-muted-foreground">{u.username}</span>
              </>,
              null,
              note,
            ]}
          />
        );
      })}
    </DialogTableRow>
  );
}
