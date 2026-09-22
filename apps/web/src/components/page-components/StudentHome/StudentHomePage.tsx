"use client";

import { PracticeButton } from "@/components/common/PracticeButton/PracticeButton";
import { PageHeader } from "@/components/common/PageHeader/PageHeader";
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
