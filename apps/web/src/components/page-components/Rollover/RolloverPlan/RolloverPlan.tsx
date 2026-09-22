"use client";

import { ArrowRight, GraduationCap } from "lucide-react";
import { ToneBadge } from "@/components/common/ToneBadge/ToneBadge";
import { Button } from "@/components/ui/button";
import { Card, CardAction, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { OptionSelect } from "@/components/common/OptionSelect/OptionSelect";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { ROLLOVER_ACTION_LABEL as ACTION_LABEL } from "@/constants/school-year.constant";
import type { RolloverAction as Action, RolloverClass as PlanClass, RolloverPlan as Plan } from "@/interfaces/school-year.interface";

export interface RolloverPlanProps {
  plan: Plan;
  onChange: (classes: PlanClass[]) => void;
}

/** One card per class: target name (editable), and an action per student (school-years AC-09/AC-10). */
export function RolloverPlan({ plan, onChange }: RolloverPlanProps) {
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
                            <OptionSelect
                              aria-label={`Năm mới của ${s.full_name}`}
                              value={s.action}
                              onValueChange={(v) =>
                                update(i, (x) => ({ ...x, students: x.students.map((y, j) => (j === k ? { ...y, action: v as Action } : y)) }))
                              }
                              options={options.map((a) => ({
                                value: a,
                                label: `${ACTION_LABEL[a]}${a === "retain" ? ` (${c.source_name})` : a === "promote" && c.target_name ? ` (${c.target_name})` : ""}`,
                              }))}
                            />
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
