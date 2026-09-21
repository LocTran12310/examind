"use client";

import { useEffect, useState } from "react";
import { Alert, Button, Field, Input } from "@/components/ui";
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
    <form onSubmit={submit} className="space-y-4">
      {error && <Alert>{error}</Alert>}
      <Field label="Tổ chức">
        <Input name="org_code" autoComplete="organization" placeholder="TrungtamA" value={org} onChange={(e) => setOrg(e.target.value)} required />
      </Field>
      <Field label="Tên đăng nhập">
        <Input name="username" autoComplete="username" value={username} onChange={(e) => setUsername(e.target.value)} required />
      </Field>
      <Field label="Mật khẩu">
        <Input name="password" type="password" autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} required />
      </Field>
      <Button variant="primary" type="submit" className="w-full" disabled={busy}>
        {busy ? "Đang đăng nhập…" : "Đăng nhập"}
      </Button>
    </form>
  );
}
