"use client";

import { useMe } from "@/app/(app)/AppShell";
import { ImportWizard } from "@/components/org/ImportWizard";
import { PageHeader } from "@/components/app/PageHeader";

export default function ImportPage() {
  const me = useMe();
  return (
    <>
      <PageHeader title="Nhập tài khoản từ file" description="CSV hoặc Excel: cột full_name (bắt buộc), username, role, class" />
      <ImportWizard orgCode={me.org.code} />
    </>
  );
}
