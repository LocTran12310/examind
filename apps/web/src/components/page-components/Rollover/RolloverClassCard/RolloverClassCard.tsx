"use client";

import { ArrowRight, ChevronDown, GraduationCap } from "lucide-react";
import { useState } from "react";
import { OptionSelect } from "@/components/common/OptionSelect/OptionSelect";
import { ToneBadge } from "@/components/common/ToneBadge/ToneBadge";
import { Button } from "@/components/ui/button";
import { Card, CardAction, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { ROLLOVER_ACTION_LABEL as ACTION_LABEL } from "@/constants/school-year.constant";
import type { RolloverAction as Action, RolloverClass as PlanClass, RolloverStudent as Student } from "@/interfaces/school-year.interface";
import { actionSummary } from "@/lib/page-libs/school-years/rollover";
import { cn } from "@/lib/utils";

export interface RolloverClassCardProps {
  c: PlanClass;
  onChange: (c: PlanClass) => void;
}

/** One class of the plan, folded by default: 7 khối × 5 lớp is 35 lines to read instead of ~900 rows to scroll.
 *  Folded it still says everything the plan is made of — new class name (still editable), head count, the actions
 *  already set, the bulk control — so folding hides the exceptions, not the decision. Deliberately no "mở tất cả":
 *  opening 35 classes at once is exactly the scroll this replaces, and a single class is one click away. */
export function RolloverClassCard({ c, onChange }: RolloverClassCardProps) {
  const [open, setOpen] = useState(false);
  const options: Action[] = c.graduating ? ["graduate", "retain", "transfer"] : ["promote", "retain", "transfer", "graduate"];
  const students = (fn: (s: Student[]) => Student[]) => onChange({ ...c, students: fn(c.students) });
  return (
    <Collapsible open={open} onOpenChange={setOpen}>
      <Card data-testid={`plan-${c.source_name}`}>
        <CardHeader>
          <CardTitle className="flex flex-wrap items-center gap-2">
            <CollapsibleTrigger className="flex items-center gap-2">
              <ChevronDown className={cn("size-4 text-muted-foreground transition-transform", open && "rotate-180")} />
              Lớp {c.source_name}
              <span className="text-sm font-normal text-muted-foreground tabular-nums">{c.students.length} học sinh</span>
            </CollapsibleTrigger>
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
                onChange={(e) => onChange({ ...c, target_name: e.target.value })}
              />
            )}
            {c.target_exists && <ToneBadge>đã có trong năm mới</ToneBadge>}
            {c.students.length > 0 && (
              <span className="text-sm font-normal text-muted-foreground" data-testid={`summary-${c.source_name}`}>
                {actionSummary(c.students)}
              </span>
            )}
          </CardTitle>
          <CardAction>
            <Button variant="outline" size="sm" onClick={() => students((s) => s.map((y) => ({ ...y, action: options[0] })))}>
              Tất cả: {ACTION_LABEL[options[0]]}
            </Button>
          </CardAction>
        </CardHeader>
        <CollapsibleContent>
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
                            onValueChange={(v) => students((x) => x.map((y, j) => (j === k ? { ...y, action: v as Action } : y)))}
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
        </CollapsibleContent>
      </Card>
    </Collapsible>
  );
}
