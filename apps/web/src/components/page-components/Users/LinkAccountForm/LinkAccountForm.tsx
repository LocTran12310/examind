"use client";

import { FormAlert } from "@/components/app/FormAlert";
import { FormField } from "@/components/app/FormField";
import { OptionSelect } from "@/components/app/OptionSelect";
import { Button } from "@/components/ui/button";
import { DialogFooter } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { ROLE_LABEL } from "@/constants/role.constant";
import { useLinkAccountForm } from "@/hooks/page-hooks/users/use-link-account-form";
import type { User } from "@/interfaces/user.interface";

const ROLES = (["teacher", "student", "org_admin"] as const).map((r) => ({ value: r, label: ROLE_LABEL[r] }));

/** Add an account that belongs to another organisation (org code + username), with a role here. */
export function LinkAccountForm({ onDone }: { onDone: (u: User) => void }) {
  const f = useLinkAccountForm(onDone);
  return (
    <form
      className="grid gap-4"
      onSubmit={(e) => {
        e.preventDefault();
        f.submit();
      }}
    >
      <p className="text-sm text-muted-foreground">Người này vẫn đăng nhập bằng tổ chức gốc, rồi chọn tổ chức này ở góc trên phải.</p>
      {f.message && !Object.keys(f.fields).length && <FormAlert>{f.message}</FormAlert>}
      <div className="grid grid-cols-2 gap-4">
        <FormField label="Mã tổ chức gốc" error={f.fields.org_code}>
          <Input value={f.orgCode} onChange={(e) => f.setOrgCode(e.target.value)} placeholder="ttb" required autoFocus />
        </FormField>
        <FormField label="Tên đăng nhập" error={f.fields.username}>
          <Input value={f.username} onChange={(e) => f.setUsername(e.target.value)} required />
        </FormField>
      </div>
      <FormField label="Vai trò ở tổ chức này">{(p) => <OptionSelect {...p} value={f.role} onValueChange={f.setRole} options={ROLES} />}</FormField>
      <DialogFooter>
        <Button type="submit" disabled={f.busy}>
          Thêm vào tổ chức
        </Button>
      </DialogFooter>
    </form>
  );
}
