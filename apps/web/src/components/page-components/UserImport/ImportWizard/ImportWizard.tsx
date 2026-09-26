"use client";

import { Checkbox } from "@/components/ui/checkbox";
import { cn } from "@/lib/utils";
import Link from "next/link";
import { FormAlert } from "@/components/common/FormAlert/FormAlert";
import { ToneBadge } from "@/components/common/ToneBadge/ToneBadge";
import { Button } from "@/components/ui/button";
import { Download } from "lucide-react";
import { FileDropField } from "@/components/common/FileDropField/FileDropField";
import { Label } from "@/components/ui/label";
import { Panel } from "@/components/common/Panel/Panel";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { ROLE_LABEL } from "@/constants/role.constant";
import { useImportWizard } from "@/hooks/page-hooks/user-import/use-import-wizard";

const IMPORT_ACCEPT = ".csv,.xlsx";
/** Static template in `public/`, its header being the columns the importer reads. */
const TEMPLATE_HREF = "/mau-nhap-tai-khoan.csv";

/** Upload a CSV/Excel file, check every row, create the valid accounts. */
export function ImportWizard({ orgCode }: { orgCode: string }) {
  const { file, preview, created, downloaded, skipErrors, setSkipErrors, hasErrors, canCommit, busy, error, onFile, commit, download } = useImportWizard(orgCode);

  if (created) {
    return (
      <Panel className="space-y-4">
        <FormAlert kind="success">Đã tạo {created.length} tài khoản.</FormAlert>
        <p className="text-sm text-muted-foreground">
          Tải file mật khẩu tạm ngay: danh sách chỉ hiển thị một lần và sẽ mất khi rời trang.
        </p>
        <div className="flex gap-2">
          <Button onClick={download}>
            Tải danh sách mật khẩu (CSV)
          </Button>
          <Link href="/org/users">
            <Button variant="outline">Về danh sách người dùng</Button>
          </Link>
        </div>
        {downloaded && <p className="text-sm text-emerald-700 dark:text-emerald-400">Đã tải file.</p>}
      </Panel>
    );
  }

  return (
    <div className="space-y-4">
      <Panel>
        <FileDropField
          label="Chọn file danh sách tài khoản"
          accept={IMPORT_ACCEPT}
          value={file}
          onChange={onFile}
          disabled={busy}
          testId="file"
          hint="Cột: Họ tên (bắt buộc), Tên đăng nhập, Vai trò, Lớp — đúng như file xuất ra, nên xuất rồi sửa rồi nhập lại được. Bỏ trống Tên đăng nhập để hệ thống tự tạo; Vai trò nhận Học sinh, Giáo viên, Quản trị trung tâm; một ô Lớp ghi nhiều lớp thì ngăn bằng dấu chấm phẩy. Tên cột tiếng Anh (full_name, username, role, class) vẫn nhận."
        >
          <a href={TEMPLATE_HREF} download className="inline-flex items-center gap-1 font-medium text-primary underline underline-offset-2">
            <Download className="size-3.5" /> Tải file mẫu (.csv)
          </a>
        </FileDropField>
        {busy && <p className="mt-2 text-sm text-muted-foreground">Đang xử lý…</p>}
      </Panel>
      {error && <FormAlert>{error}</FormAlert>}
      {preview && (
        <>
          <div className="flex flex-wrap items-center gap-3">
            <ToneBadge tone="green">{preview.valid_count} dòng hợp lệ</ToneBadge>
            {hasErrors && <ToneBadge tone="red">{preview.error_count} dòng lỗi</ToneBadge>}
            {hasErrors && (
              <Label className="font-normal">
                <Checkbox checked={skipErrors} onCheckedChange={(v) => setSkipErrors(v === true)} /> Bỏ qua các dòng lỗi
              </Label>
            )}
            <Button disabled={!canCommit || busy} onClick={commit} className="ml-auto">
              Tạo {skipErrors || !hasErrors ? preview.valid_count : preview.rows.length} tài khoản
            </Button>
          </div>
          {hasErrors && !skipErrors && <FormAlert kind="warning">Sửa file và tải lại, hoặc chọn bỏ qua các dòng lỗi. Chưa tài khoản nào được tạo.</FormAlert>}
          <div className="rounded-lg border bg-card">
<Table>
            <TableHeader>
              <TableRow>
                <TableHead>Dòng</TableHead>
                <TableHead>Họ tên</TableHead>
                <TableHead>Tên đăng nhập</TableHead>
                <TableHead>Vai trò</TableHead>
                <TableHead>Lớp</TableHead>
                <TableHead>Lỗi</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {preview.rows.map((r) => (
                <TableRow key={r.row} data-testid={`row-${r.row}`} className={cn(r.errors.length && "bg-destructive/10")}>
                  <TableCell>{r.row}</TableCell>
                  <TableCell>{r.full_name}</TableCell>
                  <TableCell className="font-mono">
                    {r.username}
                    {r.generated_username && <span className="ml-1 text-xs text-muted-foreground/70">(tự tạo)</span>}
                  </TableCell>
                  <TableCell>{ROLE_LABEL[r.role] ?? r.role}</TableCell>
                  <TableCell>{r.class}</TableCell>
                  <TableCell className="text-destructive">{r.errors.join("; ")}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
</div>
        </>
      )}
    </div>
  );
}
