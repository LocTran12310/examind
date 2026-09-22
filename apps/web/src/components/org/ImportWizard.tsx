"use client";

import { Checkbox } from "@/components/ui/checkbox";
import { cn } from "@/lib/utils";
import Link from "next/link";
import { useState } from "react";
import { FormAlert } from "@/components/app/FormAlert";
import { ToneBadge } from "@/components/app/ToneBadge";
import { Button } from "@/components/ui/button";
import { FormField } from "@/components/app/FormField";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Panel } from "@/components/app/Panel";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { api, ApiError } from "@/lib/api";
import { downloadText, toCsv } from "@/lib/csv";
import { ROLE_LABEL, type Credential, type ImportRow } from "@/lib/types";

interface Preview {
  rows: ImportRow[];
  valid_count: number;
  error_count: number;
}

export function ImportWizard({ orgCode }: { orgCode: string }) {
  const [preview, setPreview] = useState<Preview | null>(null);
  const [skipErrors, setSkipErrors] = useState(false);
  const [created, setCreated] = useState<Credential[] | null>(null);
  const [downloaded, setDownloaded] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onFile(file: File | undefined) {
    if (!file) return;
    setError(null);
    setPreview(null);
    setBusy(true);
    const form = new FormData();
    form.append("file", file);
    try {
      setPreview(await api<Preview>("/users/import/preview", { form }));
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Không đọc được file");
    } finally {
      setBusy(false);
    }
  }

  async function commit() {
    if (!preview) return;
    const rows = preview.rows.filter((r) => !r.errors.length);
    setBusy(true);
    setError(null);
    try {
      const r = await api<{ created: Credential[] }>("/users/import/commit", { body: { rows } });
      setCreated(r.created);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Có lỗi xảy ra");
    } finally {
      setBusy(false);
    }
  }

  function download() {
    if (!created) return;
    const rows = created.map((c) => ({ ...c, org: orgCode, role: c.role ? ROLE_LABEL[c.role] : "" }));
    downloadText(
      `tai-khoan-${orgCode}.csv`,
      toCsv(rows, [
        ["full_name", "Họ tên"],
        ["class", "Lớp"],
        ["org", "Tổ chức"],
        ["username", "Tên đăng nhập"],
        ["temp_password", "Mật khẩu tạm"],
      ]),
    );
    setDownloaded(true);
  }

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

  const hasErrors = !!preview?.error_count;
  const canCommit = !!preview && preview.valid_count > 0 && (!hasErrors || skipErrors);

  return (
    <div className="space-y-4">
      <Panel>
        <FormField label="Chọn file">
          <Input data-testid="file" type="file" accept=".csv,.xlsx" className="max-w-sm" onChange={(e) => onFile(e.target.files?.[0])} />
        </FormField>
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
