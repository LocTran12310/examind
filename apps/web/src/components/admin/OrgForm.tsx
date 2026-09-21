"use client";

import { useState } from "react";
import { Alert, Button, CopyButton, Field, Input } from "@/components/ui";
import { api } from "@/lib/api";
import { useMutation } from "@/lib/hooks";
import type { Org, OrgCreated } from "@/lib/types";

export function OrgCreateForm({ onDone }: { onDone: () => void }) {
  const [code, setCode] = useState("");
  const [name, setName] = useState("");
  const [adminUsername, setAdminUsername] = useState("admin");
  const [created, setCreated] = useState<OrgCreated | null>(null);
  const m = useMutation();

  if (created) {
    return (
      <div className="space-y-3">
        <Alert tone="green">Đã tạo tổ chức {created.org.code}.</Alert>
        <p className="text-sm">Mật khẩu tạm của quản trị viên (chỉ hiển thị một lần):</p>
        <div className="flex items-center gap-2 rounded-md bg-gray-50 p-3 font-mono text-sm">
          <span data-testid="temp-cred">
            {created.org.code} / {created.admin.username} / {created.admin.temp_password}
          </span>
          <CopyButton text={`Tổ chức: ${created.org.code}\nTên đăng nhập: ${created.admin.username}\nMật khẩu: ${created.admin.temp_password}`} />
        </div>
        <div className="flex justify-end">
          <Button variant="primary" onClick={onDone}>
            Xong
          </Button>
        </div>
      </div>
    );
  }

  return (
    <form
      className="space-y-4"
      onSubmit={async (e) => {
        e.preventDefault();
        const r = await m.run(() => api<OrgCreated>("/admin/orgs", { body: { code, name, admin_username: adminUsername } }));
        if (r) setCreated(r);
      }}
    >
      {m.message && !Object.keys(m.fields).length && <Alert>{m.message}</Alert>}
      <Field label="Mã tổ chức" error={m.fields.code} hint="Dùng khi đăng nhập, ví dụ TrungtamA">
        <Input value={code} onChange={(e) => setCode(e.target.value)} invalid={!!m.fields.code} required />
      </Field>
      <Field label="Tên tổ chức" error={m.fields.name}>
        <Input value={name} onChange={(e) => setName(e.target.value)} required />
      </Field>
      <Field label="Tên đăng nhập quản trị viên" error={m.fields.admin_username}>
        <Input value={adminUsername} onChange={(e) => setAdminUsername(e.target.value)} required />
      </Field>
      <div className="flex justify-end">
        <Button variant="primary" type="submit" disabled={m.busy}>
          Tạo tổ chức
        </Button>
      </div>
    </form>
  );
}

export function OrgEditForm({ org, onDone }: { org: Org; onDone: () => void }) {
  const [code, setCode] = useState(org.code);
  const [name, setName] = useState(org.name);
  const m = useMutation();
  const codeChanged = code.trim().toLowerCase() !== org.code;
  return (
    <form
      className="space-y-4"
      onSubmit={async (e) => {
        e.preventDefault();
        const r = await m.run(() => api(`/admin/orgs/${org.id}`, { method: "PATCH", body: { code, name } }));
        if (r) onDone();
      }}
    >
      {m.message && !Object.keys(m.fields).length && <Alert>{m.message}</Alert>}
      <Field label="Mã tổ chức" error={m.fields.code}>
        <Input value={code} onChange={(e) => setCode(e.target.value)} disabled={org.is_system} />
      </Field>
      {codeChanged && <Alert tone="amber">Người dùng của tổ chức sẽ phải đăng nhập bằng mã mới.</Alert>}
      <Field label="Tên tổ chức" error={m.fields.name}>
        <Input value={name} onChange={(e) => setName(e.target.value)} />
      </Field>
      <div className="flex justify-end">
        <Button variant="primary" type="submit" disabled={m.busy}>
          Lưu
        </Button>
      </div>
    </form>
  );
}
