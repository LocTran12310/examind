"use client";

import { use } from "react";
import { StudentRecordPage } from "@/components/page-components/StudentRecord/StudentRecordPage";

export default function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  return <StudentRecordPage id={id} />;
}
