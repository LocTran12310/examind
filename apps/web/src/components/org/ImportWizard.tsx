"use client";

import clsx from "clsx";
import Link from "next/link";
import { useState } from "react";
import { Alert, Badge, Button, Card, Table, td, th } from "@/components/ui";
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
      <Card className="space-y-4">
        <Alert tone="green">Đã tạo {created.length} tài khoản.</Alert>
        <p className="text-sm text-gray-600">
          Tải file mật khẩu tạm ngay: danh sách chỉ hiển thị một lần và sẽ mất khi rời trang.
        </p>
        <div className="flex gap-2">
          <Button variant="primary" onClick={download}>
            Tải danh sách mật khẩu (CSV)
          </Button>
          <Link href="/org/users">
            <Button>Về danh sách người dùng</Button>
          </Link>
        </div>
        {downloaded && <p className="text-sm text-green-700">Đã tải file.</p>}
      </Card>
    );
  }

  const hasErrors = !!preview?.error_count;
  const canCommit = !!preview && preview.valid_count > 0 && (!hasErrors || skipErrors);

  return (
    <div className="space-y-4">
      <Card>
        <label className="block text-sm font-medium">
          Chọn file
          <input
            data-testid="file"
            type="file"
            accept=".csv,.xlsx"
            className="mt-2 block text-sm"
            onChange={(e) => onFile(e.target.files?.[0])}
          />
        </label>
        {busy && <p className="mt-2 text-sm text-gray-500">Đang xử lý…</p>}
      </Card>
      {error && <Alert>{error}</Alert>}
      {preview && (
        <>
          <div className="flex flex-wrap items-center gap-3">
            <Badge tone="green">{preview.valid_count} dòng hợp lệ</Badge>
            {hasErrors && <Badge tone="red">{preview.error_count} dòng lỗi</Badge>}
            {hasErrors && (
              <label className="flex items-center gap-2 text-sm">
                <input type="checkbox" checked={skipErrors} onChange={(e) => setSkipErrors(e.target.checked)} /> Bỏ qua các dòng lỗi
              </label>
            )}
            <Button variant="primary" disabled={!canCommit || busy} onClick={commit} className="ml-auto">
              Tạo {skipErrors || !hasErrors ? preview.valid_count : preview.rows.length} tài khoản
            </Button>
          </div>
          {hasErrors && !skipErrors && <Alert tone="amber">Sửa file và tải lại, hoặc chọn bỏ qua các dòng lỗi. Chưa tài khoản nào được tạo.</Alert>}
          <Table>
            <thead className="bg-gray-50">
              <tr>
                <th className={th}>Dòng</th>
                <th className={th}>Họ tên</th>
                <th className={th}>Tên đăng nhập</th>
                <th className={th}>Vai trò</th>
                <th className={th}>Lớp</th>
                <th className={th}>Lỗi</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {preview.rows.map((r) => (
                <tr key={r.row} data-testid={`row-${r.row}`} className={clsx(r.errors.length && "bg-red-50")}>
                  <td className={td}>{r.row}</td>
                  <td className={td}>{r.full_name}</td>
                  <td className={`${td} font-mono`}>
                    {r.username}
                    {r.generated_username && <span className="ml-1 text-xs text-gray-400">(tự tạo)</span>}
                  </td>
                  <td className={td}>{ROLE_LABEL[r.role] ?? r.role}</td>
                  <td className={td}>{r.class}</td>
                  <td className={`${td} text-red-700`}>{r.errors.join("; ")}</td>
                </tr>
              ))}
            </tbody>
          </Table>
        </>
      )}
    </div>
  );
}
