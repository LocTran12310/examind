"use client";

import { StudentHome } from "@/components/exams/StudentHome";
import { PageHeader } from "@/components/ui";
import { useMe } from "../AppShell";

export default function HomePage() {
  const me = useMe();
  return (
    <>
      <PageHeader title={`Xin chào, ${me.full_name}`} subtitle={me.org.name} />
      <StudentHome />
    </>
  );
}
