"use client";

import { useState } from "react";
import { AlertCircle } from "lucide-react";
import { FormField } from "@/components/app/FormField";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
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
    <main className="flex min-h-svh items-center justify-center bg-muted/40 p-4">
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle>Đổi mật khẩu</CardTitle>
          <CardDescription>Đặt mật khẩu mới để tiếp tục.</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={submit} className="grid gap-4">
            {error && (
              <Alert variant="destructive">
                <AlertCircle />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}
            <FormField label="Mật khẩu hiện tại" error={errors.current_password}>
              {(f) => <Input {...f} type="password" value={current} onChange={(e) => setCurrent(e.target.value)} required autoComplete="current-password" />}
            </FormField>
            <FormField label="Mật khẩu mới" error={errors.new_password} hint="Tối thiểu 8 ký tự">
              {(f) => <Input {...f} type="password" value={next} onChange={(e) => setNext(e.target.value)} required autoComplete="new-password" />}
            </FormField>
            <FormField label="Nhập lại mật khẩu mới" error={errors.confirm}>
              {(f) => <Input {...f} type="password" value={confirm} onChange={(e) => setConfirm(e.target.value)} required autoComplete="new-password" />}
            </FormField>
            <Button type="submit" className="w-full">
              Lưu mật khẩu
            </Button>
          </form>
        </CardContent>
      </Card>
    </main>
  );
}
