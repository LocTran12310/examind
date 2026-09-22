import { useState } from "react";
import { useMe } from "@/hooks/common/use-me";
import { useStudentRecordQuery } from "@/hooks/react-query/use-query-student";
import { ApiError } from "@/lib/common/http";

/** Hồ sơ học sinh: the record and the history dialog (org admins only). */
export function useStudentRecordPage(id: string) {
  const me = useMe();
  const record = useStudentRecordQuery(id);
  const [history, setHistory] = useState(false);
  return {
    data: record.data,
    error: record.error ? (record.error instanceof ApiError ? record.error.message : "Không tải được dữ liệu") : null,
    isAdmin: me.role === "org_admin",
    history,
    setHistory,
  };
}
