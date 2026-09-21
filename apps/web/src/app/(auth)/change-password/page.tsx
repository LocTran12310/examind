"use client";

import { useState } from "react";
import { Alert, Button, Card, Field, Input } from "@/components/ui";
import { api, ApiError } from "@/lib/api";
import { homeFor } from "@/lib/nav";
import type { Me } from "@/lib/types";

export default function ChangePasswordPage() {
  const [current, setCurrent] = useState("");
  const [next, setNext] = useState("");
  const [confirm, setConfirm] = useState("");
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setErrors({});
    setError(null);
    if (next !== confirm) return setErrors({ confirm: "Mật khẩu nhập lại không khớp" });
    try {
      await api("/auth/change-password", { body: { current_password: current, new_password: next } });
      const me = await api<Me>("/auth/me");
      window.location.assign(homeFor(me.role));
    } catch (err) {
      if (err instanceof ApiError && err.fields) setErrors(err.fields);
      else setError(err instanceof ApiError ? err.message : "Có lỗi xảy ra");
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center p-4">
      <Card className="w-full max-w-sm">
        <h1 className="mb-1 text-lg font-semibold">Đổi mật khẩu</h1>
        <p className="mb-4 text-sm text-gray-500">Bạn cần đặt mật khẩu mới trước khi tiếp tục.</p>
        <form onSubmit={submit} className="space-y-4">
          {error && <Alert>{error}</Alert>}
          <Field label="Mật khẩu hiện tại" error={errors.current_password}>
            <Input type="password" value={current} onChange={(e) => setCurrent(e.target.value)} required autoComplete="current-password" />
          </Field>
          <Field label="Mật khẩu mới" error={errors.new_password} hint="Tối thiểu 8 ký tự">
            <Input type="password" value={next} onChange={(e) => setNext(e.target.value)} required autoComplete="new-password" />
          </Field>
          <Field label="Nhập lại mật khẩu mới" error={errors.confirm}>
            <Input type="password" value={confirm} onChange={(e) => setConfirm(e.target.value)} required autoComplete="new-password" />
          </Field>
          <Button variant="primary" type="submit" className="w-full">
            Lưu mật khẩu
          </Button>
        </form>
      </Card>
    </main>
  );
}
