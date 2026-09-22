import { useState } from "react";
import { useCreateOrgMutation, useUpdateOrgMutation } from "@/hooks/react-query/use-query-org";
import type { Org } from "@/interfaces/org.interface";
import { formErrors } from "@/lib/common/form-errors";

/** A new org with its first admin; the admin's temporary password is shown once. */
export function useOrgCreateForm() {
  const [code, setCode] = useState("");
  const [name, setName] = useState("");
  const [adminUsername, setAdminUsername] = useState("admin");
  const create = useCreateOrgMutation();
  const { fields, message } = formErrors(create.error);
  return {
    code,
    setCode,
    name,
    setName,
    adminUsername,
    setAdminUsername,
    created: create.data ?? null,
    busy: create.isPending,
    fields,
    message,
    submit: () => create.mutate({ code, name, admin_username: adminUsername }),
  };
}

/** Rename an org or change its code (its users then sign in with the new code). */
export function useOrgEditForm(org: Org, onDone: () => void) {
  const [code, setCode] = useState(org.code);
  const [name, setName] = useState(org.name);
  const update = useUpdateOrgMutation();
  const { fields, message } = formErrors(update.error);
  return {
    code,
    setCode,
    name,
    setName,
    codeChanged: code.trim().toLowerCase() !== org.code,
    busy: update.isPending,
    fields,
    message,
    submit: () => update.mutate({ id: org.id, body: { code, name } }, { onSuccess: onDone }),
  };
}
