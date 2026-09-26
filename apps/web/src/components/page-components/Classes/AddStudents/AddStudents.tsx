"use client";

import { ChevronDown, Search } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { FormDialog } from "@/components/common/FormDialog/FormDialog";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { type ClassAdder, useClassAdder, useClassRoster } from "@/hooks/page-hooks/classes/use-member-manager";
import type { SchoolClass } from "@/interfaces/class.interface";
import { cn } from "@/lib/utils";
import { StudentFinder } from "../StudentFinder/StudentFinder";

/** Fill this class from the classes that came before it: one table of every other class, each row folded over its
 *  own roster, and one request for everything ticked — across several classes if several are open. Ticking a class
 *  row takes the whole class, which is the usual job; the child rows are there for the exceptions.
 *
 *  This is not "Chuyển năm học" and does not replace it (ADR-04): that one moves a whole year by name rule
 *  (10A1 → 11A1) and records how each student left. This one is the small, pointed version — this new class, from
 *  those old classes, chosen by hand. The link below is there because the bigger door is easy to miss from in here,
 *  which is exactly how this screen came to be the only one anybody found. */
export function AddStudents({ classId, onAdd }: { classId: string; onAdd: (userIds: string[]) => Promise<boolean> }) {
  const a = useClassAdder(classId);
  const [finding, setFinding] = useState(false);
  return (
    <div className="grid gap-3">
      <div className="flex items-center justify-between gap-2">
        <p className="text-sm text-muted-foreground">Tích cả lớp cũ, hoặc mở lớp ra để tích từng em.</p>
        <Button type="button" variant="outline" size="sm" onClick={() => setFinding(true)}>
          <Search /> Tìm nâng cao
        </Button>
      </div>
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
              <ClassRows key={c.id} c={c} classId={classId} a={a} />
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
      <Button disabled={a.picked.size === 0} onClick={() => void onAdd([...a.picked])}>
        Thêm {a.picked.size} học sinh
      </Button>
      <p className="text-xs text-muted-foreground">
        Chuyển cả một năm học — mọi lớp, 10A1 lên 11A1, kèm ở lại và tốt nghiệp — thì dùng{" "}
        <Link href="/org/school-years" className="underline hover:text-primary">
          Năm học › Chuyển năm học
        </Link>
        .
      </p>
      <FormDialog open={finding} onOpenChange={setFinding} title="Tìm nâng cao" description="Tìm theo tên hoặc lớp, tích nhiều em rồi thêm một lần." wide>
        <StudentFinder classId={classId} onAdd={onAdd} />
      </FormDialog>
    </div>
  );
}

/** One old class, and its students beneath it while the row is open. */
function ClassRows({ c, classId, a }: { c: SchoolClass; classId: string; a: ClassAdder }) {
  const r = useClassRoster(a, c.id, classId);
  const open = a.isOpen(c.id);
  const whole = r.addable.length > 0 && r.addable.every((id) => a.picked.has(id));
  return (
    <>
      <TableRow>
        <TableCell>
          {/* a class with nothing left to offer: a tick that changed nothing would be a lie (A-07) */}
          <Checkbox
            aria-label={`Chọn lớp ${c.name}`}
            checked={whole}
            disabled={r.loaded ? r.addable.length === 0 : c.member_count === 0}
            onCheckedChange={() => (whole ? a.unpick(r.addable) : r.loaded ? a.pick(r.addable) : a.want(c.id))}
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
          const here = u.class_ids.includes(classId);
          return (
            <TableRow key={u.id} className="bg-muted/40">
              <TableCell>
                {/* already a member: nothing to add, and the row says so instead of vanishing (A-07) */}
                <Checkbox aria-label={`Chọn ${u.full_name}`} checked={a.picked.has(u.id)} disabled={here} onCheckedChange={() => a.toggle(u.id)} />
              </TableCell>
              <TableCell />
              <TableCell colSpan={2}>
                {u.full_name} <span className="font-mono text-xs text-muted-foreground">{u.username}</span>
              </TableCell>
              <TableCell className="text-right text-xs text-muted-foreground">{here && "đã ở trong lớp"}</TableCell>
            </TableRow>
          );
        })}
    </>
  );
}
