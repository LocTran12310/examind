"use client";

import { use } from "react";
import { StudentRecord } from "@/components/students/StudentRecord";

export default function StudentRecordPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  return <StudentRecord id={id} />;
}
