"use client";

import { useEffect, useState } from "react";
import { AlertCircle } from "lucide-react";
import { FormField } from "@/components/app/FormField";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api, ApiError } from "@/lib/api";
import { homeFor } from "@/lib/nav";
import type { Me } from "@/lib/types";

export const ORG_KEY = "examind.org_code";

function readOrg(): string {
  try {
    return localStorage.getItem(ORG_KEY) ?? "";
  } catch {
    return "";
  }
}

export function LoginForm({ onSuccess }: { onSuccess?: (me: Me) => void }) {
  const [org, setOrg] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => setOrg(readOrg()), []);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const me = await api<Me>("/auth/login", { body: { org_code: org, username, password } });
      try {
        localStorage.setItem(ORG_KEY, org);
      } catch {}
      if (onSuccess) onSuccess(me);
      else window.location.assign(me.must_change_password ? "/change-password" : homeFor(me.role));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Không kết nối được máy chủ");
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={submit} className="grid gap-4">
      {error && (
        <Alert variant="destructive">
          <AlertCircle />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}
      <FormField label="Tổ chức">
        {(f) => <Input {...f} name="org_code" autoComplete="organization" placeholder="TrungtamA" value={org} onChange={(e) => setOrg(e.target.value)} required />}
      </FormField>
      <FormField label="Tên đăng nhập">
        {(f) => <Input {...f} name="username" autoComplete="username" value={username} onChange={(e) => setUsername(e.target.value)} required />}
      </FormField>
      <FormField label="Mật khẩu">
        {(f) => <Input {...f} name="password" type="password" autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} required />}
      </FormField>
      <Button type="submit" className="w-full" disabled={busy}>
        {busy ? "Đang đăng nhập…" : "Đăng nhập"}
      </Button>
    </form>
  );
}
