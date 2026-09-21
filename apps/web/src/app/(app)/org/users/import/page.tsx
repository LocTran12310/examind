"use client";

import { useMe } from "@/app/(app)/AppShell";
import { ImportWizard } from "@/components/org/ImportWizard";
import { PageHeader } from "@/components/ui";

export default function ImportPage() {
  const me = useMe();
  return (
    <>
      <PageHeader title="Nhập tài khoản từ file" subtitle="CSV hoặc Excel: cột full_name (bắt buộc), username, role, class" />
      <ImportWizard orgCode={me.org.code} />
    </>
  );
}
