"use client";

import { PracticeButton } from "@/components/adaptive/PracticeButton";
import { PageHeader } from "@/components/app/PageHeader";
import { useStudentHomePage } from "@/hooks/page-hooks/student-home/use-student-home-page";
import { StudentAssignments } from "./StudentAssignments/StudentAssignments";

export function StudentHomePage() {
  const p = useStudentHomePage();
  return (
    <>
      <PageHeader title={p.title} description={p.orgName} actions={<PracticeButton />} />
      <StudentAssignments />
    </>
  );
}
