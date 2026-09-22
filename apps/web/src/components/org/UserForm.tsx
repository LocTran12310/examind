"use client";

import { useState } from "react";
import { CopyButton } from "@/components/app/CopyButton";
import { FormAlert } from "@/components/app/FormAlert";
import { FormField } from "@/components/app/FormField";
import { OptionSelect } from "@/components/app/OptionSelect";
import { Button } from "@/components/ui/button";
import { DialogFooter } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";
import { useMutation } from "@/lib/hooks";
import { ROLE_LABEL, type Role, type User } from "@/lib/types";

export function rolesManagedBy(role: Role): Role[] {
  return role === "org_admin" ? ["student", "teacher", "org_admin"] : ["student"];
}

const roleOptions = (role: Role) => rolesManagedBy(role).map((r) => ({ value: r, label: ROLE_LABEL[r] }));

export function TempPassword({ username, password, orgCode }: { username: string; password: string; orgCode: string }) {
  return (
    <div className="grid gap-2">
      <p className="text-sm">Mật khẩu tạm (chỉ hiển thị một lần, người dùng phải đổi khi đăng nhập):</p>
      <div className="flex items-center justify-between gap-2 rounded-md bg-muted p-3 font-mono text-sm">
        <span data-testid="temp-cred">
          {orgCode} / {username} / {password}
        </span>
        <CopyButton text={`Tổ chức: ${orgCode}\nTên đăng nhập: ${username}\nMật khẩu: ${password}`} />
      </div>
    </div>
  );
}

export function UserCreateForm({ myRole, orgCode, onDone }: { myRole: Role; orgCode: string; onDone: () => void }) {
  const roles = rolesManagedBy(myRole);
  const [fullName, setFullName] = useState("");
  const [username, setUsername] = useState("");
  const [role, setRole] = useState<Role>("student");
  const [created, setCreated] = useState<{ username: string; password: string } | null>(null);
  const m = useMutation();

  if (created)
    return (
      <div className="grid gap-4">
        <FormAlert kind="success">Đã tạo tài khoản.</FormAlert>
        <TempPassword username={created.username} password={created.password} orgCode={orgCode} />
        <DialogFooter>
          <Button onClick={onDone}>Xong</Button>
        </DialogFooter>
      </div>
    );

  return (
    <form
      className="grid gap-4"
      onSubmit={async (e) => {
        e.preventDefault();
        const r = await m.run(() => api<{ user: User; temp_password: string }>("/users", { body: { full_name: fullName, username: username || null, role } }));
        if (r) setCreated({ username: r.user.username, password: r.temp_password });
      }}
    >
      {m.message && !Object.keys(m.fields).length && <FormAlert>{m.message}</FormAlert>}
      <FormField label="Họ tên" error={m.fields.full_name}>
        {(f) => <Input {...f} value={fullName} onChange={(e) => setFullName(e.target.value)} required />}
      </FormField>
      <FormField label="Tên đăng nhập" error={m.fields.username} hint="Để trống để tự tạo từ họ tên">
        {(f) => <Input {...f} value={username} onChange={(e) => setUsername(e.target.value)} />}
      </FormField>
      {roles.length > 1 && (
        <FormField label="Vai trò">
          {(f) => <OptionSelect {...f} value={role} onValueChange={(v) => setRole(v as Role)} options={roleOptions(myRole)} />}
        </FormField>
      )}
      <DialogFooter>
        <Button type="submit" disabled={m.busy}>
          Tạo tài khoản
        </Button>
      </DialogFooter>
    </form>
  );
}

export function UserEditForm({ user, myRole, onDone }: { user: User; myRole: Role; onDone: () => void }) {
  const [fullName, setFullName] = useState(user.full_name);
  const [email, setEmail] = useState(user.email ?? "");
  const [role, setRole] = useState<Role>(user.role);
  const m = useMutation();
  return (
    <form
      className="grid gap-4"
      onSubmit={async (e) => {
        e.preventDefault();
        const body: Record<string, unknown> = { full_name: fullName, email };
        if (myRole === "org_admin") body.role = role;
        const r = await m.run(() => api(`/users/${user.id}`, { method: "PATCH", body }));
        if (r) onDone();
      }}
    >
      {m.message && !Object.keys(m.fields).length && <FormAlert>{m.message}</FormAlert>}
      <FormField label="Tên đăng nhập">{(f) => <Input {...f} value={user.username} disabled />}</FormField>
      <FormField label="Họ tên" error={m.fields.full_name}>
        {(f) => <Input {...f} value={fullName} onChange={(e) => setFullName(e.target.value)} required />}
      </FormField>
      <FormField label="Email" error={m.fields.email}>
        {(f) => <Input {...f} value={email} onChange={(e) => setEmail(e.target.value)} type="email" />}
      </FormField>
      {myRole === "org_admin" && (
        <FormField label="Vai trò">{(f) => <OptionSelect {...f} value={role} onValueChange={(v) => setRole(v as Role)} options={roleOptions(myRole)} />}</FormField>
      )}
      <DialogFooter>
        <Button type="submit" disabled={m.busy}>
          Lưu
        </Button>
      </DialogFooter>
    </form>
  );
}
