"use client";

import { ArrowRight, GraduationCap } from "lucide-react";
import { ToneBadge } from "@/components/app/ToneBadge";
import { Button } from "@/components/ui/button";
import { Card, CardAction, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { NativeSelect, NativeSelectOption } from "@/components/ui/native-select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

export type Action = "promote" | "retain" | "transfer" | "graduate";
export const ACTION_LABEL: Record<Action, string> = { promote: "Lên lớp", retain: "Ở lại lớp", transfer: "Chuyển đi", graduate: "Tốt nghiệp" };

export interface PlanStudent {
  user_id: string;
  full_name: string;
  username: string;
  current_status: string;
  action: Action;
}
export interface PlanClass {
  source_class_id: string;
  source_name: string;
  grade: number | null;
  graduating: boolean;
  target_name: string | null;
  target_grade: number | null;
  target_exists: boolean;
  students: PlanStudent[];
}
export interface Plan {
  source_year: { id: string; code: string; status: string };
  target_code: string;
  target_year_id: string | null;
  top_grade: number;
  classes: PlanClass[];
}

export function tally(classes: PlanClass[]): Record<Action, number> {
  const out: Record<Action, number> = { promote: 0, retain: 0, transfer: 0, graduate: 0 };
  for (const c of classes) for (const s of c.students) out[s.action] += 1;
  return out;
}

/** One card per class: target name (editable), and an action per student (school-years AC-09/AC-10). */
export function RolloverPlan({ plan, onChange }: { plan: Plan; onChange: (classes: PlanClass[]) => void }) {
  const update = (i: number, fn: (c: PlanClass) => PlanClass) => onChange(plan.classes.map((c, j) => (j === i ? fn(c) : c)));
  return (
    <div className="grid gap-4">
      {plan.classes.length === 0 && <p className="text-sm text-muted-foreground">Năm học này chưa có lớp.</p>}
      {plan.classes.map((c, i) => {
        const options: Action[] = c.graduating ? ["graduate", "retain", "transfer"] : ["promote", "retain", "transfer", "graduate"];
        return (
          <Card key={c.source_class_id} data-testid={`plan-${c.source_name}`}>
            <CardHeader>
              <CardTitle className="flex flex-wrap items-center gap-2">
                Lớp {c.source_name}
                <ArrowRight className="size-4 text-muted-foreground" />
                {c.graduating ? (
                  <ToneBadge tone="blue">
                    <GraduationCap className="size-3" /> Tốt nghiệp
                  </ToneBadge>
                ) : (
                  <Input
                    aria-label={`Lớp mới của ${c.source_name}`}
                    className="h-8 w-32"
                    value={c.target_name ?? ""}
                    onChange={(e) => update(i, (x) => ({ ...x, target_name: e.target.value }))}
                  />
                )}
                {c.target_exists && <ToneBadge>đã có trong năm mới</ToneBadge>}
              </CardTitle>
              <CardAction>
                <Button variant="outline" size="sm" onClick={() => update(i, (x) => ({ ...x, students: x.students.map((s) => ({ ...s, action: options[0] })) }))}>
                  Tất cả: {ACTION_LABEL[options[0]]}
                </Button>
              </CardAction>
            </CardHeader>
            <CardContent>
              {c.students.length === 0 ? (
                <p className="text-sm text-muted-foreground">Lớp không có học sinh.</p>
              ) : (
                <div className="rounded-lg border">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Học sinh</TableHead>
                        <TableHead>Tên đăng nhập</TableHead>
                        <TableHead className="w-44">Năm mới</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {c.students.map((s, k) => (
                        <TableRow key={s.user_id} className={s.action !== options[0] ? "bg-amber-500/5" : undefined}>
                          <TableCell>{s.full_name}</TableCell>
                          <TableCell className="font-mono text-muted-foreground">{s.username}</TableCell>
                          <TableCell>
                            <NativeSelect
                              aria-label={`Năm mới của ${s.full_name}`}
                              value={s.action}
                              onChange={(e) =>
                                update(i, (x) => ({ ...x, students: x.students.map((y, j) => (j === k ? { ...y, action: e.target.value as Action } : y)) }))
                              }
                            >
                              {options.map((a) => (
                                <NativeSelectOption key={a} value={a}>
                                  {ACTION_LABEL[a]}
                                  {a === "retain" ? ` (${c.source_name})` : a === "promote" && c.target_name ? ` (${c.target_name})` : ""}
                                </NativeSelectOption>
                              ))}
                            </NativeSelect>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              )}
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
