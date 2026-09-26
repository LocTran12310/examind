"use client";

import { ChevronDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { type ClassAdder, useClassAdder, useClassRoster } from "@/hooks/page-hooks/classes/use-member-manager";
import type { SchoolClass } from "@/interfaces/class.interface";
import type { User } from "@/interfaces/user.interface";
import { cn } from "@/lib/utils";

/** Chọn học sinh: picking many at once. One table of every other class of the organisation, each row folded over
 *  its own roster, ticks on class rows and on student rows; the search box answers the other question — "em này
 *  đang ở đâu?" instead of "lớp nào?" — over the same selection.
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
    <div className="grid gap-3">
      <Input autoFocus aria-label="Tìm học sinh" placeholder="Tên hoặc tên đăng nhập" value={a.q} onChange={(e) => a.setQ(e.target.value)} />
      {a.searching ? (
        <>
          <Label className="flex items-center gap-2 border-y py-2 text-sm font-normal">
            <Checkbox checked={addable.length > 0 && addable.every((u) => a.picked.has(u.id))} disabled={addable.length === 0} onCheckedChange={a.toggleAll} aria-label="Chọn tất cả" />
            Chọn tất cả ({addable.length})
          </Label>
          <ul className="max-h-72 divide-y overflow-y-auto" data-testid="found-students">
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
          {a.more > 0 && <p className="text-xs text-muted-foreground">Còn {a.more} kết quả nữa — lọc thêm để thấy.</p>}
        </>
      ) : (
        <>
          <p className="text-sm text-muted-foreground">{a.short ? "Nhập ít nhất 2 ký tự để tìm theo tên." : "Tích cả lớp cũ, hoặc mở lớp ra để tích từng em."}</p>
          <div className="max-h-96 overflow-y-auto rounded-lg border">
            <Table data-testid="source-classes">
              <TableHeader>
                <TableRow>
                  <TableHead className="w-8" />
                  <TableHead className="w-8" />
                  <TableHead>Lớp</TableHead>
                  <TableHead>Năm học</TableHead>
                  <TableHead className="text-right">Học sinh</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {a.sources.map((c) => (
                  <ClassRows key={c.id} c={c} a={a} />
                ))}
                {a.sources.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={5} className="text-muted-foreground">
                      Chưa có lớp nào khác.
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </div>
        </>
      )}
      <div className="flex justify-end gap-2">
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
    <>
      <TableRow>
        <TableCell>
          {/* a class with nothing left to offer: a tick that changed nothing would be a lie (A-07) */}
          <Checkbox
            aria-label={`Chọn lớp ${c.name}`}
            checked={whole}
            disabled={r.loaded ? r.addable.length === 0 : c.member_count === 0}
            onCheckedChange={() => (whole ? a.unpick(r.addable.map((u) => u.id)) : r.loaded ? a.pick(r.addable) : a.want(c.id))}
          />
        </TableCell>
        <TableCell>
          <button
            type="button"
            aria-label={`Xem học sinh lớp ${c.name}`}
            aria-expanded={open}
            onClick={() => a.toggleOpen(c.id)}
            className="flex items-center text-muted-foreground hover:text-foreground"
          >
            <ChevronDown className={cn("size-4 transition-transform", open && "rotate-180")} />
          </button>
        </TableCell>
        <TableCell className="font-medium">Lớp {c.name}</TableCell>
        <TableCell className="text-muted-foreground">{c.school_year}</TableCell>
        <TableCell className="text-right tabular-nums text-muted-foreground">{c.member_count}</TableCell>
      </TableRow>
      {open && r.loading && (
        <TableRow>
          <TableCell colSpan={5} className="text-muted-foreground">
            Đang tải…
          </TableCell>
        </TableRow>
      )}
      {open && r.loaded && r.students.length === 0 && (
        <TableRow>
          <TableCell colSpan={5} className="text-muted-foreground">
            Lớp này chưa có học sinh.
          </TableCell>
        </TableRow>
      )}
      {open &&
        r.students.map((u) => {
          const note = a.note(u);
          return (
            <TableRow key={u.id} className="bg-muted/40">
              <TableCell>
                {/* already a member, or already on the list: nothing to take, and the row says so instead of vanishing (A-07) */}
                <Checkbox aria-label={`Chọn ${u.full_name}`} checked={a.picked.has(u.id)} disabled={!!note} onCheckedChange={() => a.toggle(u)} />
              </TableCell>
              <TableCell />
              <TableCell colSpan={2}>
                {u.full_name} <span className="font-mono text-xs text-muted-foreground">{u.username}</span>
              </TableCell>
              <TableCell className="text-right text-xs text-muted-foreground">{note}</TableCell>
            </TableRow>
          );
        })}
    </>
  );
}
