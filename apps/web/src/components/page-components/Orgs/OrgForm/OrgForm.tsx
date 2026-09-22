"use client";

import { CopyButton } from "@/components/app/CopyButton";
import { FormAlert } from "@/components/app/FormAlert";
import { FormField } from "@/components/app/FormField";
import { Button } from "@/components/ui/button";
import { DialogFooter } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { useOrgCreateForm, useOrgEditForm } from "@/hooks/page-hooks/orgs/use-org-form";
import type { Org } from "@/interfaces/org.interface";

export function OrgCreateForm({ onDone }: { onDone: () => void }) {
  const f = useOrgCreateForm();
  const created = f.created;

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
      onSubmit={(e) => {
        e.preventDefault();
        f.submit();
      }}
    >
      {f.message && !Object.keys(f.fields).length && <FormAlert>{f.message}</FormAlert>}
      <FormField label="Mã tổ chức" error={f.fields.code} hint="Dùng khi đăng nhập, ví dụ TrungtamA">
        {(p) => <Input {...p} value={f.code} onChange={(e) => f.setCode(e.target.value)} required />}
      </FormField>
      <FormField label="Tên tổ chức" error={f.fields.name}>
        {(p) => <Input {...p} value={f.name} onChange={(e) => f.setName(e.target.value)} required />}
      </FormField>
      <FormField label="Tên đăng nhập quản trị viên" error={f.fields.admin_username}>
        {(p) => <Input {...p} value={f.adminUsername} onChange={(e) => f.setAdminUsername(e.target.value)} required />}
      </FormField>
      <DialogFooter>
        <Button type="submit" disabled={f.busy}>
          Tạo tổ chức
        </Button>
      </DialogFooter>
    </form>
  );
}

export function OrgEditForm({ org, onDone }: { org: Org; onDone: () => void }) {
  const f = useOrgEditForm(org, onDone);
  return (
    <form
      className="grid gap-4"
      onSubmit={(e) => {
        e.preventDefault();
        f.submit();
      }}
    >
      {f.message && !Object.keys(f.fields).length && <FormAlert>{f.message}</FormAlert>}
      <FormField label="Mã tổ chức" error={f.fields.code}>
        {(p) => <Input {...p} value={f.code} onChange={(e) => f.setCode(e.target.value)} disabled={org.is_system} />}
      </FormField>
      {f.codeChanged && <FormAlert kind="warning">Người dùng của tổ chức sẽ phải đăng nhập bằng mã mới.</FormAlert>}
      <FormField label="Tên tổ chức" error={f.fields.name}>
        {(p) => <Input {...p} value={f.name} onChange={(e) => f.setName(e.target.value)} />}
      </FormField>
      <DialogFooter>
        <Button type="submit" disabled={f.busy}>
          Lưu
        </Button>
      </DialogFooter>
    </form>
  );
}
