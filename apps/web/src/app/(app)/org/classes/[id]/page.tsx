"use client";

import Link from "next/link";
import { use } from "react";
import { MemberManager } from "@/components/org/MemberManager";
import { PageHeader } from "@/components/ui";
import { useApi } from "@/lib/hooks";
import type { ClassDetail } from "@/lib/types";

export default function ClassPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { data, reload, error } = useApi<ClassDetail>(`/classes/${id}`);
  if (error) return <p className="text-sm text-red-700">{error}</p>;
  if (!data) return null;
  return (
    <>
      <Link href="/org/classes" className="text-sm text-gray-500 hover:underline">
        ← Lớp học
      </Link>
      <PageHeader title={`Lớp ${data.name}`} subtitle={`${data.school_year} · ${data.member_count} học sinh`} />
      <MemberManager detail={data} onChange={reload} />
    </>
  );
}
