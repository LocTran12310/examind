"use client";

import { useState } from "react";
import { FormAlert } from "@/components/app/FormAlert";
import { FormField } from "@/components/app/FormField";
import { OptionSelect } from "@/components/app/OptionSelect";
import { Button } from "@/components/ui/button";
import { DialogFooter } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";
import { useMutation } from "@/lib/hooks";
import { ROLE_LABEL, type User } from "@/lib/types";

const ROLES = (["teacher", "student", "org_admin"] as const).map((r) => ({ value: r, label: ROLE_LABEL[r] }));

/** Add an account that belongs to another organisation (org code + username), with a role here. */
export function LinkAccountForm({ onDone }: { onDone: (u: User) => void }) {
  const [orgCode, setOrgCode] = useState("");
  const [username, setUsername] = useState("");
  const [role, setRole] = useState("teacher");
  const m = useMutation();
  return (
    <form
      className="grid gap-4"
      onSubmit={async (e) => {
        e.preventDefault();
        const u = await m.run(() => api<User>("/users/link", { body: { org_code: orgCode, username, role } }));
        if (u) onDone(u);
      }}
    >
      <p className="text-sm text-muted-foreground">Người này vẫn đăng nhập bằng tổ chức gốc, rồi chọn tổ chức này ở góc trên phải.</p>
      {m.message && !Object.keys(m.fields).length && <FormAlert>{m.message}</FormAlert>}
      <div className="grid grid-cols-2 gap-4">
        <FormField label="Mã tổ chức gốc" error={m.fields.org_code}>
          <Input value={orgCode} onChange={(e) => setOrgCode(e.target.value)} placeholder="ttb" required autoFocus />
        </FormField>
        <FormField label="Tên đăng nhập" error={m.fields.username}>
          <Input value={username} onChange={(e) => setUsername(e.target.value)} required />
        </FormField>
      </div>
      <FormField label="Vai trò ở tổ chức này">{(f) => <OptionSelect {...f} value={role} onValueChange={setRole} options={ROLES} />}</FormField>
      <DialogFooter>
        <Button type="submit" disabled={m.busy}>
          Thêm vào tổ chức
        </Button>
      </DialogFooter>
    </form>
  );
}
