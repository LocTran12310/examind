"use client";

import { PageHeader } from "@/components/common/PageHeader/PageHeader";
import { useMe } from "@/hooks/common/use-me";
import { ImportWizard } from "./ImportWizard/ImportWizard";

export function UserImportPage() {
  const me = useMe();
  return (
    <>
      <PageHeader title="Nhập tài khoản từ file" description="CSV hoặc Excel: cột full_name (bắt buộc), username, role, class" />
      <ImportWizard orgCode={me.org.code} />
    </>
  );
}
