"use client";

import { use } from "react";
import { ClassDetailPage } from "@/components/page-components/ClassDetail/ClassDetailPage";

export default function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  return <ClassDetailPage id={id} />;
}
