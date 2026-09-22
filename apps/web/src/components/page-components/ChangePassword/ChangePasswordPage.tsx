"use client";

import { AlertCircle } from "lucide-react";
import { FormField } from "@/components/app/FormField";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useChangePasswordPage } from "@/hooks/page-hooks/change-password/use-change-password-page";

export function ChangePasswordPage() {
  const p = useChangePasswordPage();
  return (
    <main className="flex min-h-svh items-center justify-center bg-muted/40 p-4">
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle>Đổi mật khẩu</CardTitle>
          <CardDescription>Đặt mật khẩu mới để tiếp tục.</CardDescription>
        </CardHeader>
        <CardContent>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              p.submit();
            }}
            className="grid gap-4"
          >
            {p.error && (
              <Alert variant="destructive">
                <AlertCircle />
                <AlertDescription>{p.error}</AlertDescription>
              </Alert>
            )}
            <FormField label="Mật khẩu hiện tại" error={p.errors.current_password}>
              {(f) => <Input {...f} type="password" value={p.current} onChange={(e) => p.setCurrent(e.target.value)} required autoComplete="current-password" />}
            </FormField>
            <FormField label="Mật khẩu mới" error={p.errors.new_password} hint="Tối thiểu 8 ký tự">
              {(f) => <Input {...f} type="password" value={p.next} onChange={(e) => p.setNext(e.target.value)} required autoComplete="new-password" />}
            </FormField>
            <FormField label="Nhập lại mật khẩu mới" error={p.errors.confirm}>
              {(f) => <Input {...f} type="password" value={p.confirm} onChange={(e) => p.setConfirm(e.target.value)} required autoComplete="new-password" />}
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
