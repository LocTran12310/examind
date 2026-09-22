"use client";

import { ArrowLeft, History } from "lucide-react";
import Link from "next/link";
import { FormDialog } from "@/components/app/FormDialog";
import { HistoryPanel } from "@/components/app/HistoryPanel";
import { PageHeader } from "@/components/app/PageHeader";
import { ToneBadge } from "@/components/app/ToneBadge";
import { ScoreBar } from "@/components/common/ScoreBar/ScoreBar";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { YEAR_STATUS_LABEL } from "@/constants/school-year.constant";
import { useStudentRecordPage } from "@/hooks/page-hooks/student-record/use-student-record-page";

const pct = (r: number | null) => (r === null ? "—" : `${Math.round(r * 100)}%`);

/** Hồ sơ học sinh: one card per school year, newest first (school-years US-04). */
export function StudentRecordPage({ id }: { id: string }) {
  const { data, error, isAdmin, history, setHistory } = useStudentRecordPage(id);
  if (error) return <p className="text-sm text-destructive">{error}</p>;
  if (!data) return <Skeleton className="h-60" />;
  return (
    <>
      <Button variant="ghost" size="sm" asChild className="mb-2">
        <Link href="/org/users">
          <ArrowLeft /> Người dùng
        </Link>
      </Button>
      <PageHeader
        title={`Hồ sơ · ${data.student.full_name}`}
        description={data.student.username}
        actions={
          isAdmin && (
            <Button variant="outline" onClick={() => setHistory(true)}>
              <History /> Lịch sử
            </Button>
          )
        }
      />
      {data.years.length === 0 && <p className="text-sm text-muted-foreground">Học sinh chưa có lớp hoặc bài làm nào.</p>}
      <ol className="grid gap-4" aria-label="Các năm học">
        {data.years.map((y) => (
          <li key={y.year?.id ?? "none"}>
            <Card>
              <CardHeader>
                <CardTitle className="flex flex-wrap items-center gap-2">
                  {y.year ? `Năm học ${y.year.code}` : "Chưa xếp năm học"}
                  {y.year && <ToneBadge tone={y.year.status === "active" ? "green" : "gray"}>{YEAR_STATUS_LABEL[y.year.status]}</ToneBadge>}
                </CardTitle>
                <CardDescription className="flex flex-wrap gap-2">
                  {y.classes.length
                    ? y.classes.map((c) => (
                        <span key={c.id} className="inline-flex items-center gap-1">
                          Lớp {c.name}
                          {c.status !== "active" && <ToneBadge tone={c.status === "retained" || c.status === "transferred" ? "amber" : "blue"}>{c.status_label}</ToneBadge>}
                        </span>
                      ))
                    : "Không có lớp"}
                </CardDescription>
              </CardHeader>
              <CardContent className="grid gap-4 md:grid-cols-[14rem_1fr]">
                <div className="grid content-start gap-1 text-sm">
                  <div className="text-2xl font-semibold text-primary">{pct(y.ratio)}</div>
                  <div className="text-muted-foreground">
                    {y.answered} câu · {y.attempts} bài
                  </div>
                  {(["hk1", "hk2"] as const).map((t) => (
                    <div key={t} className="flex justify-between text-muted-foreground">
                      <span>{t === "hk1" ? "Học kỳ 1" : "Học kỳ 2"}</span>
                      <span>{pct(y.terms[t]?.ratio ?? null)}</span>
                    </div>
                  ))}
                </div>
                <div className="grid content-start gap-2">
                  {y.topics.length === 0 && <p className="text-sm text-muted-foreground">Chưa có bài làm trong năm này.</p>}
                  {y.topics.map((t) => (
                    <div key={t.id} className="grid grid-cols-[10rem_1fr_3rem] items-center gap-2 text-sm">
                      <span className="truncate">{t.name}</span>
                      <ScoreBar ratio={t.ratio ?? 0} />
                      <span className="text-right tabular-nums">{pct(t.ratio)}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </li>
        ))}
      </ol>
      <FormDialog open={history} onOpenChange={setHistory} title={`Lịch sử · ${data.student.full_name}`} wide>
        <HistoryPanel related={data.student.id} />
      </FormDialog>
    </>
  );
}
