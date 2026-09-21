"use client";

import { useState } from "react";
import { Alert, Button, CopyButton, Field, Input, Select } from "@/components/ui";
import { api } from "@/lib/api";
import { useMutation } from "@/lib/hooks";
import { ROLE_LABEL, type Role, type User } from "@/lib/types";

export function rolesManagedBy(role: Role): Role[] {
  return role === "org_admin" ? ["student", "teacher", "org_admin"] : ["student"];
}

export function TempPassword({ username, password, orgCode }: { username: string; password: string; orgCode: string }) {
  return (
    <div className="space-y-2">
      <p className="text-sm">Mật khẩu tạm (chỉ hiển thị một lần, người dùng phải đổi khi đăng nhập):</p>
      <div className="flex items-center gap-2 rounded-md bg-gray-50 p-3 font-mono text-sm">
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
      <div className="space-y-4">
        <Alert tone="green">Đã tạo tài khoản.</Alert>
        <TempPassword username={created.username} password={created.password} orgCode={orgCode} />
        <div className="flex justify-end">
          <Button variant="primary" onClick={onDone}>
            Xong
          </Button>
        </div>
      </div>
    );

  return (
    <form
      className="space-y-4"
      onSubmit={async (e) => {
        e.preventDefault();
        const r = await m.run(() =>
          api<{ user: User; temp_password: string }>("/users", { body: { full_name: fullName, username: username || null, role } }),
        );
        if (r) setCreated({ username: r.user.username, password: r.temp_password });
      }}
    >
      {m.message && !Object.keys(m.fields).length && <Alert>{m.message}</Alert>}
      <Field label="Họ tên" error={m.fields.full_name}>
        <Input value={fullName} onChange={(e) => setFullName(e.target.value)} required />
      </Field>
      <Field label="Tên đăng nhập" error={m.fields.username} hint="Để trống để tự tạo từ họ tên">
        <Input value={username} onChange={(e) => setUsername(e.target.value)} />
      </Field>
      {roles.length > 1 && (
        <Field label="Vai trò">
          <Select value={role} onChange={(e) => setRole(e.target.value as Role)} className="w-full">
            {roles.map((r) => (
              <option key={r} value={r}>
                {ROLE_LABEL[r]}
              </option>
            ))}
          </Select>
        </Field>
      )}
      <div className="flex justify-end">
        <Button variant="primary" type="submit" disabled={m.busy}>
          Tạo tài khoản
        </Button>
      </div>
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
      className="space-y-4"
      onSubmit={async (e) => {
        e.preventDefault();
        const body: Record<string, unknown> = { full_name: fullName, email };
        if (myRole === "org_admin") body.role = role;
        const r = await m.run(() => api(`/users/${user.id}`, { method: "PATCH", body }));
        if (r) onDone();
      }}
    >
      {m.message && !Object.keys(m.fields).length && <Alert>{m.message}</Alert>}
      <Field label="Tên đăng nhập">
        <Input value={user.username} disabled />
      </Field>
      <Field label="Họ tên" error={m.fields.full_name}>
        <Input value={fullName} onChange={(e) => setFullName(e.target.value)} required />
      </Field>
      <Field label="Email" error={m.fields.email}>
        <Input value={email} onChange={(e) => setEmail(e.target.value)} type="email" />
      </Field>
      {myRole === "org_admin" && (
        <Field label="Vai trò">
          <Select value={role} onChange={(e) => setRole(e.target.value as Role)} className="w-full">
            {rolesManagedBy(myRole).map((r) => (
              <option key={r} value={r}>
                {ROLE_LABEL[r]}
              </option>
            ))}
          </Select>
        </Field>
      )}
      <div className="flex justify-end">
        <Button variant="primary" type="submit" disabled={m.busy}>
          Lưu
        </Button>
      </div>
    </form>
  );
}
