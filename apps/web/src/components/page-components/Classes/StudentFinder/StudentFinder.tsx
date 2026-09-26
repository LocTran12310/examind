"use client";

import { OptionSelect } from "@/components/common/OptionSelect/OptionSelect";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useStudentFinder } from "@/hooks/page-hooks/classes/use-member-manager";

/** Tìm nâng cao: the students of the whole organisation, narrowed by name and by class, several ticked at once.
 *
 *  It sits in its own dialog over the table of old classes, because it answers the other question — "em này đang ở
 *  đâu?" instead of "lớp nào?" — and closing it should put the classes back with their ticks, not end the job. */
export function StudentFinder({ classId, onAdd }: { classId: string; onAdd: (userIds: string[]) => Promise<boolean> }) {
  const f = useStudentFinder(classId);
  const addable = f.rows.filter((u) => !f.already.has(u.id));
  return (
    <div className="grid gap-3">
      <div className="grid gap-2 sm:grid-cols-2">
        <Input autoFocus aria-label="Tìm tên" placeholder="Tên hoặc tên đăng nhập" value={f.q} onChange={(e) => f.setQ(e.target.value)} />
        <OptionSelect
          aria-label="Lọc theo lớp"
          value={f.classFilter}
          onValueChange={f.setClassFilter}
          emptyLabel="Mọi lớp"
          options={f.classes.map((c) => ({ value: c.id, label: `${c.name} · ${c.school_year}` }))}
        />
      </div>
      <Label className="flex items-center gap-2 border-y py-2 text-sm font-normal">
        <Checkbox checked={addable.length > 0 && addable.every((u) => f.picked.has(u.id))} disabled={addable.length === 0} onCheckedChange={f.toggleAll} aria-label="Chọn tất cả" />
        Chọn tất cả ({addable.length})
      </Label>
      <ul className="max-h-72 divide-y overflow-y-auto" data-testid="wide-results">
        {f.rows.length === 0 && <li className="py-2 text-sm text-muted-foreground">Không có học sinh nào khớp.</li>}
        {f.rows.map((u) => {
          const here = f.already.has(u.id);
          return (
            <li key={u.id}>
              <Label className="flex items-center gap-2 py-2 text-sm font-normal">
                <Checkbox checked={f.picked.has(u.id)} disabled={here} onCheckedChange={() => f.toggle(u.id)} aria-label={`Chọn ${u.full_name}`} />
                {u.full_name} <span className="font-mono text-xs text-muted-foreground">{u.username}</span>
                {here && <span className="ml-auto text-xs text-muted-foreground">đã ở trong lớp</span>}
              </Label>
            </li>
          );
        })}
      </ul>
      {/* a cut-off list that says nothing about being cut off is how a teacher concludes a student does not exist */}
      {f.more > 0 && <p className="text-xs text-muted-foreground">Còn {f.more} kết quả nữa — lọc thêm để thấy.</p>}
      <Button disabled={f.picked.size === 0} onClick={() => void onAdd([...f.picked])}>
        Thêm {f.picked.size} học sinh
      </Button>
    </div>
  );
}
