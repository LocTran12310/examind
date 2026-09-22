import { useState } from "react";
import { ROLE_LABEL } from "@/constants/role.constant";
import { useImportCommitMutation, useImportPreviewMutation } from "@/hooks/react-query/use-query-user";
import { ApiError } from "@/lib/common/http";
import { downloadText, toCsv } from "@/lib/csv";

const message = (e: unknown, fallback: string) => (e ? (e instanceof ApiError ? e.message : fallback) : null);

/** File → checked rows → create the valid ones → download the temporary passwords (shown only once). */
export function useImportWizard(orgCode: string) {
  const [skipErrors, setSkipErrors] = useState(false);
  const [downloaded, setDownloaded] = useState(false);
  const preview = useImportPreviewMutation();
  const commit = useImportCommitMutation();
  const rows = preview.data;
  const created = commit.data?.created ?? null;
  const hasErrors = !!rows?.error_count;
  return {
    preview: rows,
    created,
    downloaded,
    skipErrors,
    setSkipErrors,
    hasErrors,
    canCommit: !!rows && rows.valid_count > 0 && (!hasErrors || skipErrors),
    busy: preview.isPending || commit.isPending,
    error: message(preview.error, "Không đọc được file") ?? message(commit.error, "Có lỗi xảy ra"),
    onFile: (file: File | undefined) => {
      if (!file) return;
      commit.reset();
      preview.mutate(file);
    },
    commit: () => rows && commit.mutate(rows.rows.filter((r) => !r.errors.length)),
    download: () => {
      if (!created) return;
      const out = created.map((c) => ({ ...c, org: orgCode, role: c.role ? ROLE_LABEL[c.role] : "" }));
      downloadText(
        `tai-khoan-${orgCode}.csv`,
        toCsv(out, [
          ["full_name", "Họ tên"],
          ["class", "Lớp"],
          ["org", "Tổ chức"],
          ["username", "Tên đăng nhập"],
          ["temp_password", "Mật khẩu tạm"],
        ]),
      );
      setDownloaded(true);
    },
  };
}
