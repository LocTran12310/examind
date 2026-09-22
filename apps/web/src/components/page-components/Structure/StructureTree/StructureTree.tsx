"use client";

import { ChevronRight, GraduationCap, Layers, School, Users } from "lucide-react";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import type { Structure } from "@/interfaces/structure.interface";
import type { NodeRef } from "@/lib/page-libs/structure/node";
import { cn } from "@/lib/utils";


function Count({ classes, students }: { classes?: number; students: number }) {
  return (
    <span className="ml-auto flex shrink-0 gap-2 text-xs text-muted-foreground tabular-nums">
      {classes !== undefined && <span title="Số lớp">{classes} lớp</span>}
      <span title="Số học sinh" className="inline-flex items-center gap-0.5">
        <Users className="size-3" />
        {students}
      </span>
    </span>
  );
}

/** Cấp học › Khối › Lớp with counts; selecting a node drives the table beside it. */
export function StructureTree({ data, selected, onSelect }: { data: Structure; selected: NodeRef; onSelect: (n: NodeRef) => void }) {
  const [closed, setClosed] = useState<Set<string>>(new Set());
  const toggle = (id: string) =>
    setClosed((s) => {
      const n = new Set(s);
      if (n.has(id)) n.delete(id);
      else n.add(id);
      return n;
    });
  const row = (active: boolean) =>
    cn("h-auto w-full min-w-0 shrink justify-start gap-1.5 rounded-md px-2 py-1.5 text-left font-normal", active && "bg-primary/10 font-medium text-primary hover:bg-primary/10 hover:text-primary");
  const is = (kind: string, id: string) => selected?.kind === kind && selected.id === id;
  return (
    <nav aria-label="Cơ cấu trường" className="grid gap-0.5">
      <Button type="button" variant="ghost" className={row(!selected)} onClick={() => onSelect(null)}>
        <School className="size-4" /> Toàn trường
        <Count classes={data.levels.reduce((n, l) => n + l.class_count, 0) + data.unassigned.length} students={data.levels.reduce((n, l) => n + l.student_count, 0)} />
      </Button>
      {data.levels.map((lv) => (
        <div key={lv.id} role="group" aria-label={lv.name}>
          <div className="flex items-center">
            <Button variant="ghost" size="icon-xs" aria-label={closed.has(lv.id) ? "Mở rộng" : "Thu gọn"} onClick={() => toggle(lv.id)}>
              <ChevronRight className={cn("transition-transform", !closed.has(lv.id) && "rotate-90")} />
            </Button>
            <Button type="button" variant="ghost" className={row(is("level", lv.id))} onClick={() => onSelect({ kind: "level", id: lv.id })} aria-current={is("level", lv.id) || undefined}>
              <Layers className="size-4 shrink-0" />
              <span className="truncate">{lv.name}</span>
              <span className="text-xs text-muted-foreground">
                ({lv.grade_from}–{lv.grade_to})
              </span>
              <Count classes={lv.class_count} students={lv.student_count} />
            </Button>
          </div>
          {!closed.has(lv.id) &&
            lv.grades.map((g) => (
              <div key={g.id} className="ml-6">
                <div className="flex items-center">
                  <Button variant="ghost" size="icon-xs" aria-label={closed.has(g.id) ? "Mở rộng" : "Thu gọn"} onClick={() => toggle(g.id)} disabled={!g.classes.length}>
                    <ChevronRight className={cn("transition-transform", g.classes.length && !closed.has(g.id) && "rotate-90")} />
                  </Button>
                  <Button type="button" variant="ghost" className={row(is("grade", g.id))} onClick={() => onSelect({ kind: "grade", id: g.id })} aria-current={is("grade", g.id) || undefined}>
                    <GraduationCap className="size-4 shrink-0" />
                    <span className="truncate">{g.name}</span>
                    <Count classes={g.class_count} students={g.student_count} />
                  </Button>
                </div>
                {!closed.has(g.id) &&
                  g.classes.map((c) => (
                    <Button key={c.id} type="button" variant="ghost" className={cn(row(is("class", c.id)), "ml-7 w-[calc(100%-1.75rem)]")} onClick={() => onSelect({ kind: "class", id: c.id })} aria-current={is("class", c.id) || undefined}>
                      <span className="truncate">{c.name}</span>
                      <span className="text-xs text-muted-foreground">{c.school_year}</span>
                      <Count students={c.member_count} />
                    </Button>
                  ))}
              </div>
            ))}
        </div>
      ))}
      {data.unassigned.length > 0 && (
        <div className="mt-2 border-t pt-2">
          <div className="px-2 pb-1 text-xs text-muted-foreground">Lớp chưa xếp khối</div>
          {data.unassigned.map((c) => (
            <Button key={c.id} type="button" variant="ghost" className={row(is("class", c.id))} onClick={() => onSelect({ kind: "class", id: c.id })}>
              <span className="truncate">{c.name}</span>
              <span className="text-xs text-muted-foreground">{c.school_year}</span>
              <Count students={c.member_count} />
            </Button>
          ))}
        </div>
      )}
    </nav>
  );
}
