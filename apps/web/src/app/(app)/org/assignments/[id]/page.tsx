"use client";

import { use } from "react";
import { AssignmentReportPage } from "@/components/page-components/AssignmentReport/AssignmentReportPage";

export default function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  return <AssignmentReportPage id={id} />;
}
