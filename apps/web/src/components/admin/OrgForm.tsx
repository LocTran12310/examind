"use client";

import { useState } from "react";
import { CopyButton } from "@/components/app/CopyButton";
import { FormAlert } from "@/components/app/FormAlert";
import { FormField } from "@/components/app/FormField";
import { Button } from "@/components/ui/button";
import { DialogFooter } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
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
      <div className="grid gap-3">
        <FormAlert kind="success">Đã tạo tổ chức {created.org.code}.</FormAlert>
        <p className="text-sm">Mật khẩu tạm của quản trị viên (chỉ hiển thị một lần):</p>
        <div className="flex items-center justify-between gap-2 rounded-md bg-muted p-3 font-mono text-sm">
          <span data-testid="temp-cred">
            {created.org.code} / {created.admin.username} / {created.admin.temp_password}
          </span>
          <CopyButton text={`Tổ chức: ${created.org.code}\nTên đăng nhập: ${created.admin.username}\nMật khẩu: ${created.admin.temp_password}`} />
        </div>
        <DialogFooter>
          <Button onClick={onDone}>Xong</Button>
        </DialogFooter>
      </div>
    );
  }

  return (
    <form
      className="grid gap-4"
      onSubmit={async (e) => {
        e.preventDefault();
        const r = await m.run(() => api<OrgCreated>("/admin/orgs", { body: { code, name, admin_username: adminUsername } }));
        if (r) setCreated(r);
      }}
    >
      {m.message && !Object.keys(m.fields).length && <FormAlert>{m.message}</FormAlert>}
      <FormField label="Mã tổ chức" error={m.fields.code} hint="Dùng khi đăng nhập, ví dụ TrungtamA">
        {(f) => <Input {...f} value={code} onChange={(e) => setCode(e.target.value)} required />}
      </FormField>
      <FormField label="Tên tổ chức" error={m.fields.name}>
        {(f) => <Input {...f} value={name} onChange={(e) => setName(e.target.value)} required />}
      </FormField>
      <FormField label="Tên đăng nhập quản trị viên" error={m.fields.admin_username}>
        {(f) => <Input {...f} value={adminUsername} onChange={(e) => setAdminUsername(e.target.value)} required />}
      </FormField>
      <DialogFooter>
        <Button type="submit" disabled={m.busy}>
          Tạo tổ chức
        </Button>
      </DialogFooter>
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
      className="grid gap-4"
      onSubmit={async (e) => {
        e.preventDefault();
        const r = await m.run(() => api(`/admin/orgs/${org.id}`, { method: "PATCH", body: { code, name } }));
        if (r) onDone();
      }}
    >
      {m.message && !Object.keys(m.fields).length && <FormAlert>{m.message}</FormAlert>}
      <FormField label="Mã tổ chức" error={m.fields.code}>
        {(f) => <Input {...f} value={code} onChange={(e) => setCode(e.target.value)} disabled={org.is_system} />}
      </FormField>
      {codeChanged && <FormAlert kind="warning">Người dùng của tổ chức sẽ phải đăng nhập bằng mã mới.</FormAlert>}
      <FormField label="Tên tổ chức" error={m.fields.name}>
        {(f) => <Input {...f} value={name} onChange={(e) => setName(e.target.value)} />}
      </FormField>
      <DialogFooter>
        <Button type="submit" disabled={m.busy}>
          Lưu
        </Button>
      </DialogFooter>
    </form>
  );
}
