"use client";

import { Search } from "lucide-react";
import { useState } from "react";
import { OptionSelect } from "@/components/common/OptionSelect/OptionSelect";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useStudentFinder, useStudentSearch } from "@/hooks/page-hooks/classes/use-member-manager";

/** Tìm từng em, và một nút mở bảng tìm rộng hơn.
 *
 *  Two speeds behind one input: type a name and add the one you meant, or open the wider table and tick several.
 *  The wider view replaces the content of this dialog instead of opening a second dialog on top of it — a dialog
 *  over a dialog puts two Escape keys and two focus traps on one screen for no gain.
 */
export function StudentPicker({ classId, onAdd, onAddMany }: { classId: string; onAdd: (userId: string) => Promise<boolean>; onAddMany: (userIds: string[]) => Promise<boolean> }) {
  const [wide, setWide] = useState(false);
  if (wide) return <WideSearch classId={classId} onAddMany={onAddMany} onBack={() => setWide(false)} />;
  return <QuickSearch classId={classId} onAdd={onAdd} onWide={() => setWide(true)} />;
}

function QuickSearch({ classId, onAdd, onWide }: { classId: string; onAdd: (userId: string) => Promise<boolean>; onWide: () => void }) {
  const [q, setQ] = useState("");
  const [added, setAdded] = useState<Set<string>>(new Set());
  const students = useStudentSearch(q);
  return (
    <div className="grid gap-3">
      <div className="flex gap-2">
        <Input autoFocus aria-label="Tìm học sinh" placeholder="Tìm tên hoặc tên đăng nhập (≥ 2 ký tự)" value={q} onChange={(e) => setQ(e.target.value)} className="flex-1" />
        <Button type="button" variant="outline" size="icon" aria-label="Tìm nâng cao" title="Tìm nâng cao: lọc theo lớp, chọn nhiều em" onClick={onWide}>
          <Search />
        </Button>
      </div>
      <ul className="max-h-80 divide-y overflow-y-auto" data-testid="quick-results">
        {students
          ?.filter((u) => !u.class_ids.includes(classId) && !added.has(u.id))
          .map((u) => (
            <li key={u.id} className="flex items-center justify-between py-2 text-sm">
              <span>
                {u.full_name} <span className="font-mono text-muted-foreground">{u.username}</span>
              </span>
              <Button size="sm" variant="outline" onClick={async () => (await onAdd(u.id)) && setAdded((s) => new Set(s).add(u.id))}>
                Thêm
              </Button>
            </li>
          ))}
      </ul>
    </div>
  );
}

function WideSearch({ classId, onAddMany, onBack }: { classId: string; onAddMany: (userIds: string[]) => Promise<boolean>; onBack: () => void }) {
  const f = useStudentFinder(classId);
  const addable = f.rows.filter((u) => !f.already.has(u.id));
  return (
    <div className="grid gap-3">
      <div className="flex items-center justify-between text-sm">
        <span className="font-medium">Tìm nâng cao</span>
        <Button variant="ghost" size="sm" onClick={onBack}>
          Quay lại
        </Button>
      </div>
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
      <Button disabled={f.picked.size === 0} onClick={() => void onAddMany([...f.picked])}>
        Thêm {f.picked.size} học sinh
      </Button>
    </div>
  );
}
