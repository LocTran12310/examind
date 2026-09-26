"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { useFromClass } from "@/hooks/page-hooks/classes/use-member-manager";

/** Fill this class from one old class in a single click.
 *
 *  This is not "Chuyển năm học" and does not replace it (ADR-04): that one moves a whole year by name rule
 *  (10A1 → 11A1) and records how each student left. This one is the small, pointed version — this new class,
 *  from that old class, chosen by hand. The link below is there because the bigger door is easy to miss from
 *  in here, which is exactly how this screen came to be the only one anybody found. */
export function FromClass({ classId, onAdd }: { classId: string; onAdd: (userIds: string[]) => Promise<boolean> }) {
  const f = useFromClass(classId);
  return (
    <div className="grid gap-3">
      {!f.sourceId ? (
        <>
          <p className="text-sm text-muted-foreground">Chọn lớp cũ để lấy học sinh sang lớp này.</p>
          <ul className="max-h-80 divide-y overflow-y-auto rounded-lg border" data-testid="source-classes">
            {f.sources.map((c) => (
              <li key={c.id}>
                <button type="button" className="flex w-full items-center justify-between px-3 py-2 text-left text-sm hover:bg-muted/60" onClick={() => f.choose(c.id)}>
                  <span>
                    Lớp {c.name} <span className="text-muted-foreground">· {c.school_year}</span>
                  </span>
                  <span className="text-xs text-muted-foreground">{c.member_count} học sinh</span>
                </button>
              </li>
            ))}
            {f.sources.length === 0 && <li className="px-3 py-2 text-sm text-muted-foreground">Chưa có lớp nào khác.</li>}
          </ul>
        </>
      ) : (
        <>
          <div className="flex items-center justify-between text-sm">
            <span className="font-medium">
              Lớp {f.source?.name} <span className="font-normal text-muted-foreground">· {f.source?.school_year}</span>
            </span>
            <Button variant="ghost" size="sm" onClick={() => f.choose(null)}>
              Chọn lớp khác
            </Button>
          </div>
          <ul className="max-h-72 divide-y overflow-y-auto rounded-lg border" data-testid="source-students">
            {f.loading && <li className="px-3 py-2 text-sm text-muted-foreground">Đang tải…</li>}
            {!f.loading && f.students.length === 0 && <li className="px-3 py-2 text-sm text-muted-foreground">Lớp này chưa có học sinh.</li>}
            {f.students.map((u) => {
              const here = f.already.has(u.id);
              return (
                <li key={u.id}>
                  <Label className="flex items-center gap-2 px-3 py-2 text-sm font-normal">
                    {/* already a member: nothing to add, and a tick that changed nothing would be a lie (A-07) */}
                    <Checkbox checked={f.picked.has(u.id)} disabled={here} onCheckedChange={() => f.toggle(u.id)} aria-label={`Chọn ${u.full_name}`} />
                    {u.full_name} <span className="font-mono text-xs text-muted-foreground">{u.username}</span>
                    {here && <span className="ml-auto text-xs text-muted-foreground">đã ở trong lớp</span>}
                  </Label>
                </li>
              );
            })}
          </ul>
          <Button disabled={f.picked.size === 0} onClick={() => void onAdd([...f.picked])}>
            Thêm {f.picked.size} học sinh
          </Button>
        </>
      )}
      <p className="text-xs text-muted-foreground">
        Chuyển cả một năm học — mọi lớp, 10A1 lên 11A1, kèm ở lại và tốt nghiệp — thì dùng{" "}
        <Link href="/org/school-years" className="underline hover:text-primary">
          Năm học › Chuyển năm học
        </Link>
        .
      </p>
    </div>
  );
}
