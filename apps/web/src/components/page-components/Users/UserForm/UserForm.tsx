"use client";

import { FormAlert } from "@/components/app/FormAlert";
import { FormField } from "@/components/app/FormField";
import { OptionSelect } from "@/components/app/OptionSelect";
import { Button } from "@/components/ui/button";
import { DialogFooter } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { useUserCreateForm, useUserEditForm } from "@/hooks/page-hooks/users/use-user-form";
import type { Role } from "@/interfaces/auth.interface";
import type { User } from "@/interfaces/user.interface";
import { TempPassword } from "../TempPassword/TempPassword";

export function UserCreateForm({ myRole, orgCode, onDone }: { myRole: Role; orgCode: string; onDone: () => void }) {
  const f = useUserCreateForm(myRole);

  if (f.created)
    return (
      <div className="grid gap-4">
        <FormAlert kind="success">Đã tạo tài khoản.</FormAlert>
        <TempPassword username={f.created.username} password={f.created.password} orgCode={orgCode} />
        <DialogFooter>
          <Button onClick={onDone}>Xong</Button>
        </DialogFooter>
      </div>
    );

  return (
    <form
      className="grid gap-4"
      onSubmit={(e) => {
        e.preventDefault();
        f.submit();
      }}
    >
      {f.message && !Object.keys(f.fields).length && <FormAlert>{f.message}</FormAlert>}
      <FormField label="Họ tên" error={f.fields.full_name}>
        {(p) => <Input {...p} value={f.fullName} onChange={(e) => f.setFullName(e.target.value)} required />}
      </FormField>
      <FormField label="Tên đăng nhập" error={f.fields.username} hint="Để trống để tự tạo từ họ tên">
        {(p) => <Input {...p} value={f.username} onChange={(e) => f.setUsername(e.target.value)} />}
      </FormField>
      {f.roles.length > 1 && (
        <FormField label="Vai trò">
          {(p) => <OptionSelect {...p} value={f.role} onValueChange={(v) => f.setRole(v as Role)} options={f.roleOptions} />}
        </FormField>
      )}
      <DialogFooter>
        <Button type="submit" disabled={f.busy}>
          Tạo tài khoản
        </Button>
      </DialogFooter>
    </form>
  );
}

export function UserEditForm({ user, myRole, onDone }: { user: User; myRole: Role; onDone: () => void }) {
  const f = useUserEditForm(user, myRole, onDone);
  return (
    <form
      className="grid gap-4"
      onSubmit={(e) => {
        e.preventDefault();
        f.submit();
      }}
    >
      {f.message && !Object.keys(f.fields).length && <FormAlert>{f.message}</FormAlert>}
      <FormField label="Tên đăng nhập">{(p) => <Input {...p} value={user.username} disabled />}</FormField>
      <FormField label="Họ tên" error={f.fields.full_name}>
        {(p) => <Input {...p} value={f.fullName} onChange={(e) => f.setFullName(e.target.value)} required />}
      </FormField>
      <FormField label="Email" error={f.fields.email}>
        {(p) => <Input {...p} value={f.email} onChange={(e) => f.setEmail(e.target.value)} type="email" />}
      </FormField>
      {f.admin && (
        <FormField label="Vai trò">{(p) => <OptionSelect {...p} value={f.role} onValueChange={(v) => f.setRole(v as Role)} options={f.roleOptions} />}</FormField>
      )}
      <DialogFooter>
        <Button type="submit" disabled={f.busy}>
          Lưu
        </Button>
      </DialogFooter>
    </form>
  );
}
