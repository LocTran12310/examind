"use client";

import { AlertCircle } from "lucide-react";
import { FormField } from "@/components/app/FormField";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useLoginForm } from "@/hooks/page-hooks/login/use-login-form";
import type { Me } from "@/interfaces/auth.interface";

export function LoginForm({ onSuccess }: { onSuccess?: (me: Me) => void }) {
  const f = useLoginForm(onSuccess);
  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        f.submit();
      }}
      className="grid gap-4"
    >
      {f.error && (
        <Alert variant="destructive">
          <AlertCircle />
          <AlertDescription>{f.error}</AlertDescription>
        </Alert>
      )}
      <FormField label="Tổ chức">
        {(p) => <Input {...p} name="org_code" autoComplete="organization" placeholder="TrungtamA" value={f.org} onChange={(e) => f.setOrg(e.target.value)} required />}
      </FormField>
      <FormField label="Tên đăng nhập">
        {(p) => <Input {...p} name="username" autoComplete="username" value={f.username} onChange={(e) => f.setUsername(e.target.value)} required />}
      </FormField>
      <FormField label="Mật khẩu">
        {(p) => <Input {...p} name="password" type="password" autoComplete="current-password" value={f.password} onChange={(e) => f.setPassword(e.target.value)} required />}
      </FormField>
      <Button type="submit" className="w-full" disabled={f.busy}>
        {f.busy ? "Đang đăng nhập…" : "Đăng nhập"}
      </Button>
    </form>
  );
}
